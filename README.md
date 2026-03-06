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
- **Frontend:** HTML, Tailwind CSS, JavaScript
- **Real-time:** Flask-SocketIO
- **Authentication:** Flask-Login

## Key Features

### 👤 User Authentication
- Secure registration and login
- Password hashing with Werkzeug (scrypt/pbkdf2)
- User session management
- Personalized dashboard

### 📝 Quiz Management
- **Create Quizzes**: Users can create and manage their own quizzes
- **Question Types**: Support for Multiple Choice, True/False, and Fill-in-the-blank
- **Public/Private**: Option to make quizzes public or keep them private
- **Link Sharing**: Public quizzes can be freely shared and played without login
- **Solo Mode**: Interactive UI for players to practice or authors to test their quizzes
- **Rich Editor**: Easy-to-use interface for adding and editing questions
- **Advanced (Upcoming)**: Independent study Flashcards view
- **Advanced (Upcoming)**: AI-Assisted rapid quiz creation from study notes

### 🎮 Live Game Sessions
- **Room-based Play**: Users join a lobby via room code and wait for the host to start.
- **Time Countdown**: Questions are timed to increase competitiveness.
- **Time-based Proportional Scoring**: Points are awarded depending on response speed: `⌊(1 - (({response time} / {question timer}) / 2)) * {points possible}⌉` (Default 10 points).

## Current Status

- ✅ Database structure created & normalized (3NF)
- ✅ Flask application structure & routing established
- ✅ User Authentication (Register, Login, Logout) implemented
- ✅ Password Hashing & Security integration
- ✅ User Dashboard custom view implemented
- ✅ UI Overhaul: Re-designed interface with a vibrant Neo-Brutalism aesthetic (Tailwind CSS)
- ✅ Quiz Creation & Management (CRUD)
- ✅ Question Management (Multiple Choice, True/False, Fill-in-Blank)
- ✅ Comprehensive Testing Framework (unittest) implemented
- ✅ Custom Error Pages (404/500) integrated
- ✅ Comprehensive Documentation (SRS, ERD, Progress Logs)
- ✅ Anonymous Link Sharing & Solo Practice Mode implemented
- ✅ Game Session & Participant Lobby Foundation established

## Setup Instructions

1. Install Python 3.10+ and MySQL
2. Clone the repository and navigate to the project root directory
3. Create a python virtual environment: `python -m venv .venv`
4. Activate the virtual environment:
   - Windows: `.venv\Scripts\activate`
   - Mac/Linux: `source .venv/bin/activate`
5. Install project dependencies: `pip install -r requirements.txt`
6. Create database: `CREATE DATABASE quiz_platform;`
7. Ensure your MySQL credentials are correct in `src/config/config.py`
8. Start the application: `python src/app.py`
9. Visit: `http://127.0.0.1:5000`

## Database Tables

- users
- quizzes
- questions
- game_sessions
- game_participants
- player_answers
