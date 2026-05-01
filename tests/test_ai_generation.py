import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import unittest
from unittest.mock import patch, MagicMock
from app import app, get_db_connection  # type: ignore
from werkzeug.security import generate_password_hash
import io

class AIGenerationTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE username = 'ai_host'")
        password_hash = generate_password_hash('password123')
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, role) VALUES (%s, %s, %s, %s)",
            ('ai_host', 'aihost@test.com', password_hash, 'host')
        )
        cls.host_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()

    @classmethod
    def tearDownClass(cls):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM quizzes WHERE created_by = %s", (cls.host_id,))
        cursor.execute("DELETE FROM users WHERE username = 'ai_host'")
        conn.commit()
        cursor.close()
        conn.close()

    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.app = app.test_client()
        self.login('ai_host', 'password123')

    def login(self, username, password):
        return self.app.post(
            '/login',
            data=dict(username=username, password=password),
            follow_redirects=True
        )

    def test_missing_topic(self):
        response = self.app.post('/quiz/generate', data=dict(mode='topic', topic=' '), follow_redirects=True)
        self.assertIn(b'Topic is required', response.data)

    def test_document_mode_missing_file(self):
        response = self.app.post('/quiz/generate', data=dict(mode='document', doc_title='Test Doc'), follow_redirects=True)
        self.assertIn(b'No document uploaded', response.data)

    def test_document_mode_unsupported_file(self):
        data = {
            'mode': 'document',
            'doc_title': 'Test Doc',
            'document': (io.BytesIO(b"dummy data"), 'test.xyz')
        }
        response = self.app.post('/quiz/generate', data=data, content_type='multipart/form-data', follow_redirects=True)
        self.assertIn(b'Unsupported file type', response.data)

    @patch('app.genai.Client')
    def test_generate_quiz_success(self, MockClient):
        # Mock the Gemini client and response
        mock_client_instance = MagicMock()
        MockClient.return_value = mock_client_instance
        
        mock_response = MagicMock()
        mock_response.text = '''{
            "title": "Generated Quiz",
            "description": "Mock description",
            "questions": [
                {
                    "question_text": "What is 2+2?",
                    "question_type": "multiple_choice",
                    "correct_answer": "B",
                    "option_a": "3",
                    "option_b": "4",
                    "option_c": "5",
                    "option_d": "6",
                    "time_limit": 20
                }
            ]
        }'''
        mock_client_instance.models.generate_content.return_value = mock_response

        response = self.app.post('/quiz/generate', data=dict(
            mode='topic',
            topic='Math',
            num_questions=1,
            difficulty='easy',
            is_public='1'
        ), follow_redirects=True)

        self.assertIn(b'Quiz successfully generated', response.data)
        
        # Verify it was saved
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM quizzes WHERE title = 'Generated Quiz' AND created_by = %s", (self.host_id,))
        quiz = cursor.fetchone()
        self.assertIsNotNone(quiz)
        
        cursor.execute("SELECT * FROM questions WHERE quiz_id = %s", (quiz['quiz_id'],))
        question = cursor.fetchone()
        self.assertIsNotNone(question)
        self.assertEqual(question['question_text'], 'What is 2+2?')
        self.assertEqual(question['correct_answer'], 'B')
        
        # cleanup
        cursor.execute("DELETE FROM quizzes WHERE quiz_id = %s", (quiz['quiz_id'],))
        conn.commit()
        cursor.close()
        conn.close()

if __name__ == '__main__':
    unittest.main()
