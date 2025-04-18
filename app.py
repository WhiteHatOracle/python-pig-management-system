from sqlalchemy.exc import IntegrityError
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, login_required, logout_user
<<<<<<< HEAD
from datetime import timedelta
=======
from datetime import timedelta, date
>>>>>>> 0fa0214ccb7a74187a76fd79acbe8c13625e627d
from flask import Flask, render_template, url_for, redirect, flash, make_response, request, jsonify
from dash import dcc, html, dash_table
from fpdf import FPDF
import datetime
import dash
from sqlalchemy.exc import IntegrityError
import dash_bootstrap_components as dbc
from sqlalchemy import func
from dash.exceptions import PreventUpdate
# Import models and db
from models import db, Litter, User, Boars, Sows, ServiceRecords, Invoice, Expense
# Import the forms
from forms import LitterForm, SowForm, BoarForm, RegisterForm, LoginForm, FeedCalculatorForm, InvoiceGeneratorForm, ServiceRecordForm, ExpenseForm, CompleteFeedForm

# Initialize Flask app
app = Flask(__name__)
# Initialize Dash app
dash_app = dash.Dash(
    __name__, 
    server=app,
    url_base_pathname='/dashboard_internal/',  # This sets the base path for Dash
    external_stylesheets=[dbc.themes.BOOTSTRAP, "/static/css/dashboard.css"])


# Load configuration from environment variables
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'supercalifragilisticexpialidocious' 
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

# Make `enumerate` available in Jinja2 templates
app.jinja_env.globals.update(enumerate=enumerate)

# Initialize database, bcrypt, and login manager
db.init_app(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "signin"  # Redirect here if unauthorized access is attempted

# Load user for login management
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Your routes and application logic go here...

# Utility function to parse weight ranges/ this is for the invoice generator
def parse_range(range_str):
    try:
        min_weight, max_weight = map(float, range_str.split('-'))
        return min_weight, max_weight
    except ValueError:
        return None, None

# Funnction to fetch data
def get_pig_counts():
    num_sows = Sows.query.count()
    boars = Boars.query.count()
    pokers = 98
    total_pigs = num_sows + boars + pokers   
    return total_pigs, num_sows, boars, pokers

# Function to Fetch Sow Service Records for Table
def get_sow_service_records():
    # Get latest service record for each sow
    subquery = db.session.query(
        ServiceRecords.sow_id,
        db.func.max(ServiceRecords.service_date).label("latest_service")
    ).group_by(ServiceRecords.sow_id).subquery()

    # Query service_records and join with sows to get the actual sowID
    query = db.session.query(ServiceRecords, Sows.sowID).join(
        subquery,
        (ServiceRecords.sow_id == subquery.c.sow_id) & 
        (ServiceRecords.service_date == subquery.c.latest_service)
    ).join(Sows, ServiceRecords.sow_id == Sows.id)  # Correct table join

    # Optionally filter records based on due_date
    query = query.filter(ServiceRecords.due_date >= datetime.date.today()).order_by(ServiceRecords.due_date)

    records = query.all()
    # Convert query results into a list of dictionaries for Dash DataTable
    data = [
        {
            "sow_id": record[1],  # Sow's actual sowID from the sows table
            "service_date": record[0].service_date.strftime("%d-%b-%Y"),
            "litter_guard1_date": record[0].litter_guard1_date.strftime("%d-%b-%Y") if record[0].litter_guard1_date else "",
            "litter_guard2_date": record[0].litter_guard2_date.strftime("%d-%b-%Y") if record[0].litter_guard2_date else "",
            "due_date": record[0].due_date.strftime("%d-%b-%Y") if record[0].due_date else "",
        }
        for record in records
    ]    
    return data

# Dashboard Layout
dash_app.layout = dbc.Container([
    html.Div([
        # Row for Summary Cards
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H4("Total Pigs"), 
                    html.H2(id="total-pigs")
                    ],className = "dash-card")
            ], color="transparent", inverse=True, style={"border": "none", "boxShadow": "none"})),

            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H4("Total Sows"),
                    html.H2(id="total-sows")
                    ],className = "dash-card")
            ], color="transparent", inverse=True, style={"border": "none", "boxShadow": "none"})),

            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H4("Total Boars"), 
                    html.H2(id="total-boars")
                    ],className = "dash-card")
            ], color="transparent", inverse=True, style={"border": "none", "boxShadow": "none"})),

            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H4("Total Births"), 
                    html.H2(id="total-porkers")
                    ],className = "dash-card")
            ], color="transparent", inverse=True, style={"border": "none", "boxShadow": "none"})),

            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H4("Pre-Weaners"), 
                    html.H2(id="pre_weaners")
                    ],className = "dash-card")
            ], color="transparent", inverse=True, style={"border": "none", "boxShadow": "none"})),

            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H4("Weaners"), 
                    html.H2(id="weaners")
                    ],className = "dash-card")
            ], color="transparent", inverse=True, style={"border": "none", "boxShadow": "none"})),

            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H4("Growers"), 
                    html.H2(id="growers")
                    ],className = "dash-card")
            ], color="transparent", inverse=True, style={"border": "none", "boxShadow": "none"})),

            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H4("Finishers"), 
                    html.H2(id="finishers")
                    ],className = "dash-card")
            ], color="transparent", inverse=True, style={"border": "none", "boxShadow": "none"})),

        ], className="card-grid"),

        html.Hr(),

        html.H3("Upcoming Farrowings"),
        # Table for Sow Service Records
        dash_table.DataTable(
            id="sow-service-table",
            # className='sow-service-table',
            columns=[
                {"name": "Sow ID", "id": "sow_id"},  # Now correctly shows sowID
                {"name": "Service Date", "id": "service_date"},
                {"name": "First Litter Guard", "id": "litter_guard1_date"},
                {"name": "Second Litter Guard", "id": "litter_guard2_date"},
                {"name": "Due Date", "id": "due_date"},
            ],
                sort_action="native",
                style_table={
                    'width': '100%', 
                    'backdropFilter': 'blur(10px)',# Apply backdrop blur
                    'overflowX': 'auto',
                },  
                style_header={
                    'backgroundColor': '#4CAF50',
                    'color': 'white',
                    'textAlign': 'center',
                    'fontWeight': 'bold'
                },
                style_cell={
                    'border': '1px solid #ddd',
                    'padding': '8px',
                    'textAlign': 'center',
                    'fontFamily': 'Arial, sans-serif'
                },
                style_data_conditional=[{
                    'if': {'column_id': 'due_date'},
                    'color': '#082d06',
                    'fontWeight': 'bold'
                },{
                    'if': {'row_index': 'odd'},  # Zebra striping effect
                    'backgroundColor': '#5bdc4c',
                    'color': 'white'
                }],
                css=[{
                    "selector": ".dash-table-container", 
                    "rule": "border-collapse: collapse !important;"},
                   {"selector": "tbody tr:hover", 
                    "rule": "background-color: #ddd !important;"
                }]
        ),

        dcc.Interval(
            id="interval-update",
            interval=30 * 1000, # Updates every 30 seconds
            n_intervals=0
        ),
         dcc.Location(id='url', refresh=True),
    ], className="dashboard-wrapper"),
], fluid=True)

