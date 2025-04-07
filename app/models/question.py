from app import db 

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_statement = db.Column(db.Text)
    image_filename = db.Column(db.String(255), nullable=True)
    option1 = db.Column(db.String, nullable=False)
    option2 = db.Column(db.String, nullable=True)
    option3 = db.Column(db.String, nullable=True)
    option4 = db.Column(db.String, nullable=True)
    option5 = db.Column(db.String, nullable=True)
    correct_options = db.Column(db.String, nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)