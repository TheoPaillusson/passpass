from flask import Blueprint
from flask_login import UserMixin
from app import db
from flask import render_template, redirect, flash, url_for
from app.models.chapter import Chapter
from app.models.question import Question
from app.models.quiz import Quiz
from app.models.score import Score
from app.models.subject import Subject
from app.models.subquestion import SubQuestion

from app.models.user import User
from app.forms import SubjectForm, ChapterForm, QuizForm, QuestionForm, SubQuestionForm
from flask_login import  login_required,  current_user
import os
from functools import wraps
from flask import request
from werkzeug.datastructures import CombinedMultiDict

# gestion des images
from werkzeug.utils import secure_filename
import uuid
from flask import Flask, current_app



admin_bp = Blueprint('admin', __name__)

def admin_login_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return login_required(func)(*args, **kwargs)
        if not current_user.is_admin:
            flash("Vous n'avez pas accès à cette page", category="error")
            return redirect(url_for('home'))
        return func(*args, **kwargs)

    return decorated_view

@admin_bp.route("/admin/dashboard")
@admin_login_required
def admin_dashboard():
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

@admin_bp.route("/admin/manage_subjects")
@admin_login_required
def manage_subjects():
    subjects = Subject.query.all()
    return render_template('admin/subject/manage_subjects.html', subjects=subjects)

@admin_bp.route('/admin/add_subject', methods=['GET', 'POST'])
@admin_login_required
def add_subject():
    form = SubjectForm()
    if form.validate_on_submit():
        subject = Subject(name=form.name.data,
                          description = form.description.data)
        db.session.add(subject)
        db.session.commit()
        flash('Subject enregistré avec succès', category="success")
        return redirect(url_for('admin.manage_subjects'))
    return render_template("admin/subject/add_subject.html", form=form)

@admin_bp.route('/admin/edit_subject/<int:id>', methods=['GET', 'POST'])
@admin_login_required
def edit_subject(id):
    subject = Subject.query.get_or_404(id)
    form = SubjectForm(obj=subject)
    if form.validate_on_submit():
        subject.name = form.name.data
        subject.description = form.description.data
        db.session.commit()
        flash("Subject modifié avec succès", category="success")
    return render_template("admin/subject/edit_subject.html", form=form)

@admin_bp.route('/admin/delete_subject/<int:id>', methods=['POST'])
@admin_login_required
def delete_subject(id):
    subject = Subject.query.get_or_404(id)
    db.session.delete(subject)
    db.session.commit()
    flash("Subject supprimé avec succès", category="success")
    return redirect(url_for('admin.manage_subjects'))

@admin_bp.route("/admin/manage_chapters")
@admin_login_required
def manage_chapters():
    chapters = Chapter.query.all()
    return render_template('admin/chapter/manage_chapters.html', chapters=chapters)

@admin_bp.route('/admin/add_chapter', methods=['GET', 'POST'])
@admin_login_required
def add_chapter():
    form = ChapterForm()
    form.subject_id.choices = [(s.id, s.name) for s in Subject.query.all()]
    if form.validate_on_submit():
        chapter = Chapter(name=form.name.data,
                          description = form.description.data,
                          subject_id = form.subject_id.data)
        db.session.add(chapter)
        db.session.commit()
        flash('Chapter enregistré avec succès', category="success")
        return redirect(url_for('admin.manage_chapters'))
    return render_template("admin/chapter/add_chapter.html", form=form)

@admin_bp.route('/admin/edit_chapter/<int:id>', methods=['GET', 'POST'])
@admin_login_required
def edit_chapter(id):
    chapter = Chapter.query.get_or_404(id)
    form = ChapterForm(obj=chapter)
    form.subject_id.choices = [(s.id, s.name) for s in Subject.query.all()]
    if form.validate_on_submit():
        chapter.name = form.name.data
        chapter.description = form.description.data
        chapter.subject_id = form.subject_id.data
        db.session.commit()
        flash("Chapter modifié avec succès", category="success")
        return redirect(url_for('admin.manage_chapters'))

    return render_template("admin/chapter/edit_chapter.html", form=form)