# Callback to Update Data
@dash_app.callback([
        dash.Output("total-pigs", "children"),
        dash.Output("total-sows", "children"),
        dash.Output("total-boars", "children"),
        dash.Output("total-porkers", "children"),
        dash.Output("pre_weaners", "children"),
        dash.Output("weaners", "children"),
        dash.Output("growers", "children"),
        dash.Output("finishers", "children"),
        dash.Output("sow-service-table", "data")
    ],
    [
        dash.Input("interval-update", "n_intervals")
    ],
    
)
def update_dashboard(n):
    try:
        total_pigs, total_sows, total_boars, total_porkers, pre_weaners, weaners, growers, finishers = get_total_counts()
        service_records = get_sow_service_records()
        return (
            str(total_pigs),
            str(total_sows),
            str(total_boars),
            str(total_porkers),
            str(pre_weaners),
            str(weaners),
            str(growers),
            str(finishers),
            service_records
        )
    
    except Exception as e:
        print("Error updating dashboard:", e)
        return "Error", "Error", "Error", "Error", []

def get_total_counts():
    today=date.today()

    try:
        # Fetch counts from database
        total_sows = db.session.query(Sows.id).count()  # Count total sows from Sows table
        total_boars = db.session.query(Boars.id).count()  # Count total boars from Boars table
        total_porkers = db.session.query(func.sum(Litter.bornAlive)).scalar() or 0 # Placeholder (Replace if you have a Porkers table)
                # Pre-weaners (0–20 days)
        pre_weaners = db.session.query(func.sum(Litter.bornAlive)) \
            .filter(Litter.farrowDate >= today - timedelta(days=20)) \
            .scalar() or 0

        # Weaners (21–91 days)
        weaners = db.session.query(func.sum(Litter.bornAlive)) \
            .filter(Litter.farrowDate >= today - timedelta(days=91)) \
            .filter(Litter.farrowDate < today - timedelta(days=20)) \
            .scalar() or 0

        # Growers (92–112 days)
        growers = db.session.query(func.sum(Litter.bornAlive)) \
            .filter(Litter.farrowDate >= today - timedelta(days=112)) \
            .filter(Litter.farrowDate < today - timedelta(days=91)) \
            .scalar() or 0

        # Finishers (113+ days)
        finishers = db.session.query(func.sum(Litter.bornAlive)) \
            .filter(Litter.farrowDate < today - timedelta(days=112)) \
            .scalar() or 0

        # Compute total pigs after defining all variables
        total_porkers = pre_weaners + weaners + finishers + growers
        total_pigs = total_sows + total_boars + total_porkers
        return total_pigs, total_sows, total_boars, total_porkers, pre_weaners, weaners, growers, finishers,

    except Exception as e:
        print("Error in get_total_counts:", e)
        return 0, 0, 0, 0  # Return zeroes if there is an error


