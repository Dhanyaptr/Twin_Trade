def generate_trade_signals_with_amounts(zscore_series, stock1, stock2, capital_per_trade=10000, threshold=1.0):
    signals = []
    position = None  # None, 'long', or 'short'

    for z in zscore_series:
        if position is None:
            if z > threshold:
                signals.append({
                    'action': 'Sell spread',
                    'stock1': f"Sell {stock1}",
                    'stock2': f"Buy {stock2}",
                    'amount_each': capital_per_trade
                })
                position = 'short'
            elif z < -threshold:
                signals.append({
                    'action': 'Buy spread',
                    'stock1': f"Buy {stock1}",
                    'stock2': f"Sell {stock2}",
                    'amount_each': capital_per_trade
                })
                position = 'long'
            else:
                signals.append({'action': 'Hold'})
        elif position == 'short':
            if z < 0:
                signals.append({'action': 'Close Position'})
                position = None
            else:
                signals.append({'action': 'Hold'})
        elif position == 'long':
            if z > 0:
                signals.append({'action': 'Close Position'})
                position = None
            else:
                signals.append({'action': 'Hold'})
    return signals


def generate_trade_signals_with_prices(zscore_series, stock1_prices, stock2_prices, dates, stock1_name, stock2_name, capital_per_trade=10000, threshold=1.0):
    signals = []
    position = None
    capital = 100000

    for i, z in enumerate(zscore_series):
        date = dates[i]
        price1 = stock1_prices[i]
        price2 = stock2_prices[i]

        if position is None:
            if z > threshold:
                signals.append(f"Sell {stock1_name} at ₹{price1:.2f}, Buy {stock2_name} at ₹{price2:.2f} on {date}")
                position = 'short'
            elif z < -threshold:
                signals.append(f"Buy {stock1_name} at ₹{price1:.2f}, Sell {stock2_name} at ₹{price2:.2f} on {date}")
                position = 'long'
            else:
                signals.append("Hold")
        elif position == 'short':
            if z < 0:
                signals.append(f"Exit: Spread reverted to mean on {date}")
                capital += 2500
                position = None
            else:
                signals.append("Hold")
        elif position == 'long':
            if z > 0:
                signals.append(f"Exit: Spread reverted to mean on {date}")
                capital += 2500
                position = None
            else:
                signals.append("Hold")

    # Don't add capital info to the signals list!
    return signals, capital
