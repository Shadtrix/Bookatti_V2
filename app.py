from flask import (Flask, render_template, request, jsonify,
                   redirect, url_for, flash)  # Flask for creating the web application
from flask import Blueprint, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
from books import books  # Import the book data
from librarybooks import librarybooks


# Initialize Flask app
app = Flask(__name__)
bcrypt = Bcrypt(app)
# Database configuration
app.secret_key = "your_secret_key"  # Secret key for securely managing sessions in Flask
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'  # SQLite
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Avoid warnings
db = SQLAlchemy()
db.init_app(app)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)


class SignUpForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    email = StringField(validators=[
        InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Bookati@gmail.com"})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(username=username.data).first()
        if existing_user_username:
            raise ValidationError('That username already exists. Please choose a different one.')


class LoginForm(FlaskForm):
    username = StringField(validators=[
        InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    email = StringField(validators=[
        InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Bookati@gmail.com"})

    password = PasswordField(validators=[
        InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Login')


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/bookstore")
def bookstore():
    return render_template('bookstore.html', books=books)  # Pass the book data to the template


@app.route("/library")
def library_home():
    return render_template("library_home.html")


@app.route("/book-loan")
def book_loan():
    return render_template("book_loan.html", books=librarybooks)


@app.route("/audiobooks")
def audiobooks():
    return render_template("audiobooks.html")


@app.route("/enquiries")
def enquiries():
    return render_template("enquiries.html")


@app.route("/events")
def events():
    return render_template("events.html")


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember_me.data)
            flash("Login successful!", "success")
            return redirect(url_for('home'))
        else:
            flash("Invalid username or password.", "danger")

    return render_template("login.html", form=form)


@app.route("/sign-up", methods=['GET', 'POST'])
def sign_up():
    form = SignUpForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template("sign_up.html", form=form)


if __name__ == "__main__":
    app.run(debug=True)
