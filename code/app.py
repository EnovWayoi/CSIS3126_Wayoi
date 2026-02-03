from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from config import db_config

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

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
    app.run(debug=True)