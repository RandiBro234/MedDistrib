# model/knowledge_based.py
# Tempat untuk:
# 1. perhitungan skor prioritas
# 2. ranking provinsi

import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from model.preprocessing import load_final_data

def build_priority():
    df = load_final_data()
    df = df[~df["provinsi"].str.contains("_VAR")].copy()

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

    df["dokter_scaled"] = scaler.fit_transform(df[["total_dokter"]])
    df["puskesmas_scaled"] = scaler.fit_transform(df[["total_puskesmas"]])
    df["rs_scaled"] = scaler.fit_transform(df[["total_rumah_sakit"]])
    df["rasio_scaled"] = scaler.fit_transform(df[["rasio_dokter_puskesmas"]])

    df["skor_prioritas"] = (
        0.40 * (1 - df["rasio_scaled"]) +
        0.25 * df["puskesmas_scaled"] +
        0.20 * (1 - df["dokter_scaled"]) +
        0.15 * (1 - df["rs_scaled"])
    )

    df = df.sort_values("skor_prioritas", ascending=False)
    return df

def get_priority_provinces(top_n=10):
    df = build_priority()
    return df[[
        "provinsi",
        "total_dokter",
        "total_puskesmas",
        "total_rumah_sakit",
        "rasio_dokter_puskesmas",
        "skor_prioritas"
    ]].head(top_n)