from flask import Flask, render_template, request, jsonify
import json
import os
from dotenv import load_dotenv


# --- ENVIRONMENT SETUP ---
load_dotenv()
app = Flask(__name__)

# --- AI SETUP ---
import google.genai as genai
api_key = os.getenv("API_KEY")
if not api_key:
    print("ERROR: API_KEY environment variable not set")
    client = None
else:
    client = genai.Client(api_key=api_key)

def calculate_attention_score(accuracy, time_taken, tab_switches):
    score = accuracy
    TAB_PENALTY = 15
    score -= (tab_switches * TAB_PENALTY)
    return round(max(0, min(100, score)), 2)

# --- PAGE ROUTES ---
@app.route('/')
def main_page():
    return render_template('main.html')

@app.route('/create')
def create_page():
    return render_template('create.html')

@app.route('/quiz')
def quiz_page():
    return render_template('quiz.html')

@app.route('/score')
def score_page():
    return render_template('score.html')

@app.route('/leaderboard')
def leaderboard_page():
    return render_template('leaderboard.html')

@app.route('/teacher')
def teacher_page():
    return render_template('teacher.html')

# --- API ROUTES ---
@app.route('/api/submit', methods=['POST'])
def submit_assessment():
    data = request.json
    tab_switches = data.get('switches', 0)
    time_taken = data.get('time_taken', 1)
    accuracy = data.get('accuracy', 0)
    
    attention_score = calculate_attention_score(accuracy, time_taken, tab_switches)
    
    return jsonify({
        "status": "success",
        "attention_score": attention_score,
        "time_taken": time_taken,
        "switches": tab_switches
    })

# --- AI GENERATOR ROUTE ---
@app.route('/api/generate', methods=['POST'])
def generate_quiz():
    source_text = request.json.get('text', '')
    
    # 1. Load the AI configuration from the JSON file
    try:
        with open('teacher_config.json', 'r') as config_file:
            config = json.load(config_file)
    except FileNotFoundError:
        print("Error: teacher_config.json not found.")
        return jsonify({"error": "Configuration file missing"}), 500

    # 2. Build the prompt dynamically
    prompt = f"""
    {config['persona']}
    
    OBJECTIVE:
    {config['objective']}
    
    PARAMETERS:
    {chr(10).join(['- ' + param for param in config['parameters']])}

    OUTPUT FORMAT:
    {config['output_format']}
    Must match this exact structure: {json.dumps(config['json_schema_example'])}
    
    SOURCE TEXT TO ANALYZE:
    "{source_text}"
    """
    
    # 3. Call the AI with error handling and native JSON mode
    try:
        if client is None:
            return jsonify({"error": "AI service not configured"}), 500
        
        # This tells the model to ONLY output raw JSON
        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=prompt,
            config=genai.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        generated_questions = json.loads(response.text)
        return jsonify(generated_questions)
        
    except Exception as e:
        # This will print the exact reason for the failure in your Python terminal!
        print(f"CRITICAL AI ERROR: {str(e)}")
        return jsonify({"error": "AI generation failed. Check terminal for details."}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')