from app import db

class SubQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_statement = db.Column(db.Text, nullable=False)
    question_image = db.Column(db.String(255), nullable=True)
    option1 = db.Column(db.String, nullable=False)
    option2 = db.Column(db.String, nullable=True)
    option3 = db.Column(db.String, nullable=True)
    option4 = db.Column(db.String, nullable=True)
    option5 = db.Column(db.String, nullable=True)
    correct_options = db.Column(db.String, nullable=False)

    main_question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    question  = db.relationship('Question', backref=db.backref('sub_questions', cascade='all, delete-orphan'))

    def get_options(self):
        options = [
            (1, self.option1),
            (2, self.option2),
            (3, self.option3),
            (4, self.option4),
            (5, self.option5),
        ]
        return [(index, opt) for index, opt in options if opt]
