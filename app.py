from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from sqlalchemy import func, event
from datetime import timedelta, date
from dotenv import load_dotenv
from dash import dcc, html, dash_table
from authlib.integrations.flask_client import OAuth
import datetime
import os
import re
import logging
import dash
import dash_bootstrap_components as dbc
import logging

from models import db, Litter, User, Boars, Sows, ServiceRecords, Invoice, Expense
from flask import Flask, render_template, url_for, redirect, flash, make_response, request, jsonify, session, abort
from forms import LitterForm, SowForm, BoarForm, RegisterForm, LoginForm, FeedCalculatorForm, InvoiceGeneratorForm, ServiceRecordForm, ExpenseForm, CompleteFeedForm
from utils import get_sow_service_records, parse_range, update_dashboard, get_total_counts, generate_invoice_pdf, get_litter_stage

# Configure logging to show in console
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

#Load enviroment variables 
load_dotenv()

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# Initialize Flask app
app = Flask(__name__)
app.secret_key= os.getenv("SECRET_KEY")



# Initialize Dash app
dash_app = dash.Dash(
    __name__, 
    server=app,
    url_base_pathname='/dashboard_internal/',  # This sets the base path for Dash
    external_stylesheets=[dbc.themes.BOOTSTRAP, "/static/css/dashboard.css"])

#configure OAuth
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    access_token_url='https://oauth2.googleapis.com/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint='https://openidconnect.googleapis.com/userinfo',
    client_kwargs={'scope': 'openid email profile'},
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration'
)

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
                    # 'color': '#082d06',
                    'color': 'var(--text-dark)',
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
        # dash.Output("total-porkers", "children"),
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

def callback_update_dashboard(n_intervals):
    return update_dashboard(n_intervals)

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

#payement route
@app.route('/payment_plans', methods=['GET','POST'])
def payment_plans():
    return render_template('payment_plans.html')

# Sign in route
@app.route('/signin', methods=['GET', 'POST'])
def signin():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.identifier.data.strip()

        if re.match(r"[^@]+@[^@]+\.[^@]+", username):
            user = User.query.filter_by(email=username).first()
        else:
            user =User.query.filter_by(username=username).first()
            
        if user:
            if user.password is not None:
                # Check password for local users
                if bcrypt.check_password_hash(user.password, form.password.data):
                    login_user(user, remember=form.remember.data)
                    return redirect(url_for('dashboard'))
                else:
                    flash("Invalid Password, Please try again.", "Error")
            else:
                # Handle Google users
                flash("This account is set up for Google login. Please use Google to log in.", "Error")
        else:
            flash("User does not exist. Please register.","Error")
    return render_template('signin.html', form=form)

@app.route('/signup', methods = ['GET', 'POST'])
def signup():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8') # Hash the password
        new_user = User(username=form.username.data, email=form.email.data ,password=hashed_password)
        try:
            db.session.add(new_user)
            db.session.commit() 
            flash("Registration sucessful! Please Log in.", "Success")
            return redirect(url_for('signin'))
        except Exception as e:
            db.session.rollback()
            flash("An error occurred during registration. Please try again.", "Error")
    return render_template('signup.html', form=form)

# Google login route
@app.route('/google-login')
def google_login():
    redirect_uri = url_for('google_auth', _external=True)
    return google.authorize_redirect(redirect_uri)

#google auth callback route
@app.route('/auth')
def google_auth():
    token = google.authorize_access_token()
    user_info = google.get('userinfo').json()
    
    # Check if user already exists by email (username)
    user = User.query.filter_by(username=user_info['email']).first()
    
    if user is None:
        # Create a new user with Google info
        user = User(
            username=user_info['email'],
            email=user_info['email'],
            google_id=user_info['id'],
            name=user_info.get('name'),
            profile_pic=user_info.get('picture'),
            password=None  # No password for Google users
        )
        db.session.add(user)
        db.session.commit()
    
    # Log in the user
    login_user(user)
    flash("Logged in successfully with Google!", "Success")
    return redirect(url_for('dashboard'))

