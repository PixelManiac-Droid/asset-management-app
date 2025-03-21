from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, PasswordField, DateField, SelectField
from wtforms.validators import InputRequired, NumberRange, Length, EqualTo

class SignUpForm(FlaskForm):
    first_name = StringField('First Name', validators=[InputRequired(), Length(min=0, max=20)])
    second_name = StringField('Second Name', validators=[InputRequired(), Length(min=0, max=20)])
    username = StringField('Username', validators=[InputRequired(), Length(min=0, max=20)])
    email = StringField('Email', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=8,max=50)])
    password_again = PasswordField('Confirm Password', validators=[InputRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])
    submit = SubmitField('Login')

class AddAssetForm(FlaskForm):
    name = StringField('Asset Name', validators=[InputRequired()])
    quantity = IntegerField('Quantity', validators=[InputRequired(), NumberRange(min=1)])
    category = SelectField('Category', choices=[('Vehicles','Vehicles'), ('Real Estate','Real Estate'), ('Investments','Investments'),('Personal Valuables','Personal Valuables')], validators=[InputRequired()])
    purchase_date = DateField('Year of Purchase', validators=[InputRequired()]) #hard coded must change later
    purchase_price = IntegerField('Purchase Price', validators=[InputRequired(), NumberRange(min=0)])
    current_value = IntegerField('Current Price', validators=[InputRequired(), NumberRange(min=0)])
    submit = SubmitField('Add Asset')

class EditAssetForm(FlaskForm):
    name = StringField('Asset Name', validators=[InputRequired()])
    quantity = IntegerField('Quantity', validators=[InputRequired(), NumberRange(min=1)])
    category = SelectField('Category', choices=[('Vehicles','Vehicles'), ('Real Estate','Real Estate'), ('Investments','Investments'),('Personal Valuables','Personal Valuables')], validators=[InputRequired()])
    purchase_date = DateField('Year of Purchase', validators=[InputRequired()]) #hard coded must change later
    purchase_price = IntegerField('Purchase Price', validators=[InputRequired(), NumberRange(min=0)])
    current_value = IntegerField('Current Price', validators=[InputRequired(), NumberRange(min=0)])
    submit = SubmitField('Add Asset')

class UpdateAssetForm(FlaskForm):
    price = IntegerField('New Value', validators=[InputRequired(), NumberRange(min=0)])
    submit = SubmitField('Update')

class DeleteAssetForm(FlaskForm):
    price = IntegerField('Sale Price', validators=[InputRequired(), NumberRange(min=0)])
    submit = SubmitField('Sell')

class SettingsForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[InputRequired()])
    new_password = PasswordField('New Password', validators=[InputRequired(), Length(min=8,max=50)])
    submit = SubmitField('Update')
    clear_data = SubmitField('Clear Data')

