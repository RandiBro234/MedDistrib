from flask import Flask, render_template, request, jsonify
from model.preprocessing import get_real_provinces, load_final_data
from model.knowledge_based import get_priority_provinces, build_priority
from model.content_based import get_similar_provinces
from model.hybrid import hybrid_recommendation
import json

app = Flask(__name__)

PROVINCE_DATA_CACHE = None


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


def add_decision_info(df):
    """
    Menambahkan status dan rekomendasi berdasarkan ranking prioritas nasional,
    bukan hanya berdasarkan skor numerik.
    """
    status_list = []
    rekomendasi_list = []

    for _, row in df.iterrows():
        rank = row.get("ranking_prioritas", None)

        if rank is None:
            status = "TIDAK DIKETAHUI"
            rekom = "Data ranking tidak tersedia"

        elif rank <= 10:
            status = "PRIORITAS TINGGI"
            rekom = "Tambah tenaga kesehatan"

        elif rank <= 25:
            status = "PERLU PERHATIAN"
            rekom = "Evaluasi distribusi"

        else:
            status = "STABIL"
            rekom = "Distribusi relatif memadai"

        status_list.append(status)
        rekomendasi_list.append(rekom)

    df = df.copy()
    df["status"] = status_list
    df["rekomendasi"] = rekomendasi_list

    return df


def get_selected_profile(provinsi):
    df = load_final_data()
    df = df[
        ~df["provinsi"].str.contains("_VAR", na=False)
        & (df["provinsi"] != "INDONESIA")
    ].copy()

    row = df[df["provinsi"] == provinsi]

    if row.empty:
        return {}

    row = row.iloc[0]

    cols = [
        "total_dokter",
        "total_puskesmas",
        "total_rumah_sakit",
        "rasio_dokter_puskesmas",
        "Tenaga Kebidanan",
        "Tenaga Kefarmasian",
        "Tenaga Kesehatan Masyarakat",
        "Tenaga Kesehatan Lingkungan",
    ]

    profile = {}
    for col in cols:
        if col in row:
            try:
                profile[col] = float(row[col])
            except Exception:
                profile[col] = 0.0

    return profile


def get_explainable_recommendation(selected, hybrid_result):
    selected_profile = get_selected_profile(selected)
    explanations = []

    for row in hybrid_result[:5]:
        target = row["provinsi"]
        target_profile = get_selected_profile(target)

        reasons = []

        if selected_profile and target_profile:
            rasio_gap = abs(
                selected_profile.get("rasio_dokter_puskesmas", 0)
                - target_profile.get("rasio_dokter_puskesmas", 0)
            )

            dokter_gap = abs(
                selected_profile.get("total_dokter", 0)
                - target_profile.get("total_dokter", 0)
            )

            puskesmas_gap = abs(
                selected_profile.get("total_puskesmas", 0)
                - target_profile.get("total_puskesmas", 0)
            )

            rs_gap = abs(
                selected_profile.get("total_rumah_sakit", 0)
                - target_profile.get("total_rumah_sakit", 0)
            )

            if rasio_gap <= 0.15:
                reasons.append("Rasio dokter per puskesmas relatif mirip")

            if dokter_gap <= 50:
                reasons.append("Jumlah dokter berada pada rentang yang dekat")

            if puskesmas_gap <= 100:
                reasons.append("Jumlah puskesmas memiliki karakteristik serupa")

            if rs_gap <= 30:
                reasons.append("Jumlah rumah sakit relatif sebanding")

        if row["skor_prioritas"] > 0.8:
            reasons.append("Memiliki skor prioritas distribusi tinggi")
        elif row["skor_prioritas"] > 0.6:
            reasons.append("Masih membutuhkan evaluasi distribusi tenaga kesehatan")
        else:
            reasons.append("Memiliki kondisi distribusi relatif stabil")

        explanations.append({
            "provinsi": target,
            "similarity": float(row["similarity"]),
            "skor_prioritas": float(row["skor_prioritas"]),
            "skor_hybrid": float(row["skor_hybrid"]),
            "status": row["status"],
            "rekomendasi": row["rekomendasi"],
            "reasons": reasons
        })

    return explanations


