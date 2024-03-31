from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import relationship

# Create Instance for DB; SQLAlchemy
db = SQLAlchemy()

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
    date = db.Column(db.String(250), nullable=False)
    avatar_img = db.Column(db.String(250), nullable=True)
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
    year = db.Column(db.String(30), nullable=True)
    description = db.Column(db.String(80), nullable=False)
    rating = db.Column(db.Float(5))
    ranking = db.Column(db.Integer)
    review = db.Column(db.String(80))
    img_url = db.Column(db.String(80), nullable=False)
    # __repr__ defines how instances are represented as strings (supporting debug)
    # Printing Movie as an Object returns the f sting below
    def __repr__(self):
        return f"< Movie {self.title} ranked: {self.ranking}>"