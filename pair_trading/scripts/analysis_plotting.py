import matplotlib.pyplot as plt

def calculate_zscore(spread):
    return (spread - spread.mean()) / spread.std()

def plot_top_pair(df, top_pair):
    stock1, stock2 = top_pair
    s1 = df[stock1]
    s2 = df[stock2]

    spread = s1 - s2
    zscore = calculate_zscore(spread)

    plt.figure(figsize=(12, 6))
    plt.plot(df.index, zscore, label='Z-score', color='blue')
    plt.axhline(0, color='black', linestyle='--')
    plt.axhline(1.0, color='red', linestyle='--')
    plt.axhline(-1.0, color='green', linestyle='--')
    plt.title(f"Z-Score Spread for Closest Pair: {stock1} & {stock2}")
    plt.xlabel("Date")
    plt.ylabel("Z-score")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f'plots/zscore_{stock1}_{stock2}.png')
    plt.close()


def plot_cointegration_graph(df, stock1, stock2):
    s1 = df[stock1]
    s2 = df[stock2]

    plt.figure(figsize=(12, 6))
    plt.plot(df.index, s1, label=stock1)
    plt.plot(df.index, s2, label=stock2)
    plt.title(f"Cointegration Graph: {stock1} & {stock2}")
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f'plots/cointegration_{stock1}_{stock2}.png')
    plt.close()


def plot_rolling_zscore(signal_df, stock1, stock2, window=10):
    signal_df = signal_df.dropna(subset=['Z-Score'])
    signal_df = signal_df.reset_index()
    plt.figure(figsize=(14, 6))
    plt.plot(signal_df['Z-Score'], label='Rolling Z-Score')
    plt.axhline(0, color='black', linestyle='--')
    plt.axhline(2, color='red', linestyle='--', label='+2 Std Dev (Sell)')
    plt.axhline(-2, color='green', linestyle='--', label='-2 Std Dev (Buy)')
    plt.title(f"{stock1} - {stock2} Rolling Z-Score (window={window})")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    
    filename = f"plots/{stock1}_{stock2}_rolling_zscore_signals_w{window}.png"
    plt.savefig(filename)
    print(f"Signal Z-score plot saved to: {filename}")



def plot_signal_graph(df, stock1, stock2):
    plt.figure(figsize=(14, 7))
    plt.plot(df['Date'], df['Spread'], label='Spread', color='blue')
    plt.plot(df['Date'], df['Rolling Mean'], label='Rolling Mean', color='orange')

    # Buy signals
    buy_signals = df[df['Buy Signal'] == True]
    plt.scatter(buy_signals['Date'], buy_signals['Spread'], label='Buy Signal', color='green', marker='^', s=100)

    # Sell signals
    sell_signals = df[df['Sell Signal'] == True]
    plt.scatter(sell_signals['Date'], sell_signals['Spread'], label='Sell Signal', color='red', marker='v', s=100)

    # Exit signals
    exit_signals = df[df['Exit Signal'] == True]
    plt.scatter(exit_signals['Date'], exit_signals['Spread'], label='Exit Signal', color='black', marker='x', s=80)

    plt.xlabel("Date")
    plt.ylabel("Spread")
    plt.title(f"Signal Plot for {stock1} and {stock2}")
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
