from flask import Blueprint, jsonify
from app.models.coin import Coin

market_bp = Blueprint('market', __name__)

@market_bp.route('/', methods=['GET'])
def get_market():
    coins = Coin.query.all()
    return jsonify([coin.to_dict() for coin in coins]), 200

@market_bp.route('/<symbol>', methods=['GET'])
def get_coin_detail(symbol):
    coin = Coin.query.filter_by(symbol=symbol.upper()).first()
    if not coin:
        return jsonify({'message': 'Coin not found'}), 404
    return jsonify(coin.to_dict()), 200