# Flask Route for Dash App (to embed in iframe)
@app.route("/dashboard/")
def dashboard():
    return render_template("dashboard.html")
    # return flask.redirect("/dashboard_internal/")

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
    return redirect(url_for('login'))

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
    return render_template('signup.html', form=form)

@app.route('/complete-feeds-calculator', methods=['GET','POST'])
@login_required
def complete_feeds():
    #Get input from the front end
    form = CompleteFeedForm()
    result = None #initialize result
    if form.validate_on_submit():
        #perfom calculations
        dailyConsumption = form.numberOfPigs.data * float(form.consumption.data)
        total_feed = dailyConsumption * form.numberOfDays.data
        num_of_bags = round(total_feed/50)
        total_cost = num_of_bags*form.costOfFeed.data

        result={
            "totalFeed": total_feed,
            "numOfBags": num_of_bags,
            "totalCost": total_cost,
            "totalFeed": total_feed,
            "numOfDays": form.numberOfDays.data,
            "numOfPigs": form.numberOfPigs.data,
            "feed": form.feedName.data
        }

    return render_template('complete-feeds.html', form=form, result=result)


# Feed management route
@app.route('/calculate', methods=['GET','POST'])
@login_required
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
@login_required
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
        total_weight = sum(weights)
        average_weight = total_weight / len(weights) if weights else 0
        total_pigs = len(weights)
        print(total_pigs)

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
                    "formatted_cost": f"K{cost:,.2f}",  # Format cost as currency
                    "Number_of_Pigs": f"K{total_pigs}",
                })
        return render_template('invoiceGenerator.html', 
                               form=form, 
                               company_name=company_name,
                               invoice_data=invoice_data, 
                               total_pigs=total_pigs,
                               total_cost=f"K{total_cost:,.2f}",
                               total_weight=f"{total_weight:,.2f}Kg",
                               average_weight = f"{average_weight:,.2f}Kg"
                               )

    return render_template('invoiceGenerator.html', form=form)

@app.route('/download-invoice', methods=['POST'])
@login_required
def download_invoice():
    invoice_data = eval(request.form.get("invoice_data"))  # Parse invoice data passed from the form
    company_name = request.form.get("company_name")
    total_weight = float(request.form.get("total_weight").replace("Kg", "").replace(",", ""))
    average_weight = float(request.form.get("average_weight").replace("Kg", "").replace(",",""))
    total_cost = float(request.form.get("total_cost").replace("K", "").replace(",", ""))
    total_pigs = int(request.form.get("total_pigs"))
    #generate unique invoice number
    invoice_number = f"INV-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    #store invoice data in db just before downloading
    new_invoice = Invoice(
        invoice_number=invoice_number,
        num_of_pigs=total_pigs,
        company_name=company_name,
        date=datetime.datetime.now().date(),
        total_weight=total_weight,
        average_weight=average_weight,
        total_price=total_cost
    )
    db.session.add(new_invoice)
    db.session.commit()

    pdf = generate_invoice_pdf(company_name, invoice_number, invoice_data, total_weight, average_weight, total_cost)
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename={invoice_number}.pdf'
    return response

