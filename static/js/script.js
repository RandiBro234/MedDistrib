document.addEventListener("DOMContentLoaded", () => {
    console.log("MedDistrib dashboard ready.");

    const alphaSlider = document.getElementById("alpha-slider");
    const alphaLabel = document.getElementById("alpha-label");
    const betaLabel = document.getElementById("beta-label");
    const applyBtn = document.getElementById("apply-weight-btn");
    const form = document.querySelector(".hero-form");
    const provinceSelect = document.getElementById("provinsi-select");

    // Submit dropdown provinsi pakai GET agar URL ikut berubah
    if (form && provinceSelect) {
        form.addEventListener("submit", (e) => {
            e.preventDefault();

            const selected = provinceSelect.value;
            const url = new URL(window.location.origin + "/");

            url.searchParams.set("provinsi", selected);

            if (alphaSlider) {
                const alpha = Number(alphaSlider.value) / 100;
                url.searchParams.set("alpha", alpha.toFixed(2));
            }

            url.hash = "results";
            window.location.href = url.toString();
        });
    }

    // Slider bobot hybrid
    if (alphaSlider && alphaLabel && betaLabel) {
        alphaSlider.addEventListener("input", () => {
            const alphaValue = Number(alphaSlider.value);
            const betaValue = 100 - alphaValue;

            alphaLabel.textContent = `${alphaValue}%`;
            betaLabel.textContent = `${betaValue}%`;
        });
    }

    // Tombol terapkan bobot
    if (applyBtn && alphaSlider) {
        applyBtn.addEventListener("click", () => {
            const alpha = Number(alphaSlider.value) / 100;
            const selected = provinceSelect ? provinceSelect.value : selectedProvince;

            const url = new URL(window.location.origin + "/");
            url.searchParams.set("provinsi", selected);
            url.searchParams.set("alpha", alpha.toFixed(2));
            url.hash = "results";

            window.location.href = url.toString();
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