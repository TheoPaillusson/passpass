from app import create_app, db, login_manager
from app.models.chapter import Chapter
from app.models.question import Question
from app.models.quiz import Quiz
from app.models.score import Score
from app.models.subject import Subject
from app.models.user import User
from app.forms import RegisterForm, LoginForm, SubjectForm, ChapterForm, QuizForm, QuestionForm
from flask_login import login_user, login_required, logout_user, current_user
from dotenv import load_dotenv
from random import shuffle
from config.commands import register_commands
import os
from flask import Blueprint, render_template, redirect, flash, url_for, request


auth_bp = Blueprint('auth', __name__)

##### Authentification #####

@auth_bp.route("/register", methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
                    username = form.username.data,
                    fullname = form.fullname.data,
                    qualification = form.qualification.data,
                    dob = form.dob.data
        )
        user.set_password(form.password.data)

        try:
            db.session.add(user)
            db.session.commit()
            flash('Création de compte réussie !', category="success")
            return redirect(url_for('auth.login'))
        except:
            flash('Email déjà renseigné', category="error")
            return redirect(url_for('auth.register'))

    return render_template("register.html", form=form)

@auth_bp.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            if user.is_admin:
                flash("Administrateur connecté", category="success")
                return redirect(url_for("admin.admin_dashboard"))
            else:
                flash('Authentification réussie !', category="success")
                return redirect(url_for('users.dashboard'))
        else:
            flash("Nom ou mot de passe invalide", category="error") 
    return render_template("login.html", form=form)

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash('Vous vous êtes déconnecté', category="success")
    return redirect(url_for('auth.login'))
