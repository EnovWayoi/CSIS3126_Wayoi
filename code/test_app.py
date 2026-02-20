import unittest
from app import app, get_db_connection
from werkzeug.security import generate_password_hash

class WayoiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Setup test environment
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE username = 'testuser'")
        conn.commit()
        cursor.close()
        conn.close()

    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.app = app.test_client()

    def tearDown(self):
        # Cleanup test environment
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE username = 'testuser'")
        conn.commit()
        cursor.close()
        conn.close()

    def register(self, username, email, password, confirm_password):
        return self.app.post(
            '/register',
            data=dict(
                username=username,
                email=email,
                password=password,
                confirm_password=confirm_password
            ),
            follow_redirects=True
        )

    def login(self, username, password):
        return self.app.post(
            '/login',
            data=dict(
                username=username,
                password=password
            ),
            follow_redirects=True
        )

    def logout(self):
        return self.app.get('/logout', follow_redirects=True)

    def test_index_page(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Interactive Quiz Platform'.encode('utf-8'), response.data)

    def test_register_success(self):
        response = self.register('testuser', 'testuser@example.com', 'testpassword', 'testpassword')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Registration successful', response.data)

    def test_register_password_mismatch(self):
        response = self.register('testuser', 'testuser@example.com', 'testpassword', 'wrongpassword')
        self.assertIn(b'Passwords do not match', response.data)

    def test_login_logout(self):
        self.register('testuser', 'testuser@example.com', 'testpassword', 'testpassword')
        response = self.login('testuser', 'testpassword')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome back', response.data)

        response = self.logout()
        self.assertIn(b'You have been logged out', response.data)

    def test_quiz_management(self):
        # Setup login session
        self.register('testuser', 'testuser@example.com', 'testpassword', 'testpassword')
        self.login('testuser', 'testpassword')

        # Create
        response = self.app.post(
            '/quiz/create',
            data=dict(title='Test Quiz Title', description='Test Description', is_public='1'),
            follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM quizzes WHERE title = 'Test Quiz Title' ORDER BY quiz_id DESC LIMIT 1")
        quiz = cursor.fetchone()

        self.assertIsNotNone(quiz)
        quiz_id = quiz['quiz_id']
        
        response = self.app.post(
            f'/quiz/{quiz_id}/question/add',
            data=dict(
                question_text='What is 2+2?',
                question_type='multiple_choice',
                correct_answer='A',
                option_a='4',
                option_b='3',
                option_c='5',
                option_d='6',
                points=10,
                time_limit=30
            ),
            follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        
        cursor.execute("DELETE FROM quizzes WHERE quiz_id = %s", (quiz_id,))
        conn.commit()
        
        cursor.execute("SELECT * FROM quizzes WHERE quiz_id = %s", (quiz_id,))
        deleted_quiz = cursor.fetchone()
        self.assertIsNone(deleted_quiz)

        cursor.close()
        conn.close()

if __name__ == '__main__':
    unittest.main()