@admin_bp.route('/admin/delete_chapter/<int:id>', methods=['POST'])
@admin_login_required
def delete_chapter(id):
    chapter = Chapter.query.get_or_404(id)
    db.session.delete(chapter)
    db.session.commit()
    flash("Chapter supprimé avec succès", category="success")
    return redirect(url_for('admin.manage_chapters'))

@admin_bp.route("/admin/quiz/<int:quiz_id>/questions")
@admin_login_required
def manage_questions(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz_id, parent_id=None).all()
    return render_template("admin/question/manage_questions.html",
                           quiz=quiz,
                           questions=questions)

@admin_bp.route('/admin/question/add_questions/<int:quiz_id>', methods=['GET', 'POST'])
@admin_login_required
def add_question(quiz_id):
    form = QuestionForm(prefix="form")
    empty_sub_form = SubQuestionForm(prefix="sub_questions-__prefix__")

    if form.validate_on_submit():
        print("form validé !")
        
        # Traitement de l'image pour la question principale
        image_file = form.question_image.data
        filename = None
        if image_file:
            filename = secure_filename(image_file.filename)
            upload_path = os.path.join(current_app.root_path, 'static/uploads/questions', filename)
            os.makedirs(os.path.dirname(upload_path), exist_ok=True)
            image_file.save(upload_path)

        # Enregistrement de la question principale
        question = Question(
            question_statement=form.question_statement.data,
            image_filename=filename,
            option1=form.option1.data,
            option2=form.option2.data,
            option3=form.option3.data,
            option4=form.option4.data,
            option5=form.option5.data,
            correct_options=form.correct_options.data,
            quiz_id=quiz_id
        )
        db.session.add(question)
        db.session.commit()

        # Traitement des sous-questions
        for subform in form.sub_questions.entries:
            sub_image = subform.form.question_image.data
            sub_filename = None

            if sub_image:
                sub_filename = secure_filename(sub_image.filename)
                sub_image_path = os.path.join(current_app.root_path, 'static/uploads/questions', sub_filename)
                os.makedirs(os.path.dirname(sub_image_path), exist_ok=True)
                sub_image.save(sub_image_path)

            # Enregistrement de chaque sous-question
            sub_question = SubQuestion(
                question_statement=subform.form.question_statement.data,
                question_image=sub_filename,
                option1=subform.form.option1.data,
                option2=subform.form.option2.data,
                option3=subform.form.option3.data,
                option4=subform.form.option4.data,
                option5=subform.form.option5.data,
                correct_options=subform.form.correct_options.data,
                parent=question  # Lien avec la question principale
            )
            db.session.add(sub_question)
        db.session.commit()
        flash('Question (et sous-questions) ajoutée(s) avec succès', category="success")
        return redirect(url_for('admin.manage_questions', quiz_id=quiz_id))
    
    else:
        print('Form errors', form.errors)
    
    return render_template('admin/question/add_questions.html', form=form, quiz_id=quiz_id, empty_sub_form=empty_sub_form)

