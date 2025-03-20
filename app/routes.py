from app import create_app, db
from flask import render_template, redirect, flash, url_for
from app.models import User, Subject, Chapter, Quiz, Question, Score
from app.forms import RegisterForm, LoginForm


app = create_app()

@app.cli.command('db-create')
def create_db():
    db.create_all()
    print("Database created")

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        flash('Création de compte réussie !', category="success")
        return redirect(url_for('login'))
    return render_template("register.html", form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        flash('Authentification réussie !', category="success")
        return redirect(url_for('dashboard'))
    return render_template("login.html", form=form)


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")