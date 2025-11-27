import numpy as np
import pandas as pd

def get_top_n_pairs(data, pval_matrix, n=1):
    pairs_scores = []
    stocks = data.columns

    for i in range(len(stocks)):
        for j in range(i+1, len(stocks)):
            stock1 = stocks[i]
            stock2 = stocks[j]
            pval = pval_matrix.loc[stock1, stock2]
            if pval < 0.05:
                corr = data[stock1].corr(data[stock2])
                if pd.notnull(corr) and corr != 0:
                    # Avoid division by zero or infinity
                    safe_pval = max(pval, 1e-8)
                    score = (-np.log(safe_pval)) * abs(corr)
                    pairs_scores.append((stock1, stock2, pval, corr, score))

    # Sort by score in descending order
    pairs_scores.sort(key=lambda x: x[4], reverse=True)

    # Debugging output to verify
    for rank, pair in enumerate(pairs_scores[:n], 1):
        print(f"[DEBUG] Rank {rank}: {pair[0]} & {pair[1]}, "
              f"p={pair[2]:.12g}, corr={pair[3]:.4f}, score={pair[4]:.4f}")

    return pairs_scores[:n]
def find_best_pair_within_subset(data, anchor_stock, selected_stocks, pval_matrix):
    """
    Find the best pair for anchor_stock inside selected_stocks only.
    Uses p-value + correlation score, just like automatic-mode logic.
    """

    if anchor_stock not in selected_stocks:
        raise ValueError("Anchor stock must be part of selected_stocks")

    pairs_scores = []

    for stock in selected_stocks:
        if stock == anchor_stock:
            continue

        pval = pval_matrix.loc[anchor_stock, stock]
        if pval >= 0.10:  # relax threshold for small subsets
            continue

        corr = data[anchor_stock].corr(data[stock])
        if pd.isnull(corr) or corr == 0:
            continue

        safe_pval = max(pval, 1e-8)
        score = (-np.log(safe_pval)) * abs(corr)

        pairs_scores.append((anchor_stock, stock, pval, corr, score))

    if not pairs_scores:
        return None  # No valid pair

    # Highest score = strongest relationship
    best = sorted(pairs_scores, key=lambda x: x[4], reverse=True)[0]

    return {
        "anchor": best[0],
        "pair": best[1],
        "pvalue": best[2],
        "correlation": best[3],
        "score": best[4],
    }