def generate_invoice_pdf(company_name, invoice_number, invoice_data, total_weight, average_weight, total_cost):
    class PDF(FPDF):
        def header(self):
            self.set_font("Arial", "B", 20)
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
    pdf.cell(0, 10, f"Date: {datetime.datetime.now().strftime('%d-%b-%Y')}", ln=True)
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

    # Total weight
    pdf.set_font("Arial","B", 12)
    pdf.ln(5)
    pdf.cell(130,10,"Total Weight:", border=0,align="R")
    pdf.cell(60, 10, f"{total_weight:,.2f}Kg", border=1, align="C")
    pdf.ln(8)

    #Average weight
    pdf.set_font("Arial","B",12)
    pdf.ln(5)
    pdf.cell(130, 10,"Average Weight:", border=0, align="R")
    pdf.cell(60,10,f"{average_weight:,.2f}Kg",border=1,align="C")
    pdf.ln(5)

    # Total Cost
    pdf.set_font("Arial", "B", 12)
    pdf.ln(8)
    pdf.cell(130, 10, "Total Cost:", border=0, align="R")
    pdf.cell(60, 10, f"K{total_cost:,.2f}", border=1, align="C")
    pdf.ln(20)


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

@app.route('/invoices', methods=['GET','POST'])
@login_required
def invoices():
    invoices = Invoice.query.order_by(Invoice.date.desc()).all()  # Get all invoices, newest first
    
    return render_template('invoices.html', invoices=invoices)

@app.route('/invoice_totals', methods=['GET'])
@login_required
def invoice_totals():
    total_weight = db.session.query(db.func.sum(Invoice.total_weight)).scalar() or 0
    total_revenue = db.session.query(db.func.sum(Invoice.total_price)).scalar() or 0
    avg_weight = db.session.query(db.func.avg(Invoice.average_weight)).scalar() or 0
<<<<<<< HEAD
=======
    total_pigs = db.session.query(db.func.sum(Invoice.num_of_pigs)).scalar() or 0
>>>>>>> 0fa0214ccb7a74187a76fd79acbe8c13625e627d

    return jsonify({
        'total_weight': f"{total_weight:,.2f}Kg",
        'total_revenue': f"K{total_revenue:,.2f}",
<<<<<<< HEAD
        'average_weight': f"{avg_weight:,.2f}Kg"
=======
        'average_weight': f"{avg_weight:,.2f}Kg",
        'total_pigs': f"{total_pigs:,.2f}"
>>>>>>> 0fa0214ccb7a74187a76fd79acbe8c13625e627d
    })

# Delete Invoice Route
@app.route('/delete-invoice/<int:invoice_id>', methods=['POST'])
@login_required
def delete_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    db.session.delete(invoice)
    db.session.commit()
    flash('Invoice deleted successfully', 'success')
    return redirect(url_for('invoices'))

@app.route('/boar-manager', methods=['GET','POST'])
@login_required
def boars():
    form = BoarForm()

    if form.validate_on_submit():
        boar_id = form.BoarId.data.upper()
        breed = form.Breed.data.upper()
        boar_dob = form.DOB.data

        # check if boar already exists
        if Boars.query.filter_by(BoarId = boar_id).first():
            flash('Boar ID already exists! Please use a different ID.', 'error')
        
        else:
            #add boar to the database
            try:
                new_boar = Boars(BoarId = boar_id, DOB = boar_dob, Breed=breed)
                db.session.add(new_boar)
                db.session.commit()
                flash('Boar added successfully!', 'success')
                return redirect(url_for('boars'))
            except IntegrityError:
                db.session.rollback()
                flash(f'Boar with ID {boar_id} already exists!', 'error')
            except Exception as e:
                db.session.rollback()
                flash(f'An error occurred: {str(e)}', 'error')

    boars = Boars.query.all()
    return render_template('boars.html', boars=boars, form=form)  
  
@app.route('/delete-boar/<string:BoarId>', methods=['POST'])
@login_required
def delete_boar(BoarId):
    boar = Boars.query.filter_by(BoarId = BoarId.upper()).first()
    if not boar:
        flash('Boar not found!', 'error')
        return redirect(url_for('boars'))

    try:
        db.session.delete(boar)
        db.session.commit()
        flash('Boar deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting boar: {str(e)}', 'error')

    return redirect(url_for('boars'))

