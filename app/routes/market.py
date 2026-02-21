from flask import Blueprint, jsonify, request
from app.models.coin import Coin
from app.models.price_history import PriceHistory
from app.services.price_service import get_market_summary

market_bp = Blueprint('market', __name__)

@market_bp.route('/', methods=['GET'])
def get_market():
    """Get All Coins Market Data"""
    return jsonify(get_market_summary()), 200

@market_bp.route('/<symbol>', methods=['GET'])
def get_coin_detail(symbol):
    """Get Coin Details"""
    coin = Coin.query.filter_by(symbol=symbol.upper()).first()
    if not coin:
        return jsonify({'message': 'Coin not found'}), 404
    return jsonify(coin.to_dict()), 200

@market_bp.route('/<symbol>/history', methods=['GET'])
def get_coin_history(symbol):
    """
    Get Coin Price History (Paginated)
    ---
    parameters:
      - name: page
        in: query
        type: integer
        default: 1
      - name: per_page
        in: query
        type: integer
        default: 50
    """
    coin = Coin.query.filter_by(symbol=symbol.upper()).first()
    if not coin:
        return jsonify({'message': 'Coin not found'}), 404

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    pagination = PriceHistory.query.filter_by(coin_id=coin.id)\
        .order_by(PriceHistory.timestamp.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'history': [h.to_dict() for h in reversed(pagination.items)],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': pagination.page
    }), 200