# Logout route
@app.route('/logout', methods=['POST','GET'])
@login_required
def logout():
    logout_user() # Logout the current user
    flash("You have been logged out.","Success")
    return redirect(url_for('login'))

@app.route('/complete-feeds-calculator', methods=['GET','POST'])
@login_required
def complete_feeds():
    #Get input from the front end
    form = CompleteFeedForm()
    result = None #initialize result

    if form.validate_on_submit():
        # Validate inputs for non-negative values
        if form.numberOfPigs.data <= 0 or form.consumption.data <= 0 or form.costOfFeed.data <= 0 or form.numberOfDays.data <= 0:
            flash("Please enter positive values for all fields.", "error")
            return redirect(url_for('complete_feeds'))
        
        #perfom calculations
        dailyConsumption = form.numberOfPigs.data * float(form.consumption.data)
        total_feed = dailyConsumption * form.numberOfDays.data
        num_of_bags = round(total_feed/50)
        total_cost = num_of_bags*form.costOfFeed.data

        result={
            "totalFeed": total_feed,
            "numOfBags": num_of_bags,
            "totalCost": total_cost,
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
        # validate inputs are non negative numbers
        if form.days.data <= 0 or form.pigs.data <= 0 or form.feed_consumption.data <= 0 or form.feed_cost.data <= 0 or form.num3_meal_cost.data <= 0:
            flash("Please enter positive values for all fields.", "error")
            return redirect(url_for('calculate'))

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
        weights = [float(w.strip()) for w in form.weights.data.split(',')if w.strip() != '']

        #Ensure there are weights provided
        if not weights:
            flash("Please enter valid weights.", "Error")
            return redirect(url_for('invoice_Generator'))

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
                    "Number_of_Pigs": f"{total_pigs}",
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
        total_price=total_cost,
        user_id=current_user.id
    )
    db.session.add(new_invoice)
    db.session.commit()

    pdf = generate_invoice_pdf(company_name, invoice_number, invoice_data, total_weight, average_weight, total_cost)
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename={invoice_number}.pdf'
    return response

@app.route('/invoices', methods=['GET','POST'])
@login_required
def invoices():
    # Pagination setup
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Number of invoices per page
    invoices = Invoice.query.filter_by(user_id=current_user.id).order_by(Invoice.date.desc()).paginate(page=page,per_page=per_page, error_out=False)
    invoices_list = invoices.items

    return render_template('invoices.html', invoices=invoices_list, pagination=invoices)

@app.route('/invoice_totals', methods=['GET'])
@login_required
def invoice_totals():
    total_weight    = db.session.query(db.func.sum(Invoice.total_weight))   .filter(Invoice.user_id == current_user.id).scalar() or 0
    total_revenue   = db.session.query(db.func.sum(Invoice.total_price))    .filter(Invoice.user_id == current_user.id).scalar() or 0
    avg_weight      = db.session.query(db.func.avg(Invoice.average_weight)) .filter(Invoice.user_id == current_user.id).scalar() or 0
    total_pigs      = db.session.query(db.func.sum(Invoice.num_of_pigs))    .filter(Invoice.user_id == current_user.id).scalar() or 0

    return jsonify({
        'total_weight': f"{total_weight:,.2f}Kg",
        'total_revenue': f"K{total_revenue:,.2f}",
        'average_weight': f"{avg_weight:,.2f}Kg",
        'total_pigs': f"{total_pigs:,.0f}"
    })

# Delete Invoice Route
@app.route('/delete-invoice/<int:invoice_id>', methods=['POST'])
@login_required
def delete_invoice(invoice_id):
    invoice = Invoice.query.filter_by(id=invoice_id, user_id=current_user.id).first_or_404()
    
    try:
        db.session.delete(invoice)
        db.session.commit()
        flash('Invoice deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting invoice: {str(e)}', 'error')

    return redirect(url_for('invoices'))    

