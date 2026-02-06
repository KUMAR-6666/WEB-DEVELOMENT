from app import db
from datetime import datetime

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
