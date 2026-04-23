from flask import Flask, render_template, request

from model.preprocessing import get_real_provinces
from model.content_based import get_similar_real_provinces
from model.knowledge_based import get_priority_provinces
from model.hybrid import hybrid_recommendation

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    provinces = get_real_provinces()
    selected_province = request.form.get("provinsi", provinces[0] if provinces else "")

    similar = []
    priority = []
    hybrid = []

    if selected_province:
        similar = get_similar_real_provinces(selected_province, top_n=10).to_dict("records")
        priority = get_priority_provinces(10).to_dict("records")
        hybrid = hybrid_recommendation(selected_province, top_n=10).to_dict("records")

    metrics = {
        "total_provinsi": len(provinces),
        "top_similarity": similar[0]["similarity"] if similar else 0,
        "top_priority": priority[0]["skor_prioritas"] if priority else 0,
        "top_hybrid": hybrid[0]["skor_hybrid"] if hybrid else 0,
    }

    # ini dipakai untuk bantu scroll ke hasil setelah submit
    result_anchor = "results" if request.method == "POST" else ""

    return render_template(
        "index.html",
        provinces=provinces,
        selected_province=selected_province,
        similar=similar,
        priority=priority,
        hybrid=hybrid,
        metrics=metrics,
        result_anchor=result_anchor
    )

if __name__ == "__main__":
    app.run(debug=True)