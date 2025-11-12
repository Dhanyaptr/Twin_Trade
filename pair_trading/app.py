# app.py

import sys
import os
import matplotlib.pyplot as plt
sys.path.append(os.path.abspath('..'))
import pandas as pd

from scripts.data_preparation import prepare_data
from scripts.data_loader import load_and_merge_data
from scripts.cointegration_utils import (
    find_cointegrated_pairs,
    get_hedge_ratio,
    calculate_spread,
    calculate_rolling_mean_std,
    calculate_zscore,
    generate_signals
)
from scripts.pair_selection import get_top_n_pairs


def run_automatic_mode():
    # Step 1: Load data
    raw_df = load_and_merge_data('data')
    prepared_df = prepare_data(raw_df)

    # Step 2: Cointegration analysis
    coint_pairs, pval_matrix = find_cointegrated_pairs(prepared_df)

    print("Cointegrated Pairs (p < 0.05):")
    for stock1, stock2, pval in coint_pairs:
        print(f"{stock1} & {stock2} → p-value: {pval:.4f}")

    # Step 3: Get top pair
    top_pairs = get_top_n_pairs(prepared_df, pval_matrix, n=1)
    stock1, stock2, pval, corr, score = top_pairs[0]

    # Step 4: Price plot
    y = prepared_df[stock1]
    x = prepared_df[stock2]

    plt.figure(figsize=(12, 6))
    plt.plot(y.index, y, label=stock1)
    plt.plot(x.index, x, label=stock2)
    plt.title(f"Price Series: {stock1} & {stock2}")
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.legend()
    plt.savefig('plots/Price_Movement.png', dpi=150, bbox_inches='tight')

    # Step 5: Spread plot
    hedge_ratio = get_hedge_ratio(y, x)
    spread = calculate_spread(y, x, hedge_ratio)

    plt.figure(figsize=(12, 4))
    plt.plot(spread.index, spread)
    plt.axhline(spread.mean(), color='red', linestyle='--', label='Mean')
    plt.title(f"Spread: {stock1} - {hedge_ratio:.4f} × {stock2}")
    plt.legend()
    plt.savefig('plots/spread.png', dpi=150, bbox_inches='tight')

    # Step 6: Rolling mean & std
    rolling_mean, rolling_std = calculate_rolling_mean_std(spread, window=5)
    print("\nRolling Mean (last 5):")
    print(rolling_mean.tail())
    print("\nRolling Std (last 5):")
    print(rolling_std.tail())

    # Step 7: Z-score calculation
    zscore = calculate_zscore(spread, rolling_mean, rolling_std)

    # Step 8: Generate signals
    signals = generate_signals(spread, zscore, upper_threshold=2.0, lower_threshold=-2.0, exit_threshold=0.5)
    signals_series = pd.Series(signals, index=spread.index)
    print("\nLast 10 Trading Signals:")
    print(signals_series.tail(10))

    # Step 8b: Get only the final signal
    last_signal = signals_series.iloc[-1]
    if last_signal == "BUY_A_SELL_B":
        print(f"\n📌 Final Trading Signal: BUY {stock1} and SELL {stock2}")
        print(f"At latest prices → {stock1}: {y.iloc[-1]:.2f}, {stock2}: {x.iloc[-1]:.2f}")

    elif last_signal == "SELL_A_BUY_B":
        print(f"\n📌 Final Trading Signal: SELL {stock1} and BUY {stock2}")
        print(f"At latest prices → {stock1}: {y.iloc[-1]:.2f}, {stock2}: {x.iloc[-1]:.2f}")

    elif last_signal == "HOLD":
        print(f"\n📌 Final Trading Signal: HOLD")

    elif last_signal == "CLOSE":
        print(f"\n📌 Final Trading Signal: CLOSE (exit any open positions)")

    # Step 9: Plot Z-score with thresholds
    plt.figure(figsize=(12, 4))
    plt.plot(zscore.index, zscore, label="Z-score")
    plt.axhline(2, color='red', linestyle='--', label="Sell Threshold")
    plt.axhline(-2, color='green', linestyle='--', label="Buy Threshold")
    plt.axhline(0, color='black', linestyle='-')
    plt.title(f"Z-score & Trading Signals: {stock1} / {stock2}")
    plt.legend()
    plt.savefig('plots/zscore_signals.png', dpi=150, bbox_inches='tight')
