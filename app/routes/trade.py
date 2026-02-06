from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User
from app.models.coin import Coin
from app.models.portfolio import Portfolio
from app.models.transaction import Transaction
from app.services.price_service import update_price_on_trade
from app import db

trade_bp = Blueprint('trade', __name__)

@trade_bp.route('/buy', methods=['POST'])
@jwt_required()
def buy_coin():
    user_id = int(get_jwt_identity())
    data = request.get_json()

    symbol = data.get('symbol')
    amount = data.get('amount')

    if not symbol or not amount or amount <= 0:
        return jsonify({'message': 'Invalid symbol or amount'}), 400

    coin = Coin.query.filter_by(symbol=symbol.upper()).first()
    if not coin:
        return jsonify({'message': 'Coin not found'}), 404

    user = db.session.get(User, user_id)
    total_cost = coin.current_price * amount

    if user.balance < total_cost:
        return jsonify({'message': 'Insufficient balance'}), 400

    try:
        # Process Trade
        user.balance -= total_cost

        portfolio = Portfolio.query.filter_by(user_id=user.id, coin_id=coin.id).first()
        if not portfolio:
            portfolio = Portfolio(user_id=user.id, coin_id=coin.id, amount=amount)
            db.session.add(portfolio)
        else:
            portfolio.amount += amount

        # Record Transaction
        transaction = Transaction(
            user_id=user.id,
            coin_id=coin.id,
            type='buy',
            amount=amount,
            price_at_time=coin.current_price,
            total_cash=total_cost
        )
        db.session.add(transaction)

        # Update Price
        new_price = update_price_on_trade(coin, amount, is_buy=True)

        db.session.commit()

        return jsonify({
            'message': f'Successfully bought {amount} {symbol}',
            'new_balance': user.balance,
            'new_coin_price': new_price
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Transaction failed', 'error': str(e)}), 500

@trade_bp.route('/sell', methods=['POST'])
@jwt_required()
def sell_coin():
    user_id = int(get_jwt_identity())
    data = request.get_json()

    symbol = data.get('symbol')
    amount = data.get('amount')

    if not symbol or not amount or amount <= 0:
        return jsonify({'message': 'Invalid symbol or amount'}), 400

    coin = Coin.query.filter_by(symbol=symbol.upper()).first()
    if not coin:
        return jsonify({'message': 'Coin not found'}), 404

    user = db.session.get(User, user_id)
    portfolio = Portfolio.query.filter_by(user_id=user.id, coin_id=coin.id).first()

    if not portfolio or portfolio.amount < amount:
        return jsonify({'message': 'Insufficient coin balance'}), 400

    try:
        # Process Trade
        total_gain = coin.current_price * amount
        user.balance += total_gain
        portfolio.amount -= amount

        # Record Transaction
        transaction = Transaction(
            user_id=user.id,
            coin_id=coin.id,
            type='sell',
            amount=amount,
            price_at_time=coin.current_price,
            total_cash=total_gain
        )
        db.session.add(transaction)

        # Update Price
        new_price = update_price_on_trade(coin, amount, is_buy=False)

        db.session.commit()

        return jsonify({
            'message': f'Successfully sold {amount} {symbol}',
            'new_balance': user.balance,
            'new_coin_price': new_price
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Transaction failed', 'error': str(e)}), 500
