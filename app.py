from flask import Flask, render_template, url_for, redirect, flash, make_response, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, DecimalField, TextAreaField
from wtforms.validators import InputRequired, Length, ValidationError, DataRequired
from flask_bcrypt import Bcrypt
from datetime import timedelta
import datetime

# Initalize Flask app
app = Flask(__name__)

# Load configuration from enviroment variables
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'supercalifragilisticexpialidocious'
app.config['PERMANT_SESSION_LIFETIME'] = timedelta(minutes = 30) # auto-logout after inactivity

# Make `enumerate` available in Jinja2 templates
app.jinja_env.globals.update(enumerate=enumerate)

# Initalize database, bcrypt and login manager
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "signin" # Redirect here if unauthorized access is attempted

# Load user for login management
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Define User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable = False, unique=True, index = True) # Indexed for quick lookup
    password = db.Column(db.String(80), nullable = False)

# Define registration form
class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min = 4, max = 20)], render_kw={"Placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min = 4, max = 20)], render_kw={"Placeholder": "Password"})
    submit = SubmitField("Register")

    # Custom Validator to check for existing username
    def validate_username(self, username):
        existing_user_name = User.query.filter_by(username = username.data).first()
        if existing_user_name:
            raise ValidationError('The username alredy exists. Please choose a different username')

# Define login form
class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min = 4, max = 20)], render_kw={"Placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min = 4, max = 20)], render_kw={"Placeholder": "Password"})
    remember = BooleanField("Remember Me") # Optional remember me checkbox
    submit = SubmitField("Login")

# Define feed calculation form
class FeedCalculatorForm(FlaskForm):
    days = IntegerField(validators=[InputRequired()], render_kw=({"Placeholder": "Number of days (e.g 21)"}))
    feed = StringField(validators=[InputRequired(),Length(min = 4, max = 20)], render_kw=({"Placeholder":"Feed Name(e.g weaner)"}))
    feed_cost = DecimalField(validators=[InputRequired()], render_kw=({"Placeholder":"Cost of Concentrate(e.g 850)"}))
    num3_meal_cost = DecimalField(validators=[InputRequired()], render_kw=({"Placeholder":"Cost of Number 3 Meal(e.g 5.35)"}))
    pigs = IntegerField(validators=[InputRequired()], render_kw=({"Placeholder":"Number of pigs(e.g 4)"}))
    feed_consumption = DecimalField(validators=[InputRequired()], render_kw=({"Placeholder":"Feed consumption per animal(e.g 1.5)"}))
    submit = SubmitField("Calculate")

# Define Invoice generator form
class InvoiceGeneratorForm(FlaskForm):
    company = StringField(validators=[InputRequired(), Length(min=4, max=50)], render_kw={"placeholder": "Company Name"})
    firstBandRange = StringField(validators=[InputRequired(), Length(min=4, max=10)], render_kw={"placeholder": "e.g., 65-109.9"})
    firstBandPrice = DecimalField(validators=[InputRequired()], render_kw={"placeholder": "60.0 or 60"})
    secondBandRange = StringField(validators=[InputRequired(), Length(min=4, max=10)], render_kw={"placeholder": "e.g., 65-109.9"})
    secondBandPrice = DecimalField(validators=[InputRequired()], render_kw={"placeholder": "60.0 or 60"})
    thirdBandRange = StringField(validators=[InputRequired(), Length(min=4, max=10)], render_kw={"placeholder": "e.g., 65-109.9"})
    thirdBandPrice = DecimalField(validators=[InputRequired()], render_kw={"placeholder": "60.0 or 60"})
    weights = TextAreaField(validators=[DataRequired()], render_kw={"placeholder": "e.g., 56.7, 71.5, 66.75, 69.7, ..."})
    submit = SubmitField("Generate Invoice")

# Utility function to parse weight ranges/ this is for the invoice generator
def parse_range(range_str):
    try:
        min_weight, max_weight = map(float, range_str.split('-'))
        return min_weight, max_weight
    except ValueError:
        return None, None

@app.route('/home', methods=['GET','POST'])
def home():
    return render_template('home.html')

# login route
@app.route('/')
def login():
    return render_template('login.html')  # Displays Homepage

# Sign in route
@app.route('/signin', methods=['GET', 'POST'])
def signin():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data) # Log in the user
                return redirect(url_for('dashboard'))
            else:
                flash("Invalid Password, Please try again.", "Error") # Invalid password feedback
        else:
            flash("User does not exist. Please register.","Error") # User not found feedback
    return render_template('signin.html', form=form)

# Logout route
@app.route('/logout', methods=['POST','GET'])
@login_required
def logout():
    logout_user() # Logout the current user
    flash("You have been logged out.","Success")
    return redirect(url_for('signin'))

# Dashboard route(requires login)
@app.route('/dashboard', methods=['GET','POST'])
@login_required
def dashboard():
    return render_template('dashboard.html') # Dashboard for logged in users

# Signup route
@app.route('/signup', methods = ['GET', 'POST'])
def signup():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8') # Hash the password
        new_user = User(username=form.username.data, password=hashed_password)
        try:
            db.session.add(new_user)
            db.session.commit() 
            flash("Registration sucessful! Please Log in.", "Success")
            return redirect(url_for('signin'))
        except Exception as e:
            db.session.rollback()
            flash("An error occurred during registration. Please try again.", "Error")
    return render_template('signup.html', form = form)

