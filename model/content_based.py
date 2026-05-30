# model/content_based.py
# Content-Based Filtering menggunakan Cosine Similarity
# Alur: Knowledge-Based Scoring → Content-Based Filtering → Mencari Provinsi Mirip
#
# CBF dijalankan SETELAH Knowledge-Based selesai menentukan prioritas.
# Fitur yang digunakan: total_dokter, total_puskesmas, total_rumah_sakit, rasio_dokter_puskesmas
# Metode: Cosine Similarity

import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity
from model.preprocessing import load_final_data

# Fitur untuk menghitung kemiripan antar provinsi
CB_FEATURES = [
    "total_dokter",
    "total_puskesmas",
    "total_rumah_sakit",
    "rasio_dokter_puskesmas"
]


def build_similarity():
    """
    Membangun matriks Cosine Similarity antar provinsi.
    Hanya menggunakan data provinsi asli (bukan _VAR dan bukan INDONESIA).
    Fitur di-scale terlebih dahulu dengan MinMaxScaler sebelum dihitung similarity-nya.
    """
    df = load_final_data()

    # Filter hanya provinsi asli
    df = df[
        ~df["provinsi"].str.contains("_VAR") &
        (df["provinsi"] != "INDONESIA")
    ].copy()

    for col in CB_FEATURES:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df[col] = df[col].fillna(df[col].mean())

    scaler = MinMaxScaler()
    x = scaler.fit_transform(df[CB_FEATURES])

    sim_matrix = cosine_similarity(x)

    similarity_df = pd.DataFrame(
        sim_matrix,
        index=df["provinsi"].values,
        columns=df["provinsi"].values
    )
    return similarity_df


def get_similar_provinces(provinsi, top_n=10):
    """
    Mencari provinsi yang memiliki karakteristik kesehatan serupa dengan provinsi input.
    Mengembalikan DataFrame berisi provinsi dan nilai similarity (diurutkan descending).

    Parameter:
        provinsi : str  — nama provinsi yang dipilih pengguna
        top_n    : int  — jumlah provinsi mirip yang dikembalikan
    """
    similarity_df = build_similarity()

    if provinsi not in similarity_df.index:
        return pd.DataFrame(columns=["provinsi", "similarity"])

    similar_scores = similarity_df[provinsi].sort_values(ascending=False)

    # Hapus provinsi itu sendiri dari hasil
    filtered_scores = similar_scores[similar_scores.index != provinsi].head(top_n)

    result = pd.DataFrame({
        "provinsi": filtered_scores.index,
        "similarity": filtered_scores.values
    })

    return result


# Alias untuk backward-compatibility dengan app.py lama
def get_similar_real_provinces(provinsi, top_n=10):
    return get_similar_provinces(provinsi, top_n=top_n)