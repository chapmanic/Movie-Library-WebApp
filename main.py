from flask import Flask, render_template, redirect, url_for, request
from dotenv import load_dotenv
from flask_bootstrap import Bootstrap5
from flask_login import login_user, LoginManager, current_user, logout_user, login_required
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask import flash
from forms import RegistrationForm, LoginForm, RateMovieForm, AddMovie
from models import User, Movie, db
import os
from filmsearch import MovieSearch
from datetime import date


# Load .env
load_dotenv()

# Creating an Instance of the Flask Class; Tracks configurations, URL rules, template locations, etc.
app = Flask(__name__)

# Set Secret Key for (CSRF) Cross-site request forgery
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Set image file location (.env) & Set MAX size for content
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max size

# Create Instance for BootStrap
bootstrap = Bootstrap5(app)
# Create login instance,
login_manager = LoginManager()
    # initialises with app
login_manager.init_app(app)
    # Redirects to here, creates endpoint
login_manager.login_view = "login"

# Set DB Key
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv('SQL_DATABASE')
db.init_app(app)
with app.app_context():
    db.create_all()
    
# Create a user_loader callback
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, user_id)

# Sets app with context() method allowing globally accessible
with app.app_context():
    # Checks current state of DB, creates tables if non-existent 
    db.create_all()
    # Not Best for Production builds *** Use Flask-Migrate / Alembic

# Users Movie database page -----------------------------------------------------
@app.route("/mymovies", methods=["POST", "GET"])
@login_required
def mymovies():
    all_movies = db.session.execute(
        db.select(Movie)
        .where(Movie.user_id == current_user.id)
        .order_by(Movie.rating.desc())
    ).scalars()
    return render_template("mymovies.html", data=all_movies)

# Home page, featuring public movies --------------------------------------------
@app.route("/", methods=["POST", "GET"])
def home():
    public_all_movies = db.session.execute(
        db.select(Movie)
        .order_by(Movie.rating.desc())
    ).scalars()
    return render_template("index.html", public_data=public_all_movies)

# Route for Registering Users ---------------------------------------------------
@app.route("/register", methods=["POST", "GET"])
def register():
    # Create form variable (imported from forms.py)
    form = RegistrationForm()
    # Check if users is authenticated, If so redirect
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    # Check IF POST and form correct
    if request.method == "POST" and form.validate():
        # Check passwords match, return warning if false
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
            password=hashed_password,
            date=date.today().strftime("%B %d, %Y"),
            avatar_img="people-default.jpg",
        )
        # Save image to file, add name to User table
        if form.avatar_img.data:
            avatar_img_file = form.avatar_img.data
            filename = secure_filename(avatar_img_file.filename)
            avatar_img_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            new_user.avatar_img = filename
        # Utilise try/except adding user or returning with error
        try:
            # Create user and add
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            flash("You have registered.", "info")
            return redirect(url_for("mymovies"))
        # If user already within database, rollback and redirect
        except IntegrityError:
            db.session.rollback()
            flash("That User is already Registered, Please try and login.", "danger")
            return redirect(url_for("login"))
    # Render registration form
    return render_template("register.html", form=form)

# Login Route/Page ----------------------------------------------------------------
@app.route('/login', methods=["POST", "GET"])
def login():
    form = LoginForm()
    # Check if user is already logged in, if so redirect (blocks access)
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
            return redirect(next_page) if next_page else redirect(url_for('mymovies'))
        # Action when user not in DB (does not exist), redirecting to registration
        elif not user:
            flash("That Email does not exist, Please register", "danger")
            return redirect(url_for("register"))
        else:
            flash('Invalid Username or Password', 'danger')
            return redirect(url_for("login"))
    return render_template("login.html", form=form)

# Logout route, Only access if logged in -------------------------------------------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

# calls WTForm (AddMovie), passing data into API (FilmSearch), renders results @ /select
@app.route("/add", methods=["POST", "GET"])
@login_required
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
@login_required
def create_movie_entry():
    movie_id = request.args.get('id')
    api_ext = MovieSearch()
    api_data = api_ext.more_details(movie_id)
    img_url_end = api_data["poster_path"]
    new_movie = Movie(
        user_id=current_user.id,
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
        # return redirect(url_for("edit"))
    except IntegrityError:
        db.session.rollback()
        flash("That Film is already in your Library, Please try again.", "danger")
        return redirect(url_for('mymovies'))
    except Exception as e:
        db.session.rollback()
        print(f"An unexpected error occurred: {str(e)}")
        return redirect(url_for('mymovies', status=True))
    return redirect(url_for('edit', id=new_movie_id))

# Allows user to edit data of existing film and/or newly added film.
@app.route("/edit", methods=["GET", "POST"])
@login_required
def edit():
    movie_id = request.args.get('id')
    form = RateMovieForm()
    if form.validate_on_submit():
        movie_to_update = db.get_or_404(Movie, movie_id)
        movie_to_update.rating = form.rating.data
        movie_to_update.review = form.review.data
        movie_to_update.ranking = form.ranking.data
        db.session.commit()
        return redirect(url_for('mymovies'))
    return render_template('edit.html', form=form)

# Allows user to delete entry by db ID, removes all data
@app.route("/delete", methods=["GET"])
@login_required
def delete():
    movie_id = request.args.get('id')
    movie_to_delete = db.get_or_404(Movie, movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('mymovies'))

@app.route("/profile/<int:user_id>", methods=["POST", "GET"])
@login_required
def profile(user_id):
    # form = Create user form
    user_items = db.get_or_404(User, user_id)
    # Check if user is auth, if so move on
    # Check if form Value (user modifying data, place back into BD)
    return render_template("userprofile.html")


#  Checks to see IF file has been ran directly e.g. py main.py; True if so
#  if the file is imported as a module, statement is False
if __name__ == '__main__':
    # app refers to flask instance called above
    app.run(debug=True)
