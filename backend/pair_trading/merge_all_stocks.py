import os
import pandas as pd

DATA_DIR = "backend/pair_trading/data"
OUTPUT_FILE = os.path.join(DATA_DIR, "it_stocks.csv")

def merge_all_stocks():
    combined_df = pd.DataFrame()

    for file in os.listdir(DATA_DIR):
        if file.endswith(".csv") and file.startswith("Quote-Equity"):
            file_path = os.path.join(DATA_DIR, file)
            df = pd.read_csv(file_path, index_col=0)

            # Clean data
            df.index = pd.to_datetime(df.index, errors="coerce")
            df = df[~df.index.isna()]

            # Take only "Close Price" (adjust if needed)
            if "Close Price" in df.columns:
                stock_name = file.replace("Quote-Equity-", "").replace(".csv", "")
                combined_df[stock_name] = (
                    df["Close Price"]
                    .astype(str)
                    .str.replace(",", "", regex=False)
                    .astype(float)
                )

    combined_df.sort_index(inplace=True)
    combined_df.fillna(method="ffill", inplace=True)

    combined_df.to_csv(OUTPUT_FILE)
    print(f"✅ Merged file created at: {OUTPUT_FILE}")

if __name__ == "__main__":
    merge_all_stocks()
