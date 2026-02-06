from app.models.coin import Coin

def update_price_on_trade(coin, amount, is_buy):
    """
    Updates the price of a coin based on trading volume.
    Formula: new_price = current_price * (1 + (amount / volume_impact)) if buy
             new_price = current_price * (1 - (amount / volume_impact)) if sell
    """
    impact_factor = amount / coin.volume_impact

    if is_buy:
        coin.current_price = coin.current_price * (1 + impact_factor)
    else:
        coin.current_price = coin.current_price * (1 - impact_factor)

    # Ensure price doesn't go below a tiny fraction of base price
    min_price = coin.base_price * 0.01
    if coin.current_price < min_price:
        coin.current_price = min_price

    return coin.current_price

def get_market_summary():
    coins = Coin.query.all()
    return [coin.to_dict() for coin in coins]