@app.route('/boar-manager', methods=['GET','POST'])
@login_required
def boars():
    form = BoarForm()

    if form.validate_on_submit():
        boar_id = re.sub(r'\s+', '', form.BoarId.data).upper()
        breed = re.sub(r'\s+', '', form.Breed.data).upper()
        boar_dob = form.DOB.data

        # check if boar already exists
        if Boars.query.filter_by(BoarId = boar_id, user_id=current_user.id).first():
            flash('Boar ID already exists! Please use a different ID.', 'error')
        
        else:
            #add boar to the database
            try:
                new_boar = Boars(
                    BoarId = boar_id,
                    DOB = boar_dob,
                    Breed=breed,
                    user_id=current_user.id
                    )
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
    page =request.args.get('page',1,type=int)
    per_page = 20
    boars = Boars.query.filter_by(user_id=current_user.id).order_by(Boars.DOB).paginate(page=page, per_page=per_page,error_out=False)  # Only show the boars owned by the current user
    return render_template('boars.html', boars=boars, form=form, pagination=boars)  
  
@app.route('/delete-boar/<string:BoarId>', methods=['POST'])
@login_required
def delete_boar(BoarId):
    boar = Boars.query.filter_by(BoarId = BoarId.upper(), user_id=current_user.id).first_or_404()
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

    boar = Boars.query.filter_by(id = boar_id, user_id=current_user.id).first_or_404()
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
        sow_id = re.sub(r'\s+', '', form.sowID.data).upper()
        breed = re.sub(r'\s+', '', form.Breed.data).upper()
        dob_str = form.DOB.data

        try:
            # Add sow to the database
            new_sow = Sows(
                sowID=sow_id,
                DOB=dob_str,
                Breed=breed,
                user_id=current_user.id)
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
    
    page =request.args.get('page',1,type=int)
    per_page = 20
    sows = Sows.query.filter_by(user_id=current_user.id).order_by(Sows.DOB).paginate(page=page, per_page=per_page,error_out=False)
    return render_template('sows.html', sows=sows, form=form, pagination=sows)

@app.route('/edit-sow/<int:sow_id>', methods=['GET', 'POST'])
@login_required
def edit_sow(sow_id):

    sow = Sows.query.filter_by(id=sow_id, user_id=current_user.id).first_or_404()
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
    sow = Sows.query.filter_by(sowID=sow_id.upper(), user_id=current_user.id).first_or_404()
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
    sow = Sows.query.filter_by(id=sow_id, user_id=current_user.id).first_or_404()
    boars = Boars.query.filter_by(user_id=current_user.id).all()  # Only show the boars owned by the current user
    form = ServiceRecordForm()

    if not boars:
        form.boar_used.choices = [('ai','Artificial Insemination')]
    else:
        boar_choices = [(str(boar.id),boar.BoarId)for boar in boars]
        boar_choices.append(('ai','Artificial Insemination'))
        form.boar_used.choices = boar_choices

    if form.validate_on_submit():  # Checks if the form was submitted and is valid
        
        boar_used_id = form.boar_used.data.upper() #get boar id used from form
        boar = Boars.query.filter_by(id=boar_used_id, user_id=current_user.id).first_or_404() # query the boar from the current logged in user

        service_date = form.service_date.data
        boar_used = boar.BoarId.upper() # get the boar "name"

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

