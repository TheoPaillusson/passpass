import os
from app import db
import csv
from config.seed import seed_database
from app.models.user import User
from app.models.chapter import Chapter
from app.models.subject import Subject
from app.models.question import Question
from app.models.subquestion import SubQuestion
from app.models.quiz import Quiz




def create_admin():
    admin = User.query.filter_by(username=os.getenv('ADMIN_USERNAME')).first()
    if not admin:
        admin = User(
            username= os.getenv('ADMIN_USERNAME'),
            fullname="Administrateur",
            is_admin=True
        )
        admin.set_password(os.getenv('ADMIN_PASSWORD'))
        db.session.add(admin)
        db.session.commit()
        print("Compte administrateur créé")
    else:
        print("Compte administrateur déjà créé")


def register_commands(app):
    @app.cli.group('db')
    def db_group():
        pass
    @db_group.command('create')
    def create_db():
        db.create_all()
        create_admin()
        print("Database created")
    @db_group.command('seed')
    def seed_db():
        seed_database()
        print ("Database seeded successfully")

    @db_group.command('ingest')
    def ingest_data():
        file_path = os.path.join(os.path.dirname(__file__), 'ingest.csv')
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return

        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            questions_by_csv_id = {}  # Stocke les correspondances CSV ID → DB ID

            for i, row in enumerate(reader):
                is_sub = row.get("is_subquestion", "").strip().lower() == 'true'

                # Obtenir ou créer la matière
                subject = Subject.query.filter_by(name=row['subject_name']).first()
                if not subject:
                    subject = Subject(name=row['subject_name'])
                    db.session.add(subject)
                    db.session.commit()

                # Obtenir ou créer le chapitre
                chapter = Chapter.query.filter_by(name=row['chapter_name'], subject_id=subject.id).first()
                if not chapter:
                    chapter = Chapter(name=row['chapter_name'], subject_id=subject.id)
                    db.session.add(chapter)
                    db.session.commit()

                # Obtenir ou créer le quiz
                quiz = Quiz.query.filter_by(name=row['quiz_name'], chapter_id=chapter.id).first()
                if not quiz:
                    quiz = Quiz(name=row['quiz_name'], chapter_id=chapter.id)
                    db.session.add(quiz)
                    db.session.commit()

                if is_sub:
                    parent_temp_id = row['parent_question_id']
                    parent_real_id = questions_by_csv_id.get(parent_temp_id)

                    if parent_real_id is None:
                        print(f"❌ Parent question with ID {parent_temp_id} not found. Skipping sub-question.")
                        continue

                    parent_question = Question.query.get(parent_real_id)
                    if not parent_question:
                        print(f"❌ Parent question with DB ID {parent_real_id} not found in database. Skipping.")
                        continue

                    sub_q = SubQuestion(
                        question_statement=row['question_statement'],
                        question_image=row['image_filename'] or None,
                        option1=row['option1'],
                        option2=row['option2'] or None,
                        option3=row['option3'] or None,
                        option4=row['option4'] or None,
                        option5=row['option5'] or None,
                        correct_options=row['correct_options'],
                        parent=parent_question  # ✅ Lien direct à l’objet SQLAlchemy
                    )
                    db.session.add(sub_q)

                else:
                    question = Question(
                        question_statement=row['question_statement'],
                        image_filename=row['image_filename'] or None,
                        option1=row['option1'],
                        option2=row['option2'] or None,
                        option3=row['option3'] or None,
                        option4=row['option4'] or None,
                        option5=row['option5'] or None,
                        correct_options=row['correct_options'],
                        quiz_id=quiz.id
                    )
                    db.session.add(question)
                    db.session.flush()  # pour avoir l’ID immédiatement

                    # Stocke l’ID réel pour permettre d’y référer depuis les sous-questions
                    csv_id = row.get("question_id")
                    if csv_id:
                        questions_by_csv_id[csv_id] = question.id

            db.session.commit()
            print("✅ Questions (et sous-questions) ingested successfully.") 