@app.route('/edit-boar/<int:boar_id>', methods=['GET', 'POST'])
@login_required
def edit_boar(boar_id):

    boar = Boars.query.get_or_404(boar_id)
    form = BoarForm(obj=boar)  # Pre-fill form with existing data
    form.boar_id = boar.id #prevents false validation errors

    if form.validate_on_submit():

        # Update the boar with new values
        boar.BoarId = form.BoarId.data.upper()
        boar.Breed = form.Breed.data.upper()
        boar.DOB = form.DOB.data

        try:
            db.session.commit()
            flash('Boar updated successfully!', 'success')
            return redirect(url_for('boars'))  # Redirect to the main boar manager
        except IntegrityError:
            db.session.rollback()
            flash(f'Boar with ID {boar.boarId} already exists!', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'error')

    return render_template('edit_boar.html', form=form, boar=boar)

@app.route('/sow-manager', methods=['GET', 'POST'])
@login_required
def sows():
    form = SowForm()

    if form.validate_on_submit():
        sow_id = form.sowID.data.upper()
        breed = form.Breed.data.upper()
        dob_str = form.DOB.data

        try:
            # Add sow to the database
            new_sow = Sows(sowID=sow_id, DOB=dob_str, Breed=breed)
            db.session.add(new_sow)
            db.session.commit()
            flash('Sow added successfully!', 'success')
            return redirect(url_for('sows'))
        except IntegrityError:
            db.session.rollback()
            flash(f'Sow with ID {sow_id} already exists!', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'error')

    sows = Sows.query.all()
    return render_template('sows.html', sows=sows, form=form)

@app.route('/edit-sow/<int:sow_id>', methods=['GET', 'POST'])
@login_required
def edit_sow(sow_id):

    sow = Sows.query.get_or_404(sow_id)
    form = SowForm(obj=sow)  # Pre-fill form with existing data
    form.sow_id = sow.id #prevents false validation errors

    if form.validate_on_submit():

        # Update the sow with new values
        sow.sowID = form.sowID.data.upper()
        sow.Breed = form.Breed.data.upper()
        sow.DOB = form.DOB.data

        try:
            db.session.commit()
            flash('Sow updated successfully!', 'success')
            return redirect(url_for('sows'))  # Redirect to the main sow manager
        except IntegrityError:
            db.session.rollback()
            flash(f'Sow with ID {sow.sowID} already exists!', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'error')

    return render_template('edit_sow.html', form=form, sow=sow)

@app.route('/delete-sow/<string:sow_id>', methods=['POST','GET'])
@login_required
def delete_sow(sow_id):
    sow = Sows.query.filter_by(sowID=sow_id).first()
    if not sow:
        flash('Sow not found!', 'error')
        return redirect(url_for('sows'))

    db.session.delete(sow)
    db.session.commit()
    flash('Sow deleted successfully!', 'success')
    return redirect(url_for('sows'))

@app.route('/sows/<int:sow_id>', methods=['GET', 'POST'])
@login_required
def sow_service_records(sow_id):
    sow = Sows.query.get_or_404(sow_id)
    form = ServiceRecordForm()

    if form.validate_on_submit():  # Checks if the form was submitted and is valid
        service_date = form.service_date.data
        boar_used = form.boar_used.data.upper()

        # Calculate other dates
        checkup_date = service_date + timedelta(days=21)
        litter_guard1_date = service_date + timedelta(days=68)
        feed_up_date = service_date + timedelta(days=90)
        litter_guard2_date = service_date + timedelta(days=100)
        action_date = service_date + timedelta(days=109)
        due_date = service_date + timedelta(days=114)

        # Create and add new service record
        new_record = ServiceRecords(
            sow_id=sow.id,
            service_date=service_date,
            boar_used=boar_used,
            checkup_date=checkup_date,
            litter_guard1_date=litter_guard1_date,
            litter_guard2_date=litter_guard2_date,
            feed_up_date=feed_up_date,
            due_date=due_date,
            action_date=action_date
        )

        db.session.add(new_record)
        db.session.commit()
        flash('Service record added successfully!', 'success')
        return redirect(url_for('sow_service_records', sow_id=sow.id))

    return render_template('sow_service_records.html', sow=sow, form=form)

def get_litter_stage(farrow_date):
    age_days = (date.today() - farrow_date).days
    if age_days < 21:
        return 'pre-weaning'
    elif age_days < 85:
        return 'weaner'
    elif age_days < 113:
        return 'grower'
    else:
        return 'finisher'

