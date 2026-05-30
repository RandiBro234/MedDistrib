# model/knowledge_based.py
# Knowledge-Based Scoring
# Alur: Dataset → Preprocessing → Knowledge-Based Scoring → Menentukan Prioritas Distribusi
#
# Formula Skor Prioritas:
#   skor_prioritas = 0.75 * (1 - rasio_scaled)
#                  + 0.10 * puskesmas_scaled
#                  + 0.10 * (1 - dokter_scaled)
#                  + 0.05 * (1 - rs_scaled)
#
# Penalti: jika total_dokter > 50, skor_prioritas *= 0.85
# Tujuan: provinsi dengan rasio dokter/puskesmas RENDAH = prioritas distribusi TINGGI

import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from model.preprocessing import load_final_data


def build_priority():
    """
    Menghitung Skor Prioritas Distribusi Tenaga Kesehatan untuk setiap provinsi.
    Mengembalikan DataFrame yang sudah diurutkan dari prioritas tertinggi ke terendah.
    """
    df = load_final_data()

    # Hanya gunakan data provinsi asli (bukan augmented _VAR dan bukan INDONESIA)
    df = df[
        ~df["provinsi"].str.contains("_VAR") &
        (df["provinsi"] != "INDONESIA")
    ].copy()

    kb_features = [
        "total_dokter",
        "total_puskesmas",
        "total_rumah_sakit",
        "rasio_dokter_puskesmas"
    ]

    for col in kb_features:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df[col] = df[col].fillna(df[col].mean())

    scaler = MinMaxScaler()

    df["dokter_scaled"]   = scaler.fit_transform(df[["total_dokter"]])
    df["puskesmas_scaled"] = scaler.fit_transform(df[["total_puskesmas"]])
    df["rs_scaled"]       = scaler.fit_transform(df[["total_rumah_sakit"]])
    df["rasio_scaled"]    = scaler.fit_transform(df[["rasio_dokter_puskesmas"]])

    # Formula Skor Prioritas (bobot sesuai metodologi skripsi)
    df["skor_prioritas"] = (
        0.75 * (1 - df["rasio_scaled"]) +
        0.10 * df["puskesmas_scaled"] +
        0.10 * (1 - df["dokter_scaled"]) +
        0.05 * (1 - df["rs_scaled"])
    )

    # Penalti: provinsi dengan total dokter > 50 sudah cukup terlayani
    mask_penalti = df["total_dokter"] > 50
    df.loc[mask_penalti, "skor_prioritas"] *= 0.85

    df = df.sort_values("skor_prioritas", ascending=False).reset_index(drop=True)
    return df


def get_priority_provinces(top_n=10):
    """
    Mengembalikan top-N provinsi dengan Skor Prioritas Distribusi Tenaga Kesehatan tertinggi.
    """
    df = build_priority()
    return df[[
        "provinsi",
        "total_dokter",
        "total_puskesmas",
        "total_rumah_sakit",
        "rasio_dokter_puskesmas",
        "skor_prioritas"
    ]].head(top_n)