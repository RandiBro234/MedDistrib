# model/preprocessing.py
# Preprocessing: load dataset dan filter provinsi asli

import pandas as pd


def load_final_data():
    """Memuat dataset utama (38 provinsi asli + data augmented _VAR)."""
    return pd.read_csv("data/dataset_final.csv")


def load_scaled_data():
    """Memuat dataset yang sudah di-scale (dipertahankan untuk kompatibilitas)."""
    return pd.read_csv("data/dataset_scaled.csv")


def get_real_provinces():
    """
    Mengembalikan daftar provinsi asli Indonesia (diurutkan A-Z).
    Menyaring:
    - Baris augmented (_VAR)
    - Baris agregat INDONESIA
    """
    df = load_final_data()
    mask = (
        ~df["provinsi"].str.contains("_VAR") &
        (df["provinsi"] != "INDONESIA")
    )
    return sorted(df[mask]["provinsi"].unique())
