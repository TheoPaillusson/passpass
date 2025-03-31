from app import create_app, db, login_manager
from flask import render_template, redirect, flash, url_for, request
from app.models import User, Subject, Chapter, Quiz, Question, Score
from app.forms import RegisterForm, LoginForm, SubjectForm, ChapterForm, QuizForm, QuestionForm
from flask_login import login_user, login_required, logout_user, current_user
from dotenv import load_dotenv
from seed import seed_database
from random import shuffle
import os

app = create_app()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

@app.cli.command('db-create')
def create_db():
    db.create_all()
    # create the admin
    admin = User.query.filter_by(username=os.getenv('ADMIN_USERNAME')).first()
    if not admin:
        admin = User(
            username="admin@admin.com",
            fullname="Administrateur"
        )
        admin.set_password(os.getenv('ADMIN_PASSWORD'))
        db.session.add(admin)
        db.session.commit()
        print("Compte administrateur créé")
    else:
        print("Compte administrateur déjà créé")
    print("Database created")

@app.cli.command('db-seed')
def seed_db():
    seed_database()
    print ("Database seeded successfully")


@app.route("/")
def home():
    return render_template("home.html")

##### ADMIN ROUTES #####

@app.route("/admin/login", methods=['GET', 'POST'])
def admin_login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=os.getenv('ADMIN_USERNAME')).first()
        if user and user.username == form.username.data and user.check_password(form.password.data):
            login_user(user)
            flash("Administrateur connecté", category="success")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Nom ou mot de passe invalide", category="error")
    return render_template("admin/login.html", form=form)

@app.route("/admin/dashboard")
@login_required
def admin_dashboard():
    if current_user.username != os.getenv('ADMIN_USERNAME'):
        flash("Vous n'avez pas accès à cette page", category="error")
        return redirect(url_for('home'))
    quizzes = Quiz.query.all()
    quiz_names = [quiz.name for quiz in quizzes]
    average_scores = []
    completion_rates = []

    for quiz in quizzes:
        scores = Score.query.filter_by(quiz_id=quiz.id).all()
        if scores:
            average_score = sum([s.total_scored for s in scores]) / len(scores)
            users_attempted = len(scores)       
            completion_rate = (users_attempted / (User.query.count() - 1)) * 100 # moins un pour ne pas prendre en compte l'admin
        else:
            average_score = 0
            completion_rate = 0
        average_scores.append(average_score)
        completion_rates.append(completion_rate)
    return render_template("admin/dashboard.html", 
                           quiz_names=quiz_names,
                           average_scores=average_scores,
                           completion_rates=completion_rates)

# Subjects #
@app.route("/admin/manage_subjects")
@login_required
def manage_subjects():
    if current_user.username != os.getenv('ADMIN_USERNAME'):
        flash("Vous n'avez pas accès à cette page", category="error")
        return redirect(url_for('home'))
    subjects = Subject.query.all()
    return render_template('admin/manage_subjects.html', subjects=subjects)

@app.route('/admin/add_subject', methods=['GET', 'POST'])
@login_required
def add_subject():
    if current_user.username != os.getenv('ADMIN_USERNAME'):
        flash("Vous n'avez pas accès à cette page", category="error")
        return redirect(url_for('home'))
    form = SubjectForm()
    if form.validate_on_submit():
        subject = Subject(name=form.name.data,
                          description = form.description.data)
        db.session.add(subject)
        db.session.commit()
        flash('Subject enregistré avec succès', category="success")
        return redirect(url_for('manage_subjects'))
    return render_template("admin/add_subject.html", form=form)