def get_radar_comparison(selected, target):
    selected_profile = get_selected_profile(selected)
    target_profile = get_selected_profile(target)

    labels = [
        "Dokter",
        "Puskesmas",
        "Rumah Sakit",
        "Rasio D/P",
        "Kebidanan",
        "Kefarmasian",
        "Kesmas",
        "Kesling"
    ]

    keys = [
        "total_dokter",
        "total_puskesmas",
        "total_rumah_sakit",
        "rasio_dokter_puskesmas",
        "Tenaga Kebidanan",
        "Tenaga Kefarmasian",
        "Tenaga Kesehatan Masyarakat",
        "Tenaga Kesehatan Lingkungan"
    ]

    selected_values = []
    target_values = []

    for key in keys:
        a = selected_profile.get(key, 0)
        b = target_profile.get(key, 0)
        max_value = max(a, b, 1)

        selected_values.append(round(a / max_value, 3))
        target_values.append(round(b / max_value, 3))

    return {
        "labels": labels,
        "selected_name": selected,
        "target_name": target,
        "selected_values": selected_values,
        "target_values": target_values
    }


def get_province_data_cached(provinces, kb_full):
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

    alpha = request.args.get("alpha", default=0.6, type=float)
    beta = 1 - alpha

    kb_top10 = get_priority_provinces(10)
    kb_full = build_priority()

    cb_df = get_similar_provinces(selected, top_n=10)

    hybrid_df = hybrid_recommendation(
        selected,
        top_n=10,
        alpha=alpha,
        beta=beta
    )
    hybrid_df = add_decision_info(hybrid_df)

    cb_result = cb_df.to_dict(orient="records")
    kb_result = kb_top10.to_dict(orient="records")
    hybrid_result = hybrid_df.to_dict(orient="records")

    province_data = get_province_data_cached(provinces, kb_full)

    selected_profile = get_selected_profile(selected)

    explain_result = get_explainable_recommendation(
        selected,
        hybrid_result
    )

    radar_data = {}
    if hybrid_result:
        radar_data = get_radar_comparison(
            selected,
            hybrid_result[0]["provinsi"]
        )

    return render_template(
        "index.html",
        provinces=provinces,
        selected=selected,
        alpha=alpha,
        beta=beta,
        cb_result=cb_result,
        kb_result=kb_result,
        hybrid_result=hybrid_result,
        selected_profile=selected_profile,
        explain_result=explain_result,
        radar_data_json=json.dumps(radar_data),
        province_data_json=json.dumps(province_data),
    )


@app.route("/api/hybrid")
def api_hybrid():
    provinsi = normalize_province_name(request.args.get("provinsi", "ACEH"))
    alpha = request.args.get("alpha", default=0.6, type=float)
    beta = 1 - alpha

    hybrid_df = hybrid_recommendation(
        provinsi,
        top_n=10,
        alpha=alpha,
        beta=beta
    )

    hybrid_df = add_decision_info(hybrid_df)

    return jsonify(hybrid_df.to_dict(orient="records"))


@app.route("/api/explain")
def api_explain():
    provinsi = normalize_province_name(request.args.get("provinsi", "ACEH"))
    alpha = request.args.get("alpha", default=0.6, type=float)
    beta = 1 - alpha

    hybrid_df = hybrid_recommendation(
        provinsi,
        top_n=10,
        alpha=alpha,
        beta=beta
    )

    hybrid_df = add_decision_info(hybrid_df)
    hybrid_result = hybrid_df.to_dict(orient="records")

    explain_result = get_explainable_recommendation(
        provinsi,
        hybrid_result
    )

    return jsonify(explain_result)


@app.route("/api/radar")
def api_radar():
    selected = normalize_province_name(request.args.get("selected", "ACEH"))
    target = normalize_province_name(request.args.get("target", "ACEH"))

    radar_data = get_radar_comparison(selected, target)

    return jsonify(radar_data)


@app.route("/test")
def test():
    return "Flask MedDistrib jalan"


if __name__ == "__main__":
    app.run(debug=True)