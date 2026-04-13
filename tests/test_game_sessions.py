import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import unittest
from app import app, get_db_connection  # type: ignore
from werkzeug.security import generate_password_hash

class GameSessionsTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Setup test environment user and quiz
        conn = get_db_connection()
        cursor = conn.cursor()
        # Clean up any previous test artifacts
        cursor.execute("DELETE FROM users WHERE username = 'session_host'")
        cursor.execute("DELETE FROM users WHERE username = 'other_host'")
        
        password_hash = generate_password_hash('password123')
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, role) VALUES (%s, %s, %s, %s)",
            ('session_host', 'session_host@test.com', password_hash, 'host')
        )
        cls.host_id = cursor.lastrowid
        
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, role) VALUES (%s, %s, %s, %s)",
            ('other_host', 'other_host@test.com', password_hash, 'host')
        )
        cls.other_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO quizzes (title, description, created_by, is_public) VALUES (%s, %s, %s, %s)",
            ('Session Test Quiz', 'A test quiz', cls.host_id, 1)
        )
        cls.quiz_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO quizzes (title, description, created_by, is_public) VALUES (%s, %s, %s, %s)",
            ('Empty Quiz', 'No questions here', cls.host_id, 1)
        )
        cls.empty_quiz_id = cursor.lastrowid

        cursor.execute(
            """INSERT INTO questions (quiz_id, question_text, question_type, correct_answer, points, time_limit, question_order)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (cls.quiz_id, 'Q1', 'true_false', 'A', 10, 10, 1)
        )

        conn.commit()
        cursor.close()
        conn.close()

    @classmethod
    def tearDownClass(cls):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE username = 'session_host'")
        cursor.execute("DELETE FROM users WHERE username = 'other_host'")
        conn.commit()
        cursor.close()
        conn.close()

    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.app = app.test_client()

    def tearDown(self):
        # Cleanup game sessions made during test
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM game_sessions WHERE host_id = %s", (self.host_id,))
        conn.commit()
        cursor.close()
        conn.close()

    def login(self, username, password):
        return self.app.post(
            '/login',
            data=dict(username=username, password=password),
            follow_redirects=True
        )

    def test_host_game_success(self):
        self.login('session_host', 'password123')
        response = self.app.get(f'/host/{self.quiz_id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'with Game Code:', response.data)
        
        # Verify it was added to database
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM game_sessions WHERE quiz_id = %s", (self.quiz_id,))
        session = cursor.fetchone()
        self.assertIsNotNone(session)
        self.assertEqual(session['status'], 'waiting')
        cursor.close()
        conn.close()

    def test_host_game_empty_quiz(self):
        self.login('session_host', 'password123')
        response = self.app.get(f'/host/{self.empty_quiz_id}', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Cannot host a quiz with 0 questions', response.data)

    def test_host_game_unauthorized(self):
        self.login('other_host', 'password123')
        response = self.app.get(f'/host/{self.quiz_id}', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Quiz not found or you do not have permission', response.data)

    def test_join_game_success(self):
        # First create a session
        self.login('session_host', 'password123')
        self.app.get(f'/host/{self.quiz_id}')
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM game_sessions WHERE quiz_id = %s", (self.quiz_id,))
        session = cursor.fetchone()
        session_code = session['session_code']
        session_id = session['session_id']
        cursor.close()
        conn.close()

        # Try to join anonymously
        self.app.get('/logout', follow_redirects=True)
        response = self.app.post('/join', data=dict(
            session_code=session_code,
            nickname='PlayerOne'
        ), follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Waiting for Host', response.data)
        self.assertIn(b'PlayerOne', response.data)

        # Check DB
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM game_participants WHERE session_id = %s", (session_id,))
        participant = cursor.fetchone()
        self.assertIsNotNone(participant)
        cursor.close()
        conn.close()

    def test_join_game_invalid_code(self):
        response = self.app.post('/join', data=dict(
            session_code='INVALID',
            nickname='PlayerOne'
        ), follow_redirects=True)
        self.assertIn(b'Invalid session code', response.data)

if __name__ == '__main__':
    unittest.main()