@admin_bp.route('/admin/question/edit/<int:quiz_id>/<int:question_id>', methods=['GET', 'POST'])
@admin_login_required
def edit_question(quiz_id, question_id):
    question = Question.query.get_or_404(question_id)

    if question.parent_id:
        flash("Impossible d'éditer une sous-question directement.", "warning")
        return redirect(url_for('admin.manage_questions', quiz_id=quiz_id))

    # Initialisation de form avant de manipuler quoi que ce soit
    form = QuestionForm(obj=question) if request.method == 'GET' else QuestionForm(formdata=CombinedMultiDict([request.form, request.files]), meta={'csrf': False})

    # if request.method == 'GET':
    #     for sub in question.sub_questions:
    #         if sub.question_statement.strip():
    #             print(question.sub_questions)
    #             sub_form = SubQuestionForm(obj=sub, prefix=f"sub_questions-{len(form.sub_questions)}")
    #             form.sub_questions.append_entry(sub_form)
    #             print(form.sub_questions)

    if request.method == 'POST':
        prefix_indexes = set()
        for key in request.form:
            if key.startswith("sub_questions-") and "-question_statement" in key:
                try:
                    index = int(key.split('-')[1])
                    prefix_indexes.add(index)
                except ValueError:
                    continue

        total = max(prefix_indexes) + 1 if prefix_indexes else 0        
        form.total_sub_questions.data = len(form.sub_questions.entries)

    # 1. Mise à jour de la question principale
        question.question_statement = form.question_statement.data
        question.option1 = form.option1.data
        question.option2 = form.option2.data
        question.option3 = form.option3.data
        question.option4 = form.option4.data
        question.option5 = form.option5.data
        question.correct_options = form.correct_options.data

    # Image : gestion facultative si modifiée
        image_file = request.files.get(form.question_image.name)
        filename = None
        if image_file and image_file.filename:
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(current_app.root_path, 'static/uploads/questions', filename)
            image_file.save(image_path)
            question.image_filename = filename

        # 2. Suppression des anciennes sous-questions
        for sub in question.sub_questions:
            db.session.delete(sub)

    # 3. Ajout des nouvelles sous-questions
        for i in range(total):
            prefix = f'sub_questions-{i}-'
            # On récupère tous les champs
            statement = request.form.get(prefix + 'question_statement', '').strip()
            options = [
                request.form.get(prefix + 'option1', '').strip(),
                request.form.get(prefix + 'option2', '').strip(),
                request.form.get(prefix + 'option3', '').strip(),
                request.form.get(prefix + 'option4', '').strip(),
                request.form.get(prefix + 'option5', '').strip()
            ]
            correct = request.form.get(prefix + 'correct_options', '').strip()

            sub_question = SubQuestion(
                question_statement=statement,
                option1=options[0],
                option2=options[1],
                option3=options[2],
                option4=options[3],
                option5=options[4],
                correct_options=correct,
                parent=question
            )
            db.session.add(sub_question)

        db.session.commit()  # 🔥 Ne pas oublier ça !

        flash("Question mise à jour avec succès.", "success")
        return redirect(url_for('admin.manage_questions', quiz_id=quiz_id))
    
    return render_template('admin/question/edit_question.html', form=form, question=question)


@admin_bp.route("/admin/quiz/<int:quiz_id>/delete_question/<int:question_id>", methods=['POST'])
@admin_login_required
def delete_question(quiz_id, question_id):
    question = Question.query.get_or_404(question_id)

    if question.parent_id is not None:
        flash("Impossible de supprimer une sous-question directement", category="error")
        return redirect(url_for('admin.manage_questions', quiz_id=quiz_id))
    
    db.session.delete(question)
    db.session.commit()
    flash("Question deleted successfully!", category="success")
    return redirect(url_for("admin.manage_questions", quiz_id=quiz_id))


# Quiz #
@admin_bp.route("/admin/manage_quizzes")
@admin_login_required
def manage_quizzes():
    quizzes = Quiz.query.all()
    return render_template('admin/quiz/manage_quizzes.html', quizzes=quizzes)

@admin_bp.route('/admin/add_quiz', methods=['GET', 'POST'])
@admin_login_required
def add_quiz():
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
        return redirect(url_for('admin.manage_quizzes'))
    return render_template("admin/quiz/add_quiz.html", form=form)

@admin_bp.route('/admin/edit_quiz/<int:id>', methods=['GET', 'POST'])
@admin_login_required
def edit_quiz(id):
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
            return redirect(url_for('admin.manage_quizzes'))
    return render_template("admin/quiz/edit_quiz.html", form=form)

@admin_bp.route('/admin/delete_quiz/<int:id>', methods=['POST'])
@admin_login_required
def delete_quiz(id):
    quiz = Quiz.query.get_or_404(id)
    db.session.delete(quiz)
    db.session.commit()
    flash("Quiz supprimé avec succès", category="success")
    return redirect(url_for('admin.manage_quizzes'))

@admin_bp.route("/admin/manage_users")
@admin_login_required
def manage_users():
    users = User.query.all()
    return render_template('admin/manage_users.html', users=users)