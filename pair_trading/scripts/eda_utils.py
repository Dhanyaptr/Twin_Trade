import matplotlib.pyplot as plt
import seaborn as sns

def plot_stock_prices(df, stock_list):
    plt.figure(figsize=(15, 7))
    for stock in stock_list:
        plt.plot(df.index, df[stock], label=stock)
    plt.title("Stock Closing Prices")
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

def plot_correlation_matrix(df):
    corr_matrix = df.corr()
    plt.figure(figsize=(12, 10))
    sns.heatmap(corr_matrix, annot=True, fmt=".2f", cmap="coolwarm")
    plt.title("Correlation Matrix")
    plt.show()
