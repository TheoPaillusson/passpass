from app import create_app, db, login_manager
from flask import render_template, redirect, flash, url_for, request
from app.models.chapter import Chapter
from app import db
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

#blueprints
from app.controllers.auth_controller import auth_bp
from app.controllers.users_controller import users_bp
from app.controllers.admin_controller import admin_bp

app = create_app()

app.register_blueprint(auth_bp)
app.register_blueprint(users_bp)
app.register_blueprint(admin_bp)


register_commands(app)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, user_id)

@app.route("/")
def home():
    return render_template("home.html")

if __name__ == '__main__':
    app.run(debug=True)