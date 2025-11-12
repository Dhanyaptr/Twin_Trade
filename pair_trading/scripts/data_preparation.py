import pandas as pd
import os

def prepare_data(df):
    # Step 1: Ensure the index is datetime
    df.index = pd.to_datetime(df.index, errors='coerce')
    df = df[~df.index.isna()]  # Drop rows where date is NaT

    # Step 2: Remove commas and convert all columns to float
    for col in df.columns:
        df[col] = df[col].astype(str).str.replace(',', '', regex=False)
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Step 3: Sort index
    df.sort_index(inplace=True)

    # Step 4: Fill forward missing values
    df.fillna(method='ffill', inplace=True)

    return df





