from app import db
from datetime import datetime

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
