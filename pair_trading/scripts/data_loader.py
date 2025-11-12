import os
import pandas as pd

def load_and_merge_data(data_path='data'):
    merged_df = None
    files = os.listdir(data_path)

    for file in files:
        if file.endswith('.csv'):
            file_path = os.path.join(data_path, file)
            df = pd.read_csv(file_path)
            df.columns = df.columns.str.strip()  # Remove extra spaces
            df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
            df = df.dropna(subset=['Date'])  # Drop bad date rows


            # Extract stock name from filename
            stock_name = file.split('-')[2].upper()  # Example: INFY, TCS

            # Find the close price column
            close_col = None
            for col in df.columns:
                if col.strip().lower() in ['close price', 'close']:
                    close_col = col
                    break
            if close_col is None:
                raise ValueError(f"Close price column not found in {file}")

            # Remove commas and convert to float
            df[close_col] = df[close_col].astype(str).str.replace(',', '').astype(float)

            df = df[['Date', close_col]]
            df.rename(columns={close_col: stock_name}, inplace=True)

            if merged_df is None:
                merged_df = df
            else:
                merged_df = pd.merge(merged_df, df, on='Date', how='inner')

    # ✅ Set 'Date' as index
    merged_df.set_index('Date', inplace=True)
    
    return merged_df
