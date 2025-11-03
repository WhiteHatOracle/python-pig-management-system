from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import IntegrityError
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from sqlalchemy import func, event
from flask_mail import Mail, Message
from datetime import timedelta, datetime
import datetime as dt
from dotenv import load_dotenv
from dash import dcc, html, dash_table
from authlib.integrations.flask_client import OAuth
import os
import re
import dash
import uuid
import logging
import secrets
import traceback
import dash_bootstrap_components as dbc

from models import db, Litter, User, Boars, Sows, ServiceRecords, Invoice, Expense
from flask import Flask, render_template, url_for, redirect, flash, make_response, request, jsonify, session, abort, get_flashed_messages
from forms import ResetPasswordForm, ForgotPasswordForm, LitterForm, SowForm, BoarForm, RegisterForm, LoginForm, FeedCalculatorForm, InvoiceGeneratorForm, ServiceRecordForm, ExpenseForm, CompleteFeedForm, ChangePasswordForm
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

app = Flask(__name__) # Initialize Flask app
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
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")  # Set in .env
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")  # Set in .env
# app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

# Make `enumerate` available in Jinja2 templates
app.jinja_env.globals.update(enumerate=enumerate)

# Initialize database, bcrypt, and login manager
db.init_app(app)
mail = Mail(app)  # Initialize Flask-Mail
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "signin"  # Redirect here if unauthorized access is attempted

# Load user for login management
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Dashboard Layout
dash_app.layout = dbc.Container([
    html.Div([
        # Row for Summary Cards
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H4("Herd Size"), 
                    html.H2(id="total-pigs")
                    ],className = "dash-card")
            ], color="transparent", inverse=True, style={"border": "none", "boxShadow": "none"})),

            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H4("Sows"),
                    html.H2(id="total-sows")
                    ],className = "dash-card")
            ], color="transparent", inverse=True, style={"border": "none", "boxShadow": "none"})),

            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H4("Boars"), 
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
            if not user.is_verified:
                flash("Please verify your email before logging in.", "Error")
                return render_template('signin.html', form=form)
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

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()
    if form.validate_on_submit():
        # check for an existing username
        existing_user =User.query.filter_by(username=form.username.data.strip()).first()
        if existing_user:
            flash("The username already exists. Try something different, maybe your farm name?? :)", "Error")
            return render_template('signup.html', form=form)
        
        # check if email already exists
        existing_email = User.query.filter_by(email=form.email.data.strip()).first()
        if existing_email:
            flash("Looks like that email is already registered. Forgotten your password?", "Error")
            return render_template('signup.html', form = form)

        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        token = str(uuid.uuid4())
        expiry_time = datetime.now(dt.timezone.utc) + timedelta(hours=24)  # Link expires in 24 hours

        new_user = User(
            username=form.username.data,
            email=form.email.data,
            password=hashed_password,
            verification_token=token,
            verification_expiry=expiry_time,
            is_verified=False
        )
        try:
            db.session.add(new_user)
            db.session.commit()

            # Create verification email
            verify_url = url_for('verify_email', token=token, _external=True)
            msg = Message(
                subject="Welcome to Pig Management System – Verify Your Email",
                sender=("Pig Management System", app.config['MAIL_USERNAME']),
                recipients=[form.email.data]
            )

            # Plain text version
            msg.body = f"""Hi {form.username.data},

            Thanks for signing up for Pig Management System!

            Please confirm your email address by clicking the link below:
            {verify_url}

            This link will expire in 24 hours.

            If you didn’t sign up, you can ignore this message.

            Cheers,
            The Pig Management System Team
            """

            # HTML version
            msg.html = f"""
            <p>Hi {form.username.data},</p>
            <p>Thanks for signing up for <strong>Pig Management System</strong>!</p>
            <p>Please confirm your email address by clicking the link below:</p>
            <p><a href="{verify_url}" style="color: #1a73e8;">Verify My Email</a></p>
            <p><strong>This link will expire in 24 hours.</strong></p>
            <p>If you didn’t sign up, you can ignore this message.</p>
            <p>Cheers,<br>The Pig Management System Team</p>
            """

            # Send email
            email_sent = False
            try:
                mail.send(msg)
                email_sent = True
            except Exception as e:
                app.logger.error("Email send failed:\n" + traceback.format_exc())
                flash(f"Registration successful, but we couldn't send the verification email.", "Error")

            if email_sent:
                flash("Registration successful! Please check your email to verify your account.", "Success")

            return redirect(url_for('signin'))

        except Exception as e:
            db.session.rollback()
            app.logger.error("Database error:\n" + traceback.format_exc())
            flash("An error occurred during registration. Please try again.", "Error")

    return render_template('signup.html', form=form)