# Feed management route
@app.route('/calculate', methods=['GET','POST'])
def calculate():
    # Get input data from the frontend
    form = FeedCalculatorForm()
    result = None #initialize result
    if form.validate_on_submit():
        # Perform calculations
        total_feed = form.days.data * form.pigs.data * float(form.feed_consumption.data)

        concentrates = round(0.4 * total_feed)
        num_of_bags = round(concentrates / 50)
        conc_cost = num_of_bags * float(form.feed_cost.data)

        num3_meal = round(0.6 * total_feed, 2)
        num3_meal_total_cost = num3_meal * float(form.num3_meal_cost.data)

        total_cost = conc_cost + num3_meal_total_cost

        # Prepare the result
        result = {
            "totalFeed": total_feed,
            "numOfBags": num_of_bags,
            "concCost": conc_cost,
            "num3Meal": num3_meal,
            "num3MealTotalCost": num3_meal_total_cost,
            "totalCost": total_cost,
            "feed": form.feed.data,
            "pigs": form.pigs.data,
            "days": form.days.data
        }
    return render_template('feed-calculator.html', form = form, result = result)

# Invoice Generator route
@app.route('/invoice-generator', methods=['GET','POST'])
def invoice_Generator():
    form = InvoiceGeneratorForm()
    if form.validate_on_submit():
        company_name = form.company.data
        weights = [float(w.strip()) for w in form.weights.data.split(',')]

        # Parse weight ranges and prices
        first_min, first_max = parse_range(form.firstBandRange.data)
        first_price = form.firstBandPrice.data

        second_min, second_max = parse_range(form.secondBandRange.data)
        second_price = form.secondBandPrice.data

        third_min, third_max = parse_range(form.thirdBandRange.data)
        third_price = form.thirdBandPrice.data

        # Calculate prices based on weights
        invoice_data = []
        total_cost = 0

        for weight in weights:
            if first_min <= weight <= first_max:
                price = float(first_price)
            elif second_min <= weight <= second_max:
                price = float(second_price)
            elif third_min <= weight <= third_max:
                price = float(third_price)
            else:
                price = 0  # Weight falls outside defined ranges

            cost = weight * price
            total_cost += cost
            invoice_data.append({
                    "weight": round(weight, 2),
                    "formatted_weight": f"{weight}kg",
                    "price": price,  # Keep raw price
                    "formatted_price": f"K{price:,.2f}",  # Format price as currency
                    "cost": cost,  # Keep raw cost
                    "formatted_cost": f"K{cost:,.2f}"  # Format cost as currency
                })
        return render_template('invoiceGenerator.html', 
                               form=form, 
                               company_name=company_name,
                               invoice_data=invoice_data, 
                               total_cost=f"K{total_cost:,.2f}")

    return render_template('invoiceGenerator.html', form=form)


@app.route('/download-invoice', methods=['POST'])
def download_invoice():
    company_name = request.form.get("company_name")
    invoice_data = eval(request.form.get("invoice_data"))  # Parse invoice data passed from the form
    total_cost = float(request.form.get("total_cost").replace("K", "").replace(",", ""))
    
    invoice_number = f"INV-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    pdf = generate_invoice_pdf(company_name, invoice_number, invoice_data, total_cost)
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename={invoice_number}.pdf'
    return response

from fpdf import FPDF

def generate_invoice_pdf(company_name, invoice_number, invoice_data, total_cost):
    class PDF(FPDF):
        def header(self):
            self.set_font("Arial", "B", 14)
            self.cell(0, 10, "Invoice", align="C", ln=True)
            self.ln(10)

        def footer(self):
            self.set_y(-15)
            self.set_font("Arial", "I", 8)
            self.cell(0, 10, f"Page {self.page_no()}", align="C")

    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Title and Header Section
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, f"Invoice Number: {invoice_number}", ln=True)
    pdf.cell(0, 10, f"Company Name: {company_name}", ln=True)
    pdf.cell(0, 10, f"Date: {datetime.datetime.now().strftime('%Y-%m-%d')}", ln=True)
    pdf.ln(10)

    # Table Header
    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(10, 10, "#", border=1, align="C", fill=True)
    pdf.cell(60, 10, "Weight (kg)", border=1, align="C", fill=True)
    pdf.cell(60, 10, "Price per Kg (K)", border=1, align="C", fill=True)
    pdf.cell(60, 10, "Cost (K)", border=1, align="C", fill=True)
    pdf.ln()

    # Table Data
    pdf.set_font("Arial", size=10)
    for idx, item in enumerate(invoice_data, start=1):
        pdf.cell(10, 10, str(idx), border=1, align="C")
        pdf.cell(60, 10, item["formatted_weight"], border=1, align="C")
        pdf.cell(60, 10, item["formatted_price"], border=1, align="C")
        pdf.cell(60, 10, item["formatted_cost"], border=1, align="C")
        pdf.ln()

    # Total Cost
    pdf.set_font("Arial", "B", 12)
    pdf.ln(5)
    pdf.cell(130, 10, "Total Cost:", border=0, align="R")
    pdf.cell(60, 10, f"K{total_cost:,.2f}", border=1, align="C")
    pdf.ln(40)

    # Signatures Section
    pdf.set_font("Arial", "B", 10)
    pdf.cell(90, 10, "Received by: ____________________________", border=0, ln=0)
    pdf.cell(90, 10, "Supplied by: ____________________________", border=0, ln=1)
    pdf.ln(10)
    pdf.cell(90, 10, "Signature: ____________________________", border=0, ln=0)
    pdf.cell(90, 10, "Signature: ____________________________", border=0, ln=1)

    # Footer Section
    pdf.set_font("Arial", "I", 8)
    pdf.cell(0, 10, "Thank you for your business!", align="C", ln=True)

    return pdf.output(dest='S').encode('latin1')

@app.route("/sow-manager", methods=['GET','POST'])
def sows():
    return render_template('sows.html')

# Run the app
if __name__ == '__main__':
    # app.run(debug=True)
    app.run(host="0.0.0.0", port=5000, debug=True)