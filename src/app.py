import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_socketio import SocketIO, join_room, leave_room, emit
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from config.config import db_config
import random
import string
import socket

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

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


# Database helper function
def get_db_connection():
    return mysql.connector.connect(**db_config)


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
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        user_data = cursor.fetchone()
        cursor.close()
        conn.close()

        if user_data:
            return User(
                user_id=user_data['user_id'],
                username=user_data['username'],
                email=user_data['email'],
                role=user_data['role']
            )
        return None
    except Exception as e:
        print(f"Error loading user: {e}")
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
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                flash('Username already exists', 'danger')
                cursor.close()
                conn.close()
                return render_template('register.html')

            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                flash('Email already registered', 'danger')
                cursor.close()
                conn.close()
                return render_template('register.html')

            # Hash password and create user
            password_hash = generate_password_hash(password)

            cursor.execute(
                "INSERT INTO users (username, email, password_hash, role) VALUES (%s, %s, %s, %s)",
                (username, email, password_hash, 'host')  # Default role is 'host'
            )
            conn.commit()

            cursor.close()
            conn.close()

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
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            # Find user by username or email
            cursor.execute(
                "SELECT * FROM users WHERE username = %s OR email = %s",
                (username, username)
            )
            user_data = cursor.fetchone()

            cursor.close()
            conn.close()

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
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

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

        cursor.close()
        conn.close()

        return render_template('dashboard.html', quizzes=quizzes)

    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'danger')
        return render_template('dashboard.html', quizzes=[])