@app.route('/litter-records/<int:service_id>', methods=['GET', 'POST'])
@login_required
def litter_records(service_id):
    form = LitterForm()
    serviceRecord = ServiceRecords.query.get_or_404(service_id)

    if serviceRecord.sow.user_id != current_user.id:
        abort(403)

    sow_id = serviceRecord.sow_id
    existing_litter = serviceRecord.litter
    sow = Sows.query.filter_by(id=sow_id, user_id=current_user.id).first_or_404()

    # Add stage if there's a litter
    litters = [existing_litter] if existing_litter else []
    for litter in litters:
        if litter:
            litter.stage = get_litter_stage(litter.farrowDate)

    if form.validate_on_submit():
        if existing_litter:
            flash("This service record already has an associated litter. You can't add another.", "error")
            return redirect(url_for('litter_records', service_id=service_id))

        farrowDate = form.farrowDate.data
        totalBorn = form.totalBorn.data
        bornAlive = form.bornAlive.data
        stillBorn = form.stillBorn.data

        try:
            weights = [float(w.strip()) for w in form.weights.data.split(',') if w.strip()]
        except ValueError:
            flash('Please enter valid numeric weight values separated by commas.', 'error')
            return redirect(url_for('litter_records', service_id=service_id))

        if not weights or len(weights) != bornAlive:
            flash('Number of weights must match the number of piglets born alive!', 'error')
            return redirect(url_for('litter_records', service_id=service_id))
        
        if stillBorn + bornAlive != totalBorn:
            flash('The total  number of piglets born are not equal to the still born and born alive')
            return redirect(url_for('litter_records', service_id=service_id))
            


        averageWeight = round(sum(weights) / len(weights), 1)

        # Date calculations
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
            sow_id=sow_id
        )

        try:
            db.session.add(new_litter)
            db.session.commit()
            flash('Litter recorded successfully!', 'success')
            return redirect(url_for('litter_records', service_id=service_id))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while saving the litter: {str(e)}', 'error')

    return render_template('litterRecord.html', form=form, sow=sow ,serviceRecord=serviceRecord, litters=litters, sow_id=sow_id, existing_litter=existing_litter)

@app.route('/delete-litter/<int:litter_id>', methods=['POST'])
@login_required
def delete_litter(litter_id):
    litter = Litter.query.get_or_404(litter_id)
    # Fetch the litter and join with the service record to check ownership
    service_id = litter.service_record_id

    # Optional: Add a confirmation check here if needed
    db.session.delete(litter)
    db.session.commit()
    flash('Litter record deleted successfully!', 'success')
    
    # Redirect back to the litter records page or wherever you want
    return redirect(url_for('litter_records', service_id=service_id))

@app.route('/delete-service-record/<int:record_id>', methods=['POST'])
@login_required
def delete_service_record(record_id):
    # Query the record by ID
    record = (
        db.session.query(ServiceRecords)
        .join(Sows, ServiceRecords.sow_id == Sows.id)
        .filter(ServiceRecords.id == record_id, Sows.user_id == current_user.id)
        .first_or_404()
    )

    if not record:
        abort(403) # Unauthorized access

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
            invoice_number=form.invoice_number.data,
            category=form.category.data,
            vendor=form.vendor.data,
            description=form.description.data,
            user_id = current_user.id
        )
        db.session.add(expense)
        db.session.commit()
        flash('Expense logged successfully!', 'success')
        return redirect(url_for('expenses'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Number of Exepenses per page
    expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).paginate(page=page,per_page=per_page, error_out=False)
    expenses_list = expenses.items
    return render_template('expenses.html', form=form, expenses=expenses_list, pagination=expenses)

@app.route('/edit_expense/<int:expense_id>', methods=['GET','POST'])
@login_required
def edit_expense(expense_id):
    
    expense = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first_or_404()
    form = ExpenseForm(obj=expense) #pre fill the data
    form.expense_id = expense.id

    if form.validate_on_submit():
        expense.date = form.date.data
        expense.amount = form.amount.data
        expense.invoice_number = form.invoice_number.data
        expense.category = form.category.data
        expense.vendor = form.vendor.data
        expense.description = form.description.data

        try:
            db.session.commit()
            flash('Expense Updated','success')
            return redirect(url_for('expenses'))
        except IntegrityError:
            db.session.rollback()
            flash(f'Expense with receipt number {expense.invoice_number} already exists', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'error')
    return render_template('edit_expense.html', form=form, expense=expense)

@app.route('/expense_totals', methods=['GET'])
@login_required
def expense_totals():
    total_expenses = (
        db.session.query(db.func.sum(Expense.amount))
        .filter_by(user_id = current_user.id)
        .scalar()
    ) or 0
    return jsonify({'total_expenses': f"K{total_expenses:,.2f}"})

@app.route('/delete-expense/<int:expense_id>', methods=['POST'])
@login_required
def delete_expense(expense_id):
    #Query the expense id
    expense = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first_or_404()

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