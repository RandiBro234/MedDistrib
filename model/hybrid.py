# model/hybrid.py
# Tempat untuk:
# 1. gabungkan similarity + skor prioritas
# 2. hasil hybrid recommendation

import pandas as pd
from model.content_based import get_similar_real_provinces
from model.knowledge_based import build_priority

def hybrid_recommendation(provinsi, top_n=5, alpha=0.6, beta=0.4):
    df_sim = get_similar_real_provinces(provinsi, top_n=20)
    df_priority = build_priority()[["provinsi", "skor_prioritas"]]

    df_hybrid = pd.merge(df_sim, df_priority, on="provinsi")

    df_hybrid["skor_hybrid"] = (
        alpha * df_hybrid["similarity"] +
        beta * df_hybrid["skor_prioritas"]
    )

    df_hybrid = df_hybrid.sort_values("skor_hybrid", ascending=False)

    return df_hybrid.head(top_n)