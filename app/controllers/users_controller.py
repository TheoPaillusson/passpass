from flask import Blueprint, session
from app import  db
from flask import render_template, redirect, flash, url_for, request
from app.models.chapter import Chapter
from app.models.question import Question
from app.models.quiz import Quiz
from app.models.score import Score
from app.models.subject import Subject
from app.models.user import User
from app.models.questionattempt import QuestionAttempt
from app.models.useranswer import UserAnswer
from app.models.subquestion import SubQuestion
from flask_login import  login_required, current_user
import random
from app.forms import TestMeForm
import uuid
from sqlalchemy.orm import joinedload

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

@users_bp.route('/attempt_quiz/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
def attempt_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = quiz.questions.copy()

    full_questions = []
    for q in questions:
        if q:
            full_questions.append(q)
            full_questions.extend(q.sub_questions)

    if request.method == 'POST':
        score = 0
        batch_id = str(uuid.uuid4())
        session["last_batch_id"] = batch_id

        for question in full_questions:
            selected_answers = request.form.getlist(f'question_{question.id}')
            correct_answers = set(question.correct_options.split(',')) if question.correct_options else set()

            is_correct = set(selected_answers) == correct_answers
            if is_correct:
                score += 1
                user_answer = UserAnswer(
                    user_id=current_user.id,
                    question_id=question.id,
                    selected_options=",".join(selected_answers),
                    is_correct=is_correct,
                    batch_id=batch_id
                )
                db.session.add(user_answer)

            # Enregistrer ou mettre à jour la tentative
            attempt = QuestionAttempt.query.filter_by(user_id=current_user.id, question_id=question.id).first()
            if attempt:
                attempt.is_correct = is_correct
            else:
                attempt = QuestionAttempt(user_id=current_user.id, question_id=question.id, is_correct=is_correct)
                db.session.add(attempt)

        existing_score = Score.query.filter_by(user_id=current_user.id, quiz_id=quiz_id).first()
        if existing_score:
            existing_score.total_scored = score
        else:
            user_score = Score(
                total_scored=score,
                quiz_id=quiz_id,
                user_id=current_user.id,
            )
            db.session.add(user_score)

        db.session.commit()
        flash(f'Votre score : {score}/{len(full_questions)}', category="success")
        return redirect(url_for("users.quiz_results", quiz_id=quiz_id, scored=score, total=len(full_questions)))

    test = request.args.get("test")
    return render_template("user/attempt_quiz.html", quiz=quiz, questions=full_questions, test=test)

@users_bp.route('/quiz_results/<int:quiz_id>', )
@login_required
def quiz_results(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    score = Score.query.filter_by(user_id=current_user.id, quiz_id=quiz_id).first()
    len_quiz = sum(1 + len(q.sub_questions) for q in quiz.questions)
     
    return render_template("user/quiz_results.html", quiz=quiz, score=score, len_quiz=len_quiz)

@users_bp.route("/test_me", methods=["GET", "POST"])
@login_required
def test_me():
    subjects = Subject.query.order_by(Subject.name).all()
    selected_subject_id = request.form.get("subject_id", type=int)
    selected_chapter_ids = request.form.getlist("chapter_ids", type=int)
    number = request.form.get("number_of_questions", type=int)
    only_unanswered_or_wrong = bool(request.form.get("only_unanswered_or_wrong"))

    chapters = []
    selected_questions = []

    if selected_subject_id:
        chapters = Chapter.query.filter_by(subject_id=selected_subject_id).order_by(Chapter.name).all()

    if request.method == "POST" and selected_chapter_ids and number:
        quizzes = Quiz.query.filter(Quiz.chapter_id.in_(selected_chapter_ids)).all()
        quiz_ids = [quiz.id for quiz in quizzes]
        all_questions = Question.query.filter(Question.quiz_id.in_(quiz_ids)).all()

        if only_unanswered_or_wrong:
            attempted_question_ids = db.session.query(QuestionAttempt.question_id)\
                .filter(QuestionAttempt.user_id == current_user.id,
                        QuestionAttempt.is_correct == True).all()
            attempted_ids_set = set(qid for (qid,) in attempted_question_ids)

            # Filtrer les questions jamais réussies
            all_questions = [q for q in all_questions if q.id not in attempted_ids_set]

        selected_questions = random.sample(all_questions, min(len(all_questions), number))

        # Stocker les IDs des questions dans la session
        session["test_question_ids"] = [q.id for q in selected_questions]
        return redirect(url_for("users.attempt_test"))

    return render_template("user/test_me.html",
                           subjects=subjects,
                           chapters=chapters,
                           selected_subject_id=selected_subject_id,
                           selected_chapter_ids=selected_chapter_ids,
                           number=number,
                           only_unanswered_or_wrong=only_unanswered_or_wrong)

@users_bp.route('/attempt_test', methods=['GET', 'POST'])
@login_required
def attempt_test():
    question_ids = session.get("test_question_ids", [])
    if not question_ids:
        flash("Aucune question sélectionnée pour ce test.", "warning")
        return redirect(url_for("users.test_me"))

    questions = Question.query.filter(Question.id.in_(question_ids)).all()

    full_questions = []
    for q in questions:
        full_questions.append(q)
        full_questions.extend(q.sub_questions)

    if request.method == 'POST':
        score = 0
        batch_id = str(uuid.uuid4())
        session["last_batch_id"] = batch_id

        print("Form Data:", request.form)  # Debug print

        for question in full_questions:
            if isinstance(question, SubQuestion):
                form_field_name = f"subquestion_{question.id}"
            else:
                form_field_name = f"question_{question.id}"

            selected_answers = request.form.getlist(form_field_name)

            # Debug: Print retrieved answers
            print(f"{form_field_name} selected:", selected_answers)

            correct_answers = set(question.correct_options.split(',')) if question.correct_options else set()
            is_correct = set(selected_answers) == correct_answers
            if is_correct:
                score += 1

            # Check if an existing UserAnswer record exists
            user_answer = UserAnswer.query.filter_by(
                user_id=current_user.id,
                question_id=question.main_question_id if isinstance(question, SubQuestion) else question.id,
                subquestion_id=question.id if isinstance(question, SubQuestion) else None,
                batch_id=batch_id
            ).first()

            if user_answer:
                user_answer.selected_options = ",".join(selected_answers)
                user_answer.is_correct = is_correct
            else:
                user_answer = UserAnswer(
                    user_id=current_user.id,
                    question_id=question.main_question_id if isinstance(question, SubQuestion) else question.id,
                    subquestion_id=question.id if isinstance(question, SubQuestion) else None,
                    selected_options=",".join(selected_answers),
                    is_correct=is_correct,
                    batch_id=batch_id,
                )
                db.session.add(user_answer)

            # Check if an existing QuestionAttempt record exists
            existing_attempt = QuestionAttempt.query.filter_by(
                user_id=current_user.id,
                question_id=question.main_question_id if isinstance(question, SubQuestion) else question.id
            ).first()

            if existing_attempt:
                existing_attempt.is_correct = is_correct
            else:
                attempt = QuestionAttempt(
                    user_id=current_user.id,
                    question_id=question.main_question_id if isinstance(question, SubQuestion) else question.id,
                    is_correct=is_correct
                )
                db.session.add(attempt)

        db.session.commit()
        flash(f'Votre score : {score}/{len(full_questions)}', category="success")
        session.pop("test_question_ids", None)
        return redirect(url_for("users.test_results", scored=score, total=len(full_questions)))

    return render_template("user/attempt_test.html", questions=full_questions)

@users_bp.route('/test_results')
@login_required
def test_results():
    scored = request.args.get("scored", type=int)
    total = request.args.get("total", type=int)

    if scored is None or total is None:
        flash("Résultat du test introuvable.", "warning")
        return redirect(url_for("users.test_me"))

    return render_template("user/test_results.html", scored=scored, total=total)

@users_bp.route('/correction')
@login_required
def correction():
    batch_id = session.get("last_batch_id")
    if not batch_id:
        flash("Aucune correction disponible.", "warning")
        return redirect(url_for("users.test_me"))

    # Retrieve all answers for the given batch with eager loading
    answers = UserAnswer.query.options(
        db.joinedload(UserAnswer.question),
        db.joinedload(UserAnswer.subquestion)
    ).filter_by(
        user_id=current_user.id,
        batch_id=batch_id
    ).all()

    questions_with_answers = []

    for answer in answers:
        print("⤵ ID:", answer.id)
        print("→ subquestion_id:", answer.subquestion_id)
        print("→ subquestion object:", answer.subquestion)
        print("→ question_id:", answer.question_id)
        print("→ question object:", answer.question)

        if answer.subquestion_id is not None and answer.subquestion is not None:
            sub = answer.subquestion
            questions_with_answers.append({
                "question": sub,
                "selected": answer.selected_options.split(","),
                "correct": set(sub.correct_options.split(",")) if sub.correct_options else set(),
                "is_correct": answer.is_correct,
                "correction": sub.correction,
                "is_subquestion": True
            })
        elif answer.question is not None:
            question = answer.question
            questions_with_answers.append({
                "question": question,
                "selected": answer.selected_options.split(","),
                "correct": set(question.correct_options.split(",")) if question.correct_options else set(),
                "is_correct": answer.is_correct,
                "correction": question.correction,
                "is_subquestion": False
            })

    for q in questions_with_answers:
        print("→", "SUB" if q["is_subquestion"] else "MAIN", q["question"].question_statement)

    return render_template("user/correction.html", questions=questions_with_answers)
