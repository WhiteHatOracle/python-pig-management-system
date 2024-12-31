from flask import Flask, render_template, url_for, redirect, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, DecimalField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
from datetime import timedelta
# from decouple import config

# Initalize Flask app
app = Flask(__name__)

# Load configuration from enviroment variables
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'supercalifragilisticexpialidocious'
app.config['PERMANT_SESSION_LIFETIME'] = timedelta(minutes = 30) # auto-logout after inactivity

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

# Home route
@app.route('/')
def home():
    return render_template('home.html')  # Displays Homepage

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

# Run the app
if __name__ == '__main__':
    app.run(debug=True)