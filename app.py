from flask import Flask, render_template, request, jsonify  # Flask for creating the web application

# Initialize Flask app
app = Flask(_name_)
app.secret_key = "your_secret_key"  # Secret key for securely managing sessions in Flask
@app.route("/")
def home():
    return render_template("home.html")
@app.route("/shop")
def shop():
    return render_template("shop.html")


@app.route("/library")
def library_home():
    return render_template("library_home.html")


@app.route("/book-loan")
def book_loan():
    return render_template("book_loan.html")


@app.route("/audiobooks")
def audiobooks():
    return render_template("audiobooks.html")


@app.route("/enquiries")
def enquiries():
    return render_template("enquiries.html")


@app.route("/events")
def events():
    return render_template("events.html")

@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/sign-up")
def sign_up():
    return render_template("sign_up.html")

if _name_ == "_main_":
    app.run(debug=True)