import pandas as pd

def calculate_rolling_strategy(df, stock1, stock2, window=10, threshold=2):
    spread = df[stock1] - df[stock2]
    rolling_mean = spread.rolling(window=window).mean()
    rolling_std = spread.rolling(window=window).std()
    zscore = (spread - rolling_mean) / rolling_std

    buy_signal = zscore < -threshold
    sell_signal = zscore > threshold
    exit_signal = zscore.abs() < 0.1

    signal_df = pd.DataFrame({
        'Spread': spread,
        'Rolling Mean': rolling_mean,
        'Rolling Std': rolling_std,
        'Z-Score': zscore,
        'Buy Signal': buy_signal,
        'Sell Signal': sell_signal,
        'Exit Signal': exit_signal
    }, index=df.index)

    return signal_df
