import os
import re
from datetime import datetime, timedelta
from flask import Flask, Blueprint, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from flask_migrate import Migrate
from flask_cors import CORS
from flasgger import Swagger
from email_validator import validate_email, EmailNotValidError

from models import db, User, Coin, Portfolio, Transaction, LimitOrder, PriceHistory
from services import get_market_summary, update_price_on_trade

# Configuration
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'kripto-market-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///crypto_market.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)

# Extensions
jwt = JWTManager()
migrate = Migrate()
swagger = Swagger()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    CORS(app)
    swagger.init_app(app)

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(market_bp, url_prefix='/api/market')
    app.register_blueprint(trade_bp, url_prefix='/api/trade')
    app.register_blueprint(user_bp, url_prefix='/api/user')

    return app

# --- Auth Routes ---
auth_bp = Blueprint('auth', __name__)

def is_password_strong(password):
    if len(password) < 8: return False
    if not re.search("[a-z]", password): return False
    if not re.search("[A-Z]", password): return False
    if not re.search("[0-9]", password): return False
    return True

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or not all(k in data for k in ('username', 'email', 'password')):
        return jsonify({'message': 'Missing required fields'}), 400
    try:
        validate_email(data['email'], check_deliverability=False)
    except EmailNotValidError:
        return jsonify({'message': 'Invalid email format'}), 400
    if not is_password_strong(data['password']):
        return jsonify({'message': 'Password too weak. Must be at least 8 characters and contain uppercase, lowercase, and numbers.'}), 400
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'Username already exists'}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already exists'}), 400
    user = User(username=data['username'], email=data['email'])
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully'}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Missing required fields'}), 400
    user = User.query.filter_by(username=data['username']).first()
    if user is None or not user.check_password(data['password']):
        return jsonify({'message': 'Invalid username or password'}), 401
    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))
    return jsonify({'access_token': access_token, 'refresh_token': refresh_token, 'user': user.to_dict()}), 200

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    return jsonify({'access_token': access_token}), 200

# --- Market Routes ---
market_bp = Blueprint('market', __name__)

@market_bp.route('/', methods=['GET'])
def get_market():
    return jsonify(get_market_summary()), 200

@market_bp.route('/<symbol>', methods=['GET'])
def get_coin_detail(symbol):
    coin = Coin.query.filter_by(symbol=symbol.upper()).first()
    if not coin: return jsonify({'message': 'Coin not found'}), 404
    return jsonify(coin.to_dict()), 200

@market_bp.route('/<symbol>/history', methods=['GET'])
def get_coin_history(symbol):
    coin = Coin.query.filter_by(symbol=symbol.upper()).first()
    if not coin: return jsonify({'message': 'Coin not found'}), 404
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    pagination = PriceHistory.query.filter_by(coin_id=coin.id).order_by(PriceHistory.timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        'history': [h.to_dict() for h in reversed(pagination.items)],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': pagination.page
    }), 200

# --- Trade Routes ---
trade_bp = Blueprint('trade', __name__)
TRADING_FEE_RATE = 0.001

def get_market_wallet():
    return User.query.filter_by(is_market_wallet=True).first()

@trade_bp.route('/buy', methods=['POST'])
@jwt_required()
def buy_coin():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    symbol = data.get('symbol'); amount = data.get('amount')
    if not symbol or not amount or amount <= 0: return jsonify({'message': 'Invalid symbol or amount'}), 400
    coin = Coin.query.filter_by(symbol=symbol.upper()).first()
    if not coin: return jsonify({'message': 'Coin not found'}), 404
    user = db.session.get(User, user_id)
    market_wallet = get_market_wallet()
    raw_cost = coin.current_price * amount; fee = raw_cost * TRADING_FEE_RATE; total_cost = raw_cost + fee
    if user.balance < total_cost: return jsonify({'message': 'Insufficient balance'}), 400
    try:
        user.balance -= total_cost; market_wallet.balance += fee
        portfolio = Portfolio.query.filter_by(user_id=user.id, coin_id=coin.id).first()
        if not portfolio:
            portfolio = Portfolio(user_id=user.id, coin_id=coin.id, amount=amount); db.session.add(portfolio)
        else: portfolio.amount += amount
        transaction = Transaction(user_id=user.id, coin_id=coin.id, type='buy', amount=amount, price_at_time=coin.current_price, total_cash=total_cost)
        db.session.add(transaction)
        new_price = update_price_on_trade(coin, amount, is_buy=True); db.session.commit()
        return jsonify({'message': f'Successfully bought {amount} {symbol}', 'new_balance': user.balance, 'fee_paid': fee, 'new_coin_price': new_price}), 200
    except Exception as e:
        db.session.rollback(); return jsonify({'message': 'Transaction failed', 'error': str(e)}), 500

@trade_bp.route('/sell', methods=['POST'])
@jwt_required()
def sell_coin():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    symbol = data.get('symbol'); amount = data.get('amount')
    if not symbol or not amount or amount <= 0: return jsonify({'message': 'Invalid symbol or amount'}), 400
    coin = Coin.query.filter_by(symbol=symbol.upper()).first()
    if not coin: return jsonify({'message': 'Coin not found'}), 404
    user = db.session.get(User, user_id)
    portfolio = Portfolio.query.filter_by(user_id=user.id, coin_id=coin.id).first()
    market_wallet = get_market_wallet()
    if not portfolio or portfolio.amount < amount: return jsonify({'message': 'Insufficient coin balance'}), 400
    try:
        raw_gain = coin.current_price * amount; fee = raw_gain * TRADING_FEE_RATE; total_gain = raw_gain - fee
        user.balance += total_gain; market_wallet.balance += fee; portfolio.amount -= amount
        transaction = Transaction(user_id=user.id, coin_id=coin.id, type='sell', amount=amount, price_at_time=coin.current_price, total_cash=total_gain)
        db.session.add(transaction)
        new_price = update_price_on_trade(coin, amount, is_buy=False); db.session.commit()
        return jsonify({'message': f'Successfully sold {amount} {symbol}', 'new_balance': user.balance, 'fee_paid': fee, 'new_coin_price': new_price}), 200
    except Exception as e:
        db.session.rollback(); return jsonify({'message': 'Transaction failed', 'error': str(e)}), 500

