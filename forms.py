from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, DecimalField, TextAreaField, DateField, FloatField, SelectField
from wtforms.validators import InputRequired, Length, ValidationError, DataRequired
from flask_wtf import FlaskForm
from models import Sows, Boars, User  # Importing the models for validation

# Define Sow Management Form
class SowForm(FlaskForm):
    sowID = StringField(validators=[InputRequired(), Length(min=3, max=20)])
    Breed = StringField(validators=[InputRequired(), Length(min=3, max=50)])
    DOB = DateField(validators=[InputRequired()])
    submit = SubmitField("Add Sow")
        
    def validate_sowID(self, sowID):
        existing_sow = Sows.query.filter_by(sowID=sowID.data).first()
        if existing_sow and existing_sow.id != self.sow_id:
            raise ValidationError('The sow already exists. Please choose a different sow ID')

#Defin sow service record Form
class ServiceRecordForm(FlaskForm):
    service_date = DateField('Service Date', validators=[InputRequired()])
    boar_used = StringField('Boar Used', validators=[InputRequired()])

# Define Boar Form
class BoarForm(FlaskForm):
    BoarId = StringField(validators=[InputRequired(), Length(min=3, max=20)])
    Breed = StringField(validators=[InputRequired(), Length(min=3, max=50)])
    DOB = DateField(validators=[InputRequired()])
    submit = SubmitField("Add Boar")

    def validate_BoarId(self, BoarId):
        existing_boar = Boars.query.filter_by(BoarId=BoarId.data).first()
        if existing_boar:
            raise ValidationError('The Boar already exists. Please Choose a different ID')

# Define Registration Form
class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"Placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"Placeholder": "Password"})
    submit = SubmitField("Register")

    # Custom Validator to check for existing username
    def validate_username(self, username):
        existing_user_name = User.query.filter_by(username=username.data).first()
        if existing_user_name:
            raise ValidationError('The username already exists. Please choose a different username')

# Define Login Form
class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"Placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"Placeholder": "Password"})
    remember = BooleanField("Remember Me")  # Optional remember me checkbox
    submit = SubmitField("Login")

# Define Feed Calculation Form
class FeedCalculatorForm(FlaskForm):
    days = IntegerField(validators=[InputRequired()], render_kw={"Placeholder": "Number of days (e.g 21)"})
    feed = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"Placeholder": "Feed Name (e.g weaner)"})
    feed_cost = DecimalField(validators=[InputRequired()], render_kw={"Placeholder": "Cost of Concentrate (e.g 850)"})
    num3_meal_cost = DecimalField(validators=[InputRequired()], render_kw={"Placeholder": "Cost of Number 3 Meal (e.g 5.35)"})
    pigs = IntegerField(validators=[InputRequired()], render_kw={"Placeholder": "Number of pigs (e.g 4)"})
    feed_consumption = DecimalField(validators=[InputRequired()], render_kw={"Placeholder": "Feed consumption per animal (e.g 1.5)"})
    submit = SubmitField("Calculate")

class CompleteFeedForm(FlaskForm):
    feedName = StringField(validators=[InputRequired()])
    numberOfDays = IntegerField(validators=[InputRequired()])
    consumption = DecimalField(validators=[InputRequired()])
    costOfFeed = DecimalField(validators=[InputRequired()])
    numberOfPigs = IntegerField(validators=[InputRequired()])
    submit = SubmitField("Calculate")

# Define Invoice Generator Form
class InvoiceGeneratorForm(FlaskForm):
    company = StringField(validators=[InputRequired(), Length(min=4, max=50)], render_kw={"Placeholder": "Company Name"})
    firstBandRange = StringField(validators=[InputRequired(), Length(min=4, max=10)], render_kw={"Placeholder": "e.g., 65-109.9"})
    firstBandPrice = DecimalField(validators=[InputRequired()], render_kw={"Placeholder": "60.0 or 60"})
    secondBandRange = StringField(validators=[InputRequired(), Length(min=4, max=10)], render_kw={"Placeholder": "e.g., 65-109.9"})
    secondBandPrice = DecimalField(validators=[InputRequired()], render_kw={"Placeholder": "60.0 or 60"})
    thirdBandRange = StringField(validators=[InputRequired(), Length(min=4, max=10)], render_kw={"Placeholder": "e.g., 65-109.9"})
    thirdBandPrice = DecimalField(validators=[InputRequired()], render_kw={"Placeholder": "60.0 or 60"})
    weights = TextAreaField(validators=[DataRequired()], render_kw={"Placeholder": "e.g., 56.7, 71.5, 66.75, 69.7, ..."})
    submit = SubmitField("Generate Invoice")

class ExpenseForm(FlaskForm):
    date = DateField( validators=[InputRequired()])
    amount = FloatField(validators=[InputRequired()])
    category = SelectField(choices=[('feed', 'Feed'), ('vet', 'Veterinary'), ('labor', 'Labor'), ('equipment', 'Equipment')], validators=[DataRequired()])
    vendor = StringField(validators=[InputRequired()])
    description = StringField()
    submit = SubmitField("Add Expense")