@app.route('/verify/<token>')
def verify_email(token):
    user = User.query.filter_by(verification_token=token).first()
    if user:
        # check if the token is expired
        if user.verification_expiry and datetime.now(dt.timezone.utc) > user.verification_expiry:
            db.session.delete(user)
            db.session.commit()
            flash("Verification link expired. Please register again.", "Error")
            return redirect(url_for('signup'))

        # If the token is valid and not expired, verify the user
        user.is_verified = True
        user.verification_token = None
        user.verification_expiry = None
        db.session.commit()
        flash("Your email has been verified. You can now log in.", "Success")
    else:
        flash("Invalid or expired verification link.", "Error")
    return redirect(url_for('signin'))

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
    invoice_number = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    #store invoice data in db just before downloading
    new_invoice = Invoice(
        invoice_number=invoice_number,
        num_of_pigs=total_pigs,
        company_name=company_name,
        date=datetime.now().date(),
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
            flash(f'{boar_id} added successfully!', 'success')
            return redirect(url_for('boars'))
        except IntegrityError:
            db.session.rollback()
            flash(f'{boar_id} already exists!', 'error')
            return redirect(url_for('boars'))
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
            flash('Updated successfully!', 'success')
            return redirect(url_for('boars'))  # Redirect to the main boar manager
        except IntegrityError:
            db.session.rollback()
            flash(f'{form.BoarId.data.upper()} already exists!', 'error')
            # Render the template to show the error message
            return render_template('edit_boar.html', form=form, boar=boar)
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'error')
            # Render the template to show the error message
            return render_template('edit_boar.html', form=form, boar=boar)

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
            flash(f'{sow_id} successfully added!', 'success')
            return redirect(url_for('sows'))
        except IntegrityError:
            db.session.rollback()
            flash(f'{sow_id} already exists!', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'error')
    
    page = request.args.get('page',1,type=int)
    per_page = 20
    sows = Sows.query.filter_by(user_id=current_user.id).order_by(Sows.DOB).paginate(page=page, per_page=per_page,error_out=False)
    return render_template('sows.html', sows=sows, form=form, pagination=sows)

@app.route('/edit-sow/<int:sow_id>', methods=['GET', 'POST'])
@login_required
def edit_sow(sow_id):

    sow = Sows.query.filter_by(id=sow_id, user_id=current_user.id).first_or_404()
    form = SowForm(sow_id=sow.id, obj=sow)  # Pre-fill form with existing data
    form.sow_id = sow.id #prevents false validation errors

    if form.validate_on_submit():

        # Update the sow with new values
        sow.sowID = form.sowID.data.upper()
        sow.Breed = form.Breed.data.upper()
        sow.DOB = form.DOB.data

        try:
            db.session.commit()
            flash('Updated successfully!', 'success')
            return redirect(url_for('sows'))
        except IntegrityError:
            db.session.rollback()
            flash(f'{sow.sowID} already exists!', 'error')
            return redirect(url_for('edit_sow', sow_id=sow.id))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'error')
            return redirect(url_for('edit_sow', sow_id=sow.id))

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
        wean_date = farrowDate + timedelta(days=28)

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

    return render_template('litterRecord.html', form=form, sow=sow ,serviceRecord=serviceRecord, litters=litters, sow_id=sow_id, existing_litter=existing_litter, service_id=service_id)

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
        try:
            db.session.add(expense)
            db.session.commit()
            flash('Expense logged successfully!', 'success')
            return redirect(url_for('expenses'))
        except IntegrityError:
            db.session.rollback()
            flash('An expense with the same invoice is available','error')
    
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
            flash(f'you already have an expense with that Reciept number', 'error')
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

# change password route
@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()

    if form.validate_on_submit():
        # Verify current password
        if not bcrypt.check_password_hash(current_user.password, form.current_password.data):
            flash("Current password is incorrect.", "error")
            return redirect(url_for('change_password'))

        new_password = form.new_password.data.strip()

        # Ensure new password is not empty or same as current
        if not new_password:
            flash("New password cannot be empty.", "error")
            return redirect(url_for('change_password'))

        if bcrypt.check_password_hash(current_user.password, new_password):
            flash("New password cannot be the same as the current password.", "error")
            return redirect(url_for('change_password'))

        # Update password
        current_user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        db.session.commit()

        flash("Password changed successfully!", "success")
        return redirect(url_for('settings'))
    if form.is_submitted() and not form.validate():
        flash("There seems to have been a problem, please try again", "error")
    return render_template('change_password.html', form=form)

