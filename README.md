# CSIS3126_Wayoi

# Interactive Quiz Show Platform

A web-based interactive quiz platform for educators, trainers, and quiz enthusiasts.

## Project Information

- **Course:** CSIS3126 - Design Project I
- **Semester:** Spring 2026
- **Institution:** Johnson & Wales University
- **Instructor:** Professor Jeffrey Tagen

## Technology Stack

- **Backend:** Python with Flask
- **Database:** MySQL
- **Frontend:** HTML, CSS, JavaScript, Bootstrap
- **Real-time:** Flask-SocketIO
- **Authentication:** Flask-Login

## Current Status

✅ Database structure created & normalized (3NF)
✅ Flask application structure & routing established
✅ User Authentication (Register, Login, Logout) implemented
✅ Password Hashing & Security integration
✅ User Dashboard custom view implemented
✅ Bootstrap 5 UI integration
✅ Comprehensive Documentation (SRS, ERD, Progress Logs)

## Setup Instructions

1. Install Python 3.10+
2. Install MySQL
3. Create database: `CREATE DATABASE quiz_platform;`
4. Install dependencies: `pip install flask flask-socketio flask-login mysql-connector-python`
5. Navigate to the code directory: `cd code`
6. Run: `python app.py`
7. Visit: `http://127.0.0.1:5000`

## Database Tables

- users
- quizzes
- questions
- game_sessions
- player_answers
- session_participants
