from app import db
from datetime import datetime
import uuid

class UserAnswer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    question = db.relationship("Question")

    subquestion_id = db.Column(db.Integer, db.ForeignKey('sub_question.id'), nullable=True)
    subquestion = db.relationship("SubQuestion")
    
    selected_options = db.Column(db.String, nullable=False)  # stocké en format CSV ex : "A,B"
    is_correct = db.Column(db.Boolean, nullable=False)
    batch_id = db.Column(db.String(36), index=True, nullable=False)  # UUID
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    