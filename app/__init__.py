from flask import Flask
from .models import db, User
import os

def create_app():
    app = Flask(__name__)
    
    app.config['SECRET_KEY'] = 'super-secret-key-change-this'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    with app.app_context():
        db.create_all() 
        
        if not User.query.filter_by(username='prof_aditya').first():
            teacher = User(username='prof_aditya', role='teacher')
            teacher.set_password('admin')
            db.session.add(teacher)
            
        if not User.query.filter_by(username='student1').first():
            student = User(username='student1', role='student',branch='BTech AIML',
                year='2nd Year (SE)',
                division='A Div',
                batch='A-1')
            student.set_password('pass')
            db.session.add(student)
            
        db.session.commit()

    from . import routes
    app.register_blueprint(routes.bp)

    return app