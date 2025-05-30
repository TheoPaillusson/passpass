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
    correction = db.Column(db.Text, nullable=True)
   
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=True)
    sub_questions = db.relationship(
        'SubQuestion', 
        back_populates="parent", 
        cascade = "all, delete-orphan")
    question_attempts = db.relationship('QuestionAttempt', back_populates='question', cascade="all, delete-orphan")
    
    def get_options(self):
        options = [
            (1, self.option1),
            (2, self.option2),
            (3, self.option3),
            (4, self.option4),
            (5, self.option5),
        ]
        return [(index, opt) for index, opt in options if opt]