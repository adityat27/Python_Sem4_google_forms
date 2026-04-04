from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    branch = db.Column(db.String(100), nullable=True)
    year = db.Column(db.String(50), nullable=True)
    division = db.Column(db.String(20), nullable=True)
    batch = db.Column(db.String(20), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    is_ai_generated = db.Column(db.Boolean, default=False)
    questions = db.relationship('Question', backref='quiz', lazy=True)
    time_limit = db.Column(db.Integer, default=5) # 5 minutes default
    questions = db.relationship('Question', backref='quiz', lazy=True)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    options_data = db.Column(db.JSON, nullable=False)

# NEW: This saves the student's final score for the teacher to see!
class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(80), nullable=False)
    attention_score = db.Column(db.Float, nullable=False)
    time_taken = db.Column(db.Integer, nullable=False)
    tab_switches = db.Column(db.Integer, nullable=False)
    video_filename = db.Column(db.String(255), nullable=True)
    question_times = db.Column(db.JSON, nullable=True)
    auto_submitted = db.Column(db.Boolean, default=False)
    question_results = db.Column(db.JSON, nullable=True)
    tab_timestamps = db.Column(db.JSON, nullable=True)