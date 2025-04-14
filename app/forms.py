from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, DateField, SubmitField, TextAreaField, SelectField, IntegerField, DateTimeLocalField, SelectMultipleField, FieldList, FormField, HiddenField
from wtforms.validators import Email, Length, EqualTo, DataRequired, Optional, NumberRange
from flask_wtf.file import FileField, FileAllowed


class RegisterForm(FlaskForm):
    username = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(),EqualTo('password')])
    fullname = StringField('Full Name')
    qualification = StringField('Qualification')
    dob = DateField('Date of Birth', format="%Y-%m-%d", validators=[DataRequired()])
    submit = SubmitField('Submit')

class LoginForm(FlaskForm):
    username = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    submit = SubmitField('Submit')

class SubjectForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description')
    submit = SubmitField('Submit')

class ChapterForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description')
    subject_id = SelectField('Subject', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Submit')

class QuizForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    date_of_quiz = DateTimeLocalField('Date of Quiz', validators=[DataRequired()])
    time_duration = IntegerField('Time Duration (In Seconds)')
    chapter_id = SelectField('Chapter', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Submit')     

class SubQuestionForm(FlaskForm):
    question_statement = StringField('Énoncé de la sous-question', validators=[DataRequired()])
    question_image = FileField('Image', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images seulement')])
    image_filename = HiddenField() # pour afficher l'image de la sous question
    option1 = StringField('Option 1', validators=[DataRequired()])
    option2 = StringField('Option 2', validators=[DataRequired()])
    option3 = StringField('Option 3')
    option4 = StringField('Option 4')
    option5 = StringField('Option 5')
    correct_options = TextAreaField('Bonne(s) réponse(s)', validators=[DataRequired()])

    class Meta:
        csrf = False #DÉSACTIVATION du CSRF pour les sous-formulaires

class QuestionForm(FlaskForm):
    question_statement = TextAreaField('Question Statement', validators=[DataRequired()])
    question_image = FileField('Question Image', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif'], 'Formats acceptés : jpg, jpeg, png, gif')])
    option1 = StringField('Option 1', validators=[DataRequired()])
    option2 = StringField('Option 2', validators=[DataRequired()])
    option3 = StringField('Option 3')
    option4 = StringField('Option 4')
    option5 = StringField('Option 5')
    correct_options = TextAreaField('Correct Option (1-5)', validators=[DataRequired()])
    sub_questions = FieldList(FormField(SubQuestionForm), min_entries=0, label="Sous-Questions")
    submit = SubmitField('Valider')
    total_sub_questions = HiddenField()

class TestMeForm(FlaskForm):
    subject = SelectField("Matière", coerce=int, validators=[DataRequired()])
    chapters = SelectMultipleField("Chapitres", coerce=int, validators=[DataRequired()])
    number_of_questions = IntegerField("Nombre de questions", validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField("Lancer le test")    

