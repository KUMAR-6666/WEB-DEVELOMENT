from app import db
from datetime import datetime

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
