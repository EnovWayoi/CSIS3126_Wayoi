from flask import Flask, render_template, request, redirect, url_for, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import mysql.connector
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'secret'  # Change this!

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'password123',
    'database': 'quiz_platform'
}


@app.route('/')
def home():
    return "Flask is working! Your quiz platform is starting..."

@app.route('/test-db')
def test_db():
    try:
        conn = mysql.connector.connect(**db_config)
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
        conn = mysql.connector.connect(**db_config)
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