from pydantic import BaseModel
class CustomRequest(BaseModel):
    selected_stocks: list[str]
    anchor_stock: str
from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
import os, glob
from backend.pair_trading.scripts.pair_selection import get_top_n_pairs,find_best_pair_within_subset
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
    selected_stocks = body.selected_stocks
    anchor = body.anchor_stock

    if not selected_stocks or len(selected_stocks) < 2:
        return {"status": "error", "message": "Select at least 2 stocks."}

    if anchor not in selected_stocks:
        return {"status": "error", "message": "Anchor stock must be selected in the list."}

    # Load all CSV files
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

    # Keep only user-selected stocks
    available = [s for s in selected_stocks if s in combined_df.columns]
    if len(available) < 2:
        return {"status": "error", "message": "Selected stocks not found in dataset."}

    user_df = combined_df[available].ffill()

    # Cointegration within subset
    pairs, pval_matrix = find_cointegrated_pairs(user_df, significance=0.1)

    # Filter pairs that include anchor
    subset_pairs = [(a, b, p) for (a, b, p) in pairs if anchor in (a, b)]

    # Determine best pair
    if subset_pairs:
        a, b, pval = sorted(subset_pairs, key=lambda x: x[2])[0]
        pair_stock = b if a == anchor else a
    else:
        # fallback: top-scoring pair from your utility
        try:
            top = get_top_n_pairs(user_df, pval_matrix, n=1)
            stock1, stock2, pval, corr, score = top[0]
            pair_stock = stock2 if stock1 == anchor else stock1
        except:
            # final fallback: correlation
            corr_series = user_df.corr()[anchor].drop(anchor)
            pair_stock = corr_series.idxmax()
            pval = 1.0

    # ============= Build Pair DataFrame (CORRECT PLACE) =============
    stock_a = anchor
    stock_b = pair_stock

    df_pair = user_df[[stock_a, stock_b]].dropna()
    if df_pair.empty:
        return {"status": "error", "message": "Insufficient overlapping data"}

    y = df_pair[stock_a]
    x = df_pair[stock_b]

    # === Analytics ===
    hedge_ratio = get_hedge_ratio(y, x)
    spread = calculate_spread(y, x, hedge_ratio)

    rolling_mean = spread.rolling(window=20, min_periods=1).mean()
    rolling_std = spread.rolling(window=20, min_periods=1).std()
    zscore = (spread - rolling_mean) / rolling_std

    # Rolling correlation
    y_norm = (y - y.mean()) / y.std()
    x_norm = (x - x.mean()) / x.std()
    rolling_corr = y_norm.rolling(window=20, min_periods=1).corr(x_norm)

    signals = list(generate_signals(spread, zscore))
    idx = df_pair.index

    # Recommendation
    avg_z = np.mean(zscore[-5:]) if len(zscore) >= 5 else np.mean(zscore)
    if avg_z > 1.2:
        anchor_sig, pair_sig = "SELL", "BUY"
    elif avg_z < -1.2:
        anchor_sig, pair_sig = "BUY", "SELL"
    else:
        anchor_sig, pair_sig = "HOLD", "HOLD"

    latest_recommendation = {
        stock_a: anchor_sig,
        stock_b: pair_sig
    }

    # Backtest
    from backend.pair_trading.scripts.cointegration_utils import backtest_pair
    trade_results = backtest_pair(
        y.values,
        x.values,
        signals,
        idx,
        stock_a,
        stock_b
    )

    return {
        "status": "ok",
        "anchor": stock_a,
        "best_pair": [stock_a, stock_b],
        "pvalue": float(pval),
        "hedge_ratio": float(hedge_ratio),
        "latest_recommendation": latest_recommendation,
        "dates": idx.strftime("%Y-%m-%d").tolist(),
        "stock1_prices": y.tolist(),
        "stock2_prices": x.tolist(),
        "spread": clean_series(spread),
        "rolling_mean": clean_series(rolling_mean),
        "zscore": clean_series(zscore),
        "correlation": clean_series(rolling_corr),
        "signals": [("HOLD" if s is None else str(s)) for s in signals],
        "backtest_results": trade_results,
    }
