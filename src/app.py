import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_socketio import SocketIO, join_room, emit
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from config.config import db_config, GEMINI_API_KEY
from google import genai
from pydantic import BaseModel, Field
import random
import string
import socket
import time
import math
from typing import Optional
import tempfile
from werkzeug.utils import secure_filename

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# In-memory store for active game state (question start times, streak toggle)
# Key: session_code, Value: dict with question_start_time, streak_enabled, etc.
active_games = {}

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


from contextlib import contextmanager

# Database helper function
def get_db_connection():
    return mysql.connector.connect(**db_config)

@contextmanager
def get_db_cursor(dictionary=False):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=dictionary)
    try:
        yield conn, cursor
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass


def get_quiz_and_check_access(cursor, quiz_id, require_ownership=False):
    """
    Helper function to fetch a quiz and check access permissions.
    Returns (quiz, error_message, redirect_target)
    """
    cursor.execute("SELECT * FROM quizzes WHERE quiz_id = %s", (quiz_id,))
    quiz = cursor.fetchone()

    if not quiz:
        return None, 'Quiz not found', 'index'

    if require_ownership:
        if not current_user.is_authenticated or quiz['created_by'] != int(current_user.id):
            return None, 'You do not have permission to modify this quiz', 'dashboard'
    else:
        if quiz['is_public'] == 0:
            if not current_user.is_authenticated or quiz['created_by'] != int(current_user.id):
                return None, 'You do not have permission to view this private quiz', 'index'

    return quiz, None, None


# User class for Flask-Login
class User(UserMixin):
    def __init__(self, user_id, username, email, role):
        self.id = user_id
        self.username = username
        self.email = email
        self.role = role


# Load user for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    try:
        with get_db_cursor(dictionary=True) as (conn, cursor):
            cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
            user_data = cursor.fetchone()

            if user_data:
                return User(
                    user_id=user_data['user_id'],
                    username=user_data['username'],
                    email=user_data['email'],
                    role=user_data['role']
                )
            return None
    except Exception as e:
        app.logger.error(f"Error loading user: {e}")
        return None



# Home/Landing page
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


# Registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validation
        errors = []

        if len(username) < 3:
            errors.append('Username must be at least 3 characters long')

        if len(password) < 8:
            errors.append('Password must be at least 8 characters long')

        if password != confirm_password:
            errors.append('Passwords do not match')

        if '@' not in email:
            errors.append('Invalid email address')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('register.html')

        # Check if username or email already exists
        try:
            with get_db_cursor() as (conn, cursor):
                cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
                if cursor.fetchone():
                    flash('Username already exists', 'danger')
                    return render_template('register.html')
    
                cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
                if cursor.fetchone():
                    flash('Email already registered', 'danger')
                    return render_template('register.html')
    
                # Hash password and create user
                password_hash = generate_password_hash(password)
    
                cursor.execute(
                    "INSERT INTO users (username, email, password_hash, role) VALUES (%s, %s, %s, %s)",
                    (username, email, password_hash, 'host')  # Default role is 'host'
                )
                conn.commit()

            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))

        except Exception as e:
            flash(f'Registration failed: {str(e)}', 'danger')
            return render_template('register.html')

    return render_template('register.html')


# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        try:
            with get_db_cursor(dictionary=True) as (conn, cursor):
                # Find user by username or email
                cursor.execute(
                    "SELECT * FROM users WHERE username = %s OR email = %s",
                    (username, username)
                )
                user_data = cursor.fetchone()

            if user_data and check_password_hash(user_data['password_hash'], password):
                # Create user object and log in
                user = User(
                    user_id=user_data['user_id'],
                    username=user_data['username'],
                    email=user_data['email'],
                    role=user_data['role']
                )
                login_user(user)
                flash(f'Welcome back, {user.username}!', 'success')

                # Redirect to next page or dashboard
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password', 'danger')

        except Exception as e:
            flash(f'Login failed: {str(e)}', 'danger')

    return render_template('login.html')


# Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))


# Dashboard (requires login)
@app.route('/dashboard')
@login_required
def dashboard():
    try:
        with get_db_cursor(dictionary=True) as (conn, cursor):
            # Get user's quizzes
            cursor.execute(
                """SELECT q.*, COUNT(qs.question_id) as question_count
                   FROM quizzes q
                            LEFT JOIN questions qs ON q.quiz_id = qs.quiz_id
                   WHERE q.created_by = %s
                   GROUP BY q.quiz_id
                   ORDER BY q.created_at DESC""",
                (current_user.id,)
            )
            quizzes = cursor.fetchall()

        return render_template('dashboard.html', quizzes=quizzes)

    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'danger')
        return render_template('dashboard.html', quizzes=[])


# =============================================
# Quiz Management Routes
# =============================================

# Pydantic schemas for AI generation
class GeneratedQuestion(BaseModel):
    question_text: str = Field(description="The actual question text")
    question_type: str = Field(description="Must be one of: multiple_choice, true_false, fill_blank")
    correct_answer: str = Field(description="For multiple_choice, must be exactly 'A', 'B', 'C', or 'D'. For true_false, must be exactly 'A' (True) or 'B' (False). For fill_blank, the exact text answer.")
    option_a: Optional[str] = Field(description="Option A (for multiple choice) or 'True' (for true_false) or null (for fill_blank)")
    option_b: Optional[str] = Field(description="Option B (for multiple choice) or 'False' (for true_false) or null (for fill_blank)")
    option_c: Optional[str] = Field(description="Option C (for multiple choice only)")
    option_d: Optional[str] = Field(description="Option D (for multiple choice only)")
    time_limit: int = Field(description="Time limit in seconds. Suggest 20 for MC, 15 for T/F, 25 for Fill Blank")

