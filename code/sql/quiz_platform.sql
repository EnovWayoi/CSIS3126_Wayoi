-- CREATE DATABASE quiz_platform;
-- USE quiz_platform

/*
-- Users table
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'host', 'player') DEFAULT 'player',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Quizzes table
CREATE TABLE quizzes (
    quiz_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    created_by INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_public BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Questions table
CREATE TABLE questions (
    question_id INT AUTO_INCREMENT PRIMARY KEY,
    quiz_id INT NOT NULL,
    question_text TEXT NOT NULL,
    question_type ENUM('multiple_choice', 'true_false', 'fill_blank') DEFAULT 'multiple_choice',
    correct_answer VARCHAR(255) NOT NULL,
    option_a VARCHAR(255),
    option_b VARCHAR(255),
    option_c VARCHAR(255),
    option_d VARCHAR(255),
    points INT DEFAULT 10,
    time_limit INT DEFAULT 30,
    question_order INT DEFAULT 0,
    FOREIGN KEY (quiz_id) REFERENCES quizzes(quiz_id) ON DELETE CASCADE
);

-- Game sessions table
CREATE TABLE game_sessions (
    session_id INT AUTO_INCREMENT PRIMARY KEY,
    quiz_id INT NOT NULL,
    host_id INT NOT NULL,
    session_code VARCHAR(10) UNIQUE NOT NULL,
    status ENUM('waiting', 'active', 'completed') DEFAULT 'waiting',
    current_question INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP NULL,
    ended_at TIMESTAMP NULL,
    FOREIGN KEY (quiz_id) REFERENCES quizzes(quiz_id) ON DELETE CASCADE,
    FOREIGN KEY (host_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Player answers table
CREATE TABLE player_answers (
    answer_id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    player_id INT NOT NULL,
    question_id INT NOT NULL,
    answer_given VARCHAR(255),
    is_correct BOOLEAN DEFAULT FALSE,
    points_earned INT DEFAULT 0,
    answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES game_sessions(session_id) ON DELETE CASCADE,
    FOREIGN KEY (player_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES questions(question_id) ON DELETE CASCADE
);

-- Session participants table (track who joined which game)
CREATE TABLE session_participants (
    participant_id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    user_id INT NOT NULL,
    score INT DEFAULT 0,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES game_sessions(session_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
); */

