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
            # Seed a coin
            coin = Coin(name='Bitcoin', symbol='BTC', current_price=60000.0, base_price=60000.0, volume_impact=1000000.0)
            db.session.add(coin)
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_auth_and_trade(self):
        # 1. Register
        res = self.client.post('/api/auth/register', json={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123'
        })
        self.assertEqual(res.status_code, 201)

        # 2. Login
        res = self.client.post('/api/auth/login', json={
            'username': 'testuser',
            'password': 'password123'
        })
        self.assertEqual(res.status_code, 200)
        token = res.get_json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}

        # 3. Deposit
        res = self.client.post('/api/user/deposit', headers=headers, json={'amount': 100000})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()['new_balance'], 100000)

        # 4. Check Market
        res = self.client.get('/api/market/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.get_json()), 1)
        btc_price = res.get_json()[0]['current_price']

        # 5. Buy BTC
        res = self.client.post('/api/trade/buy', headers=headers, json={
            'symbol': 'BTC',
            'amount': 0.5
        })
        self.assertEqual(res.status_code, 200)
        new_price = res.get_json()['new_coin_price']
        self.assertGreater(new_price, btc_price)

        # 6. Check Portfolio
        res = self.client.get('/api/user/portfolio', headers=headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()[0]['amount'], 0.5)

        # 7. Sell BTC
        res = self.client.post('/api/trade/sell', headers=headers, json={
            'symbol': 'BTC',
            'amount': 0.2
        })
        self.assertEqual(res.status_code, 200)
        final_price = res.get_json()['new_coin_price']
        self.assertLess(final_price, new_price)

if __name__ == '__main__':
    unittest.main()