class GeneratedQuiz(BaseModel):
    title: str = Field(description="A catchy, relevant title for the quiz")
    description: str = Field(description="A short description of the quiz topic")
    questions: list[GeneratedQuestion]

# Generate Quiz with AI
@app.route('/quiz/generate', methods=['GET', 'POST'])
@login_required
def generate_quiz():
    if request.method == 'POST':
        mode = request.form.get('mode', 'topic')
        is_public = 1 if request.form.get('is_public') else 0
        
        contents = None
        uploaded_file_obj = None
        temp_path = None
        user_defined_title = ''

        try:
            # Prepare Gemini inputs based on mode
            client = genai.Client(api_key=GEMINI_API_KEY)
            
            if mode == 'topic':
                topic = request.form.get('topic', '').strip()
                notes = request.form.get('notes', '').strip()
                num_questions = int(request.form.get('num_questions', 5))
                difficulty = request.form.get('difficulty', 'medium')
                
                if not topic:
                    flash('Topic is required', 'danger')
                    return render_template('generate_quiz.html')
                    
                user_defined_title = topic
                prompt = f"Generate a quiz about '{topic}'."
                if notes:
                    prompt += f" Base the quiz strictly on these notes: {notes}."
                prompt += f" Make it {difficulty} difficulty. Generate exactly {num_questions} questions."
                prompt += " Mix up the question types between multiple_choice, true_false, and fill_blank where appropriate."
                contents = prompt
                
            elif mode == 'document':
                user_defined_title = request.form.get('doc_title', '').strip()
                if not user_defined_title:
                    flash('Quiz Title is required', 'danger')
                    return render_template('generate_quiz.html')
                    
                if 'document' not in request.files:
                    flash('No document uploaded', 'danger')
                    return render_template('generate_quiz.html')
                    
                file = request.files['document']
                if file.filename == '':
                    flash('No selected file', 'danger')
                    return render_template('generate_quiz.html')

                filename = secure_filename(file.filename)
                allowed_extensions = {'.pdf', '.txt'}
                ext = os.path.splitext(filename)[1].lower()
                
                if ext not in allowed_extensions:
                    flash(f'Unsupported file type: {ext}. Please upload a PDF or TXT file.', 'danger')
                    return render_template('generate_quiz.html')
                    
                temp_dir = tempfile.gettempdir()
                # Use a unique identifier to avoid collisions
                temp_path = os.path.join(temp_dir, f"wayoi_{int(time.time())}_{filename}")
                file.save(temp_path)
                
                # Upload to Gemini File API
                uploaded_file_obj = client.files.upload(file=temp_path)
                
                prompt = f"Analyze the attached document and generate a comprehensive quiz. Make the quiz highly relevant to the provided text. Determine the appropriate number of questions based on the length, depth, and detail of the material. Mix up the question types between multiple_choice, true_false, and fill_blank where appropriate."
                contents = [uploaded_file_obj, prompt]
                
            else:
                flash('Invalid generation mode', 'danger')
                return render_template('generate_quiz.html')

            # Call Gemini API
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=contents,
                config=genai.types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=GeneratedQuiz,
                    temperature=0.7,
                ),
            )
            
            quiz_data = GeneratedQuiz.model_validate_json(response.text)
            
            # Prefer the user title for Document Mode, fallback to generated otherwise
            final_title = user_defined_title if mode == 'document' else quiz_data.title
            
            # Save to Database
            with get_db_cursor() as (conn, cursor):
                # 1. Insert Quiz
                cursor.execute(
                    "INSERT INTO quizzes (title, description, created_by, is_public) VALUES (%s, %s, %s, %s)",
                    (final_title, quiz_data.description, current_user.id, is_public)
                )
                conn.commit()
                quiz_id = cursor.lastrowid
                
                # 2. Insert Questions
                order = 1
                for q in quiz_data.questions:
                    # normalize options for DB
                    opt_a = q.option_a if q.question_type == 'multiple_choice' else ('True' if q.question_type == 'true_false' else None)
                    opt_b = q.option_b if q.question_type == 'multiple_choice' else ('False' if q.question_type == 'true_false' else None)
                    opt_c = q.option_c if q.question_type == 'multiple_choice' else None
                    opt_d = q.option_d if q.question_type == 'multiple_choice' else None
                    
                    # Normalization fallback
                    normalized_correct = q.correct_answer.strip()
                    if q.question_type == 'multiple_choice':
                        # Assume Gemini gave 'A', 'B', 'C', or 'D', but if it gave length > 1, try matching the actual options
                        up_correct = normalized_correct.upper()
                        if up_correct not in ['A', 'B', 'C', 'D']:
                            lower_correct = normalized_correct.lower()
                            if opt_a and lower_correct == str(opt_a).strip().lower():
                                normalized_correct = 'A'
                            elif opt_b and lower_correct == str(opt_b).strip().lower():
                                normalized_correct = 'B'
                            elif opt_c and lower_correct == str(opt_c).strip().lower():
                                normalized_correct = 'C'
                            elif opt_d and lower_correct == str(opt_d).strip().lower():
                                normalized_correct = 'D'
                            else:
                                normalized_correct = 'A' # fallback
                        else:
                            normalized_correct = up_correct
                    elif q.question_type == 'true_false':
                        if normalized_correct.upper() == 'TRUE':
                            normalized_correct = 'A'
                        elif normalized_correct.upper() == 'FALSE':
                            normalized_correct = 'B'
                        elif normalized_correct.upper() not in ['A', 'B']:
                            normalized_correct = 'A' # fallback
                        else:
                            normalized_correct = normalized_correct.upper()
                    
                    cursor.execute(
                        """INSERT INTO questions
                           (quiz_id, question_text, question_type, correct_answer,
                            option_a, option_b, option_c, option_d, points, time_limit, question_order)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                        (quiz_id, q.question_text, q.question_type, normalized_correct,
                         opt_a, opt_b, opt_c, opt_d, 1000, q.time_limit, order)
                    )
                    order += 1
                    
                conn.commit()
            
            flash('Quiz successfully generated! Please review and edit if necessary.', 'success')
            return redirect(url_for('edit_quiz', quiz_id=quiz_id))

        except Exception as e:
            app.logger.error(f"Error calling Gemini API: {e}")
            flash('Error generating quiz. Please try again or check your API key.', 'danger')
            return render_template('generate_quiz.html')
            
        finally:
            # Clean up generated files safely
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception as e:
                    app.logger.error(f"Error deleting temp file {temp_path}: {e}")
                    
            if uploaded_file_obj and 'client' in locals():
                try:
                    client.files.delete(name=uploaded_file_obj.name)
                except Exception as e:
                    app.logger.error(f"Error deleting remote file {uploaded_file_obj.name}: {e}")

    return render_template('generate_quiz.html')

# Create Quiz
@app.route('/quiz/create', methods=['GET', 'POST'])
@login_required
def create_quiz():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        is_public = 1 if request.form.get('is_public') else 0

        if not title:
            flash('Quiz title is required', 'danger')
            return render_template('create_quiz.html')

        try:
            with get_db_cursor() as (conn, cursor):
                cursor.execute(
                    "INSERT INTO quizzes (title, description, created_by, is_public) VALUES (%s, %s, %s, %s)",
                    (title, description, current_user.id, is_public)
                )
                conn.commit()
                quiz_id = cursor.lastrowid

            flash('Quiz created successfully! Now add some questions.', 'success')
            return redirect(url_for('edit_quiz', quiz_id=quiz_id))

        except Exception as e:
            flash(f'Error creating quiz: {str(e)}', 'danger')
            return render_template('create_quiz.html')

    return render_template('create_quiz.html')


# View Quiz (read-only)
@app.route('/quiz/<int:quiz_id>')
def view_quiz(quiz_id):
    try:
        with get_db_cursor(dictionary=True) as (conn, cursor):
            quiz, error_msg, redirect_target = get_quiz_and_check_access(cursor, quiz_id, require_ownership=False)
            
            if error_msg:
                flash(error_msg, 'danger')
                return redirect(url_for(redirect_target))
    
            cursor.execute(
                "SELECT * FROM questions WHERE quiz_id = %s ORDER BY question_order ASC",
                (quiz_id,)
            )
            questions = cursor.fetchall()

        return render_template('view_quiz.html', quiz=quiz, questions=questions)

    except Exception as e:
        flash(f'Error loading quiz: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))


# Solo Mode (Test Quiz)
@app.route('/quiz/<int:quiz_id>/solo')
def solo_quiz(quiz_id):
    try:
        with get_db_cursor(dictionary=True) as (conn, cursor):
            quiz, error_msg, redirect_target = get_quiz_and_check_access(cursor, quiz_id, require_ownership=False)
            
            if error_msg:
                flash(error_msg, 'danger')
                return redirect(url_for(redirect_target))
    
            cursor.execute(
                "SELECT * FROM questions WHERE quiz_id = %s ORDER BY question_order ASC",
                (quiz_id,)
            )
            questions = cursor.fetchall()
            
            if not questions:
                flash('Cannot play a quiz with no questions. Please add questions first.', 'danger')
                if current_user.is_authenticated:
                    return redirect(url_for('view_quiz', quiz_id=quiz_id))
                else:
                    return redirect(url_for('index'))

        # Render the solo game interface
        return render_template('solo_game.html', quiz=quiz, questions=questions)

    except Exception as e:
        flash(f'Error loading solo quiz: {str(e)}', 'danger')
        return redirect(url_for('dashboard') if current_user.is_authenticated else url_for('index'))


# Flashcards Mode
@app.route('/quiz/<int:quiz_id>/flashcards')
def flashcards_quiz(quiz_id):
    try:
        with get_db_cursor(dictionary=True) as (conn, cursor):
            quiz, error_msg, redirect_target = get_quiz_and_check_access(cursor, quiz_id, require_ownership=False)
            
            if error_msg:
                flash(error_msg, 'danger')
                return redirect(url_for(redirect_target))
    
            cursor.execute(
                "SELECT * FROM questions WHERE quiz_id = %s ORDER BY question_order ASC",
                (quiz_id,)
            )
            questions = cursor.fetchall()
            
            if not questions:
                flash('Cannot use flashcards with a quiz with no questions. Please add questions first.', 'danger')
                if current_user.is_authenticated:
                    return redirect(url_for('view_quiz', quiz_id=quiz_id))
                else:
                    return redirect(url_for('index'))

        # Render the flashcards interface
        return render_template('flashcards.html', quiz=quiz, questions=questions)

    except Exception as e:
        flash(f'Error loading flashcards: {str(e)}', 'danger')
        return redirect(url_for('dashboard') if current_user.is_authenticated else url_for('index'))


# Edit Quiz
@app.route('/quiz/<int:quiz_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_quiz(quiz_id):
    try:
        with get_db_cursor(dictionary=True) as (conn, cursor):
            quiz, error_msg, redirect_target = get_quiz_and_check_access(cursor, quiz_id, require_ownership=True)
            
            if error_msg:
                flash(error_msg, 'danger')
                return redirect(url_for(redirect_target))
    
            if request.method == 'POST':
                title = request.form.get('title', '').strip()
                description = request.form.get('description', '').strip()
                is_public = 1 if request.form.get('is_public') else 0
    
                if not title:
                    flash('Quiz title is required', 'danger')
                else:
                    cursor.execute(
                        "UPDATE quizzes SET title = %s, description = %s, is_public = %s WHERE quiz_id = %s",
                        (title, description, is_public, quiz_id)
                    )
                    conn.commit()
                    flash('Quiz updated successfully!', 'success')
    
                    # Refresh quiz data
                    cursor.execute("SELECT * FROM quizzes WHERE quiz_id = %s", (quiz_id,))
                    quiz = cursor.fetchone()
    
            # Get questions for this quiz
            cursor.execute(
                "SELECT * FROM questions WHERE quiz_id = %s ORDER BY question_order ASC",
                (quiz_id,)
            )
            questions = cursor.fetchall()

        return render_template('edit_quiz.html', quiz=quiz, questions=questions)

    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))


# Delete Quiz
@app.route('/quiz/<int:quiz_id>/delete', methods=['POST'])
@login_required
def delete_quiz(quiz_id):
    try:
        with get_db_cursor(dictionary=True) as (conn, cursor):
            quiz, error_msg, redirect_target = get_quiz_and_check_access(cursor, quiz_id, require_ownership=True)
            
            if error_msg:
                flash(error_msg, 'danger')
            else:
                cursor.execute("DELETE FROM quizzes WHERE quiz_id = %s", (quiz_id,))
                conn.commit()
                flash('Quiz deleted successfully', 'success')

    except Exception as e:
        flash(f'Error deleting quiz: {str(e)}', 'danger')

    return redirect(url_for('dashboard'))


# =============================================
# Question Management Routes
# =============================================

# Add Question
@app.route('/quiz/<int:quiz_id>/question/add', methods=['GET', 'POST'])
@login_required
def add_question(quiz_id):
    try:
        with get_db_cursor(dictionary=True) as (conn, cursor):
            quiz, error_msg, redirect_target = get_quiz_and_check_access(cursor, quiz_id, require_ownership=True)
            
            if error_msg:
                flash(error_msg, 'danger')
                return redirect(url_for(redirect_target))
    
            if request.method == 'POST':
                question_text = request.form.get('question_text', '').strip()
                question_type = request.form.get('question_type', 'multiple_choice')
                correct_answer = request.form.get('correct_answer', '').strip()
                option_a = request.form.get('option_a', '').strip() or None
                option_b = request.form.get('option_b', '').strip() or None
                option_c = request.form.get('option_c', '').strip() or None
                option_d = request.form.get('option_d', '').strip() or None
                points = int(request.form.get('points', 1000))
                # Default time limits: MC=20s, T/F=15s, Fill-blank=25s
                default_times = {'multiple_choice': 20, 'true_false': 15, 'fill_blank': 25}
                time_limit = int(request.form.get('time_limit', default_times.get(question_type, 20)))
    
                if not question_text:
                    flash('Question text is required', 'danger')
                    return render_template('add_question.html', quiz=quiz)
    
                if not correct_answer:
                    flash('Correct answer is required', 'danger')
                    return render_template('add_question.html', quiz=quiz)
    
                # Handle true/false options
                if question_type == 'true_false':
                    option_a = 'True'
                    option_b = 'False'
                    option_c = None
                    option_d = None
    
                # Handle fill_blank options
                if question_type == 'fill_blank':
                    option_a = None
                    option_b = None
                    option_c = None
                    option_d = None
    
                # Get next question order
                cursor.execute(
                    "SELECT COALESCE(MAX(question_order), 0) + 1 AS next_order FROM questions WHERE quiz_id = %s",
                    (quiz_id,)
                )
                next_order = cursor.fetchone()['next_order']
    
                cursor.execute(
                    """INSERT INTO questions
                       (quiz_id, question_text, question_type, correct_answer,
                        option_a, option_b, option_c, option_d, points, time_limit, question_order)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (quiz_id, question_text, question_type, correct_answer,
                     option_a, option_b, option_c, option_d, points, time_limit, next_order)
                )
                conn.commit()
    
                flash('Question added successfully!', 'success')
                return redirect(url_for('edit_quiz', quiz_id=quiz_id))

        return render_template('add_question.html', quiz=quiz)

    except Exception as e:
        flash(f'Error adding question: {str(e)}', 'danger')
        return redirect(url_for('edit_quiz', quiz_id=quiz_id))


