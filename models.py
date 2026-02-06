from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    balance = db.Column(db.Float, default=0.0)
    locked_balance = db.Column(db.Float, default=0.0) # Funds in pending buy orders
    is_market_wallet = db.Column(db.Boolean, default=False)

    portfolios = db.relationship('Portfolio', backref='owner', lazy='dynamic')
    transactions = db.relationship('Transaction', backref='user', lazy='dynamic')
    limit_orders = db.relationship('LimitOrder', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'balance': self.balance,
            'locked_balance': self.locked_balance,
            'is_market_wallet': self.is_market_wallet
        }

class Coin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    symbol = db.Column(db.String(10), unique=True, nullable=False, index=True)
    current_price = db.Column(db.Float, nullable=False)
    base_price = db.Column(db.Float, nullable=False)
    # volume_impact is used for price simulation logic
    volume_impact = db.Column(db.Float, default=1000000.0)
    last_update = db.Column(db.DateTime, default=datetime.utcnow)

    histories = db.relationship('PriceHistory', backref='coin', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'symbol': self.symbol,
            'current_price': self.current_price,
            'last_update': self.last_update.isoformat() if self.last_update else None
        }

class Portfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    coin_id = db.Column(db.Integer, db.ForeignKey('coin.id'), nullable=False)
    amount = db.Column(db.Float, default=0.0)
    locked_amount = db.Column(db.Float, default=0.0) # Coins in pending sell orders

    coin = db.relationship('Coin')

    def to_dict(self):
        return {
            'coin_symbol': self.coin.symbol,
            'coin_name': self.coin.name,
            'amount': self.amount,
            'locked_amount': self.locked_amount,
            'current_value': (self.amount + self.locked_amount) * self.coin.current_price
        }

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    coin_id = db.Column(db.Integer, db.ForeignKey('coin.id'), nullable=True) # Null for deposits
    type = db.Column(db.String(10), nullable=False) # 'buy', 'sell', 'deposit'
    amount = db.Column(db.Float, nullable=False) # Amount of coins (for buy/sell) or cash (for deposit)
    price_at_time = db.Column(db.Float, nullable=True)
    total_cash = db.Column(db.Float, nullable=False) # Total cash involved
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    coin = db.relationship('Coin')

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'coin': self.coin.symbol if self.coin else None,
            'amount': self.amount,
            'price_at_time': self.price_at_time,
            'total_cash': self.total_cash,
            'timestamp': self.timestamp.isoformat()
        }

class PriceHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    coin_id = db.Column(db.Integer, db.ForeignKey('coin.id'), nullable=False)
    price = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def to_dict(self):
        return {
            'price': self.price,
            'timestamp': self.timestamp.isoformat()
        }

class LimitOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    coin_id = db.Column(db.Integer, db.ForeignKey('coin.id'), nullable=False)
    type = db.Column(db.String(10), nullable=False) # 'buy' or 'sell'
    amount = db.Column(db.Float, nullable=False)
    target_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending') # 'pending', 'completed', 'cancelled'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    coin = db.relationship('Coin')

    def to_dict(self):
        return {
            'id': self.id,
            'coin_symbol': self.coin.symbol,
            'type': self.type,
            'amount': self.amount,
            'target_price': self.target_price,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }
