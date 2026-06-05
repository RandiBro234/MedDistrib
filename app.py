from flask import Flask, render_template, request
from model.preprocessing import get_real_provinces
from model.knowledge_based import get_priority_provinces, build_priority
from model.content_based import get_similar_provinces
from model.hybrid import hybrid_recommendation
import json

app = Flask(__name__)

# Cache agar province_data tidak dihitung ulang setiap refresh
PROVINCE_DATA_CACHE = None


def add_decision_info(df):
    """
    Menambahkan kolom status dan rekomendasi distribusi tenaga kesehatan
    berdasarkan Skor Hybrid dan Skor Prioritas.
    """
    status_list = []
    rekomendasi_list = []

    for _, row in df.iterrows():
        hybrid = row["skor_hybrid"]
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
    df["status"] = status_list
    df["rekomendasi"] = rekomendasi_list
    return df


def normalize_province_name(name):
    if not name:
        return "UNKNOWN"

    upper = str(name).strip().upper()

    if upper.startswith("DI. ") and "YOGYAKARTA" not in upper:
        upper = upper.replace("DI. ", "")

    upper = upper.replace("NUSATENGGARA", "NUSA TENGGARA")
    upper = upper.replace("DAERAH ISTIMEWA YOGYAKARTA", "DI YOGYAKARTA")
    upper = upper.replace("YOGYAKARTA", "DI YOGYAKARTA")
    upper = upper.replace("IRIAN JAYA TIMUR", "PAPUA")
    upper = upper.replace("IRIAN JAYA TENGAH", "PAPUA TENGAH")
    upper = upper.replace("IRIAN JAYA BARAT", "PAPUA BARAT")

    if upper == "PROBANTEN":
        upper = "BANTEN"
    if upper == "BANGKA BELITUNG":
        upper = "KEPULAUAN BANGKA BELITUNG"
    if upper == "JAKARTA":
        upper = "DKI JAKARTA"

    return upper


def get_province_data_cached(provinces, kb_full):
    """
    Membuat data untuk panel peta.
    Data ini disimpan di cache agar tidak dihitung ulang setiap refresh.
    """
    global PROVINCE_DATA_CACHE

    if PROVINCE_DATA_CACHE is not None:
        return PROVINCE_DATA_CACHE

    province_data = {}

    for prov in provinces:
        try:
            cb_tmp = get_similar_provinces(prov, top_n=5).to_dict(orient="records")

            hybrid_tmp = hybrid_recommendation(prov, top_n=5)
            hybrid_tmp = add_decision_info(hybrid_tmp).to_dict(orient="records")

            priority_row = kb_full[kb_full["provinsi"] == prov]

            if not priority_row.empty:
                priority_info = {
                    "skor_prioritas": float(priority_row.iloc[0]["skor_prioritas"]),
                    "rasio_dokter_puskesmas": float(
                        priority_row.iloc[0]["rasio_dokter_puskesmas"]
                    ),
                }
            else:
                priority_info = {
                    "skor_prioritas": 0.0,
                    "rasio_dokter_puskesmas": 0.0,
                }

            province_data[prov] = {
                "content_based": cb_tmp,
                "knowledge_based": priority_info,
                "hybrid": hybrid_tmp,
            }

        except Exception as e:
            print(f"Error processing province {prov}: {e}")

            province_data[prov] = {
                "content_based": [],
                "knowledge_based": {
                    "skor_prioritas": 0.0,
                    "rasio_dokter_puskesmas": 0.0,
                },
                "hybrid": [],
            }

    PROVINCE_DATA_CACHE = province_data
    return PROVINCE_DATA_CACHE


@app.route("/", methods=["GET", "POST"])
def index():
    provinces = get_real_provinces()

    raw_selected = (
        request.args.get("provinsi")
        or request.form.get("provinsi")
        or "ACEH"
    )
    selected = normalize_province_name(raw_selected)

    # Knowledge-Based Scoring
    kb_top10 = get_priority_provinces(10)
    kb_full = build_priority()

    # Content-Based Filtering
    cb_df = get_similar_provinces(selected, top_n=10)

    # Hybrid Recommendation
    hybrid_df = hybrid_recommendation(selected, top_n=10)
    hybrid_df = add_decision_info(hybrid_df)

    cb_result = cb_df.to_dict(orient="records")
    kb_result = kb_top10.to_dict(orient="records")
    hybrid_result = hybrid_df.to_dict(orient="records")

    # Ambil data peta dari cache
    province_data = get_province_data_cached(provinces, kb_full)

    return render_template(
        "index.html",
        provinces=provinces,
        selected=selected,
        cb_result=cb_result,
        kb_result=kb_result,
        hybrid_result=hybrid_result,
        province_data_json=json.dumps(province_data),
    )


@app.route("/test")
def test():
    return "Flask MedDistrib jalan"


if __name__ == "__main__":
    app.run(debug=True)