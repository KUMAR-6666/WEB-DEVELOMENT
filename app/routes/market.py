from flask import Blueprint, jsonify
from app.models.coin import Coin
from app.models.price_history import PriceHistory
from app.services.price_service import get_market_summary

market_bp = Blueprint('market', __name__)

@market_bp.route('/', methods=['GET'])
def get_market():
    """
    Get All Coins Market Data
    ---
    responses:
      200:
        description: List of coins with current prices
        schema:
          type: array
          items:
            properties:
              id: {type: integer}
              name: {type: string}
              symbol: {type: string}
              current_price: {type: number}
    """
    return jsonify(get_market_summary()), 200

@market_bp.route('/<symbol>', methods=['GET'])
def get_coin_detail(symbol):
    """
    Get Coin Details
    ---
    parameters:
      - name: symbol
        in: path
        required: true
        type: string
    responses:
      200:
        description: Coin details
      404:
        description: Coin not found
    """
    coin = Coin.query.filter_by(symbol=symbol.upper()).first()
    if not coin:
        return jsonify({'message': 'Coin not found'}), 404
    return jsonify(coin.to_dict()), 200

@market_bp.route('/<symbol>/history', methods=['GET'])
def get_coin_history(symbol):
    """
    Get Coin Price History
    ---
    parameters:
      - name: symbol
        in: path
        required: true
        type: string
    responses:
      200:
        description: List of historical price points
    """
    coin = Coin.query.filter_by(symbol=symbol.upper()).first()
    if not coin:
        return jsonify({'message': 'Coin not found'}), 404
    histories = PriceHistory.query.filter_by(coin_id=coin.id).order_by(PriceHistory.timestamp.desc()).limit(50).all()
    return jsonify([h.to_dict() for h in reversed(histories)]), 200
