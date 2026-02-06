from app import create_app, db
from app.models.coin import Coin
from app.models.user import User

app = create_app()

def seed_db():
    coins_data = [
        {'name': 'Bitcoin', 'symbol': 'BTC', 'price': 60000.0, 'impact': 10000000.0},
        {'name': 'Ethereum', 'symbol': 'ETH', 'price': 3000.0, 'impact': 5000000.0},
        {'name': 'Binance Coin', 'symbol': 'BNB', 'price': 500.0, 'impact': 1000000.0},
        {'name': 'Solana', 'symbol': 'SOL', 'price': 150.0, 'impact': 500000.0},
        {'name': 'XRP', 'symbol': 'XRP', 'price': 0.5, 'impact': 500000.0},
        {'name': 'Cardano', 'symbol': 'ADA', 'price': 0.4, 'impact': 300000.0},
        {'name': 'Dogecoin', 'symbol': 'DOGE', 'price': 0.15, 'impact': 200000.0},
        {'name': 'TRON', 'symbol': 'TRX', 'price': 0.12, 'impact': 200000.0},
        {'name': 'Polkadot', 'symbol': 'DOT', 'price': 7.0, 'impact': 100000.0},
        {'name': 'Polygon', 'symbol': 'MATIC', 'price': 0.7, 'impact': 100000.0},
    ]

    with app.app_context():
        db.drop_all()
        db.create_all()
        for data in coins_data:
            new_coin = Coin(name=data['name'], symbol=data['symbol'], current_price=data['price'], base_price=data['price'], volume_impact=data['impact'])
            db.session.add(new_coin)
        market_wallet = User(username='Market_Wallet', email='market@exchange.com', is_market_wallet=True, balance=0.0)
        market_wallet.set_password('MarketSecretPass123')
        db.session.add(market_wallet)
        db.session.commit()
        print("Database initialized, coins seeded, and Market Wallet created!")

if __name__ == '__main__':
    seed_db()