# Edit Question
@app.route('/quiz/<int:quiz_id>/question/<int:question_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_question(quiz_id, question_id):
    try:
        with get_db_cursor(dictionary=True) as (conn, cursor):
            # Verify quiz ownership
            quiz, error_msg, redirect_target = get_quiz_and_check_access(cursor, quiz_id, require_ownership=True)
            
            if error_msg:
                flash(error_msg, 'danger')
                return redirect(url_for(redirect_target))
    
            cursor.execute(
                "SELECT * FROM questions WHERE question_id = %s AND quiz_id = %s",
                (question_id, quiz_id)
            )
            question = cursor.fetchone()
    
            if not question:
                flash('Question not found', 'danger')
                return redirect(url_for('edit_quiz', quiz_id=quiz_id))
    
            if request.method == 'POST':
                question_text = request.form.get('question_text', '').strip()
                question_type = request.form.get('question_type', 'multiple_choice')
                correct_answer = request.form.get('correct_answer', '').strip()
                option_a = request.form.get('option_a', '').strip() or None
                option_b = request.form.get('option_b', '').strip() or None
                option_c = request.form.get('option_c', '').strip() or None
                option_d = request.form.get('option_d', '').strip() or None
                points = int(request.form.get('points', 1000))
                # Default time limits: MC=20s, T/F=15s, Fill-blank=25s
                default_times = {'multiple_choice': 20, 'true_false': 15, 'fill_blank': 25}
                time_limit = int(request.form.get('time_limit', default_times.get(question_type, 20)))
    
                if not question_text or not correct_answer:
                    flash('Question text and correct answer are required', 'danger')
                    return render_template('edit_question.html', quiz=quiz, question=question)
    
                if question_type == 'true_false':
                    option_a = 'True'
                    option_b = 'False'
                    option_c = None
                    option_d = None
    
                if question_type == 'fill_blank':
                    option_a = None
                    option_b = None
                    option_c = None
                    option_d = None
    
                cursor.execute(
                    """UPDATE questions SET
                       question_text = %s, question_type = %s, correct_answer = %s,
                       option_a = %s, option_b = %s, option_c = %s, option_d = %s,
                       points = %s, time_limit = %s
                       WHERE question_id = %s AND quiz_id = %s""",
                    (question_text, question_type, correct_answer,
                     option_a, option_b, option_c, option_d,
                     points, time_limit, question_id, quiz_id)
                )
                conn.commit()
    
                flash('Question updated successfully!', 'success')
                return redirect(url_for('edit_quiz', quiz_id=quiz_id))

        return render_template('edit_question.html', quiz=quiz, question=question)

    except Exception as e:
        flash(f'Error editing question: {str(e)}', 'danger')
        return redirect(url_for('edit_quiz', quiz_id=quiz_id))


# Delete Question
@app.route('/quiz/<int:quiz_id>/question/<int:question_id>/delete', methods=['POST'])
@login_required
def delete_question(quiz_id, question_id):
    try:
        with get_db_cursor(dictionary=True) as (conn, cursor):
            # Verify quiz ownership
            quiz, error_msg, redirect_target = get_quiz_and_check_access(cursor, quiz_id, require_ownership=True)
            
            if error_msg:
                flash(error_msg, 'danger')
                return redirect(url_for(redirect_target))
    
            cursor.execute(
                "DELETE FROM questions WHERE question_id = %s AND quiz_id = %s",
                (question_id, quiz_id)
            )
            conn.commit()
    
            flash('Question deleted successfully', 'success')

    except Exception as e:
        flash(f'Error deleting question: {str(e)}', 'danger')

    return redirect(url_for('edit_quiz', quiz_id=quiz_id))


# =============================================
# Game Session Routes
# =============================================

@app.route('/host/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
def host_game(quiz_id):
    try:
        with get_db_cursor(dictionary=True) as (conn, cursor):
            quiz, error_msg, redirect_target = get_quiz_and_check_access(cursor, quiz_id, require_ownership=True)
            
            if error_msg:
                flash(error_msg, 'danger')
                return redirect(url_for(redirect_target))
    
            cursor.execute("SELECT COUNT(*) as count FROM questions WHERE quiz_id = %s", (quiz_id,))
            question_count = cursor.fetchone()['count']
    
            if question_count == 0:
                flash('Cannot host a quiz with 0 questions. Please add questions first.', 'danger')
                return redirect(url_for('dashboard'))
    
            # Generate a 6-character random alphanumeric session code
            session_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
            cursor.execute(
                "INSERT INTO game_sessions (session_code, quiz_id, host_id, status) VALUES (%s, %s, %s, %s)",
                (session_code, quiz_id, current_user.id, 'waiting')
            )
            conn.commit()
            session_id = cursor.lastrowid
            
            # Fetch the created session for the template
            cursor.execute("SELECT * FROM game_sessions WHERE session_id = %s", (session_id,))
            game_session = cursor.fetchone()

        # Get local IP and port for display
        local_ip = get_local_ip()
        port = request.host.split(':')[1] if ':' in request.host else '5000'
        host_url = f"{local_ip}:{port}"

        # Render the Host lobby stub
        return render_template('host_lobby_stub.html', quiz=quiz, session=game_session, host_url=host_url)

    except Exception as e:
        flash(f'Error starting session: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/cancel_session/<int:session_id>', methods=['POST'])
@login_required
def cancel_session(session_id):
    try:
        with get_db_cursor(dictionary=True) as (conn, cursor):
            cursor.execute("SELECT * FROM game_sessions WHERE session_id = %s", (session_id,))
            game_session = cursor.fetchone()
    
            if game_session and game_session['host_id'] == current_user.id:
                # Notify players in the lobby
                session_code = game_session['session_code']
                socketio.emit('session_cancelled', room=session_code)
    
                cursor.execute("DELETE FROM game_sessions WHERE session_id = %s", (session_id,))
                conn.commit()
                flash('Game session cancelled successfully.', 'success')
            else:
                flash('Unauthorized or session not found.', 'danger')

    except Exception as e:
        flash(f'Error cancelling session: {str(e)}', 'danger')

    return redirect(url_for('dashboard'))


@app.route('/join', methods=['POST'])
def join_game():
    session_code = request.form.get('session_code', '').strip().upper()
    nickname = request.form.get('nickname', '').strip()

    if not session_code or not nickname:
        flash('Session code and nickname are required to join.', 'danger')
        return redirect(url_for('index'))

    try:
        with get_db_cursor(dictionary=True) as (conn, cursor):
            # Check if session exists and is waiting
            cursor.execute(
                "SELECT * FROM game_sessions WHERE session_code = %s AND status = 'waiting'",
                (session_code,)
            )
            game_session = cursor.fetchone()
    
            if not game_session:
                flash('Invalid session code or the game has already started.', 'danger')
                return redirect(url_for('index'))
    
            # Check if nickname already taken in this session
            cursor.execute(
                "SELECT * FROM game_participants WHERE session_id = %s AND nickname = %s",
                (game_session['session_id'], nickname)
            )
            if cursor.fetchone():
                flash('That nickname is already taken in this game!', 'danger')
                return redirect(url_for('index'))
    
            # Insert participant
            cursor.execute(
                "INSERT INTO game_participants (session_id, nickname) VALUES (%s, %s)",
                (game_session['session_id'], nickname)
            )
            conn.commit()
            participant_id = cursor.lastrowid

        # Save participant ID to Flask session
        session['participant_id'] = participant_id
        session['nickname'] = nickname
        session['game_session_id'] = game_session['session_id']

        # Render the Player lobby stub
        return render_template('player_lobby_stub.html', session=game_session, nickname=nickname)

    except Exception as e:
        flash(f'Error joining game: {str(e)}', 'danger')
        return redirect(url_for('index'))


# =============================================
# Live Game Routes
# =============================================

@app.route('/host/game/<session_code>')
@login_required
def host_game_control(session_code):
    """Host game control screen — shows questions and controls during live play."""
    try:
        with get_db_cursor(dictionary=True) as (conn, cursor):
            # Verify session exists and belongs to this host
            cursor.execute(
                "SELECT gs.*, q.title as quiz_title FROM game_sessions gs "
                "JOIN quizzes q ON gs.quiz_id = q.quiz_id "
                "WHERE gs.session_code = %s AND gs.host_id = %s",
                (session_code, current_user.id)
            )
            game_session = cursor.fetchone()
    
            if not game_session:
                flash('Session not found or you are not the host.', 'danger')
                return redirect(url_for('dashboard'))
    
            # Get all questions for this quiz
            cursor.execute(
                "SELECT * FROM questions WHERE quiz_id = %s ORDER BY question_order ASC",
                (game_session['quiz_id'],)
            )
            questions = cursor.fetchall()

        return render_template(
            'host_game.html',
            session=game_session,
            questions=questions,
            total_questions=len(questions)
        )

    except Exception as e:
        flash(f'Error loading game control: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))


@app.route('/play/<session_code>')
def player_game(session_code):
    """Player game screen — shows questions and collects answers in real-time."""
    # Get participant info from Flask session
    participant_id = session.get('participant_id')

    if not participant_id:
        flash('You need to join a game first.', 'danger')
        return redirect(url_for('index'))

    try:
        with get_db_cursor(dictionary=True) as (conn, cursor):
            # Verify the session exists and is active
            cursor.execute(
                "SELECT gs.*, q.title as quiz_title FROM game_sessions gs "
                "JOIN quizzes q ON gs.quiz_id = q.quiz_id "
                "WHERE gs.session_code = %s AND gs.status = 'active'",
                (session_code,)
            )
            game_session = cursor.fetchone()
    
            if not game_session:
                flash('Game session not found or not active.', 'danger')
                return redirect(url_for('index'))
    
            # Fetch the nickname from the DB using participant_id
            cursor.execute(
                "SELECT nickname FROM game_participants WHERE participant_id = %s",
                (participant_id,)
            )
            participant = cursor.fetchone()
    
            if not participant:
                flash('Participant record not found. Please rejoin the game.', 'danger')
                return redirect(url_for('index'))
    
            nickname = participant['nickname']

        return render_template(
            'player_game.html',
            session=game_session,
            nickname=nickname,
            participant_id=participant_id
        )

    except Exception as e:
        flash(f'Error loading game: {str(e)}', 'danger')
        return redirect(url_for('index'))




# =============================================
# WebSocket Events
# =============================================

# Track which socket SID belongs to which session/nickname (for disconnect cleanup)
connected_players = {}  # { sid: {'session_code': ..., 'nickname': ...} }


@socketio.on('join_room_event')
def handle_join_room_event(data):
    """Handle a user (host or player) joining a SocketIO room."""
    session_code = data.get('session_code')
    nickname = data.get('nickname')

    if session_code:
        join_room(session_code)
        # Track this connection for disconnect cleanup
        connected_players[request.sid] = {
            'session_code': session_code,
            'nickname': nickname
        }
        # Broadcast to the room that a player joined
        emit('player_joined', {'nickname': nickname}, room=session_code)


@socketio.on('disconnect')
def handle_disconnect():
    """When a socket disconnects, remove the player from the lobby if the game hasn't started yet."""
    info = connected_players.pop(request.sid, None)
    if not info:
        return

    session_code = info.get('session_code')
    nickname = info.get('nickname')

    # Do not remove the HOST or players mid-game
    if not session_code or nickname == 'HOST':
        return

    try:
        with get_db_cursor(dictionary=True) as (conn, cursor):
            # Only remove the participant if the game is still in 'waiting' status
            cursor.execute(
                "SELECT gs.session_id FROM game_sessions gs "
                "WHERE gs.session_code = %s AND gs.status = 'waiting'",
                (session_code,)
            )
            game_session = cursor.fetchone()
    
            if game_session:
                cursor.execute(
                    "DELETE FROM game_participants "
                    "WHERE session_id = %s AND nickname = %s",
                    (game_session['session_id'], nickname)
                )
                conn.commit()
                # Tell the host to refresh the player list
                emit('player_joined', {'nickname': None}, room=session_code)
    except Exception:
        pass


@socketio.on('request_players')
def handle_request_players(data):
    """Return the current list of players in a session's lobby."""
    session_code = data.get('session_code')

    if session_code:
        try:
            with get_db_cursor(dictionary=True) as (conn, cursor):
                cursor.execute(
                    """SELECT gp.nickname
                       FROM game_participants gp
                       JOIN game_sessions gs ON gp.session_id = gs.session_id
                       WHERE gs.session_code = %s""",
                    (session_code,)
                )
                participants = cursor.fetchall()
            emit('update_players', {'players': participants})
        except Exception as e:
            emit('error', {'message': str(e)})


@socketio.on('start_game')
def handle_start_game(data):
    """Host starts the game — transition status to 'active' and notify players."""
    session_code = data.get('session_code')
    streak_enabled = data.get('streak_enabled', False)

    if not session_code:
        return

    try:
        with get_db_cursor(dictionary=True) as (conn, cursor):
            # Update game session status to active
            cursor.execute(
                "UPDATE game_sessions SET status = 'active', started_at = NOW(), current_question = 1 "
                "WHERE session_code = %s AND status = 'waiting'",
                (session_code,)
            )
            conn.commit()

            if cursor.rowcount == 0:
                emit('error', {'message': 'Session not found or already started.'})
                return

            # Initialize in-memory game state
            active_games[session_code] = {
                'streak_enabled': streak_enabled,
                'question_start_time': None,
                'answers_received': 0,
                'answer_counts': {}
            }

        # Notify all players in the room that the game has started
        emit('game_started', {
            'session_code': session_code,
            'redirect_url': f'/play/{session_code}'
        }, room=session_code)

    except Exception as e:
        emit('error', {'message': str(e)})


@socketio.on('host_next_question')
def handle_next_question(data):
    """Host advances to the next question — fetch and broadcast it to all players."""
    session_code = data.get('session_code')

    if not session_code:
        return

    try:
        with get_db_cursor(dictionary=True) as (conn, cursor):
            # Get current session state
            cursor.execute(
                "SELECT * FROM game_sessions WHERE session_code = %s AND status = 'active'",
                (session_code,)
            )
            game_session = cursor.fetchone()

            if not game_session:
                emit('error', {'message': 'Active session not found.'})
                return

            current_q_num = game_session['current_question']

            # Fetch the question at the current position
            cursor.execute(
                "SELECT * FROM questions WHERE quiz_id = %s ORDER BY question_order ASC "
                "LIMIT 1 OFFSET %s",
                (game_session['quiz_id'], current_q_num - 1)
            )
            question = cursor.fetchone()

            if not question:
                # No more questions — game is over
                cursor.execute(
                    "UPDATE game_sessions SET status = 'completed', ended_at = NOW() "
                    "WHERE session_code = %s",
                    (session_code,)
                )
                conn.commit()

                # Fetch final leaderboard
                cursor.execute(
                    "SELECT nickname, score, streak FROM game_participants "
                    "WHERE session_id = %s ORDER BY score DESC",
                    (game_session['session_id'],)
                )
                leaderboard = cursor.fetchall()

                # Clean up in-memory state
                active_games.pop(session_code, None)

                emit('game_over', {'session_code': session_code, 'leaderboard': leaderboard}, room=session_code)
                return

            # Get total question count for progress display
            cursor.execute(
                "SELECT COUNT(*) as total FROM questions WHERE quiz_id = %s",
                (game_session['quiz_id'],)
            )
            total_questions = cursor.fetchone()['total']

            # Get participant count for auto-end tracking
            cursor.execute(
                "SELECT COUNT(*) as count FROM game_participants WHERE session_id = %s",
                (game_session['session_id'],)
            )
            player_count = cursor.fetchone()['count']

            # Record start time in memory for scoring
            # Add 3 seconds to offset the intro animation shown on the frontend
            if session_code in active_games:
                active_games[session_code]['question_start_time'] = time.time() + 3
                active_games[session_code]['answers_received'] = 0
                active_games[session_code]['answer_counts'] = {}
                active_games[session_code]['player_count'] = player_count
                active_games[session_code]['current_question_id'] = question['question_id']
                active_games[session_code]['current_correct_answer'] = question['correct_answer']

            # Build question data to send (WITHOUT the correct answer)
            question_data = {
                'question_id': question['question_id'],
                'question_text': question['question_text'],
                'question_type': question['question_type'],
                'option_a': question['option_a'],
                'option_b': question['option_b'],
                'option_c': question['option_c'],
                'option_d': question['option_d'],
                'points': question['points'],
                'time_limit': question['time_limit'],
                'question_number': current_q_num,
                'total_questions': total_questions
            }

            # Broadcast question to all players and the host
            emit('new_question', question_data, room=session_code)

    except Exception as e:
        emit('error', {'message': str(e)})


@socketio.on('submit_answer')
def handle_submit_answer(data):
    """Player submits an answer. Validate, score, and record in the database."""
    session_code = data.get('session_code')
    participant_id = data.get('participant_id')
    question_id = data.get('question_id')
    answer_given = data.get('answer')

    if not session_code or not participant_id or not question_id:
        return

    try:
        with get_db_cursor(dictionary=True) as (conn, cursor):
            # Fetch the correct answer and points for this question
            cursor.execute(
                "SELECT correct_answer, points, time_limit FROM questions WHERE question_id = %s",
                (question_id,)
            )
            question = cursor.fetchone()
    
            if not question:
                return
    
            # Determine correctness (case-insensitive comparison)
            is_correct = False
            if answer_given:
                is_correct = answer_given.strip().lower() == question['correct_answer'].strip().lower()
    
            # Calculate time-based proportional score
            # Formula: floor((1 - ((response_time / time_limit) / 2)) * points)
            points_earned = 0
            game_state = active_games.get(session_code, {})
            question_start = game_state.get('question_start_time', time.time())
            response_time = time.time() - question_start
            time_limit = question['time_limit']
    
            if is_correct:
                time_ratio = min(response_time / time_limit, 1.0)  # Cap at 1.0
                points_earned = math.floor((1 - (time_ratio / 2)) * question['points'])
                points_earned = max(points_earned, 1)  # Minimum 1 point if correct
    
            # Handle streak logic
            streak_bonus = 0
            streak_enabled = game_state.get('streak_enabled', False)
    
            # Get current streak from database
            cursor.execute(
                "SELECT score, streak FROM game_participants WHERE participant_id = %s",
                (participant_id,)
            )
            participant = cursor.fetchone()
    
            if not participant:
                return
    
            current_streak = participant['streak']
    
            if is_correct:
                new_streak = current_streak + 1
                if streak_enabled and new_streak > 1:
                    # Streak bonus: +100 points for each consecutive correct answer after the first, capped at 500
                    streak_bonus = min(new_streak - 1, 5) * 100
            else:
                new_streak = 0  # Reset streak on incorrect answer
    
            total_points = points_earned + streak_bonus
    
            # Record the answer in player_answers
            cursor.execute(
                "INSERT INTO player_answers (participant_id, question_id, answer_given, is_correct, points_earned) "
                "VALUES (%s, %s, %s, %s, %s)",
                (participant_id, question_id, answer_given, is_correct, total_points)
            )
    
            # Update answer counts
            if session_code in active_games:
                ans_key = (answer_given or '').strip()
                active_games[session_code]['answer_counts'][ans_key] = active_games[session_code]['answer_counts'].get(ans_key, 0) + 1
    
            # Update participant score and streak
            cursor.execute(
                "UPDATE game_participants SET score = score + %s, streak = %s WHERE participant_id = %s",
                (total_points, new_streak, participant_id)
            )
            conn.commit()
    
        # Send feedback to the player who submitted
        emit('answer_result', {
            'is_correct': is_correct,
            'points_earned': total_points,
            'streak': new_streak,
            'streak_bonus': streak_bonus,
            'correct_answer': question['correct_answer']
        })
    
        # Notify host that a player answered
        emit('player_answered', {
            'participant_id': participant_id,
            'is_correct': is_correct
        }, room=session_code)

        # Auto-end round check: if all players have answered
        if session_code in active_games:
            active_games[session_code]['answers_received'] += 1
            answered = active_games[session_code]['answers_received']
            total_players = active_games[session_code].get('player_count', 0)

            if answered >= total_players:
                # Advance the current_question counter in the database
                try:
                    with get_db_cursor() as (conn2, cursor2):
                        cursor2.execute(
                            "UPDATE game_sessions SET current_question = current_question + 1 "
                            "WHERE session_code = %s",
                            (session_code,)
                        )
                        conn2.commit()
                except Exception:
                    pass

                # Fetch leaderboard
                leaderboard = []
                try:
                    with get_db_cursor(dictionary=True) as (conn3, cursor3):
                        cursor3.execute(
                            "SELECT nickname, score, streak FROM game_participants "
                            "WHERE session_id = (SELECT session_id FROM game_sessions WHERE session_code = %s) "
                            "ORDER BY score DESC", (session_code,)
                        )
                        leaderboard = cursor3.fetchall()
                except Exception:
                    pass

                # Include the correct answer so players can see the reveal
                correct_ans = active_games[session_code].get('current_correct_answer', '')
                ans_counts = active_games[session_code].get('answer_counts', {})
                emit('round_ended', {
                    'all_answered': True,
                    'correct_answer': correct_ans,
                    'answer_counts': ans_counts,
                    'leaderboard': leaderboard
                }, room=session_code)

    except Exception as e:
        emit('error', {'message': str(e)})

@socketio.on('force_end_round')
def handle_force_end_round(data):
    """Host forces the round to end when the timer expires, preventing the game from getting stuck."""
    session_code = data.get('session_code')
    if not session_code or session_code not in active_games:
        return

    answers_received = active_games[session_code].get('answers_received', 0)

    # Handle advancing the question if no answers were received
    if answers_received == 0:
        try:
            with get_db_cursor() as (conn, cursor):
                cursor.execute(
                    "UPDATE game_sessions SET current_question = current_question + 1 "
                    "WHERE session_code = %s",
                    (session_code,)
                )
                conn.commit()
        except Exception:
            pass

    # Fetch leaderboard
    leaderboard = []
    try:
        with get_db_cursor(dictionary=True) as (conn_lb, cursor_lb):
            cursor_lb.execute(
                "SELECT nickname, score, streak FROM game_participants "
                "WHERE session_id = (SELECT session_id FROM game_sessions WHERE session_code = %s) "
                "ORDER BY score DESC", (session_code,)
            )
            leaderboard = cursor_lb.fetchall()
    except Exception:
        pass

    # Include the correct answer so players can see the reveal
    correct_ans = active_games[session_code].get('current_correct_answer', '')
    ans_counts = active_games[session_code].get('answer_counts', {})
    emit('round_ended', {
        'all_answered': True,
        'correct_answer': correct_ans,
        'answer_counts': ans_counts,
        'leaderboard': leaderboard
    }, room=session_code)


# =============================================
# Error Handlers
# =============================================

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    # In a production app, we would log the error to a file/monitoring service here
    return render_template('500.html'), 500

# Test routes (keep these for now)
@app.route('/test-db')
def test_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 'Database connected!'")
        result = cursor.fetchone()
        conn.close()
        return f"Success! {result[0]}"
    except Exception as e:
        return f"Database error: {str(e)}"


@app.route('/show-tables')
def show_tables():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        cursor.close()
        conn.close()

        html = "<h2>Database Tables:</h2><ul>"
        for table in tables:
            html += f"<li>{table[0]}</li>"
        html += "</ul>"
        return html
    except Exception as e:
        return f"Error: {str(e)}"


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)