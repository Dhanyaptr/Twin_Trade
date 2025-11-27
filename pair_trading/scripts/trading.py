def simulate_pair_trading_strategy(signal_df, stock1, stock2, capital=100000, capital_per_trade=10000):
    position = None
    entry_prices = {}
    trade_log = []
    final_capital = capital

    for date, row in signal_df.iterrows():
        s1_price = row[stock1]
        s2_price = row[stock2]

        if position is None:
            if row['Buy Signal']:
                position = 'long'
                entry_prices = {stock1: s1_price, stock2: s2_price}
                trade_log.append(f"Buy {stock1} at ₹{s1_price:.2f}, Sell {stock2} at ₹{s2_price:.2f}")
            elif row['Sell Signal']:
                position = 'short'
                entry_prices = {stock1: s1_price, stock2: s2_price}
                trade_log.append(f"Sell {stock1} at ₹{s1_price:.2f}, Buy {stock2} at ₹{s2_price:.2f}")

        elif row['Exit Signal'] and position:
            exit_prices = {stock1: s1_price, stock2: s2_price}
            if position == 'long':
                profit = (exit_prices[stock1] - entry_prices[stock1]) * (capital_per_trade / entry_prices[stock1]) \
                       - (exit_prices[stock2] - entry_prices[stock2]) * (capital_per_trade / entry_prices[stock2])
            else:  # short
                profit = (entry_prices[stock1] - exit_prices[stock1]) * (capital_per_trade / entry_prices[stock1]) \
                       - (entry_prices[stock2] - exit_prices[stock2]) * (capital_per_trade / entry_prices[stock2])
            
            final_capital += profit
            trade_log.append(f"Exit: Spread reverted to mean on {date.strftime('%Y-%m-%d')}, Profit: ₹{profit:.2f}")
            position = None
            entry_prices = {}

    trade_log.append(f"\nFinal Capital: ₹{final_capital:.2f}")
    for line in trade_log:
        print(line)

    return final_capital
