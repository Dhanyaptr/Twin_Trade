import os
import sys
import pandas as pd
from matplotlib import pyplot as plt

# Ensure 'scripts' folder is importable
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))

from scripts.data_loader import load_and_merge_data
from scripts.cointegration_utils import find_cointegrated_pairs
from scripts.analysis_plotting import (
    plot_top_pair,
    plot_cointegration_graph,
    plot_rolling_zscore,
    plot_signal_graph  # ✅ newly added import
)
from analysis.rolling_strategy import calculate_rolling_strategy
from scripts.signal_generator import generate_trade_signals_with_prices

# Step 1: Load & merge cleaned data
merged_df = load_and_merge_data('data')  # Make sure 'Date' is set as index in this function

# Optional: Debug merged data structure
print("Merged DataFrame columns:", merged_df.columns)

# Step 2: Find cointegrated pairs
cointegrated_pairs, _ = find_cointegrated_pairs(merged_df)

# Safety check: Ensure at least one pair is found
if not cointegrated_pairs:
    print("No cointegrated pairs found.")
    sys.exit()

# Step 3: Pick the top cointegrated pair
top_pair = cointegrated_pairs[0]
stock1, stock2, _ = top_pair

# Debug: Show which pair we're plotting
print(f"Top cointegrated pair: {stock1} & {stock2}")

# Step 4: Plot cointegration and z-score
plot_cointegration_graph(merged_df, stock1, stock2)
plot_top_pair(merged_df, (stock1, stock2))

# Step 5: Calculate rolling strategy signals
signal_df = calculate_rolling_strategy(merged_df, stock1, stock2, window=10, threshold=1.0)

# Debug: Show last few rows of the signal DataFrame
print(signal_df.tail())

# Step 6: Plot Z-score with buy/sell signal levels
plot_rolling_zscore(signal_df, stock1, stock2, window=5)
signal_df = signal_df.reset_index()
# Prepare required inputs for enhanced signal generation
z_scores = signal_df['Z-Score'].values
dates = signal_df['Date'].astype(str).values
stock1_prices = merged_df[stock1].loc[signal_df['Date']].values
stock2_prices = merged_df[stock2].loc[signal_df['Date']].values

# Generate natural language signals
trade_signals, final_capital = generate_trade_signals_with_prices(
    zscore_series=z_scores,
    stock1_prices=stock1_prices,
    stock2_prices=stock2_prices,
    dates=dates,
    stock1_name=stock1,
    stock2_name=stock2,
    capital_per_trade=10000,
    threshold=1.0
)

signal_df['Signal'] = trade_signals
# ✅ Step 7: Generate natural language trade messages
print("\n📢 Trading Instructions for Top Cointegrated Pair:\n")
# Sort by date before printing
signal_df = signal_df.sort_values(by='Date')

with open(f"signals/{stock1}_{stock2}_trade_instructions.txt", "w") as f:
    f.write(f"📢 Trading Instructions for {stock1} & {stock2}:\n\n")

    for i, row in signal_df.iterrows():
        date_str = pd.to_datetime(row['Date']).strftime('%Y-%m-%d')
        signal = row['Signal']

        if "buy" in signal.lower() and "sell" in signal.lower():
            price1 = merged_df[stock1].loc[row['Date']]
            price2 = merged_df[stock2].loc[row['Date']]

            qty1 = int(5000 // price1)
            qty2 = int(5000 // price2)

            message = (
                f"{date_str} 👉 {signal} "
                f"(Buy {qty2} shares of {stock2} at ₹{price2:.2f}, "
                f"Sell {qty1} shares of {stock1} at ₹{price1:.2f})"
            )
        elif "exit" in signal.lower():
            message = f"{date_str} 🚪 {signal}"
        else:
            message = f"{date_str} 📌 HOLD (No Action)"

        print(message)
        f.write(message + "\n")




# print(f"Final Capital after trading: ₹{final_capital:.2f}")
os.makedirs("signals", exist_ok=True)
signal_df.to_csv(f"signals/{stock1}_{stock2}_detailed_signals.csv")

# ✅ Step 7: Plot signal chart with Buy/Sell/Exit markers
plot_signal_graph(signal_df, stock1, stock2)

# ✅ Step 8: Save signal DataFrame to CSV
os.makedirs("signals", exist_ok=True)
signal_df.to_csv(f"signals/{stock1}_{stock2}_signals.csv")

plt.tight_layout()