@trade_bp.route('/limit-order', methods=['POST'])
@jwt_required()
def create_limit_order():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    symbol = data.get('symbol'); amount = data.get('amount'); target_price = data.get('target_price'); order_type = data.get('type')
    if not all([symbol, amount, target_price, order_type]) or amount <= 0 or target_price <= 0: return jsonify({'message': 'Missing or invalid fields'}), 400
    coin = Coin.query.filter_by(symbol=symbol.upper()).first()
    if not coin: return jsonify({'message': 'Coin not found'}), 404
    user = db.session.get(User, user_id)
    try:
        if order_type == 'buy':
            total_cost = (target_price * amount) * (1 + TRADING_FEE_RATE)
            if user.balance < total_cost: return jsonify({'message': 'Insufficient balance'}), 400
            user.balance -= total_cost; user.locked_balance += total_cost
        else:
            portfolio = Portfolio.query.filter_by(user_id=user.id, coin_id=coin.id).first()
            if not portfolio or portfolio.amount < amount: return jsonify({'message': 'Insufficient coin balance'}), 400
            portfolio.amount -= amount; portfolio.locked_amount += amount
        new_order = LimitOrder(user_id=user.id, coin_id=coin.id, type=order_type, amount=amount, target_price=target_price, status='pending')
        db.session.add(new_order); db.session.commit()
        return jsonify({'message': f'Limit {order_type} order created successfully', 'order': new_order.to_dict()}), 201
    except Exception as e:
        db.session.rollback(); return jsonify({'message': 'Failed to create limit order', 'error': str(e)}), 500

@trade_bp.route('/limit-order/<int:order_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_limit_order(order_id):
    user_id = int(get_jwt_identity())
    order = db.session.get(LimitOrder, order_id)
    if not order or order.user_id != user_id: return jsonify({'message': 'Order not found'}), 404
    if order.status != 'pending': return jsonify({'message': f'Cannot cancel order with status {order.status}'}), 400
    user = db.session.get(User, user_id)
    try:
        if order.type == 'buy':
            locked_total = (order.target_price * order.amount) * (1 + TRADING_FEE_RATE); user.locked_balance -= locked_total; user.balance += locked_total
        else:
            portfolio = Portfolio.query.filter_by(user_id=user.id, coin_id=order.coin_id).first()
            portfolio.locked_amount -= order.amount; portfolio.amount += order.amount
        order.status = 'cancelled'; db.session.commit()
        return jsonify({'message': 'Order cancelled successfully'}), 200
    except Exception as e:
        db.session.rollback(); return jsonify({'message': 'Failed to cancel order', 'error': str(e)}), 500

@trade_bp.route('/limit-orders', methods=['GET'])
@jwt_required()
def get_limit_orders():
    user_id = int(get_jwt_identity())
    orders = LimitOrder.query.filter_by(user_id=user_id).all()
    return jsonify([o.to_dict() for o in orders]), 200

# --- User Routes ---
user_bp = Blueprint('user', __name__)

@user_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    user_id = int(get_jwt_identity()); user = db.session.get(User, user_id)
    return jsonify(user.to_dict()), 200

@user_bp.route('/portfolio', methods=['GET'])
@jwt_required()
def get_portfolio():
    user_id = int(get_jwt_identity()); portfolios = Portfolio.query.filter_by(user_id=user_id).all()
    return jsonify([p.to_dict() for p in portfolios if (p.amount + p.locked_amount) > 0]), 200

@user_bp.route('/deposit', methods=['POST'])
@jwt_required()
def deposit():
    user_id = int(get_jwt_identity()); data = request.get_json(); amount = data.get('amount')
    if not amount or amount <= 0: return jsonify({'message': 'Invalid amount'}), 400
    user = db.session.get(User, user_id); user.balance += amount
    transaction = Transaction(user_id=user.id, type='deposit', amount=amount, total_cash=amount)
    db.session.add(transaction); db.session.commit()
    return jsonify({'message': f'Successfully deposited ${amount}', 'new_balance': user.balance}), 200

@user_bp.route('/transactions', methods=['GET'])
@jwt_required()
def get_transactions():
    user_id = int(get_jwt_identity())
    page = request.args.get('page', 1, type=int); per_page = request.args.get('per_page', 10, type=int)
    pagination = Transaction.query.filter_by(user_id=user_id).order_by(Transaction.timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        'transactions': [t.to_dict() for t in pagination.items],
        'total': pagination.total, 'pages': pagination.pages, 'current_page': pagination.page
    }), 200

@user_bp.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    users = User.query.all(); leaderboard = []
    for user in users:
        portfolio_value = 0; portfolios = Portfolio.query.filter_by(user_id=user.id).all()
        for p in portfolios: portfolio_value += (p.amount + p.locked_amount) * p.coin.current_price
        total_wealth = user.balance + user.locked_balance + portfolio_value
        leaderboard.append({'username': user.username, 'total_wealth': total_wealth, 'is_market_wallet': user.is_market_wallet})
    leaderboard.sort(key=lambda x: x['total_wealth'], reverse=True)
    return jsonify(leaderboard), 200

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Coin': Coin, 'Portfolio': Portfolio, 'Transaction': Transaction}

if __name__ == '__main__':
    app.run(debug=True)
