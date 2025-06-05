from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask import make_response
from xhtml2pdf import pisa
from io import BytesIO
from flask_migrate import Migrate
import io
import traceback
import contextlib
from flask import request, jsonify

import os
from dotenv import load_dotenv
import subprocess
import requests
import json

from transformers import pipeline
import tempfile
import subprocess


app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


load_dotenv()

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    skill_level = db.Column(db.String(50), default=None)


# Load the error explanations from the JSON file
with open('python_error_dataset.json', 'r') as file:
    error_explanations = json.load(file)

# Function to get error explanation based on user level
def get_error_explanation(error_name, level):
    for error in error_explanations:
        if error['error'] == error_name:
            if level == 'beginner':
                return error['beginner_explanation']
            elif level == 'intermediate':
                return error['intermediate_explanation']
            else:
                return "Explanation level not recognized."
    return "Error not found."

@app.route('/get_explanation', methods=['POST'])
def get_explanation():
    error_name = request.form.get('error_name')
    level = request.form.get('level')
    explanation = get_error_explanation(error_name, level)
    return jsonify({'explanation': explanation})

# Home route (Dashboard)
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    return render_template('dashboard.html', user=user)

import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv

import os
if not os.path.exists("D:/huggingface"):
    os.makedirs("D:/huggingface")
os.environ["HF_HOME"] = "D:/huggingface"

from flask import request, jsonify
from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL_NAME = "Ankithar/deepseek-model"
HF_TOKEN = os.getenv("HF_TOKEN")  # Set this in Railway → Settings → Variables

# Load model and tokenizer only once at startup
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, token=HF_TOKEN)
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME, token=HF_TOKEN)

@app.route('/optimize_code', methods=['POST'])
def optimize_code():
    data = request.get_json()
    code_input = data['code']

    prompt = f"""You are a Python expert. Optimize the following code for performance and readability.

        ### Original Code
        {code_input}

        ### Optimized Code
    """

    inputs = tokenizer(prompt, return_tensors="pt")

    output_tokens = model.generate(
        **inputs,
        max_new_tokens=256,
        pad_token_id=tokenizer.eos_token_id,
        do_sample=False,
        temperature=0.7
    )

    full_output = tokenizer.decode(output_tokens[0], skip_special_tokens=True)

    # Extract only the optimized part
    optimized_code = full_output.split("### Optimized Code")[-1].strip()

    return jsonify({'optimized_code': optimized_code})


# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        if User.query.filter_by(email=email).first():
            flash('Email already exists. Try logging in.', 'danger')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        new_user = User(name=name, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'danger')
            return redirect(url_for('dashboard'))
    
    return render_template('login.html')

# Home Page
@app.route('/')
def home():
    return render_template('home.html')

