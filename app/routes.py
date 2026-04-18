from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
import json
import os
import time
from .models import db, User, Quiz, Question, Submission
import google.genai as genai

bp = Blueprint('main', __name__)

api_key = os.getenv("API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

def calculate_attention_score(accuracy, time_taken, tab_switches):
    score = accuracy
    TAB_PENALTY = 15
    score -= (tab_switches * TAB_PENALTY)
    return round(max(0, min(100, score)), 2)

@bp.route('/', methods=['GET', 'POST'])
def login_page():
    error = None
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and user.check_password(request.form.get('password')) and user.role == request.form.get('role'):
            session['user_id'] = user.id
            session['role'] = user.role
            session['username'] = user.username
            return redirect(url_for('main.teacher_page' if user.role == 'teacher' else 'main.main_page'))
        error = "Invalid username, password, or role."
    return render_template('login.html', error=error)

@bp.route('/dashboard')
def main_page(): 
    if 'user_id' not in session: return redirect(url_for('main.login_page'))
    recent_quizzes = Quiz.query.order_by(Quiz.id.desc()).limit(5).all()
    return render_template('main.html', quizzes=recent_quizzes, role=session.get('role'), username=session.get('username'))

@bp.route('/settings')
def settings_page(): 
    if 'user_id' not in session: return redirect(url_for('main.login_page'))
    return render_template('settings.html', role=session.get('role'), username=session.get('username'))

@bp.route('/create')
def create_page(): 
    if session.get('role') != 'teacher': return redirect(url_for('main.main_page'))
    return render_template('create.html')

@bp.route('/manual_create')
def manual_create_page():
    if session.get('role') != 'teacher': return redirect(url_for('main.main_page'))
    return render_template('manual_create.html')

@bp.route('/score')
def score_page(): 
    if 'user_id' not in session: return redirect(url_for('main.login_page'))
    return render_template('score.html')

@bp.route('/leaderboard')
def leaderboard_page(): 
    if 'user_id' not in session: return redirect(url_for('main.login_page'))
    top_scores = Submission.query.order_by(Submission.attention_score.desc()).limit(10).all()
    return render_template('leaderboard.html', leaderboard=top_scores)

@bp.route('/quiz')
def quiz_page(): 
    if 'user_id' not in session: return redirect(url_for('main.login_page'))
    
    latest_quiz = Quiz.query.order_by(Quiz.id.desc()).first()
    if not latest_quiz: return "<h2 style='color:white; font-family:sans-serif;'>No quizzes found!</h2>"
    questions_list = [{'id': q.id, 'question': q.text, 'option_a': q.options_data['a'], 'option_b': q.options_data['b'], 'option_c': q.options_data['c'], 'option_d': q.options_data['d'], 'correct_option': q.options_data['correct']} for q in latest_quiz.questions]
    return render_template('quiz.html', 
                           quiz_title=latest_quiz.title, 
                           quiz_data=json.dumps(questions_list),
                           time_limit=latest_quiz.time_limit)

@bp.route('/teacher')
def teacher_page(): 
    if session.get('role') != 'teacher': return redirect(url_for('main.main_page'))
    
    submissions = Submission.query.order_by(Submission.id.desc()).all()
    students = User.query.filter_by(role='student').all()
    
    analytics = {}
    for sub in submissions:
        if sub.question_results and isinstance(sub.question_results, dict):
            for q, is_correct in sub.question_results.items():
                if q not in analytics:
                    analytics[q] = {'correct': 0, 'total': 0}
                analytics[q]['total'] += 1
                if is_correct:
                    analytics[q]['correct'] += 1
    
    alerts = []
    for q, data in analytics.items():
        if data['total'] > 0:
            success_rate = (data['correct'] / data['total']) * 100
            if success_rate < 50:
                alerts.append({'question': q, 'success_rate': round(success_rate, 1)})
    
    return render_template('teacher.html', submissions=submissions, students=students, alerts=alerts)

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.login_page'))

@bp.route('/api/submit', methods=['POST'])
def submit_assessment():
    if 'video' in request.files:
        video_file = request.files['video']
        data = json.loads(request.form.get('data', '{}'))
        
        os.makedirs('app/static/videos', exist_ok=True)
        filename = f"{session.get('username')}_{int(time.time())}.webm"
        filepath = os.path.join('app/static/videos', filename)
        video_file.save(filepath)
    else:
        data = request.json
        filename = "no_video.webm"

    attention_score = calculate_attention_score(data.get('accuracy', 0), data.get('time_taken', 1), data.get('switches', 0))
    
    student = User.query.get(session.get('user_id'))
    student_name = student.username if student else "Student"
    
    new_submission = Submission(
        student_name=student_name,
        attention_score=attention_score,
        time_taken=data.get('time_taken', 1),
        tab_switches=data.get('switches', 0),
        video_filename=filename,
        question_times=data.get('question_times', {}),
        auto_submitted=data.get('auto_submitted', False),
        question_results=data.get('question_results', {}),
        tab_timestamps=data.get('switch_logs', [])
    )
    db.session.add(new_submission)
    db.session.commit()
    
    return jsonify({"status": "success", "attention_score": attention_score, "time_taken": data.get('time_taken', 1), "switches": data.get('switches', 0)})

@bp.route('/api/save_quiz', methods=['POST'])
def save_quiz():
    data = request.json
    new_quiz = Quiz(
        title=data.get('title', 'Untitled Quiz'), 
        is_ai_generated=data.get('is_ai', False)
    )
    db.session.add(new_quiz)
    db.session.commit()
    for q in data.get('questions', []):
        new_q = Question(quiz_id=new_quiz.id, text=q['question'], options_data={'a': q['option_a'], 'b': q['option_b'], 'c': q['option_c'], 'd': q['option_d'], 'correct': q['correct_option']})
        db.session.add(new_q)
    db.session.commit()
    return jsonify({"status": "success", "quiz_id": new_quiz.id})

@bp.route('/api/generate', methods=['POST'])
def generate_quiz():
    source_text = request.json.get('text', '')
    try:
        mock_questions = [{"question": "Primary Python memory mechanism?", "option_a": "Manual allocation", "option_b": "Reference counting", "option_c": "Pointer arithmetic", "option_d": "Stack clearing", "correct_option": "b"}, {"question": "Why is reference counting alone insufficient?", "option_a": "Too slow", "option_b": "Cannot resolve cycles", "option_c": "Uses too much memory", "option_d": "Requires manual intervention", "correct_option": "b"}]
        if client is None: return jsonify(mock_questions)
        
        base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        config_path = os.path.join(base_dir, 'teacher_config.json')
        
        with open(config_path, 'r') as f: 
            config = json.load(f)
            
        prompt = f"{config['persona']} OBJECTIVE: {config['objective']} FORMAT: {config['output_format']} Must match this exact structure: {json.dumps(config['json_schema_example'])} SOURCE TEXT: {source_text}"
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        raw_text = response.text.strip().replace('```json', '').replace('```', '')
        return jsonify(json.loads(raw_text))
    except Exception as e: 
        print(f"AI Generation Error: {e}")
        return jsonify(mock_questions)