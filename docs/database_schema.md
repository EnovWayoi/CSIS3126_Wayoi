```sql
-- ============================================
-- Interactive Quiz Show Platform
-- Database Schema (Ver. 3)
-- ============================================
-- Author: Enov Wayoi
-- Course: CSIS3126 - Design Project I
-- Date: February 2026
-- REVISION: Removed session_participants (login required)
--           Added game_participants (anonymous nickname joins)
--           Updated player_answers FK relationships
-- ============================================

-- Create database
CREATE DATABASE IF NOT EXISTS quiz_platform;
USE quiz_platform;

-- ============================================
-- Table: users
-- Description: Stores all user accounts
-- ============================================
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'host', 'player') DEFAULT 'player',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_users_username (username),
    INDEX idx_users_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- Table: quizzes
-- Description: Stores quiz metadata
-- ============================================
CREATE TABLE quizzes (
    quiz_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    created_by INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_public BOOLEAN DEFAULT FALSE,
    
    FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_quizzes_created_by (created_by)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- Table: questions
-- Description: Stores quiz questions
-- NOTE: No direct relationship to game_sessions
--       Questions are accessed via quiz_id
-- ============================================
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
    
    FOREIGN KEY (quiz_id) REFERENCES quizzes(quiz_id) ON DELETE CASCADE,
    INDEX idx_questions_quiz_id (quiz_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- Table: game_sessions
-- Description: Stores game session information
-- ============================================
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
    FOREIGN KEY (host_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_sessions_code (session_code),
    INDEX idx_sessions_host (host_id),
    INDEX idx_sessions_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- Table: game_participants
-- Description: Stores anonymous players who join a game
-- NOTE: Players join using nicknames, no login required.
-- ============================================
CREATE TABLE game_participants (
    participant_id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    nickname VARCHAR(50) NOT NULL,
    score INT DEFAULT 0,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (session_id) REFERENCES game_sessions(session_id) ON DELETE CASCADE,
    INDEX idx_participants_session (session_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- Table: player_answers
-- Description: Stores player answer submissions
-- NOTE: REVISED - Now uses participant_id instead of
--       separate session_id and player_id fields
--       Simpler joins and clearer relationship
-- ============================================
CREATE TABLE player_answers (
    answer_id INT AUTO_INCREMENT PRIMARY KEY,
    participant_id INT NOT NULL,
    question_id INT NOT NULL,
    answer_given VARCHAR(255),
    is_correct BOOLEAN DEFAULT FALSE,
    points_earned INT DEFAULT 0,
    answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (participant_id) REFERENCES game_participants(participant_id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES questions(question_id) ON DELETE CASCADE,
    INDEX idx_answers_participant (participant_id),
    INDEX idx_answers_question (question_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- Sample Data for Testing (Optional)
-- ============================================

-- Insert sample admin user
-- Password: admin123 (hashed with bcrypt)
INSERT INTO users (username, email, password_hash, role) VALUES
('admin', 'admin@quiz.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7667fLBkTm', 'admin');

-- Insert sample host user
-- Password: host123
INSERT INTO users (username, email, password_hash, role) VALUES
('testhost', 'host@quiz.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7667fLBkTm', 'host');

-- Insert sample quiz
INSERT INTO quizzes (title, description, created_by) VALUES
('Sample Quiz', 'This is a sample quiz for testing', 2);

-- Insert sample questions
INSERT INTO questions (quiz_id, question_text, question_type, correct_answer, option_a, option_b, option_c, option_d, question_order) VALUES
(1, 'What is 2 + 2?', 'multiple_choice', 'A', '4', '3', '5', '6', 1),
(1, 'Is Python a programming language?', 'true_false', 'A', 'True', 'False', NULL, NULL, 2),
(1, 'What is the capital of France?', 'multiple_choice', 'B', 'London', 'Paris', 'Berlin', 'Madrid', 3);

-- ============================================
-- Verification Queries
-- ============================================

-- Show all tables
SHOW TABLES;

-- Show table structures
DESCRIBE users;
DESCRIBE quizzes;
DESCRIBE questions;
DESCRIBE game_sessions;
DESCRIBE game_participants;
DESCRIBE player_answers;

-- Count records in each table
SELECT 'users' AS table_name, COUNT(*) AS count FROM users
UNION ALL
SELECT 'quizzes', COUNT(*) FROM quizzes
UNION ALL
SELECT 'questions', COUNT(*) FROM questions
UNION ALL
SELECT 'game_sessions', COUNT(*) FROM game_sessions
UNION ALL
SELECT 'game_participants', COUNT(*) FROM game_participants
UNION ALL
SELECT 'player_answers', COUNT(*) FROM player_answers;
```