# =============================================
# Quiz Management Routes
# =============================================

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
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO quizzes (title, description, created_by, is_public) VALUES (%s, %s, %s, %s)",
                (title, description, current_user.id, is_public)
            )
            conn.commit()
            quiz_id = cursor.lastrowid
            cursor.close()
            conn.close()

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
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM quizzes WHERE quiz_id = %s", (quiz_id,))
        quiz = cursor.fetchone()

        if not quiz:
            flash('Quiz not found', 'danger')
            cursor.close()
            conn.close()
            return redirect(url_for('index'))

        # Check access permission: public quizzes can be viewed by anyone,
        # private quizzes only by the creator.
        if quiz['is_public'] == 0:
            if not current_user.is_authenticated or quiz['created_by'] != int(current_user.id):
                flash('You do not have permission to view this private quiz', 'danger')
                cursor.close()
                conn.close()
                return redirect(url_for('dashboard') if current_user.is_authenticated else url_for('index'))

        cursor.execute(
            "SELECT * FROM questions WHERE quiz_id = %s ORDER BY question_order ASC",
            (quiz_id,)
        )
        questions = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template('view_quiz.html', quiz=quiz, questions=questions)

    except Exception as e:
        flash(f'Error loading quiz: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))


# Solo Mode (Test Quiz)
@app.route('/quiz/<int:quiz_id>/solo')
def solo_quiz(quiz_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM quizzes WHERE quiz_id = %s", (quiz_id,))
        quiz = cursor.fetchone()

        if not quiz:
            flash('Quiz not found', 'danger')
            cursor.close()
            conn.close()
            return redirect(url_for('index'))

        # Check access permission: public quizzes can be viewed by anyone,
        # private quizzes only by the creator.
        if quiz['is_public'] == 0:
            if not current_user.is_authenticated or quiz['created_by'] != int(current_user.id):
                flash('You do not have permission to play this private quiz', 'danger')
                cursor.close()
                conn.close()
                return redirect(url_for('dashboard') if current_user.is_authenticated else url_for('index'))

        cursor.execute(
            "SELECT * FROM questions WHERE quiz_id = %s ORDER BY question_order ASC",
            (quiz_id,)
        )
        questions = cursor.fetchall()
        
        if not questions:
            flash('Cannot play a quiz with no questions. Please add questions first.', 'danger')
            cursor.close()
            conn.close()
            if current_user.is_authenticated:
                return redirect(url_for('view_quiz', quiz_id=quiz_id))
            else:
                return redirect(url_for('index'))

        cursor.close()
        conn.close()

        # Render the solo game interface
        return render_template('solo_game.html', quiz=quiz, questions=questions)

    except Exception as e:
        flash(f'Error loading solo quiz: {str(e)}', 'danger')
        return redirect(url_for('dashboard') if current_user.is_authenticated else url_for('index'))


# Edit Quiz
@app.route('/quiz/<int:quiz_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_quiz(quiz_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM quizzes WHERE quiz_id = %s", (quiz_id,))
        quiz = cursor.fetchone()

        if not quiz:
            flash('Quiz not found', 'danger')
            cursor.close()
            conn.close()
            return redirect(url_for('dashboard'))

        if quiz['created_by'] != int(current_user.id):
            flash('You do not have permission to edit this quiz', 'danger')
            cursor.close()
            conn.close()
            return redirect(url_for('dashboard'))

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

        cursor.close()
        conn.close()

        return render_template('edit_quiz.html', quiz=quiz, questions=questions)

    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))


# Delete Quiz
@app.route('/quiz/<int:quiz_id>/delete', methods=['POST'])
@login_required
def delete_quiz(quiz_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM quizzes WHERE quiz_id = %s", (quiz_id,))
        quiz = cursor.fetchone()

        if not quiz:
            flash('Quiz not found', 'danger')
        elif quiz['created_by'] != int(current_user.id):
            flash('You do not have permission to delete this quiz', 'danger')
        else:
            cursor.execute("DELETE FROM quizzes WHERE quiz_id = %s", (quiz_id,))
            conn.commit()
            flash('Quiz deleted successfully', 'success')

        cursor.close()
        conn.close()

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
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM quizzes WHERE quiz_id = %s", (quiz_id,))
        quiz = cursor.fetchone()

        if not quiz:
            flash('Quiz not found', 'danger')
            cursor.close()
            conn.close()
            return redirect(url_for('dashboard'))

        if quiz['created_by'] != int(current_user.id):
            flash('You do not have permission to modify this quiz', 'danger')
            cursor.close()
            conn.close()
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            question_text = request.form.get('question_text', '').strip()
            question_type = request.form.get('question_type', 'multiple_choice')
            correct_answer = request.form.get('correct_answer', '').strip()
            option_a = request.form.get('option_a', '').strip() or None
            option_b = request.form.get('option_b', '').strip() or None
            option_c = request.form.get('option_c', '').strip() or None
            option_d = request.form.get('option_d', '').strip() or None
            points = int(request.form.get('points', 10))
            time_limit = int(request.form.get('time_limit', 30))

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
            cursor.close()
            conn.close()
            return redirect(url_for('edit_quiz', quiz_id=quiz_id))

        cursor.close()
        conn.close()
        return render_template('add_question.html', quiz=quiz)

    except Exception as e:
        flash(f'Error adding question: {str(e)}', 'danger')
        return redirect(url_for('edit_quiz', quiz_id=quiz_id))


# Edit Question
@app.route('/quiz/<int:quiz_id>/question/<int:question_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_question(quiz_id, question_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Verify quiz ownership
        cursor.execute("SELECT * FROM quizzes WHERE quiz_id = %s", (quiz_id,))
        quiz = cursor.fetchone()

        if not quiz or quiz['created_by'] != int(current_user.id):
            flash('You do not have permission to modify this quiz', 'danger')
            cursor.close()
            conn.close()
            return redirect(url_for('dashboard'))

        cursor.execute(
            "SELECT * FROM questions WHERE question_id = %s AND quiz_id = %s",
            (question_id, quiz_id)
        )
        question = cursor.fetchone()

        if not question:
            flash('Question not found', 'danger')
            cursor.close()
            conn.close()
            return redirect(url_for('edit_quiz', quiz_id=quiz_id))

        if request.method == 'POST':
            question_text = request.form.get('question_text', '').strip()
            question_type = request.form.get('question_type', 'multiple_choice')
            correct_answer = request.form.get('correct_answer', '').strip()
            option_a = request.form.get('option_a', '').strip() or None
            option_b = request.form.get('option_b', '').strip() or None
            option_c = request.form.get('option_c', '').strip() or None
            option_d = request.form.get('option_d', '').strip() or None
            points = int(request.form.get('points', 10))
            time_limit = int(request.form.get('time_limit', 30))

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
            cursor.close()
            conn.close()
            return redirect(url_for('edit_quiz', quiz_id=quiz_id))

        cursor.close()
        conn.close()
        return render_template('edit_question.html', quiz=quiz, question=question)

    except Exception as e:
        flash(f'Error editing question: {str(e)}', 'danger')
        return redirect(url_for('edit_quiz', quiz_id=quiz_id))


# Delete Question
@app.route('/quiz/<int:quiz_id>/question/<int:question_id>/delete', methods=['POST'])
@login_required
def delete_question(quiz_id, question_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Verify quiz ownership
        cursor.execute("SELECT * FROM quizzes WHERE quiz_id = %s", (quiz_id,))
        quiz = cursor.fetchone()

        if not quiz or quiz['created_by'] != int(current_user.id):
            flash('You do not have permission to modify this quiz', 'danger')
            cursor.close()
            conn.close()
            return redirect(url_for('dashboard'))

        cursor.execute(
            "DELETE FROM questions WHERE question_id = %s AND quiz_id = %s",
            (question_id, quiz_id)
        )
        conn.commit()

        flash('Question deleted successfully', 'success')
        cursor.close()
        conn.close()

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
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM quizzes WHERE quiz_id = %s", (quiz_id,))
        quiz = cursor.fetchone()

        if not quiz or quiz['created_by'] != int(current_user.id):
            flash('Quiz not found or you do not have permission to host it.', 'danger')
            cursor.close()
            conn.close()
            return redirect(url_for('dashboard'))

        cursor.execute("SELECT COUNT(*) as count FROM questions WHERE quiz_id = %s", (quiz_id,))
        question_count = cursor.fetchone()['count']

        if question_count == 0:
            flash('Cannot host a quiz with 0 questions. Please add questions first.', 'danger')
            cursor.close()
            conn.close()
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

        cursor.close()
        conn.close()

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
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

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

        cursor.close()
        conn.close()
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
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Check if session exists and is waiting
        cursor.execute(
            "SELECT * FROM game_sessions WHERE session_code = %s AND status = 'waiting'",
            (session_code,)
        )
        game_session = cursor.fetchone()

        if not game_session:
            flash('Invalid session code or the game has already started.', 'danger')
            cursor.close()
            conn.close()
            return redirect(url_for('index'))

        # Check if nickname already taken in this session
        cursor.execute(
            "SELECT * FROM game_participants WHERE session_id = %s AND nickname = %s",
            (game_session['session_id'], nickname)
        )
        if cursor.fetchone():
            flash('That nickname is already taken in this game!', 'danger')
            cursor.close()
            conn.close()
            return redirect(url_for('index'))

        # Insert participant
        cursor.execute(
            "INSERT INTO game_participants (session_id, nickname) VALUES (%s, %s)",
            (game_session['session_id'], nickname)
        )
        conn.commit()
        participant_id = cursor.lastrowid

        cursor.close()
        conn.close()

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
# WebSocket Events
# =============================================

@socketio.on('join_room_event')
def handle_join_room_event(data):
    session_code = data.get('session_code')
    nickname = data.get('nickname')
    
    if session_code:
        join_room(session_code)
        # Broadcast to the room that a player joined
        emit('player_joined', {'nickname': nickname}, room=session_code)

@socketio.on('request_players')
def handle_request_players(data):
    session_code = data.get('session_code')
    
    if session_code:
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Get session ID and participants
            cursor.execute(
                """SELECT gp.nickname 
                   FROM game_participants gp
                   JOIN game_sessions gs ON gp.session_id = gs.session_id
                   WHERE gs.session_code = %s""",
                (session_code,)
            )
            participants = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            emit('update_players', {'players': participants})
        except Exception as e:
            emit('error', {'message': str(e)})

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
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)