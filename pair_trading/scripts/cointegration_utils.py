import pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.stattools import coint

def find_cointegrated_pairs(data, significance=0.05):
    """
    Finds all pairs of columns in `data` that are cointegrated.
    Cleans numeric columns first (remove commas, convert to float).
    """
    import numpy as np
    
    # Clean numeric columns: remove commas and convert to float
    data = data.apply(lambda col: 
                      pd.to_numeric(col.astype(str).str.replace(",", ""), errors="coerce")
                      if col.dtype == object else col)
    
    n = data.shape[1]
    pval_matrix = pd.DataFrame(1.0, index=data.columns, columns=data.columns)
    pairs = []

    for i in range(n):
        for j in range(i + 1, n):
            stock1 = data.columns[i]
            stock2 = data.columns[j]
            try:
                _, pval, _ = coint(data[stock1].dropna(), data[stock2].dropna())
                pval_matrix.loc[stock1, stock2] = pval
                if pval < significance:
                    pairs.append((stock1, stock2, pval))
            except Exception as e:
                print(f"[ERROR] coint({stock1},{stock2}): {e}")

    return pairs, pval_matrix



def get_hedge_ratio(y, x):
    """
    Calculate hedge ratio (beta) using OLS regression.
    y = dependent series
    x = independent series
    """
    x_const = sm.add_constant(x)
    model = sm.OLS(y, x_const).fit()
    # prefer name-based access; fall back to iloc
    beta = model.params.get(x.name)
    if beta is None:
        beta = model.params.iloc[1]   # second coefficient
    return beta



def calculate_spread(y, x, hedge_ratio):
    """
    Calculate spread = y - βx.
    """
    return y - hedge_ratio * x


def calculate_rolling_mean_std(spread, window=5):
    n = spread.dropna().shape[0]
    if n < window:
        # adapt window to available data but warn user
        eff_window = max(2, n)   # at least 2
        print(f"[WARN] requested window={window} larger than data length={n}. Using window={eff_window}.")
    else:
        eff_window = window
    rolling_mean = spread.rolling(window=eff_window).mean()
    rolling_std  = spread.rolling(window=eff_window).std()
    return rolling_mean, rolling_std

def calculate_zscore(spread, rolling_mean, rolling_std):
    return (spread - rolling_mean) / rolling_std

def generate_signals(spread, zscore):
    signals = []
    position = None  # NONE, BUY_Y_SELL_X or SELL_Y_BUY_X

    for i in range(len(zscore)):
        z = zscore.iloc[i] if hasattr(zscore, "iloc") else zscore[i]

        if z > 2 and position != "SELL_Y_BUY_X":
            signals.append("SELL_Y_BUY_X")
            position = "SELL_Y_BUY_X"

        elif z < -2 and position != "BUY_Y_SELL_X":
            signals.append("BUY_Y_SELL_X")
            position = "BUY_Y_SELL_X"

        elif position is not None and abs(z) < 0.5:
            signals.append("EXIT")
            position = None

        else:
            signals.append(None)

    return signals
def backtest_pair(y_prices, x_prices, signals, dates, stock1, stock2):
    trades = []
    position = None
    entry_y = entry_x = entry_date = None

    for i in range(len(signals)):
        signal = signals[i]

        # ✅ BUY Y SELL X
        if signal == "BUY_Y_SELL_X" and position is None:
            position = "BUY_Y_SELL_X"
            entry_y = y_prices[i]
            entry_x = x_prices[i]
            entry_date = dates[i]

        # ✅ SELL Y BUY X
        elif signal == "SELL_Y_BUY_X" and position is None:
            position = "SELL_Y_BUY_X"
            entry_y = y_prices[i]
            entry_x = x_prices[i]
            entry_date = dates[i]

        # ✅ EXIT CONDITION
        elif signal == "EXIT" and position is not None:
            exit_y = y_prices[i]
            exit_x = x_prices[i]
            exit_date = dates[i]

            # PnL calculation remains same
            if position == "BUY_Y_SELL_X":
                pnl = (exit_y - entry_y) - (exit_x - entry_x)
            else:  # SELL_Y_BUY_X
                pnl = (entry_y - exit_y) + (entry_x - exit_x)

            trades.append({
                "date_entry": entry_date.strftime("%Y-%m-%d"),
                "date_exit": exit_date.strftime("%Y-%m-%d"),
                "stock_buy": stock1 if position == "BUY_Y_SELL_X" else stock2,
                "stock_sell": stock2 if position == "BUY_Y_SELL_X" else stock1,
                "entry_y": entry_y,
                "entry_x": entry_x,
                "exit_y": exit_y,
                "exit_x": exit_x,
                "pnl": pnl
            })

            position = None
            entry_y = entry_x = entry_date = None

    return trades




