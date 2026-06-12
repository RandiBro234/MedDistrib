document.addEventListener("DOMContentLoaded", () => {
    console.log("MedDistrib dashboard ready.");

    const alphaSlider = document.getElementById("alpha-slider");
    const alphaLabel = document.getElementById("alpha-label");
    const betaLabel = document.getElementById("beta-label");
    const applyBtn = document.getElementById("apply-weight-btn");
    const form = document.querySelector(".hero-form");
    const provinceSelect = document.getElementById("provinsi-select");

    function getAlphaValue() {
        if (!alphaSlider) return 0.6;
        return Number(alphaSlider.value) / 100;
    }

    function buildUrl(selected, alpha, hash = "") {
        const url = new URL(window.location.origin + "/");
        url.searchParams.set("provinsi", selected);
        url.searchParams.set("alpha", alpha.toFixed(2));

        if (hash) {
            url.hash = hash;
        }

        return url.toString();
    }

    // Tombol Analisis: reload dan langsung menuju section Analisis
    if (form && provinceSelect) {
        form.addEventListener("submit", (e) => {
            e.preventDefault();

            const selected = provinceSelect.value;
            const alpha = getAlphaValue();

            window.location.href = buildUrl(selected, alpha, "analysis");
        });
    }

    // Slider bobot: hanya update label persentase
    if (alphaSlider && alphaLabel && betaLabel) {
        alphaSlider.addEventListener("input", () => {
            const alphaValue = Number(alphaSlider.value);
            const betaValue = 100 - alphaValue;

            alphaLabel.textContent = `${alphaValue}%`;
            betaLabel.textContent = `${betaValue}%`;
        });
    }

    // Tombol Terapkan Bobot: tanpa reload, tanpa scroll
    if (applyBtn && alphaSlider) {
        applyBtn.addEventListener("click", async () => {
            const selected = provinceSelect ? provinceSelect.value : selectedProvince;
            const alpha = getAlphaValue();

            try {
                const response = await fetch(
                    `/api/hybrid?provinsi=${encodeURIComponent(selected)}&alpha=${alpha.toFixed(2)}`
                );

                const data = await response.json();

                const hybridList = document.getElementById("hybrid-list");

                if (!hybridList) return;

                hybridList.innerHTML = "";

                data.slice(0, 5).forEach((item, index) => {
                    hybridList.innerHTML += `
                        <div class="hybrid-item ${index === 0 ? "highlight" : ""}">
                            <div class="hybrid-left">
                                <h4>${item.provinsi}</h4>
                                <p>${item.rekomendasi} — ${item.status}</p>
                            </div>

                            <div class="hybrid-right">
                                <span class="hybrid-score">
                                    ${Number(item.skor_hybrid).toFixed(3)}
                                </span>
                            </div>
                        </div>
                    `;
                });

            } catch (error) {
                console.error("Gagal memperbarui hybrid recommendation:", error);
            }
        });
    }

    renderRadarChart();
});


function renderRadarChart() {
    const canvas = document.getElementById("radarChart");

    if (!canvas || typeof radarData === "undefined" || !radarData || !radarData.labels) {
        return;
    }

    new Chart(canvas, {
        type: "radar",
        data: {
            labels: radarData.labels,
            datasets: [
                {
                    label: radarData.selected_name,
                    data: radarData.selected_values,
                    borderWidth: 2,
                    pointRadius: 3,
                    fill: true
                },
                {
                    label: radarData.target_name,
                    data: radarData.target_values,
                    borderWidth: 2,
                    pointRadius: 3,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
                    min: 0,
                    max: 1,
                    ticks: {
                        stepSize: 0.2
                    }
                }
            },
            plugins: {
                legend: {
                    position: "bottom"
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.raw}`;
                        }
                    }
                }
            }
        }
    });
}