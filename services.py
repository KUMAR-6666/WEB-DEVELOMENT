import random
from datetime import datetime, timedelta
from sqlalchemy import func
from models import db, User, Coin, Portfolio, Transaction, LimitOrder, PriceHistory

def check_and_execute_limit_orders(coin):
    """
    Checks all pending limit orders for a specific coin and executes them if conditions are met.
    """
    # Fetch orders that are still pending
    pending_orders = LimitOrder.query.filter_by(coin_id=coin.id, status='pending').all()

    for order in pending_orders:
        # Refresh order from DB to get latest status
        db.session.refresh(order)
        if order.status != 'pending':
            continue

        should_execute = False
        if order.type == 'buy' and coin.current_price <= order.target_price:
            should_execute = True
        elif order.type == 'sell' and coin.current_price >= order.target_price:
            should_execute = True

        if should_execute:
            execute_limit_order(order, coin)

def execute_limit_order(order, coin):
    user = db.session.get(User, order.user_id)
    market_wallet = User.query.filter_by(is_market_wallet=True).first()

    try:
        if order.type == 'buy':
            # Actual cost at execution time:
            actual_raw_cost = coin.current_price * order.amount
            actual_fee = actual_raw_cost * 0.001
            actual_total_cost = actual_raw_cost + actual_fee

            # Use funds from locked_balance
            locked_total = (order.target_price * order.amount) * (1.001)
            user.locked_balance -= locked_total

            # Refund difference if we bought cheaper than target
            diff = locked_total - actual_total_cost
            if diff > 0:
                user.balance += diff

            # Transfer fee to Market Wallet
            market_wallet.balance += actual_fee

            portfolio = Portfolio.query.filter_by(user_id=user.id, coin_id=coin.id).first()
            if not portfolio:
                portfolio = Portfolio(user_id=user.id, coin_id=coin.id, amount=order.amount)
                db.session.add(portfolio)
            else:
                portfolio.amount += order.amount

        elif order.type == 'sell':
            # Coins were in locked_amount
            portfolio = Portfolio.query.filter_by(user_id=user.id, coin_id=coin.id).first()
            portfolio.locked_amount -= order.amount

            raw_gain = coin.current_price * order.amount
            fee = raw_gain * 0.001
            total_gain = raw_gain - fee

            user.balance += total_gain
            market_wallet.balance += fee

        order.status = 'completed'

        # Record Transaction
        transaction = Transaction(
            user_id=user.id,
            coin_id=coin.id,
            type=f'limit_{order.type}',
            amount=order.amount,
            price_at_time=coin.current_price,
            total_cash=coin.current_price * order.amount
        )
        db.session.add(transaction)

        # Update price due to this execution
        update_price_on_trade(coin, order.amount, is_buy=(order.type == 'buy'), check_limit=False)

    except Exception as e:
        db.session.rollback()
        print(f"Failed to execute limit order {order.id}: {e}")

def apply_volatility(coin, force=False):
    """Simulates price movement based on elapsed time."""
    now = datetime.utcnow()
    time_diff = (now - coin.last_update).total_seconds()
    if time_diff < 60 and not force:
        check_and_execute_limit_orders(coin)
        return coin.current_price

    volatility_rate = 0.005
    intervals = time_diff / 600
    if intervals == 0 and force: intervals = 0.1
    change_percent = random.uniform(-volatility_rate, volatility_rate) * intervals
    coin.current_price *= (1 + change_percent)
    min_price = coin.base_price * 0.01
    if coin.current_price < min_price: coin.current_price = min_price
    coin.last_update = now
    record_price_history(coin)
    check_and_execute_limit_orders(coin)
    return coin.current_price

def update_price_on_trade(coin, amount, is_buy, check_limit=True):
    """Updates price and optionally checks limit orders."""
    impact_factor = amount / coin.volume_impact
    if is_buy: coin.current_price = coin.current_price * (1 + impact_factor)
    else: coin.current_price = coin.current_price * (1 - impact_factor)
    min_price = coin.base_price * 0.01
    if coin.current_price < min_price: coin.current_price = min_price
    coin.last_update = datetime.utcnow()
    record_price_history(coin)
    if check_limit:
        check_and_execute_limit_orders(coin)
    return coin.current_price

def record_price_history(coin):
    history = PriceHistory(coin_id=coin.id, price=coin.current_price)
    db.session.add(history)

def get_24h_stats(coin_id):
    """Calculates High, Low, and % Change in last 24h."""
    yesterday = datetime.utcnow() - timedelta(days=1)
    stats = db.session.query(
        func.max(PriceHistory.price).label('high'),
        func.min(PriceHistory.price).label('low')
    ).filter(PriceHistory.coin_id == coin_id, PriceHistory.timestamp >= yesterday).first()

    first_price_24h = PriceHistory.query.filter(
        PriceHistory.coin_id == coin_id,
        PriceHistory.timestamp >= yesterday
    ).order_by(PriceHistory.timestamp.asc()).first()

    current_price = db.session.get(Coin, coin_id).current_price
    change_pct = 0
    if first_price_24h:
        change_pct = ((current_price - first_price_24h.price) / first_price_24h.price) * 100

    return {
        'high_24h': stats.high or current_price,
        'low_24h': stats.low or current_price,
        'change_24h_pct': change_pct
    }

def get_market_summary():
    coins = Coin.query.all()
    summary = []
    for coin in coins:
        apply_volatility(coin)
        stats = get_24h_stats(coin.id)
        coin_dict = coin.to_dict()
        coin_dict.update(stats)
        summary.append(coin_dict)
    db.session.commit()
    return summary
