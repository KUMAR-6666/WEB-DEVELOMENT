import unittest
import json
from app import create_app, db
from app.models.user import User
from app.models.coin import Coin
from app.models.limit_order import LimitOrder
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
            # Seed Market Wallet
            mw = User(username='Market_Wallet', email='mw@test.com', is_market_wallet=True)
            mw.set_password('pass')
            db.session.add(mw)
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_fee_and_leaderboard(self):
        # 1. Register & Login
        self.client.post('/api/auth/register', json={'username': 'testuser', 'email': 'test@example.com', 'password': 'password123'})
        res = self.client.post('/api/auth/login', json={'username': 'testuser', 'password': 'password123'})
        token = res.get_json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}

        # 2. Deposit
        self.client.post('/api/user/deposit', headers=headers, json={'amount': 100000})

        # 3. Buy BTC (Check Fee)
        res = self.client.post('/api/trade/buy', headers=headers, json={'symbol': 'BTC', 'amount': 1})
        data = res.get_json()
        self.assertEqual(res.status_code, 200)
        self.assertIn('fee_paid', data)
        fee = data['fee_paid']
        self.assertEqual(fee, 60000.0 * 0.001)

        # 4. Check Leaderboard
        res = self.client.get('/api/user/leaderboard')
        lb = res.get_json()
        # Find Market Wallet
        mw_entry = next(item for item in lb if item['username'] == 'Market_Wallet')
        self.assertEqual(mw_entry['total_wealth'], fee)

    def test_limit_order(self):
        # 1. Setup User
        self.client.post('/api/auth/register', json={'username': 'limituser', 'email': 'limit@example.com', 'password': 'password123'})
        res = self.client.post('/api/auth/login', json={'username': 'limituser', 'password': 'password123'})
        token = res.get_json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        self.client.post('/api/user/deposit', headers=headers, json={'amount': 100000})

        # 2. Create Limit Order (Buy BTC when price drops to 50000)
        res = self.client.post('/api/trade/limit-order', headers=headers, json={
            'symbol': 'BTC',
            'amount': 1,
            'target_price': 50000,
            'type': 'buy'
        })
        self.assertEqual(res.status_code, 201)

        # 3. Check Order Pending
        res = self.client.get('/api/trade/limit-orders', headers=headers)
        self.assertEqual(res.get_json()[0]['status'], 'pending')

        # 4. Trigger price drop via Volatility (simulated)
        with self.app.app_context():
            coin = Coin.query.filter_by(symbol='BTC').first()
            coin.current_price = 49000
            db.session.commit()

            # This should trigger the limit order when market summary is requested
            from app.services.price_service import get_market_summary
            get_market_summary()

            # 5. Check Order Completed
            order = LimitOrder.query.first()
            self.assertEqual(order.status, 'completed')

if __name__ == '__main__':
    unittest.main()
