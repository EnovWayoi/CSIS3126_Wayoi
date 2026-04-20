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

### User Authentication
- Secure registration and login
- Password hashing with Werkzeug (scrypt/pbkdf2)
- User session management
- Personalized dashboard

### Quiz Management
- **Create Quizzes**: Users can create and manage their own quizzes
- **Question Types**: Support for Multiple Choice, True/False, and Fill-in-the-blank
- **Public/Private**: Option to make quizzes public or keep them private
- **Link Sharing**: Public quizzes can be freely shared and played without login
- **Solo Mode**: Interactive UI for players to practice or authors to test their quizzes
- **Rich Editor**: Easy-to-use interface for adding and editing questions
- **Advanced**: Independent study Flashcards view

### AI-Assisted Quiz Generation
- **Topic Generation**: Automatically generate full quizzes by simply entering a topic and configuring difficulty/length.
- **Document Analysis**: Upload course materials (PDF or TXT) and let the AI extract context and formulate relevant questions directly from the text.
- **Mix Question Types**: AI automatically determines the best mix of Multiple Choice, True/False, and Fill-in-the-Blank based on context.

### Live Game Sessions
- **Room-based Play**: Users join a lobby via room code and wait for the host to start.
- **Real-time Socket.IO**: Live gameplay is driven by WebSocket connections to ensure minimal latency for answers and question transitions.
- **Dynamic Time Limits**: Questions have distinct default timers based on type (MC: 20s, T/F: 15s, Fill-in-Blank: 25s).
- **Proportional Scoring**: Points are rewarded based on exact millisecond response speed: `⌊(1 - (({response time} / {question timer}) / 2)) * {points possible}⌉`. By default, questions are worth 1000 points.
- **Streak Bonus**: Consecutive correct answers grant a stacking +100 bonus points (capped at +500 at a streak of 5).
- **Smooth Real-Time Timers**: 60fps monitor-synced timers utilizing requestAnimationFrame for maximum visual precision across Solo and Live modes.
- **Live Leaderboards**: Post-round host UI displays answer distributions, and player UIs show their live score gaps, ultimately ending with a dynamic podium.
- **Host Controls**: Hosts control the pace of the game, manually advancing questions while tracking how many players have answered.

## Prerequisites

Before you begin, ensure you have the following installed and set up on your machine:

- **Python 3.10+**: Required to run the Flask backend and related dependencies.
- **MySQL Server**: Required for the application's database. Ensure the MySQL service is running.
- **Google Gemini API Key**: Needed to use the AI-Assisted quiz generation feature (can be obtained for free from Google AI Studio).

## Setup Instructions

1. Clone the repository and navigate to the project root directory
2. Create a python virtual environment: `python -m venv .venv`
3. Activate the virtual environment:
   - Windows: `.venv\Scripts\activate`
   - Mac/Linux: `source .venv/bin/activate`
4. Install project dependencies: `pip install -r requirements.txt`
5. Create the database and tables:
   - Create the empty database: `CREATE DATABASE quiz_platform;`
   - Execute all the SQL `CREATE TABLE` scripts found in `docs/database_schema.md` to initialize your database.
6. Create a `.env` file from the example (`cp .env.example .env`) and add your database credentials and Gemini API key.
7. Start the application: `python src/app.py`
8. Visit: `http://127.0.0.1:5000`

## Database Tables

- users
- quizzes
- questions
- game_sessions
- game_participants
- player_answers