# Skill Test
@app.route('/take-skill-test', methods=['GET', 'POST'])
def take_skill_test():
    questions = [
    {"id": 1, "text": "What is the purpose of a for loop in Python?", "topic": "Loops", "options": ["A) Iterate over a sequence", "B) Store data", "C) Define functions", "D) Handle exceptions"]},
    {"id": 2, "text": "Which of the following is an example of recursion?", "topic": "Recursion", "options": ["A) A function calling itself", "B) A for loop", "C) A variable declaration", "D) A conditional statement"]},
    {"id": 3, "text": "What does the 'def' keyword do in Python?", "topic": "Functions", "options": ["A) Defines a function", "B) Defines a class", "C) Creates a variable", "D) Imports a module"]},
    {"id": 4, "text": "What is inheritance in OOP?", "topic": "OOP", "options": ["A) A class inherits properties from another class", "B) A class is defined inside another class", "C) A class contains no methods", "D) A class can be instantiated multiple times"]},
    {"id": 5, "text": "Which of the following is a primitive data type in Python?", "topic": "Data Types", "options": ["A) int", "B) list", "C) dict", "D) set"]},
    {"id": 6, "text": "How do you declare an array in Python?", "topic": "Arrays", "options": ["A) array = [1, 2, 3]", "B) array = (1, 2, 3)", "C) array = {1, 2, 3}", "D) array = 1, 2, 3"]},
    {"id": 7, "text": "Which function is used to reverse a string in Python?", "topic": "Strings", "options": ["A) reverse()", "B) reversed()", "C) flip()", "D) reverse_string()"]},
    {"id": 8, "text": "Which algorithm is used to sort a list in ascending order in Python?", "topic": "Sorting", "options": ["A) Quick sort", "B) Bubble sort", "C) Merge sort", "D) All of the above"]},
    {"id": 9, "text": "What does binary search do?", "topic": "Searching", "options": ["A) Finds an item in a sorted list", "B) Sorts a list", "C) Performs addition on numbers", "D) Multiplies two numbers"]},
    {"id": 10, "text": "What is a stack data structure?", "topic": "Stacks", "options": ["A) LIFO (Last In, First Out) principle", "B) FIFO (First In, First Out) principle", "C) A collection of unordered elements", "D) A linear data structure with random access"]},
    {"id": 11, "text": "What is the main feature of a queue data structure?", "topic": "Queues", "options": ["A) FIFO (First In, First Out) principle", "B) LIFO (Last In, First Out) principle", "C) Dynamic size", "D) Random access"]},
    {"id": 12, "text": "Which operation does a linked list support?", "topic": "Linked Lists", "options": ["A) Insertion", "B) Deletion", "C) Traversal", "D) All of the above"]},
    {"id": 13, "text": "What is a binary tree?", "topic": "Trees", "options": ["A) A tree where each node has at most two children", "B) A tree with only two nodes", "C) A tree with multiple children", "D) A tree with no children"]},
    {"id": 14, "text": "What is a graph in data structures?", "topic": "Graphs", "options": ["A) A set of vertices connected by edges", "B) A linear data structure", "C) A tree with multiple branches", "D) A sorted list"]},
    {"id": 15, "text": "What is hashing used for in data structures?", "topic": "Hashing", "options": ["A) Storing data in a fixed-size table", "B) Sorting data", "C) Searching data", "D) Storing data in a sequence"]},
]
    if request.method == 'POST':
        # Collect MCQ answers
        mcq_answers = {f"q{i}": request.form.get(f"q{i}") for i in range(1, 16)}
        code_answer_1 = request.form.get("code1", "").strip()
        code_answer_2 = request.form.get("code2", "").strip()

        


        # Correct MCQ answers
        correct_answers = {
    "1": "a",  # Iterate over a sequence
    "2": "a",  # A function calling itself
    "3": "a",  # Defines a function
    "4": "a",  # A class inherits properties from another class
    "5": "a",  # int
    "6": "a",  # array = [1, 2, 3]
    "7": "b",  # reversed()
    "8": "d",  # All of the above (Quick sort, Bubble sort, Merge sort)
    "9": "a",  # Finds an item in a sorted list
    "10": "a", # LIFO (Last In, First Out) principle
    "11": "a", # FIFO (First In, First Out) principle
    "12": "d", # All of the above (Insertion, Deletion, Traversal)
    "13": "a", # A tree where each node has at most two children
    "14": "a", # A set of vertices connected by edges
    "15": "a"  # Storing data in a fixed-size table
}

        # Topics for each MCQ
        topics = {
            "1": "Loops", "2": "Recursion", "3": "Functions", "4": "OOP",
            "5": "Data Types", "6": "Arrays", "7": "Strings", "8": "Sorting",
            "9": "Searching", "10": "Stacks", "11": "Queues", "12": "Linked Lists",
            "13": "Trees", "14": "Graphs", "15": "Hashing"
        }

        # Evaluate MCQs
        score = 0
        topic_scores = {}
        for q, ans in mcq_answers.items():
            question_number = q[1:]  # "q1" -> "1"
            if ans is None:
                continue
            ans = ans.strip().lower()
            correct_ans = correct_answers[question_number].strip().lower()
            correct = ans == correct_ans
            score += correct
            topic = topics[question_number]
            topic_scores[topic] = topic_scores.get(topic, 0) + (1 if correct else 0)


        # Evaluate coding answers
        code_score, code_feedback = evaluate_coding_answers({
                                    'code1': code_answer_1,
                                    'code2': code_answer_2
        })

        # Total score (MCQ + Code)
        total_score = score + code_score

        # Analyze strong, weak, and needs improvement concepts
        strong = [t for t, s in topic_scores.items() if s == 1]
        weak = [t for t, s in topic_scores.items() if s == 0]
        needs_improvement = [t for t, s in topic_scores.items() if 0 < s < 1]

        # Suggested book
        book = "Data Structures and Algorithms Made Easy by Narasimha Karumanchi"

        # Generate the report
        # Strong concepts count
        strong_concepts_count = len(strong)

        # Classify user
        if total_score >= 20 and code_score>5:
            level = "Expert"
        elif total_score >= 13 and code_score>=5:
            level = "Intermediate"
        else:
            level = "Beginner"

        # Final Report
        report = {
            'score': total_score,
            'mcq_score': score,
            'code_score': code_score,
            'level': level,
            'strong_concepts': strong,
            'weak_concepts': weak,
            'needs_improvement': needs_improvement,
            'suggested_book': book,
            'code_feedback': code_feedback
        }

        if 'user_id' in session:
            user = User.query.get(session['user_id'])
            user.skill_level = level
            db.session.commit()


        # Store the report in session
        session['report'] = report

        # Redirect to the skill report page
        return redirect(url_for('skill_report'))

    return render_template("skill_test.html",questions=questions)

