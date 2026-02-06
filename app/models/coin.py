from app import db

class Coin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    symbol = db.Column(db.String(10), unique=True, nullable=False, index=True)
    current_price = db.Column(db.Float, nullable=False)
    base_price = db.Column(db.Float, nullable=False)
    # volume_impact is used for price simulation logic
    # Higher volume_impact means more price volatility when trading
    volume_impact = db.Column(db.Float, default=1000000.0)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'symbol': self.symbol,
            'current_price': self.current_price
        }
