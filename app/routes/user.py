from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User
from app.models.portfolio import Portfolio
from app.models.transaction import Transaction
from app.models.coin import Coin
from app import db

user_bp = Blueprint('user', __name__)

@user_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """
    Get User Profile
    ---
    security:
      - Bearer: []
    responses:
      200:
        description: User profile data
    """
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    return jsonify(user.to_dict()), 200

@user_bp.route('/portfolio', methods=['GET'])
@jwt_required()
def get_portfolio():
    """
    Get User Portfolio
    ---
    security:
      - Bearer: []
    responses:
      200:
        description: List of owned coins
    """
    user_id = int(get_jwt_identity())
    portfolios = Portfolio.query.filter_by(user_id=user_id).all()
    return jsonify([p.to_dict() for p in portfolios if (p.amount + p.locked_amount) > 0]), 200

@user_bp.route('/deposit', methods=['POST'])
@jwt_required()
def deposit():
    """
    Deposit Virtual Cash
    ---
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          properties:
            amount: {type: number}
    responses:
      200:
        description: Deposit successful
    """
    user_id = int(get_jwt_identity())
    data = request.get_json()
    amount = data.get('amount')
    if not amount or amount <= 0:
        return jsonify({'message': 'Invalid amount'}), 400
    user = db.session.get(User, user_id)
    user.balance += amount
    transaction = Transaction(user_id=user.id, type='deposit', amount=amount, total_cash=amount)
    db.session.add(transaction)
    db.session.commit()
    return jsonify({'message': f'Successfully deposited ${amount}', 'new_balance': user.balance}), 200

@user_bp.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    """
    Get Market Leaderboard
    ---
    responses:
      200:
        description: List of users ranked by wealth
    """
    users = User.query.all()
    leaderboard = []
    for user in users:
        portfolio_value = 0
        portfolios = Portfolio.query.filter_by(user_id=user.id).all()
        for p in portfolios:
            portfolio_value += (p.amount + p.locked_amount) * p.coin.current_price
        total_wealth = user.balance + user.locked_balance + portfolio_value
        leaderboard.append({'username': user.username, 'total_wealth': total_wealth, 'is_market_wallet': user.is_market_wallet})
    leaderboard.sort(key=lambda x: x['total_wealth'], reverse=True)
    return jsonify(leaderboard), 200
