from flask import Flask, render_template, request
from model.preprocessing import get_real_provinces
from model.knowledge_based import get_priority_provinces, build_priority
from model.content_based import get_similar_provinces
from model.hybrid import hybrid_recommendation
import json

app = Flask(__name__)


def add_decision_info(df):
    """
    Menambahkan kolom status dan rekomendasi distribusi tenaga kesehatan
    berdasarkan Skor Hybrid dan Skor Prioritas.
    """
    status_list = []
    rekomendasi_list = []

    for _, row in df.iterrows():
        hybrid  = row["skor_hybrid"]
        priority = row["skor_prioritas"]

        if hybrid > 0.9:
            status = "PRIORITAS TINGGI"
        elif hybrid > 0.8:
            status = "PERLU PERHATIAN"
        else:
            status = "STABIL"

        if priority > 0.8:
            rekom = "Tambah tenaga kesehatan"
        elif priority > 0.6:
            rekom = "Evaluasi distribusi"
        else:
            rekom = "Cukup stabil"

        status_list.append(status)
        rekomendasi_list.append(rekom)

    df = df.copy()
    df["status"]      = status_list
    df["rekomendasi"] = rekomendasi_list
    return df


@app.route("/", methods=["GET", "POST"])
def index():
    # ------------------------------------------------------------------ #
    # Alur: KB Scoring → CBF → Hybrid Recommendation                      #
    # ------------------------------------------------------------------ #

    provinces = get_real_provinces()

    # Baca provinsi dari query param (klik peta) atau form, default ACEH
    selected = request.args.get("provinsi") or request.form.get("provinsi") or "ACEH"

    # 1. Knowledge-Based Scoring — menentukan Prioritas Distribusi Tenaga Kesehatan
    kb_top10 = get_priority_provinces(10)
    kb_full  = build_priority()

    # 2. Content-Based Filtering — mencari Provinsi Mirip
    cb_df = get_similar_provinces(selected, top_n=10)

    # 3. Hybrid Recommendation — menggabungkan similarity + skor prioritas
    hybrid_df = hybrid_recommendation(selected, top_n=10)
    hybrid_df = add_decision_info(hybrid_df)

    cb_result     = cb_df.to_dict(orient="records")
    kb_result     = kb_top10.to_dict(orient="records")
    hybrid_result = hybrid_df.to_dict(orient="records")

    # ------------------------------------------------------------------ #
    # Bangun province_data untuk panel peta (semua provinsi, top-5 each)  #
    # ------------------------------------------------------------------ #
    province_data = {}
    for prov in provinces:
        try:
            # Content-Based: Provinsi Mirip
            cb_tmp = get_similar_provinces(prov, top_n=5).to_dict(orient="records")

            # Hybrid Recommendation
            hybrid_tmp = hybrid_recommendation(prov, top_n=5)
            hybrid_tmp = add_decision_info(hybrid_tmp).to_dict(orient="records")

            # Knowledge-Based: Skor Prioritas & Rasio Dokter/Puskesmas
            priority_row = kb_full[kb_full["provinsi"] == prov]
            if not priority_row.empty:
                priority_info = {
                    "skor_prioritas":        float(priority_row.iloc[0]["skor_prioritas"]),
                    "rasio_dokter_puskesmas": float(priority_row.iloc[0]["rasio_dokter_puskesmas"])
                }
            else:
                priority_info = {
                    "skor_prioritas":        0.0,
                    "rasio_dokter_puskesmas": 0.0
                }

            province_data[prov] = {
                "content_based":   cb_tmp,
                "knowledge_based": priority_info,
                "hybrid":          hybrid_tmp
            }
        except Exception:
            province_data[prov] = {
                "content_based":   [],
                "knowledge_based": {"skor_prioritas": 0.0, "rasio_dokter_puskesmas": 0.0},
                "hybrid":          []
            }

    return render_template(
        "index.html",
        provinces=provinces,
        selected=selected,
        cb_result=cb_result,
        kb_result=kb_result,
        hybrid_result=hybrid_result,
        province_data_json=json.dumps(province_data)
    )


if __name__ == "__main__":
    app.run(debug=True)