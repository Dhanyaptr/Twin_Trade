from pydantic import BaseModel
class CustomRequest(BaseModel):
    stock: str
from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
import os, glob

from backend.pair_trading.scripts.cointegration_utils import (
    find_cointegrated_pairs,
    get_hedge_ratio,
    calculate_spread,
    calculate_rolling_mean_std,
    calculate_zscore,
    generate_signals,
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = "backend/pair_trading/data"

# ✅ Clean values so JSON does not break
def clean_series(series):
    return (
        pd.Series(series)
        .replace([np.inf, -np.inf], np.nan)
        .fillna(0)
        .tolist()
    )


@app.get("/automatic-mode")
def automatic_mode():
    all_files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    dfs = []

    for f in all_files:
        df = pd.read_csv(f)
        df.columns = df.columns.str.strip().str.lower()
        if "date" not in df.columns or "close" not in df.columns:
            continue

        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"]).set_index("date")

        stock_name = os.path.basename(f).replace("Quote-Equity-", "").replace(".csv", "")
        stock_name = stock_name.split("-EQ")[0]

        df = df[["close"]].rename(columns={"close": stock_name})
        df[stock_name] = pd.to_numeric(df[stock_name].astype(str).str.replace(",", ""), errors="coerce")
        dfs.append(df)

    if not dfs:
        return {"status": "error", "message": "No valid CSVs found"}

    combined_df = pd.concat(dfs, axis=1).ffill()

    pairs, _ = find_cointegrated_pairs(combined_df, significance=0.05)
    if not pairs:
        return {"status": "error", "message": "No pairs found"}

    stock1, stock2, pval = sorted(pairs, key=lambda t: t[2])[0]

    y = combined_df[stock1]
    x = combined_df[stock2]
    df_pair = pd.concat([y, x], axis=1).dropna()
    y_clean, x_clean = df_pair.iloc[:, 0], df_pair.iloc[:, 1]

    y_norm = (y_clean - y_clean.mean()) / y_clean.std()
    x_norm = (x_clean - x_clean.mean()) / x_clean.std()

    # ✅ min_periods fix
    rolling_corr = y_norm.rolling(window=20, min_periods=1).corr(x_norm)

    hedge_ratio = get_hedge_ratio(y_clean, x_clean)
    spread = calculate_spread(y_clean, x_clean, hedge_ratio)

    # ✅ rolling start from day 1
    rolling_mean = spread.rolling(window=20, min_periods=1).mean()
    rolling_std = spread.rolling(window=20, min_periods=1).std()
    zscore = (spread - rolling_mean) / rolling_std

    signals = generate_signals(spread, zscore)
    # --- Adaptive recommendation logic (same as Custom Mode) ---
    recent_z = zscore[-5:] if len(zscore) >= 5 else zscore
    avg_z = np.mean(recent_z)

    if avg_z > 1.2:
        trade_action = f"Sell {stock1}, Buy {stock2}"
    elif avg_z < -1.2:
        trade_action = f"Buy {stock1}, Sell {stock2}"
    else:
        trade_action = "No trade suggestion"


    from backend.pair_trading.scripts.cointegration_utils import backtest_pair

    # ✅ Run backtest
    trade_results = backtest_pair(
    y_clean.values,
    x_clean.values,
    signals,
    df_pair.index,   # ✅ pass dates
    stock1,
    stock2
)

    # ✅ Convert P&L result to JSON-safe structure
    backtest_output = trade_results

    idx = df_pair.index

    return {
        "status": "ok",
        "best_pair": [stock1, stock2],
        "hedge_ratio": float(hedge_ratio),
        "latest_signal": signals[-1] if signals else None,
        "trade_action": trade_action,
        "zscore": clean_series(zscore),
        "spread": clean_series(spread),
        "rolling_mean": clean_series(rolling_mean),
        "correlation": clean_series(rolling_corr),
        "dates": idx.strftime("%Y-%m-%d").tolist(),
        "stock1_prices": y_clean.reindex(idx).tolist(),
        "stock2_prices": x_clean.reindex(idx).tolist(),
        "signals": [(None if s is None else str(s)) for s in signals],
        "backtest_results": backtest_output,
    }


@app.get("/dashboard")
def dashboard():
    all_data = automatic_mode()
    if all_data.get("status") != "ok":
        return all_data

    stock1, stock2 = all_data["best_pair"]
    return {
        "best_pair": {
            "pair": f"{stock1} - {stock2}",
            "correlation": None,
            "zscore": all_data["zscore"][-1],
            "change": "+2.34%",
        },
        "rolling_zscore": all_data["zscore"][-1],
        "trading_signal": {
            "signal": all_data["latest_signal"],
            "strength": "STRONG" if all_data["latest_signal"] else "NONE",
        },
    }


@app.post("/custom-mode")
async def custom_mode(body: CustomRequest):
    stock = body.stock

    if not stock:
        return {"status": "error", "message": "Stock symbol is required"}

    all_files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    dfs = []
    for f in all_files:
        df = pd.read_csv(f)
        df.columns = df.columns.str.strip().str.lower()
        if "date" not in df.columns or "close" not in df.columns:
            continue
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"]).set_index("date")

        stock_name = os.path.basename(f).replace("Quote-Equity-", "").replace(".csv", "")
        stock_name = stock_name.split("-EQ")[0]

        df = df[["close"]].rename(columns={"close": stock_name})
        df[stock_name] = pd.to_numeric(df[stock_name].astype(str).str.replace(",", ""), errors="coerce")
        dfs.append(df)

    combined_df = pd.concat(dfs, axis=1).ffill()

    if stock not in combined_df.columns:
        return {"status": "error", "message": f"Stock {stock} not found"}

    # --- STEP 1: Build full symmetric pair map ---
    pairs, _ = find_cointegrated_pairs(combined_df, significance=0.1)

    pair_map = {}
    for s1, s2, p in pairs:
        key = tuple(sorted([s1, s2]))  # ensures (A,B) and (B,A) are treated the same
        if key not in pair_map or p < pair_map[key]:
            pair_map[key] = p

    # --- STEP 2: Find all pairs that involve selected stock ---
    candidates = [(a, b, p) for (a, b), p in pair_map.items() if stock in (a, b)]

    # --- STEP 3: Pick the best (lowest p-value) pair ---
    if not candidates:
        # fallback: correlation
        corr_matrix = combined_df.corr()
        if stock not in corr_matrix.columns:
            return {"status": "error", "message": f"No data for {stock}"}

        top_corr = corr_matrix[stock].drop(index=stock).sort_values(ascending=False).head(1)
        if top_corr.empty:
            return {"status": "error", "message": f"No correlated pair found for {stock}"}

        pair_stock = top_corr.index[0]
        pval = 0.2
    else:
        a, b, pval = sorted(candidates, key=lambda t: t[2])[0]
        pair_stock = b if a == stock else a

    # --- STEP 4: Ensure consistent spread direction ---
    stock_a, stock_b = sorted([stock, pair_stock])
    y = combined_df[stock_a]
    x = combined_df[stock_b]
    df_pair = pd.concat([y, x], axis=1).dropna()

    hedge_ratio = get_hedge_ratio(df_pair[stock_a], df_pair[stock_b])
    spread = calculate_spread(df_pair[stock_a], df_pair[stock_b], hedge_ratio)

    # rolling stats
    rolling_mean = spread.rolling(window=20, min_periods=1).mean()
    rolling_std = spread.rolling(window=20, min_periods=1).std()
    zscore = (spread - rolling_mean) / rolling_std

    # --- Flip sign if user selected reverse stock ---
    if stock != stock_a:
        zscore = -zscore

    # correlation
    y_norm = (df_pair[stock_a] - df_pair[stock_a].mean()) / df_pair[stock_a].std()
    x_norm = (df_pair[stock_b] - df_pair[stock_b].mean()) / df_pair[stock_b].std()
    rolling_corr = y_norm.rolling(window=20, min_periods=1).corr(x_norm)

    # signals
    signals = generate_signals(spread, zscore)
    signals = list(signals)
    idx = df_pair.index

    # latest recommendation
    avg_z = np.mean(zscore[-5:]) if len(zscore) > 5 else np.mean(zscore)
    if avg_z > 1.2:
        stock_signal, pair_signal = "SELL", "BUY"
    elif avg_z < -1.2:
        stock_signal, pair_signal = "BUY", "SELL"
    else:
        stock_signal, pair_signal = "HOLD", "HOLD"

    latest_recommendation = {
        stock: stock_signal,
        pair_stock: pair_signal
    }

    from backend.pair_trading.scripts.cointegration_utils import backtest_pair
    trade_results = backtest_pair(
        df_pair[stock_a].values,
        df_pair[stock_b].values,
        signals,
        idx,
        stock_a,
        stock_b
    )

    return {
        "status": "ok",
        "selected_stock": stock,
        "pair_stock": pair_stock,
        "pair_order": f"{stock} - {pair_stock}",
        "pvalue": float(pval),
        "hedge_ratio": float(hedge_ratio),
        "latest_recommendation": latest_recommendation,
        "dates": idx.strftime("%Y-%m-%d").tolist(),
        "stock1_prices": df_pair[stock_a].reindex(idx).tolist(),
        "stock2_prices": df_pair[stock_b].reindex(idx).tolist(),
        "spread": clean_series(spread),
        "rolling_mean": clean_series(rolling_mean),
        "zscore": clean_series(zscore),
        "correlation": clean_series(rolling_corr),
        "signals": [("HOLD" if s is None else str(s)) for s in signals],
        "backtest_results": trade_results,
    }