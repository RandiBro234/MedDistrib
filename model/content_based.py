# model/content_based.py
# Tempat untuk:
# 1. normalisasi content-based
# 2. cosine similarity
# 3. fungsi provinsi mirip

import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from model.preprocessing import load_scaled_data

CB_FEATURES = [
    "total_dokter",
    "total_puskesmas",
    "total_rumah_sakit",
    "Tenaga Kebidanan",
    "Tenaga Kefarmasian",
    "Tenaga Kesehatan Masyarakat",
    "Tenaga Kesehatan Lingkungan",
    "rasio_dokter_puskesmas"
]

def build_similarity():
    df = load_scaled_data()
    x = df[CB_FEATURES].fillna(0)

    sim_matrix = cosine_similarity(x)

    similarity_df = pd.DataFrame(
        sim_matrix,
        index=df["provinsi"],
        columns=df["provinsi"]
    )
    return similarity_df

def get_similar_real_provinces(provinsi, top_n=10):
    similarity_df = build_similarity()
    similar_scores = similarity_df[provinsi].sort_values(ascending=False)

    base_name = provinsi.split("_VAR")[0]

    mask_real_only = ~similar_scores.index.str.contains("_VAR")
    mask_not_self = similar_scores.index != base_name

    filtered_scores = similar_scores[mask_real_only & mask_not_self].head(top_n)

    result = pd.DataFrame({
        "provinsi": filtered_scores.index,
        "similarity": filtered_scores.values
    })

    return result