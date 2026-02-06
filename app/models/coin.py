from app import db
from datetime import datetime

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
