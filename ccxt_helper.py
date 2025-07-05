import ccxt

def get_balance_in_usdt(exchange: ccxt.Exchange):
    """
    Fetches your Binance account balance and converts all assets to their
    USDT equivalent, returning the sum as a float.

    Args:
        api_key (str): Your Binance API key.
        api_secret (str): Your Binance API secret.

    Returns:
        float: The total estimated value of your assets in USDT, or None if an error occurs.
    """
    total_usdt_value = 0
    try:
        # Fetch account balance
        # 'total' key in the balance dictionary gives you { 'ASSET': total_amount }
        balance = exchange.fetch_balance()
        non_zero_assets = {
            asset: amount
            for asset, amount in balance['total'].items()
            if amount > 0
        }

        if not non_zero_assets:
            print("No assets found in your balance.")

        # Fetch all tickers once to get current prices
        tickers = exchange.fetch_tickers()

        for asset, amount in non_zero_assets.items():
            if asset == 'USDT':
                usdt_equivalent = amount
                total_usdt_value += usdt_equivalent
            else:
                pair_usdt = f"{asset}/USDT"
                price = None
                if pair_usdt in tickers:
                    price = tickers[pair_usdt]['last']
                if price:
                    usdt_equivalent = amount * price
                    total_usdt_value += usdt_equivalent
                else:
                    print(f"Warning: Could not find price for {asset}. Skipping conversion for this asset.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    return total_usdt_value