from flask import Flask, render_template, redirect, url_for, request
from forms import RegistrationForm, LoginForm, RateMovieForm, AddMovie
from dotenv import load_dotenv
import os
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from wtforms import StringField, SubmitField, IntegerField
from wtforms.validators import DataRequired
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
import requests
from filmsearch import MovieSearch
from flask import flash

# Load .env
load_dotenv()
# Creating an Instance of the Flask Class; Tracks configurations, URL rules, template locations, etc.
app = Flask(__name__)
# Set Secret Key for (CSRF) Cross-site request forgery
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
# Set DB Key
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv('SQL_DATABASE')
# Create Instance for BootStrap
bootstrap = Bootstrap5(app)
# Create login instance,
login_manager = LoginManager()
    # initialises with app
login_manager.init_app(app)
    # Redirects to here, creates endpoint
login_manager.login_view = "login"
# Create Instance for DB; SQLAlchemy
db = SQLAlchemy(app)

# Create a user_loader callback
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, user_id)

# Create user DB here
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    first_name = db.Column(db.String(1000))
    last_name = db.Column(db.String(1000))
    is_admin = db.Column(db.Integer, default=0)
    movies = relationship("Movie", back_populates="user")



# Define class called "Movie", db.Model maps to table in SQLAch called "Model"
class Movie(db.Model):
    # Each attribute below represents a column wthin the database table.
    # primary_key=True indicates uniquely ID; id is column name
    __tablename__ = "movie"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    user = relationship("User", back_populates="movies")
    title = db.Column(db.String(80), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(80), nullable=False)
    rating = db.Column(db.Float(5))
    ranking = db.Column(db.Integer)
    review = db.Column(db.String(80))
    img_url = db.Column(db.String(80), nullable=False)
    # __repr__ defines how instances are represented as strings (supporting debug)
    # Printing Movie as an Object returns the f sting below
    def __repr__(self):
        return f"< Movie {self.title} ranked: {self.ranking}>"

# Sets app with context() method allowing globally accessible
with app.app_context():
    # Checks current state of DB, creates tables if non-existent 
    db.create_all()
    # Not Best for Production builds *** Use Flask-Migrate / Alembic


@app.route("/")
def home():
    all_movies = Movie.query.order_by(Movie.rating.desc()).all()
    return render_template("index.html", data=all_movies)

# Route for Registering Users
@app.route("/register", methods=["POST", "GET"])
def register():
    # Create form variable (imported from forms.py)
    form = RegistrationForm()
    # Check IF POST and form correct
    if request.method == "POST" and form.validate():
        # Check passwords match, return wardning if false
        if form.password.data != form.password_confirm.data:
            flash("Password do not match, Please try again", "danger")
            return redirect(url_for("register"))
        # Hash password
        hashed_password = generate_password_hash(
            form.password.data,
            method="pbkdf2:sha256",
            salt_length=8
        )
        # Crate new user w/ form data
        new_user = User(
            email=form.email.data,
            username=form.username.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            password=hashed_password
        )
        # Utilise try/except adding user or returning with error
        try:
            # Create user and add
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            flash("You have registered.", "info")
            return redirect(url_for("home"))
        # If user already within database, rollback and redirect
        except IntegrityError:
            db.session.rollback()
            flash("That User is already Registered, Please try and login.", "danger")
            return redirect(url_for("login"))
    # Render registration form
    return render_template("register.html", form=form)

@app.route('/login', methods=["POST", "GET"])
def login():
    form = LoginForm()
    # Ceck if user is already logged in, if so redirect (blocks access)
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    # Check if user POST login details
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()
        # Check user stored password w/ entered 
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("You are Now Logged In", "info")
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        # Action when user not in DB (does not exist), redirecting to registration
        elif not user:
            flash("That Email does not exist, Please register", "danger")
            return redirect(url_for("register"))
        else:
            flash('Invalid Username or Password', 'danger')
            return redirect(url_for("login"))
    return render_template("login.html", form=form)

# Logout route, Only access if logged in
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

# calls WTForm (AddMovie), passing data into API (filmsearch), renders results @ /select
@app.route("/add", methods=["POST", "GET"])
def add_movie():
    api_temp = MovieSearch()
    form = AddMovie()
    if form.validate_on_submit():
        movie_title_input = form.title.data
        api_data = api_temp.search_api(movie_title_input)
        num_titles = api_data["total_results"]
        return render_template('select.html', data=api_data, total=num_titles)
    return render_template('add.html', form=form)

# Uses existing API film ID to grab more info, then adds to db, returning errors w/ try/except
@app.route("/get-movie-details", methods=["GET"])
def create_movie_entry():
    movie_id = request.args.get('id')
    api_ext = MovieSearch()
    api_data = api_ext.more_details(movie_id)
    img_url_end = api_data["poster_path"]
    new_movie = Movie(
        title=api_data["original_title"],
        year=api_data["release_date"],
        description=api_data["overview"],
        rating=0,
        ranking=0,
        review="NONE",
        img_url=f"https://image.tmdb.org/t/p/w600_and_h900_bestv2{img_url_end}"
    )
    try:
        db.session.add(new_movie)
        db.session.commit()
        i = db.session.execute(db.select(Movie).where(Movie.title == api_data["original_title"])).scalar()
        new_movie_id = i.id
        flash("That Film has been added to your Library, Please add another", "info")
    except IntegrityError:
        db.session.rollback()
        flash("That Film is already in your Library, Please try again.", "danger")
        return redirect(url_for('home'))
    except Exception as e:
        db.session.rollback()
        print(f"An unexpected error occurred: {str(e)}")
        return redirect(url_for('home', status=True))
    return redirect(url_for('edit', id=new_movie_id))

# Allows user to edit data of existing film and/or newly added film.
@app.route("/edit", methods=["GET", "POST"])
def edit():
    movie_id = request.args.get('id')
    form = RateMovieForm()
    if form.validate_on_submit():
        movie_to_update = db.get_or_404(Movie, movie_id)
        movie_to_update.rating = form.rating.data
        movie_to_update.review = form.review.data
        movie_to_update.ranking = form.ranking.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('edit.html', form=form)

# Allows user to delete entry by db ID, removes all data
@app.route("/delete", methods=["GET"])
def delete():
    movie_id = request.args.get('id')
    movie_to_delete = db.get_or_404(Movie, movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))

#  Checks to see IF file has been ran directly e.g. py main.py; True if so
#  if the file is imported as a module, statment is False
if __name__ == '__main__':
    # app refers to flask instance called above
    app.run(debug=True, port=5002)
