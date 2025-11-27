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

