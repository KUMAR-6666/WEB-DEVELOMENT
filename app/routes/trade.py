from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User
from app.models.coin import Coin
from app.models.portfolio import Portfolio
from app.models.transaction import Transaction
from app.models.limit_order import LimitOrder
from app.services.price_service import update_price_on_trade
from app import db

trade_bp = Blueprint('trade', __name__)

TRADING_FEE_RATE = 0.001 # 0.1%

def get_market_wallet():
    return User.query.filter_by(is_market_wallet=True).first()

@trade_bp.route('/buy', methods=['POST'])
@jwt_required()
def buy_coin():
    """
    Buy Coin (Market Order)
    ---
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          properties:
            symbol: {type: string}
            amount: {type: number}
    responses:
      200:
        description: Buy successful
    """
    user_id = int(get_jwt_identity())
    data = request.get_json()
    symbol = data.get('symbol')
    amount = data.get('amount')
    if not symbol or not amount or amount <= 0:
        return jsonify({'message': 'Invalid symbol or amount'}), 400
    coin = Coin.query.filter_by(symbol=symbol.upper()).first()
    if not coin: return jsonify({'message': 'Coin not found'}), 404
    user = db.session.get(User, user_id)
    market_wallet = get_market_wallet()
    raw_cost = coin.current_price * amount
    fee = raw_cost * TRADING_FEE_RATE
    total_cost = raw_cost + fee
    if user.balance < total_cost: return jsonify({'message': 'Insufficient balance'}), 400
    try:
        user.balance -= total_cost
        market_wallet.balance += fee
        portfolio = Portfolio.query.filter_by(user_id=user.id, coin_id=coin.id).first()
        if not portfolio:
            portfolio = Portfolio(user_id=user.id, coin_id=coin.id, amount=amount)
            db.session.add(portfolio)
        else:
            portfolio.amount += amount
        transaction = Transaction(user_id=user.id, coin_id=coin.id, type='buy', amount=amount, price_at_time=coin.current_price, total_cash=total_cost)
        db.session.add(transaction)
        new_price = update_price_on_trade(coin, amount, is_buy=True)
        db.session.commit()
        return jsonify({'message': f'Successfully bought {amount} {symbol}', 'new_balance': user.balance, 'fee_paid': fee, 'new_coin_price': new_price}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Transaction failed', 'error': str(e)}), 500

@trade_bp.route('/sell', methods=['POST'])
@jwt_required()
def sell_coin():
    """
    Sell Coin (Market Order)
    ---
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          properties:
            symbol: {type: string}
            amount: {type: number}
    responses:
      200:
        description: Sell successful
    """
    user_id = int(get_jwt_identity())
    data = request.get_json()
    symbol = data.get('symbol')
    amount = data.get('amount')
    if not symbol or not amount or amount <= 0: return jsonify({'message': 'Invalid symbol or amount'}), 400
    coin = Coin.query.filter_by(symbol=symbol.upper()).first()
    if not coin: return jsonify({'message': 'Coin not found'}), 404
    user = db.session.get(User, user_id)
    portfolio = Portfolio.query.filter_by(user_id=user.id, coin_id=coin.id).first()
    market_wallet = get_market_wallet()
    if not portfolio or portfolio.amount < amount: return jsonify({'message': 'Insufficient coin balance'}), 400
    try:
        raw_gain = coin.current_price * amount
        fee = raw_gain * TRADING_FEE_RATE
        total_gain = raw_gain - fee
        user.balance += total_gain
        market_wallet.balance += fee
        portfolio.amount -= amount
        transaction = Transaction(user_id=user.id, coin_id=coin.id, type='sell', amount=amount, price_at_time=coin.current_price, total_cash=total_gain)
        db.session.add(transaction)
        new_price = update_price_on_trade(coin, amount, is_buy=False)
        db.session.commit()
        return jsonify({'message': f'Successfully sold {amount} {symbol}', 'new_balance': user.balance, 'fee_paid': fee, 'new_coin_price': new_price}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Transaction failed', 'error': str(e)}), 500

@trade_bp.route('/limit-order', methods=['POST'])
@jwt_required()
def create_limit_order():
    """
    Create Limit Order
    ---
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          properties:
            symbol: {type: string}
            amount: {type: number}
            target_price: {type: number}
            type: {type: string, enum: [buy, sell]}
    responses:
      201:
        description: Limit order created
    """
    user_id = int(get_jwt_identity())
    data = request.get_json()
    symbol = data.get('symbol')
    amount = data.get('amount')
    target_price = data.get('target_price')
    order_type = data.get('type')
    if not all([symbol, amount, target_price, order_type]) or amount <= 0 or target_price <= 0:
        return jsonify({'message': 'Missing or invalid fields'}), 400
    coin = Coin.query.filter_by(symbol=symbol.upper()).first()
    if not coin: return jsonify({'message': 'Coin not found'}), 404
    user = db.session.get(User, user_id)
    try:
        if order_type == 'buy':
            total_cost = (target_price * amount) * (1 + TRADING_FEE_RATE)
            if user.balance < total_cost: return jsonify({'message': 'Insufficient balance'}), 400
            user.balance -= total_cost
            user.locked_balance += total_cost
        else:
            portfolio = Portfolio.query.filter_by(user_id=user.id, coin_id=coin.id).first()
            if not portfolio or portfolio.amount < amount: return jsonify({'message': 'Insufficient coin balance'}), 400
            portfolio.amount -= amount
            portfolio.locked_amount += amount
        new_order = LimitOrder(user_id=user.id, coin_id=coin.id, type=order_type, amount=amount, target_price=target_price, status='pending')
        db.session.add(new_order)
        db.session.commit()
        return jsonify({'message': f'Limit {order_type} order created successfully', 'order': new_order.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to create limit order', 'error': str(e)}), 500

@trade_bp.route('/limit-orders', methods=['GET'])
@jwt_required()
def get_limit_orders():
    """
    Get User Limit Orders
    ---
    security:
      - Bearer: []
    responses:
      200:
        description: List of user limit orders
    """
    user_id = int(get_jwt_identity())
    orders = LimitOrder.query.filter_by(user_id=user_id).all()
    return jsonify([o.to_dict() for o in orders]), 200