@app.route('/run_code_skill', methods=['POST'])
def run_code_skill():
    data = request.get_json()
    code = data.get('code', '')

    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp:
            temp.write(code)
            temp.flush()
            result = subprocess.run(
                ['python', temp.name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )
        output = result.stdout if result.stdout else result.stderr
    except Exception as e:
        output = str(e)

    return jsonify({"output": output})

# Debug
@app.route('/debug_code', methods=['POST'])
def debug_code():
    data = request.get_json()
    error_message = data.get("error", "")
    debug_level = data.get("level", "Beginner")

    try:
        with open('python_error_dataset.json') as f:
            explanations = json.load(f)

        explanation = None
        for entry in explanations:
            if entry['error'].lower() in error_message.lower():
                if debug_level == "Beginner":
                    explanation = entry.get('beginner_explanation')
                elif debug_level == "Intermediate":
                    explanation = entry.get('intermediate_explanation')
                break

        if explanation:
            return jsonify({"message": explanation})
        else:
            return jsonify({"message": "⚠️ Could not find an explanation for the error."})

    except Exception as e:
        return jsonify({"message": f"⚠️ Error reading explanations: {str(e)}"})

        
# Reset Test
@app.route('/reset-test')
def reset_test():
    session.pop('report', None)
    return redirect(url_for('take_skill_test'))

# Skill Report
@app.route('/skill-report')
def skill_report():
    report = session.get('report')
    if not report:
        return redirect(url_for('take_skill_test'))
    return render_template('skill_report.html', report=report)

def evaluate_coding_answers(user_code):
    import io, contextlib
    results = []
    score = 0

    # Prime Checker
    expected_output_1 = "True\nFalse\n"
    try:
        output1 = io.StringIO()
        code1 = user_code['code1'] + "\nprint(prime(7))\nprint(prime(8))"
        with contextlib.redirect_stdout(output1):
            exec(code1, {})
        actual_output1 = output1.getvalue()
        correct1 = actual_output1.strip() == expected_output_1.strip()
        score += 5 if correct1 else 0
        results.append(("Prime Checker", correct1, actual_output1.strip()))
    except Exception as e:
        results.append(("Prime Checker", False, f"Error: {e}"))

    # Factorial
    expected_output_2 = "120\n"
    try:
        output2 = io.StringIO()
        code2 = user_code['code2'] + "\nprint(fact(5))"
        with contextlib.redirect_stdout(output2):
            exec(code2, {})
        actual_output2 = output2.getvalue()
        correct2 = actual_output2.strip() == expected_output_2.strip()
        score += 5 if correct2 else 0
        results.append(("Factorial", correct2, actual_output2.strip()))
    except Exception as e:
        results.append(("Factorial", False, f"Error: {e}"))

    return score, results

# Download PDF
@app.route('/download-pdf')
def download_pdf():
    report = session.get('report')
    if not report:
        return redirect(url_for('skill_report'))

    rendered = render_template('skill_report_pdf.html', report=report)
    pdf = BytesIO()
    pisa.CreatePDF(BytesIO(rendered.encode('utf-8')), dest=pdf)

    response = make_response(pdf.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=skill_report.pdf'
    return response

# Run Code
@app.route('/run_code', methods=['POST'])
def run_code():
    data = request.get_json()
    code = data.get("code", "")

    try:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exec(code, {})
        return jsonify({"output": output.getvalue()})
    except Exception as e:
        # Return full error including the exception type (e.g., NameError: ...)
        error_type = type(e).__name__
        full_error = f"{error_type}: {e}"
        return jsonify({"error": full_error})

# Logout route
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# Initialize DB
@app.before_request
def create_tables():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
