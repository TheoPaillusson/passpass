from app import db 


class QuestionAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

    user = db.relationship('User', back_populates='question_attempts')
    question = db.relationship('Question', back_populates='question_attempts')    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'question_id', name='unique_user_question'),
    )