@app.route('/admin/edit_subject/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_subject(id):
    if current_user.username != os.getenv('ADMIN_USERNAME'):
        flash("Vous n'avez pas accès à cette page", category="error")
        return redirect(url_for('home'))
    subject = Subject.query.get_or_404(id)
    form = SubjectForm(obj=subject)
    if form.validate_on_submit():
        subject.name = form.name.data
        subject.description = form.description.data
        db.session.commit()
        flash("Subject modifié avec succès", category="success")
    return render_template("admin/edit_subject.html", form=form)

@app.route('/admin/delete_subject/<int:id>', methods=['POST'])
@login_required
def delete_subject(id):
    if current_user.username != os.getenv('ADMIN_USERNAME'):
        flash("Vous n'avez pas accès à cette page", category="error")
        return redirect(url_for('home'))
    subject = Subject.query.get_or_404(id)
    db.session.delete(subject)
    db.session.commit()
    flash("Subject supprimé avec succès", category="success")
    return redirect(url_for('manage_subjects'))

# Chapters #
@app.route("/admin/manage_chapters")
@login_required
def manage_chapters():
    if current_user.username != os.getenv('ADMIN_USERNAME'):
        flash("Vous n'avez pas accès à cette page", category="error")
        return redirect(url_for('home'))
    chapters = Chapter.query.all()
    return render_template('admin/manage_chapters.html', chapters=chapters)

@app.route('/admin/add_chapter', methods=['GET', 'POST'])
@login_required
def add_chapter():
    if current_user.username != os.getenv('ADMIN_USERNAME'):
        flash("Vous n'avez pas accès à cette page", category="error")
        return redirect(url_for('home'))
    form = ChapterForm()
    form.subject_id.choices = [(s.id, s.name) for s in Subject.query.all()]
    if form.validate_on_submit():
        chapter = Chapter(name=form.name.data,
                          description = form.description.data,
                          subject_id = form.subject_id.data)
        db.session.add(chapter)
        db.session.commit()
        flash('Chapter enregistré avec succès', category="success")
        return redirect(url_for('manage_chapters'))
    return render_template("admin/add_chapter.html", form=form)

@app.route('/admin/edit_chapter/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_chapter(id):
    if current_user.username != os.getenv('ADMIN_USERNAME'):
        flash("Vous n'avez pas accès à cette page", category="error")
        return redirect(url_for('home'))
    chapter = Chapter.query.get_or_404(id)
    form = ChapterForm(obj=chapter)
    form.subject_id.choices = [(s.id, s.name) for s in Subject.query.all()]
    if form.validate_on_submit():
        chapter.name = form.name.data
        chapter.description = form.description.data
        chapter.subject_id = form.subject_id.data
        db.session.commit()
        flash("Chapter modifié avec succès", category="success")
        return redirect(url_for('manage_chapters'))

    return render_template("admin/edit_chapter.html", form=form)

@app.route('/admin/delete_chapter/<int:id>', methods=['POST'])
@login_required
def delete_chapter(id):
    if current_user.username != os.getenv('ADMIN_USERNAME'):
        flash("Vous n'avez pas accès à cette page", category="error")
        return redirect(url_for('home'))
    chapter = Chapter.query.get_or_404(id)
    db.session.delete(chapter)
    db.session.commit()
    flash("Chapter supprimé avec succès", category="success")
    return redirect(url_for('manage_chapters'))

# Questions #

@app.route('/admin/manage_quiz_questions/<int:quiz_id>')
@login_required
def manage_quiz_questions(quiz_id):
    if current_user.username != os.getenv('ADMIN_USERNAME'):
        flash("Vous n'avez pas accès à cette page", category="error")
        return redirect(url_for('home'))    
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = quiz.questions
    return render_template("admin/manage_quiz_questions.html", quiz=quiz, questions=questions)

@app.route('/admin/add_questions/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
def add_question(quiz_id):
    if current_user.username != os.getenv('ADMIN_USERNAME'):
        flash("Vous n'avez pas accès à cette page", category="error")
        return redirect(url_for('home'))   
    form = QuestionForm()
    if form.validate_on_submit():
        question = Question(
            question_statement = form.question_statement.data,
            option1 = form.option1.data,
            option2 = form.option2.data,
            option3 = form.option3.data,
            option4 = form.option4.data,
            correct_option = form.correct_option.data,
            quiz_id = quiz_id
        )
        db.session.add(question)
        db.session.commit()
        flash('Question ajoutée avec succès', category="success")
        return redirect(url_for('manage_quiz_questions', quiz_id=quiz_id))
    return render_template('admin/add_questions.html', form=form, quiz_id=quiz_id)

# Quiz #
@app.route("/admin/manage_quizzes")
@login_required
def manage_quizzes():
    if current_user.username != os.getenv('ADMIN_USERNAME'):
        flash("Vous n'avez pas accès à cette page", category="error")
        return redirect(url_for('home'))
    quizzes = Quiz.query.all()
    return render_template('admin/manage_quizzes.html', quizzes=quizzes)

@app.route('/admin/add_quiz', methods=['GET', 'POST'])
@login_required
def add_quiz():
    if current_user.username != os.getenv('ADMIN_USERNAME'):
        flash("Vous n'avez pas accès à cette page", category="error")
        return redirect(url_for('home'))
    form = QuizForm()
    form.chapter_id.choices = [(c.id, c.name) for c in Chapter.query.all()]
    if form.validate_on_submit():
        quiz = Quiz(
            name = form.name.data,
            date_of_quiz = form.date_of_quiz.data,
            time_duration = form.time_duration.data,
            chapter_id = form.chapter_id.data
        )
        db.session.add(quiz)
        db.session.commit()
        flash('Chapter enregistré avec succès', category="success")
        return redirect(url_for('manage_quizzes'))
    return render_template("admin/add_quiz.html", form=form)

@app.route('/admin/edit_quiz/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_quiz(id):
    if current_user.username != os.getenv('ADMIN_USERNAME'):
        flash("Vous n'avez pas accès à cette page", category="error")
        return redirect(url_for('home'))
    quiz = Quiz.query.get_or_404(id)
    form = QuizForm(obj=quiz)
    form.chapter_id.choices = [(c.id, c.name) for c in Chapter.query.all()]
    if form.validate_on_submit():
            quiz.name = form.name.data
            quiz.date_of_quiz = form.date_of_quiz.data
            quiz.time_duration = form.time_duration.data
            quiz.chapter_id = form.chapter_id.data
            db.session.commit()
            flash("Quiz modifié avec succès", category="success")
            return redirect(url_for('manage_quizzes'))
    return render_template("admin/edit_quiz.html", form=form)

@app.route('/admin/delete_quiz/<int:id>', methods=['POST'])
@login_required
def delete_quiz(id):
    if current_user.username != os.getenv('ADMIN_USERNAME'):
        flash("Vous n'avez pas accès à cette page", category="error")
        return redirect(url_for('home'))
    quiz = Quiz.query.get_or_404(id)
    db.session.delete(quiz)
    db.session.commit()
    flash("Quiz supprimé avec succès", category="success")
    return redirect(url_for('manage_quizzes'))


# Users #
@app.route("/admin/manage_users")
@login_required
def manage_users():
    if current_user.username != os.getenv('ADMIN_USERNAME'):
        flash("Vous n'avez pas accès à cette page", category="error")
        return redirect(url_for('home'))
    users = User.query.all()
    return render_template('admin/manage_users.html', users=users)

@app.route("/register", methods=['GET', 'POST'])
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
        db.session.add(user)
        db.session.commit()
        flash('Création de compte réussie !', category="success")
        return redirect(url_for('login'))
    return render_template("register.html", form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Authentification réussie !', category="success")
            return redirect(url_for('dashboard'))
        else:
            flash("Authentification échouée", category="error") 
    return render_template("login.html", form=form)

@app.route("/dashboard")
@login_required
def dashboard():
    quizzes = Quiz.query.all()
    return render_template("dashboard.html", quizzes=quizzes)


@app.route('/quiz/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
def attempt_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = quiz.questions.copy()
    shuffle(questions)
    if request.method == 'POST':
        score = 0
        for question in questions:
            user_answer = request.form.get(f'question_{question.id}')
            if user_answer and int(user_answer) == question.correct_option:
                score += 1
        user_score = Score(
            total_scored = score,
            quiz_id = quiz_id,
            user_id = current_user.id,  
        )
        db.session.add(user_score)
        db.session.commit()
        flash(f'Votre score : {score}/{len(questions)}', category="success")
        return redirect(url_for("quiz_results", quiz_id=quiz_id))
    return render_template("attempt_quiz.html", quiz=quiz, questions=questions)

@app.route('/quiz_results/<int:quiz_id>', )
@login_required
def quiz_results(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    score = Score.query.filter_by(user_id=current_user.id, quiz_id=quiz_id).first()
    return render_template("quiz_results.html", quiz=quiz, score=score)



# Scores #

##### END OF ADMIN ROUTES #####

##### CRUD ROUTES #####

##### END OF CRUD ROUTES #####

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash('Vous vous êtes déconnecté', category="success")
    return redirect(url_for('login'))