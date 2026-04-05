import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import unittest
from app import app, socketio, get_db_connection, active_games
from werkzeug.security import generate_password_hash
import time

class WebsocketsTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE username = 'ws_host'")
        password_hash = generate_password_hash('password123')
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, role) VALUES (%s, %s, %s, %s)",
            ('ws_host', 'wshost@test.com', password_hash, 'host')
        )
        cls.host_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO quizzes (title, description, created_by, is_public) VALUES (%s, %s, %s, %s)",
            ('WS Test Quiz', 'A test quiz', cls.host_id, 1)
        )
        cls.quiz_id = cursor.lastrowid

        cursor.execute(
            """INSERT INTO questions (quiz_id, question_text, question_type, correct_answer, points, time_limit, question_order)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (cls.quiz_id, 'Q1 WS', 'multiple_choice', 'A', 1000, 10, 1)
        )
        cls.question_1_id = cursor.lastrowid
        
        cursor.execute(
            """INSERT INTO questions (quiz_id, question_text, question_type, correct_answer, points, time_limit, question_order)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (cls.quiz_id, 'Q2 WS', 'multiple_choice', 'B', 1000, 10, 2)
        )
        cls.question_2_id = cursor.lastrowid

        conn.commit()
        cursor.close()
        conn.close()

    @classmethod
    def tearDownClass(cls):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE username = 'ws_host'")
        conn.commit()
        cursor.close()
        conn.close()

    def setUp(self):
        app.config['TESTING'] = True
        self.flask_app = app.test_client()
        self.socket_client_host = socketio.test_client(app, flask_test_client=self.flask_app)
        self.socket_client_player1 = socketio.test_client(app, flask_test_client=self.flask_app)
        
        # Create a session in DB for testing
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO game_sessions (session_code, quiz_id, host_id, status) VALUES (%s, %s, %s, %s)",
            ('WSTEST', self.quiz_id, self.host_id, 'waiting')
        )
        self.session_id = cursor.lastrowid
        
        cursor.execute(
            "INSERT INTO game_participants (session_id, nickname) VALUES (%s, %s)",
            (self.session_id, 'Player1')
        )
        self.participant1_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        
        # Connect to rooms before each test
        self.socket_client_host.emit('join_room_event', {'session_code': 'WSTEST', 'nickname': 'HOST'})
        self.socket_client_player1.emit('join_room_event', {'session_code': 'WSTEST', 'nickname': 'Player1'})
        
        # clear queue of join events
        self.socket_client_host.get_received()
        self.socket_client_player1.get_received()

    def tearDown(self):
        self.socket_client_host.disconnect()
        self.socket_client_player1.disconnect()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM game_sessions WHERE session_code = 'WSTEST'")
        conn.commit()
        cursor.close()
        conn.close()
        
        # Cleanup memory
        active_games.pop('WSTEST', None)

    def test_join_room_and_request_players(self):
        # We joined in setUp, so we can just request players directly
        self.socket_client_host.emit('request_players', {'session_code': 'WSTEST'})
        received = self.socket_client_host.get_received()
        
        update_events = [r for r in received if r['name'] == 'update_players']
        self.assertGreaterEqual(len(update_events), 1)
        players = update_events[-1]['args'][0]['players']
        self.assertTrue(any(p['nickname'] == 'Player1' for p in players))

    def test_start_game_and_host_next_question(self):
        # Start game
        self.socket_client_host.emit('start_game', {'session_code': 'WSTEST', 'streak_enabled': True})
        
        # Verify broadcast
        received = self.socket_client_player1.get_received()
        started_events = [r for r in received if r['name'] == 'game_started']
        self.assertEqual(len(started_events), 1)
        
        # Host next question
        self.socket_client_host.emit('host_next_question', {'session_code': 'WSTEST'})
        received = self.socket_client_player1.get_received()
        
        q_events = [r for r in received if r['name'] == 'new_question']
        self.assertEqual(len(q_events), 1)
        q_data = q_events[0]['args'][0]
        self.assertEqual(q_data['question_number'], 1)
        self.assertEqual(q_data['question_text'], 'Q1 WS')

    def test_submit_answer_and_scoring(self):
        self.socket_client_host.emit('start_game', {'session_code': 'WSTEST', 'streak_enabled': True})
        self.socket_client_host.emit('host_next_question', {'session_code': 'WSTEST'})
        
        # Simulate wait
        time.sleep(1)
        self.socket_client_player1.get_received() # Clear queue
        
        self.socket_client_player1.emit('submit_answer', {
            'session_code': 'WSTEST',
            'participant_id': self.participant1_id,
            'question_id': self.question_1_id,
            'answer': 'A'
        })
        
        received = self.socket_client_player1.get_received()
        ans_events = [r for r in received if r['name'] == 'answer_result']
        self.assertTrue(len(ans_events) > 0)
        self.assertTrue(ans_events[0]['args'][0]['is_correct'])
        self.assertGreater(ans_events[0]['args'][0]['points_earned'], 0)
        
        # Test auto round end
        round_events = [r for r in received if r['name'] == 'round_ended']
        self.assertTrue(len(round_events) > 0)
        self.assertTrue(round_events[0]['args'][0]['all_answered'])

        # Now test next question to verify it goes to Q2
        self.socket_client_host.emit('host_next_question', {'session_code': 'WSTEST'})
        received_q2 = self.socket_client_player1.get_received()
        q_events = [r for r in received_q2 if r['name'] == 'new_question']
        self.assertEqual(q_events[0]['args'][0]['question_number'], 2)

if __name__ == '__main__':
    unittest.main()