@app.route('/litter-records/<int:service_id>', methods=['POST','GET'])
@login_required
def litter_records(service_id):
    form = LitterForm()
    serviceRecord = ServiceRecords.query.get_or_404(service_id)
    sow_id = serviceRecord.sow_id

        # Fetch all litters for this service record
    litters = Litter.query.filter_by(service_record_id=service_id).all()

    # Attach dynamic stage info to each litter (not saved to DB)
    for litter in litters:
        litter.stage = get_litter_stage(litter.farrowDate)

    if form.validate_on_submit():
        farrowDate = form.farrowDate.data
        totalBorn = form.totalBorn.data
        bornAlive = form.bornAlive.data
        stillBorn = form.stillBorn.data
        weights = [float(w.strip()) for w in form.weights.data.split(',')]          
        if len(weights) != bornAlive:
            flash('Number of weights must match the number of piglets born!', 'error')
            return redirect(url_for('litter_records', service_id=service_id))
    
        totalWeight = sum(weights)
        averageWeight = round (totalWeight / len(weights),1) if weights else 0

        # calculate other dates
        iron_injection_date = farrowDate + timedelta(days=3)
        tail_dorking_date = farrowDate + timedelta(days=3)
        castration_date = farrowDate + timedelta(days=3)
        teeth_clipping_date = farrowDate + timedelta(days=3)
        wean_date = farrowDate + timedelta(days=21)
    
        new_litter = Litter(
            service_record_id=serviceRecord.id,
            farrowDate=farrowDate,
            totalBorn=totalBorn,
            bornAlive=bornAlive,   
            stillBorn=stillBorn,
            averageWeight=averageWeight,
            iron_injection_date=iron_injection_date,
            tail_dorking_date=tail_dorking_date,
            castration_date=castration_date,
            wean_date=wean_date,
            teeth_clipping_date=teeth_clipping_date,
        )
        
        # try:
        db.session.add(new_litter)
        db.session.commit()
        flash('Litter Recorded successfully!', 'success')
        return redirect(url_for('litter_records', service_id=serviceRecord.id))

    return render_template('litterRecord.html', form=form, serviceRecord=serviceRecord, litters=litters, sow_id=sow_id)

@app.route('/delete-litter/<int:litter_id>', methods=['POST'])
@login_required
def delete_litter(litter_id):
    litter = Litter.query.get_or_404(litter_id)

    # Optional: Add a confirmation check here if needed
    db.session.delete(litter)
    db.session.commit()
    flash('Litter record deleted successfully!', 'success')
    
    # Redirect back to the litter records page or wherever you want
    return redirect(url_for('litter_records', service_id=litter.service_record_id))


@app.route('/delete-service-record/<int:record_id>', methods=['POST'])
@login_required
def delete_service_record(record_id):
    # Query the record by ID
    record = ServiceRecords.query.get_or_404(record_id)
    
    try:
        # Delete the record
        db.session.delete(record)
        db.session.commit()
        flash('Service record deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred while deleting the record: {str(e)}', 'error')
    
    # Redirect back to the sow's service records page
    return redirect(url_for('sow_service_records', sow_id=record.sow_id))

@app.route('/expenses', methods=['GET', 'POST'])
@login_required
def expenses():
    form = ExpenseForm()

    if form.validate_on_submit():
        expense = Expense(
            date=form.date.data,
            amount=form.amount.data,
            category=form.category.data,
            vendor=form.vendor.data,
            description=form.description.data
        )
        db.session.add(expense)
        db.session.commit()
        flash('Expense logged successfully!', 'success')
        return redirect(url_for('expenses'))

    expenses = Expense.query.all()
    return render_template('expenses.html', form=form, expenses=expenses)

@app.route('/expense_totals', methods=['GET'])
@login_required
def expense_totals():
    total_expenses = db.session.query(db.func.sum(Expense.amount)).scalar() or 0
    return jsonify({'total_expenses': f"K{total_expenses:,.2f}"})

@app.route('/delete-expense/<int:expense_id>', methods=['POST'])
@login_required
def delete_expense(expense_id):
    #Query the expense id
    expense = Expense.query.get_or_404(expense_id)

    try:
        #Delete the record
        db.session.delete(expense)
        db.session.commit()
        flash('Expense record deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred while deleting the record: {str(e)}', 'error')

    #Redirect back to the expenses record page
    return redirect(url_for('expenses'))

@app.route('/settings',methods=['POST','GET'])
@login_required
def settings():
    return render_template('settings.html')

# Run the Dashboard
if dash_app.layout is None:
    raise Exception("Dash layout must be set before running the server.")

# Run the app
if __name__ == '__main__':
    # app.run(debug=True)
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)