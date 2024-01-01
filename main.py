from flask import Flask, render_template, redirect, url_for, request
from dotenv import load_dotenv
import os
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField
from wtforms.validators import DataRequired
from sqlalchemy.exc import IntegrityError
import requests
from filmsearch import MovieSearch
from flask import flash

# Loads .env, creats app, applys CSRF key and db url
load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv('SQL_DATABASE')
bootstrap = Bootstrap5(app)
db = SQLAlchemy(app)


# Create movie database
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(80), nullable=False)
    rating = db.Column(db.Float(5))
    ranking = db.Column(db.Integer)
    review = db.Column(db.String(80))
    img_url = db.Column(db.String(80), nullable=False)

    def __repr__(self):
        return f"< Movie {self.title} ranked: {self.ranking}>"

# WTForm; Used for adding customer ranking, rating and review. Gets called @Edit
class RateMovieForm(FlaskForm):
    rating = StringField('Your rating out of 10 e.g. 7.5', validators=[DataRequired()])
    review = StringField('Your Review', validators=[DataRequired()])
    ranking = IntegerField('Your new ranking', validators=[DataRequired()])
    submit = SubmitField("Update")

# WTForm for Movie API search. Gets called @add_movie
class AddMovie(FlaskForm):
    title = StringField('Movie Title', validators=[DataRequired()])
    sumit = SubmitField("Add Movie")

# Sets app content for all db interactions
with app.app_context():
    db.create_all()


@app.route("/")
def home():
    all_movies = Movie.query.order_by(Movie.rating.desc()).all()
    return render_template("index.html", data=all_movies)

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

# Runs app in debug
if __name__ == '__main__':
    app.run(debug=True)
