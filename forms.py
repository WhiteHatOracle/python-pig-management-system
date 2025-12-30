from wtforms import EmailField,StringField, PasswordField, SubmitField, BooleanField, IntegerField, DecimalField, TextAreaField, DateField, FloatField, SelectField
from wtforms.validators import InputRequired, Length, ValidationError, InputRequired, DataRequired, EqualTo, Optional, NumberRange
from flask_wtf import FlaskForm
from models import Sows, Boars, User
from wtforms.fields import DateField
from flask_login import current_user
from datetime import date
# Define Sow Management Form
class SowForm(FlaskForm):
    sowID = StringField(validators=[DataRequired(), Length(min=3, max=20)])
    Breed = StringField(validators=[DataRequired(), Length(min=3, max=50)])
    DOB = DateField(format='%d-%m-%Y',validators=[DataRequired()])
    submit = SubmitField("Add Sow")

    def __init__(self, sow_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sow_id = sow_id    #store the sow for validation    
    
    def validate_sowID(self, sowID):
        existing_sow = Sows.query.filter_by(sowID=sowID.data.strip().upper(),user_id=current_user.id).first()
        if existing_sow and existing_sow.id != self.sow_id:
            raise ValidationError('The sow already exists. Please choose a different sow ID')
     
#Define sow service record Form
class ServiceRecordForm(FlaskForm):
    service_date = DateField(format='%d-%m-%Y',validators=[DataRequired()])
    boar_used = SelectField('Boar Used', choices=[], coerce=str)
    
# Define Boar Form
class BoarForm(FlaskForm):
    BoarId = StringField(validators=[DataRequired(), Length(min=3, max=20)])
    Breed = StringField(validators=[DataRequired(), Length(min=3, max=50)])
    DOB = DateField(format="%d-%m-%Y",validators=[DataRequired()])
    submit = SubmitField("Add Boar")

    def validate_BoarId(self, BoarId):
        existing_boar = Boars.query.filter_by(BoarId=BoarId.data.strip().upper(),user_id=current_user.id).first()
        if existing_boar and existing_boar.id != self.BoarId.data:
            raise ValidationError('The Boar already exists. Please Choose a different ID')

# Define Registration Form
class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"Placeholder": "Username"})
    email = EmailField(validators=[InputRequired()],render_kw={"Placeholder": "Email"})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=20)],render_kw={"Placeholder": "Password"})
    submit = SubmitField("Register")

    # Custom Validator to check for existing username
    def validate_email(self, email):
        existing_email = User.query.filter_by(email=email.data).first()
        if existing_email:
            raise ValidationError('The email already exists. Please choose a different email')

# Define Login Form
class LoginForm(FlaskForm):
    identifier = StringField('username or Email', validators=[InputRequired()],render_kw={"Placeholder": "Username or Email"})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=20)],render_kw={"Placeholder": "Password"})
    remember = BooleanField("Remember Me")  # Optional remember me checkbox
    submit = SubmitField("Login")

# Define Feed Calculation Forms
class FeedCalculatorForm(FlaskForm):
    days = IntegerField(validators=[InputRequired()])
    feed = StringField(validators=[InputRequired(), Length(min=4, max=20)])
    feed_cost = DecimalField(validators=[InputRequired()])
    num3_meal_cost = DecimalField(validators=[InputRequired()])
    pigs = IntegerField(validators=[InputRequired()])
    feed_consumption = DecimalField(validators=[InputRequired()])
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
    company         = StringField(validators=[InputRequired(), Length(min=4, max=50)])
    firstBandRange  = StringField(validators=[InputRequired(), Length(min=4, max=10)])
    firstBandPrice  = DecimalField(validators=[InputRequired()])
    secondBandRange = StringField(validators=[InputRequired(), Length(min=4, max=10)])
    secondBandPrice = DecimalField(validators=[InputRequired()])
    thirdBandRange  = StringField(validators=[InputRequired(), Length(min=4, max=10)])
    thirdBandPrice  = DecimalField(validators=[InputRequired()])
    weights         = TextAreaField(validators=[InputRequired()])

    # ADD THIS NEW FIELD
    invoice_date = DateField(
        'Invoice Date',
        format='%Y-%m-%d',
        default=date.today,
        validators=[DataRequired()]
    )

    submit          = SubmitField("Generate Invoice")

class ExpenseForm(FlaskForm):
    date            = DateField(format='%d-%m-%Y',validators=[DataRequired()])
    amount          = FloatField(validators=[InputRequired()])
    category        = SelectField(choices=[('feed', 'Feed'), ('vet', 'Veterinary'), ('labor', 'Labor'), ('equipment', 'Equipment'),('transport', 'Transport'),('utilities','Utilities')], validators=[InputRequired()])
    invoice_number  = StringField(validators=[InputRequired()])
    vendor          = StringField(validators=[InputRequired()])
    description     = StringField()
    submit          = SubmitField("Add Expense")

# litter management form
class LitterForm(FlaskForm):
    farrowDate = DateField("Farrow Date", format="%d-%m-%Y", validators=[DataRequired()])
    totalBorn = IntegerField("Total Born", validators=[InputRequired()])
    bornAlive = IntegerField("Born Alive", validators=[InputRequired()])
    stillBorn = IntegerField("Still Born", validators=[InputRequired()])  # 👈 allow 0
    weights = TextAreaField("Weights", validators=[DataRequired()],render_kw={"Placeholder": "e.g 5,3.1,4,..."})
    mummified = IntegerField('Mummified', validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField("Add Litter")

# change password form
class ChangePasswordForm(FlaskForm):
    current_password = PasswordField(validators=[DataRequired(), Length(min=4, max=20)])
    new_password = PasswordField(validators=[DataRequired(), Length(min=4, max=20)])
    confirm_password = PasswordField("Confirm New Password", validators=[DataRequired(),EqualTo('new_password', message='Passwords must match')])
    submit = SubmitField("Change Password")

class ForgotPasswordForm(FlaskForm):
    email = EmailField(validators=[InputRequired()])
    submit = SubmitField("Reset Password")

    def validate_email(self, email):
        existing_user = User.query.filter_by(email=email.data).first()
        if not existing_user:
            raise ValidationError('No account found with that email address. Please try again.')

class ResetPasswordForm(FlaskForm):
    new_password = PasswordField(validators=[DataRequired(), Length(min=4, max=20)])
    confirm_password = PasswordField(validators=[DataRequired(), EqualTo('new_password', message='Passwords must match')])
    submit = SubmitField("Reset Password")