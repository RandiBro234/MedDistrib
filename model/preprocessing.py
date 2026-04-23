# model/preprocessing.py
# Tempat untuk:
# 1. load dataset
# 2. merge dataset dokter + fasilitas
# 3. cleaning
# 4. feature engineering

import pandas as pd

def load_final_data():
    return pd.read_csv("data/dataset_final.csv")

def load_scaled_data():
    return pd.read_csv("data/dataset_scaled.csv")

def get_real_provinces():
    df = load_final_data()
    return sorted(df[~df["provinsi"].str.contains("_VAR")]["provinsi"].unique())