@app.route("/delete_account", methods=["POST","GET"])
@login_required
def delete_account():
    is_google_user = current_user.password is None
    if request.method == "POST":
        if is_google_user:
            user_id = current_user.id
            logout_user()
            session.clear()
            user = User.query.get(user_id)
            if user:
                db.session.delete(user)
                db.session.commit()
                flash("Your account has been permanently deleted.", "info")
            else:
                flash("User not found.", "danger")
            return redirect(url_for("goodbye"))
        else:
            password = request.form.get("password")
            if not bcrypt.check_password_hash(current_user.password, password):
                flash("Incorrect password. Account not deleted.", "danger")
                return redirect(url_for("delete_account"))
            user_id = current_user.id
            logout_user()
            session.clear()
            user = User.query.get(user_id)
            if user:
                db.session.delete(user)
                db.session.commit()
                flash("Your account has been permanently deleted.", "info")
            else:
                flash("User not found.", "danger")
            return redirect(url_for("goodbye"))
    return render_template("delete_account.html", is_google_user=is_google_user)

@app.route("/goodbye")
def goodbye():
    return "<h3>We're sorry to see you go. Your account has been deleted.</h3>"

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            # Generate a password reset token
            token = secrets.token_urlsafe(32)
            user.password_reset_token = token
            user.password_reset_expiry = datetime.now(dt.timezone.utc) + timedelta(hours=1)  # Token valid for 1 hour
            db.session.commit()

            reset_url = url_for('reset_password', token=token, _external=True)

            # Send email with reset link
            msg = Message(
                subject     = "Password Reset Request - Pig Management System",
                sender      = ("Pig Management System", app.config['MAIL_USERNAME']),
                recipients  = [user.email]
            )
            msg.body = f"""
                Hi {user.username},

                You requested to reset your password.

                Click the link below to reset your password (expires in 1 hour):
                {reset_url}

                If you didn’t request this, ignore this email.

                Cheers,
                Pig Management System Team
                """
            msg.html = f"""
                <p>Hi {user.username},</p>
                <p>You requested to reset your password.</p>
                <p>Click the link below to reset your password (expires in 1 hour):</p>
                <p><a href="{reset_url}" style="color: #1a73e8;">Reset Password</a></p>
                <p>If you didn’t request this, ignore this email.</p>
                <p>Cheers,<br>Pig Management System Team</p>
                """
            try:
                mail.send(msg)
                flash("A password reset link has been sent to your email.", "success")
            except Exception as e:
                flash(f"We ran into a problem trying to send the email. Please try again later. Error: {str(e)}", "error")
        else:
            flash("No account found with that email address.", "error")
            return redirect(url_for('sign_in'))
    return render_template('forgot_password.html', form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.query.filter_by(password_reset_token=token).first()
    if not user or user.password_reset_expiry < datetime.now(dt.timezone.utc).replace(tzinfo=None):  # Now both are naive
        flash("Invalid or expired password reset link.", "error")
        return redirect(url_for('forgot_password'))

    form = ResetPasswordForm()

    if form.validate_on_submit():
        new_password = form.new_password.data.strip()
        confirm_password = form.confirm_password.data.strip()

        if not new_password:
            flash("The password can't be empty.", "error")
            return redirect(url_for('reset_password', token=token))
        
        if new_password != confirm_password:
            flash("Passwords do not match. Please try again.", "error")
            return redirect(url_for('reset_password', token=token))
        
        # Hash the new password and update the user record
        hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        user.password = hashed_password
        user.password_reset_token = None  # Clear the token
        user.password_reset_expiry = None  # Clear the expiry time

        db.session.commit()

        flash("Your password has been reset successfully. You can now log in with your new password.", "success")
        return redirect(url_for('signin'))
    return render_template('reset_password.html', form=form, token=token)

# Run the Dashboard
if dash_app.layout is None:
    raise Exception("Dash layout must be set before running the server.")

# Run the app
if __name__ == '__main__':
    # app.run(debug=True)
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)