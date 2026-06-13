# model/hybrid.py
# Hybrid Recommendation

import pandas as pd
from model.content_based import get_similar_provinces
from model.knowledge_based import build_priority


def hybrid_recommendation(provinsi, top_n=5, alpha=0.6, beta=0.4):
    """
    Menghasilkan Hybrid Recommendation dengan menggabungkan:
    - Cosine Similarity dari Content-Based Filtering
    - Skor Prioritas dari Knowledge-Based Scoring

    Return:
        DataFrame dengan kolom:
        provinsi, similarity, skor_prioritas, ranking_prioritas, skor_hybrid
    """

    df_sim = get_similar_provinces(provinsi, top_n=50)

    df_priority = build_priority()[[
        "provinsi",
        "skor_prioritas",
        "ranking_prioritas"
    ]]

    df_hybrid = pd.merge(
        df_sim,
        df_priority,
        on="provinsi",
        how="inner"
    )

    df_hybrid["skor_hybrid"] = (
        alpha * df_hybrid["similarity"] +
        beta * df_hybrid["skor_prioritas"]
    )

    df_hybrid = df_hybrid.sort_values(
        "skor_hybrid",
        ascending=False
    ).reset_index(drop=True)

    return df_hybrid.head(top_n)