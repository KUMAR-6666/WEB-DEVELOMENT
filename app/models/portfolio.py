from app import db

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
