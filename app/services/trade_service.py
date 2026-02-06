from app import db
from app.models.user import User
from app.models.coin import Coin
from app.models.portfolio import Portfolio
from app.models.transaction import Transaction
from app.models.limit_order import LimitOrder

def check_and_execute_limit_orders(coin):
    """
    Checks all pending limit orders for a specific coin and executes them if conditions are met.
    """
    # Fetch orders that are still pending
    pending_orders = LimitOrder.query.filter_by(coin_id=coin.id, status='pending').all()

    for order in pending_orders:
        # Refresh order from DB to get latest status (in case it was executed in a nested call)
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
            # Funds were in locked_balance.
            # The total_cost was target_price * amount * (1 + fee)
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

        # Update price due to this execution, but DON'T trigger recursive check
        from app.services.price_service import update_price_on_trade
        update_price_on_trade(coin, order.amount, is_buy=(order.type == 'buy'), check_limit=False)

    except Exception as e:
        db.session.rollback()
        print(f"Failed to execute limit order {order.id}: {e}")
