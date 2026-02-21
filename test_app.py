import unittest
import json
from app import create_app, db
from app.models.user import User
from app.models.coin import Coin
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

class MarketTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
            coin = Coin(name='Bitcoin', symbol='BTC', current_price=60000.0, base_price=60000.0, volume_impact=1000000.0)
            db.session.add(coin)
            mw = User(username='Market_Wallet', email='mw@test.com', is_market_wallet=True)
            mw.set_password('MarketPass123')
            db.session.add(mw)
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_auth_validation_and_refresh(self):
        # 1. Test Weak Password
        res = self.client.post('/api/auth/register', json={'username': 'u1', 'email': 'e1@t.com', 'password': '123'})
        self.assertEqual(res.status_code, 400)

        # 2. Test Strong Password & Valid Email
        res = self.client.post('/api/auth/register', json={'username': 'user1', 'email': 'user1@test.com', 'password': 'Password123'})
        if res.status_code != 201:
            print(f"Registration failed: {res.get_json()}")
        self.assertEqual(res.status_code, 201)

        # 3. Test Refresh Token
        res = self.client.post('/api/auth/login', json={'username': 'user1', 'password': 'Password123'})
        data = res.get_json()
        self.assertEqual(res.status_code, 200)
        refresh_token = data['refresh_token']

        res = self.client.post('/api/auth/refresh', headers={'Authorization': f'Bearer {refresh_token}'})
        self.assertEqual(res.status_code, 200)
        self.assertIn('access_token', res.get_json())

    def test_cancel_order(self):
        # Use a password that definitely passes
        password = 'StrongPassword123'
        reg_res = self.client.post('/api/auth/register', json={'username': 'user2', 'email': 'user2@test.com', 'password': password})
        self.assertEqual(reg_res.status_code, 201)

        res = self.client.post('/api/auth/login', json={'username': 'user2', 'password': password})
        self.assertEqual(res.status_code, 200)
        token = res.get_json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        self.client.post('/api/user/deposit', headers=headers, json={'amount': 100000})

        # Create Limit Order
        res = self.client.post('/api/trade/limit-order', headers=headers, json={
            'symbol': 'BTC', 'amount': 1, 'target_price': 50000, 'type': 'buy'
        })
        self.assertEqual(res.status_code, 201)
        order_id = res.get_json()['order']['id']

        # Cancel Order
        res = self.client.post(f'/api/trade/limit-order/{order_id}/cancel', headers=headers)
        self.assertEqual(res.status_code, 200)

        # Check Balance Refunded
        res = self.client.get('/api/user/profile', headers=headers)
        self.assertEqual(res.get_json()['balance'], 100000)

if __name__ == '__main__':
    unittest.main()
