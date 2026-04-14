from flask import Flask
from .models import db, User
import os

def create_app():
    app = Flask(__name__)
    
    app.config['SECRET_KEY'] = 'super-secret-key-change-this'

    # DATABASE CONFIGURATION 
    db_url = os.environ.get('DATABASE_URL')
    
    if db_url:
       
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    elif os.environ.get('VERCEL') == '1':
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/database.db'
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
        
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    with app.app_context():
        db.create_all() 
  
        if not User.query.filter_by(username='prof_bhavesh').first():
            teacher = User(username='prof_bhavesh', role='teacher')
            teacher.set_password('admin')
            db.session.add(teacher)
 
        if not User.query.filter_by(username='aditya').first():
            student1 = User(username='aditya', role='student', branch='BTech AIML', year='2nd Year (SE)', division='A Div', batch='A-1')
            student1.set_password('pass')
            db.session.add(student1)
 
        if not User.query.filter_by(username='lavanya').first():
            student2 = User(username='lavanya', role='student', branch='BTech AIML', year='2nd Year (SE)', division='B Div', batch='B-1')
            student2.set_password('pass')
            db.session.add(student2)

        if not User.query.filter_by(username='vihanga').first():
            student3 = User(username='vihanga', role='student', branch='BTech AIML', year='2nd Year (SE)', division='B Div', batch='B-1')
            student3.set_password('pass')
            db.session.add(student3)
            
        if not User.query.filter_by(username='ishaan').first():
            student4 = User(username='ishaan', role='student', branch='BTech AIML', year='2nd Year (SE)', division='A Div', batch='A-3')
            student4.set_password('pass')
            db.session.add(student4)
            
        db.session.commit()

    from . import routes
    app.register_blueprint(routes.bp)

    return app