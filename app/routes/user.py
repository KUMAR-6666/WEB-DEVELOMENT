from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User
from app.models.portfolio import Portfolio
from app.models.transaction import Transaction
from app import db

user_bp = Blueprint('user', __name__)

@user_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    return jsonify(user.to_dict()), 200

@user_bp.route('/portfolio', methods=['GET'])
@jwt_required()
def get_portfolio():
    user_id = int(get_jwt_identity())
    portfolios = Portfolio.query.filter_by(user_id=user_id).all()
    return jsonify([p.to_dict() for p in portfolios if p.amount > 0]), 200

@user_bp.route('/deposit', methods=['POST'])
@jwt_required()
def deposit():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    amount = data.get('amount')

    if not amount or amount <= 0:
        return jsonify({'message': 'Invalid amount'}), 400

    user = db.session.get(User, user_id)
    user.balance += amount

    transaction = Transaction(
        user_id=user.id,
        type='deposit',
        amount=amount,
        total_cash=amount
    )
    db.session.add(transaction)
    db.session.commit()

    return jsonify({
        'message': f'Successfully deposited ${amount}',
        'new_balance': user.balance
    }), 200

@user_bp.route('/transactions', methods=['GET'])
@jwt_required()
def get_transactions():
    user_id = int(get_jwt_identity())
    transactions = Transaction.query.filter_by(user_id=user_id).order_by(Transaction.timestamp.desc()).all()
    return jsonify([t.to_dict() for t in transactions]), 200
