import random
from datetime import datetime
from app import db
from app.models.coin import Coin
from app.models.price_history import PriceHistory

def apply_volatility(coin, force=False):
    """
    Simulates price movement based on elapsed time.
    """
    now = datetime.utcnow()
    time_diff = (now - coin.last_update).total_seconds()

    if time_diff < 60 and not force:
        from app.services.trade_service import check_and_execute_limit_orders
        check_and_execute_limit_orders(coin)
        return coin.current_price

    volatility_rate = 0.005
    intervals = time_diff / 600
    if intervals == 0 and force: intervals = 0.1

    change_percent = random.uniform(-volatility_rate, volatility_rate) * intervals
    coin.current_price *= (1 + change_percent)

    min_price = coin.base_price * 0.01
    if coin.current_price < min_price:
        coin.current_price = min_price

    coin.last_update = now
    record_price_history(coin)

    from app.services.trade_service import check_and_execute_limit_orders
    check_and_execute_limit_orders(coin)

    return coin.current_price

def update_price_on_trade(coin, amount, is_buy, check_limit=True):
    """
    Updates price and optionally checks limit orders.
    check_limit is False when called from within limit order execution to avoid recursion.
    """
    impact_factor = amount / coin.volume_impact
    if is_buy:
        coin.current_price = coin.current_price * (1 + impact_factor)
    else:
        coin.current_price = coin.current_price * (1 - impact_factor)

    min_price = coin.base_price * 0.01
    if coin.current_price < min_price:
        coin.current_price = min_price

    coin.last_update = datetime.utcnow()
    record_price_history(coin)

    if check_limit:
        from app.services.trade_service import check_and_execute_limit_orders
        check_and_execute_limit_orders(coin)

    return coin.current_price

def record_price_history(coin):
    history = PriceHistory(coin_id=coin.id, price=coin.current_price)
    db.session.add(history)

def get_market_summary():
    coins = Coin.query.all()
    for coin in coins:
        apply_volatility(coin)
    db.session.commit()
    return [coin.to_dict() for coin in coins]
