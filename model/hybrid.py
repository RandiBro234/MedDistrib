# model/hybrid.py
# Hybrid Recommendation
# Alur: Knowledge-Based Scoring → Content-Based Filtering → Hybrid Recommendation
#
# Formula:
#   skor_hybrid = 0.6 * similarity + 0.4 * skor_prioritas
#
# Tujuan:
#   Menghasilkan rekomendasi yang mempertimbangkan:
#   1. Kemiripan karakteristik wilayah (Content-Based Filtering)
#   2. Tingkat kebutuhan distribusi tenaga kesehatan (Knowledge-Based Scoring)

import pandas as pd
from model.content_based import get_similar_provinces
from model.knowledge_based import build_priority


def hybrid_recommendation(provinsi, top_n=5, alpha=0.6, beta=0.4):
    """
    Menghasilkan Hybrid Recommendation dengan menggabungkan:
    - Cosine Similarity dari Content-Based Filtering  (bobot alpha = 0.6)
    - Skor Prioritas dari Knowledge-Based Scoring     (bobot beta  = 0.4)

    Parameter:
        provinsi : str   — nama provinsi yang dipilih pengguna
        top_n    : int   — jumlah rekomendasi yang dikembalikan
        alpha    : float — bobot similarity (default 0.6)
        beta     : float — bobot skor_prioritas (default 0.4)

    Return:
        DataFrame dengan kolom: provinsi, similarity, skor_prioritas, skor_hybrid
    """
    # Step 1: Ambil provinsi mirip dari Content-Based Filtering
    df_sim = get_similar_provinces(provinsi, top_n=50)

    # Step 2: Ambil Skor Prioritas dari Knowledge-Based Scoring
    df_priority = build_priority()[["provinsi", "skor_prioritas"]]

    # Step 3: Gabungkan keduanya
    df_hybrid = pd.merge(df_sim, df_priority, on="provinsi", how="inner")

    # Step 4: Hitung Skor Hybrid
    df_hybrid["skor_hybrid"] = (
        alpha * df_hybrid["similarity"] +
        beta  * df_hybrid["skor_prioritas"]
    )

    df_hybrid = df_hybrid.sort_values("skor_hybrid", ascending=False).reset_index(drop=True)

    return df_hybrid.head(top_n)