from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import json

app = Flask(__name__)

# --- AI SETUP ---
# Put the API key you got from Google AI Studio right here!
genai.configure(api_key="AIzaSyA-bMfgptWyEMphqkyU9MAr1B-oZ_T0ZOc")

# --- CORE AI BEHAVIORAL ALGORITHM ---
def calculate_attention_score(accuracy, time_taken, tab_switches):
    score = accuracy
    TAB_PENALTY = 15 # Lose 15 points per tab switch
    score -= (tab_switches * TAB_PENALTY)
    return round(max(0, min(100, score)), 2)

# --- ROUTES ---
@app.route('/')
def home():
    return render_template('index.html')

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
    
    # Advanced Prompt Engineering
    prompt = f"""
    Act as a strict, expert university professor. Read the following text:
    "{source_text}"

    Generate exactly 3 difficult, university-level multiple-choice questions based on this text.
    Do not ask simple factual recall questions. Ask questions that require critical thinking, application, or deep comprehension.
    The incorrect options (distractors) must be highly plausible to challenge the student.

    Respond ONLY with a valid JSON array matching this exact format, with no markdown or extra text:
    [
      {{
        "question": "Complex question text...",
        "option_a": "Plausible wrong answer",
        "option_b": "Another plausible wrong answer",
        "option_c": "The actual correct answer",
        "option_d": "A tricky wrong answer",
        "correct_option": "c"
      }}
    ]
    """
    
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content(prompt)
    
    # Clean up the text so Python can read it as JSON
    clean_text = response.text.replace('```json', '').replace('```', '').strip()
    generated_questions = json.loads(clean_text)
    
    return jsonify(generated_questions)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')