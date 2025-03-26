from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, DateField, SubmitField, TextAreaField, SelectField, IntegerField, DateTimeField, DateTimeLocalField
from wtforms.validators import Email, Length, EqualTo, DataRequired

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
    date_of_quiz = DateTimeLocalField('Date of Quiz', validators=[DataRequired()])
    time_duration = IntegerField('Time Duration (In Seconds)', validators=[DataRequired()])
    chapter_id = SelectField('Chapter', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Submit')                    