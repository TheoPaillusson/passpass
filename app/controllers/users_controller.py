from flask import Blueprint
from app import  db
from flask import render_template, redirect, flash, url_for, request
from app.models.chapter import Chapter
from app.models.question import Question
from app.models.quiz import Quiz
from app.models.score import Score
from app.models.subject import Subject
from app.models.user import User
from flask_login import  login_required, current_user
from random import shuffle, random
from app.forms import TestMeForm


users_bp = Blueprint('users', __name__)

@users_bp.route("/dashboard")
@login_required
def dashboard():
    scores = Score.query.filter_by(user_id=current_user.id).all()
    total_attempted_quizzes = len(scores)

    average_score = sum([s.total_scored for s in scores]) / total_attempted_quizzes if total_attempted_quizzes > 0 else 0


    quizzes = Quiz.query.all()
    return render_template("user/dashboard.html",
                           scores=scores,
                           total_attempted_quizzes=total_attempted_quizzes, 
                           average_score=average_score)

@users_bp.route('/attempt_quiz/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
def attempt_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = quiz.questions.copy()

    full_questions = []
    for q in questions:
        full_questions.append(q)
        full_questions.extend(q.sub_questions)

    if request.method == 'POST':
        score = 0
        for question in full_questions:
            selected_answers = request.form.getlist(f'question_{question.id}')
            correct_answers = set(question.correct_options.split(',')) if question.correct_options else set()
            
            if set(selected_answers) == correct_answers:
                score+= 1

        existing_score = Score.query.filter_by(user_id=current_user.id, quiz_id=quiz_id).first()
            
        # Mise à jour du score existant
        if existing_score:
            existing_score.total_scored = score
            db.session.commit()
        else:
            user_score = Score(
                total_scored = score,
                quiz_id = quiz_id,
                user_id = current_user.id,  
            )
            db.session.add(user_score)
            db.session.commit()
        flash(f'Votre score : {score}/{len(full_questions)}', category="success")
        return redirect(url_for("users.quiz_results", 
                                quiz_id=quiz_id, 
                                scored=score, 
                                total=len(full_questions)))
    
    test = request.args.get("test")
    return render_template("user/attempt_quiz.html", quiz=quiz, questions=full_questions, test=test)

@users_bp.route('/quiz_results/<int:quiz_id>', )
@login_required
def quiz_results(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    score = Score.query.filter_by(user_id=current_user.id, quiz_id=quiz_id).first()
    len_quiz = sum(1 + len(q.sub_questions) for q in quiz.questions)
     
    return render_template("user/quiz_results.html", quiz=quiz, score=score, len_quiz=len_quiz)

@users_bp.route('/leaderboard')
@login_required
def leaderboard():
    users = User.get_all_users()
    leaderboard_data = []
    for user in users:
        scores = Score.query.filter_by(user_id=user.id).all()
        total_score = sum([s.total_scored for s in scores])
        leaderboard_data.append({
            "user_fullname": user.fullname,
            "total_score": total_score
        })
        leaderboard_data.sort(key=lambda x:x['total_score'], reverse=True)
        user_fullnames = [x['user_fullname'] for x in leaderboard_data]
        user_total_scores = [x["total_score"] for x in leaderboard_data]
    return render_template('user/leaderboard.html',
                           leaderboard_data=leaderboard_data,
                           user_fullnames=user_fullnames,
                           user_total_scores=user_total_scores)

@users_bp.route('/select-quiz', methods=['GET', 'POST'])
@login_required
def select_quiz():
    subjects = Subject.query.all()
    chapters = Chapter.query.all()
    quizzes = Quiz.query.all()

    if request.method =='POST':
        subject_id = request.form.get('subject_id')
        chapter_id = request.form.get('chapter_id')
        if subject_id:
            quizzes = Quiz.query.join(Chapter).filter(Chapter.subject_id == subject_id).all()
        if chapter_id:
            quizzes = Quiz.query.filter_by(chapter_id=chapter_id).all()

    return render_template("user/select-quiz.html", 
                           subjects=subjects,
                           chapters=chapters,
                           quizzes=quizzes)


@users_bp.route("/test_me", methods=["GET", "POST"])
@login_required
def test_me():
    subjects = Subject.query.order_by(Subject.name).all()
    selected_subject_id = request.form.get("subject_id", type=int)
    selected_chapter_ids = request.form.getlist("chapter_ids", type=int)
    number = request.form.get("number_of_questions", type=int)

    chapters = []
    selected_questions = []

    if selected_subject_id:
        chapters = Chapter.query.filter_by(subject_id=selected_subject_id).order_by(Chapter.name).all()

    if request.method == "POST" and selected_chapter_ids and number:
        quizzes = Quiz.query.filter(Quiz.chapter_id.in_(selected_chapter_ids)).all()
        quiz_ids = [quiz.id for quiz in quizzes]
        all_questions = Question.query.filter(Question.quiz_id.in_(quiz_ids)).all()
        selected_questions = random.sample(all_questions, min(len(all_questions), number))
        return render_template("user/test_me_results.html", questions=selected_questions)

    return render_template("user/test_me.html",
                           subjects=subjects,
                           chapters=chapters,
                           selected_subject_id=selected_subject_id,
                           selected_chapter_ids=selected_chapter_ids,
                           number=number)
