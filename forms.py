from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, SelectField, IntegerField
from wtforms.validators import DataRequired, URL

# RegisterForm to register new users
# Create registration form
class RegistrationForm(FlaskForm):
    email = StringField('Email Address', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    password_confirm = PasswordField('Confirm Password', validators=[DataRequired()])
    first_name = StringField('First name', validators=[DataRequired()])
    last_name = StringField('Last name', validators=[DataRequired()])
    submit = SubmitField('Register')

# LoginForm to login existing users
class LoginForm(FlaskForm):
    email = StringField('Email Address', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# Used for adding customer ranking, rating and review; Used within Edit route
class RateMovieForm(FlaskForm):
    # DataRequired() ensures user completes that section
    rating = StringField('Your rating out of 10 e.g. 7.5', validators=[DataRequired()])
    review = StringField('Your Review', validators=[DataRequired()])
    ranking = IntegerField('Your new ranking', validators=[DataRequired()])
    submit = SubmitField("Update")

# WTForm for Movie API search. Gets called @add_movie
class AddMovie(FlaskForm):
    title = StringField('Movie Title', validators=[DataRequired()])
    sumit = SubmitField("Add Movie")