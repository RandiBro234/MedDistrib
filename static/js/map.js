const map = L.map('map').setView([-2.5, 118], 5);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

function normalizeProvinceName(name) {
    if (!name) return "UNKNOWN";

    let upper = name.trim().toUpperCase();

    const mapping = {
        "DI. ACEH": "ACEH",
        "DAERAH ISTIMEWA ACEH": "ACEH",
        "NANGGROE ACEH DARUSSALAM": "ACEH",

        "PROBANTEN": "BANTEN",

        "BANGKA BELITUNG": "KEPULAUAN BANGKA BELITUNG",
        "KEP. BANGKA BELITUNG": "KEPULAUAN BANGKA BELITUNG",

        "DAERAH ISTIMEWA YOGYAKARTA": "DI YOGYAKARTA",
        "YOGYAKARTA": "DI YOGYAKARTA",

        "JAKARTA": "DKI JAKARTA",

        "NUSATENGGARA BARAT": "NUSA TENGGARA BARAT",
        "NUSATENGGARA TIMUR": "NUSA TENGGARA TIMUR",

        "IRIAN JAYA TIMUR": "PAPUA",
        "IRIAN JAYA TENGAH": "PAPUA TENGAH",
        "IRIAN JAYA BARAT": "PAPUA BARAT"
    };

    return mapping[upper] || upper;
}

function getProvinceName(feature) {
    return normalizeProvinceName(
        feature.properties.Propinsi ||
        feature.properties.name ||
        feature.properties.PROVINSI ||
        feature.properties.NAME_1 ||
        "UNKNOWN"
    );
}

// Calculate min and max scores for choropleth interpolation
let minScore = 1;
let maxScore = 0;
for (const prov in provinceData) {
    if (provinceData[prov] && provinceData[prov].knowledge_based) {
        const s = provinceData[prov].knowledge_based.skor_prioritas;
        if (s < minScore) minScore = s;
        if (s > maxScore) maxScore = s;
    }
}

function getColor(score, minS, maxS) {
    if (maxS === minS) return "#f7b267";
    let t = (score - minS) / (maxS - minS);
    t = Math.max(0, Math.min(1, t)); // clamp 0 to 1

    let r, g, b;
    if (t < 0.5) {
        // interpolate from low (#1e8a6e) to mid (#f7b267)
        let t2 = t / 0.5;
        r = Math.round(30 + t2 * (247 - 30));
        g = Math.round(138 + t2 * (178 - 138));
        b = Math.round(110 + t2 * (103 - 110));
    } else {
        // interpolate from mid (#f7b267) to high (#f26430)
        let t2 = (t - 0.5) / 0.5;
        r = Math.round(247 + t2 * (242 - 247));
        g = Math.round(178 + t2 * (100 - 178));
        b = Math.round(103 + t2 * (48 - 103));
    }
    return `rgb(${r}, ${g}, ${b})`;
}

function updateInfoPanel(provinsi) {
    const normalized = normalizeProvinceName(provinsi);
    const data = provinceData[normalized];

    document.getElementById("map-provinsi-title").textContent = normalized;

    if (!data) {
        document.getElementById("map-priority").textContent = "-";
        document.getElementById("map-rasio").textContent = "-";
        document.getElementById("map-cb-list").innerHTML = "<li>Data tidak ditemukan</li>";
        document.getElementById("map-hybrid-list").innerHTML = "<li>Data tidak ditemukan</li>";
        return;
    }

    document.getElementById("map-priority").textContent =
        Number(data.knowledge_based.skor_prioritas).toFixed(3);

    document.getElementById("map-rasio").textContent =
        Number(data.knowledge_based.rasio_dokter_puskesmas).toFixed(3);

    const cbList = document.getElementById("map-cb-list");
    cbList.innerHTML = "";
    data.content_based.slice(0, 5).forEach(item => {
        const li = document.createElement("li");
        li.textContent = `${item.provinsi} (${Number(item.similarity).toFixed(3)})`;
        cbList.appendChild(li);
    });

    const hybridList = document.getElementById("map-hybrid-list");
    hybridList.innerHTML = "";
    data.hybrid.slice(0, 5).forEach(item => {
        const li = document.createElement("li");
        li.textContent = `${item.provinsi} (${Number(item.skor_hybrid).toFixed(3)})`;
        hybridList.appendChild(li);
    });

    const select = document.getElementById("provinsi-select");
    if (select) {
        select.value = normalized;
    }
}

function styleFeature(feature) {
    const provinsi = getProvinceName(feature);
    const isSelected = provinsi === currentSelectedProvince;
    const data = provinceData[provinsi];
    
    let score = minScore;
    if (data && data.knowledge_based && data.knowledge_based.skor_prioritas) {
        score = data.knowledge_based.skor_prioritas;
    }

    const fillColor = getColor(score, minScore, maxScore);

    return {
        fillColor: fillColor,
        weight: isSelected ? 3 : 1,
        opacity: 1,
        color: isSelected ? "#ffffff" : "#ffffff", // Light border to pop against choropleth
        fillOpacity: isSelected ? 1.0 : 0.8
    };
}

function highlightFeature(e) {
    const layer = e.target;
    layer.setStyle({
        weight: 3,
        color: "#ffffff",
        fillOpacity: 1.0
    });

    if (!L.Browser.ie && !L.Browser.opera && !L.Browser.edge) {
        layer.bringToFront();
    }
}

let geojsonLayer;
let currentSelectedProvince = "";

function resetHighlight(e) {
    if (geojsonLayer) {
        geojsonLayer.resetStyle(e.target);
    }
}

function onEachFeature(feature, layer) {
    const normalized = getProvinceName(feature);

    layer.on({
        mouseover: highlightFeature,
        mouseout: resetHighlight,
        click: function () {
            currentSelectedProvince = normalized;

            // update panel kanan langsung
            updateInfoPanel(normalized);

            // update style semua layer agar provinsi terpilih berubah warna
            if (geojsonLayer) {
                geojsonLayer.setStyle(styleFeature);
            }

            // sinkronkan dropdown
            const select = document.getElementById("provinsi-select");
            if (select) {
                select.value = normalized;
            }

            // redirect ke Flask supaya hasil bawah ikut berubah
            const url = new URL(window.location.href);
            url.searchParams.set("provinsi", normalized);
            url.hash = "results";
            window.location.href = url.toString();
        }
    });

    // Buat Tooltip HTML
    const data = provinceData[normalized];
    let scoreText = "-";
    let rasioText = "-";
    if (data && data.knowledge_based) {
        scoreText = Number(data.knowledge_based.skor_prioritas).toFixed(3);
        rasioText = Number(data.knowledge_based.rasio_dokter_puskesmas).toFixed(3);
    }

    const tooltipContent = `
        <div style="text-align:center; min-width: 140px;">
            <strong style="display:block; margin-bottom:4px; font-size:15px; color:#183434;">${normalized}</strong>
            <div style="font-size:13px; color:#1f6f68; display:flex; justify-content:space-between; margin-bottom:2px;">
                <span>Skor Prioritas:</span>
                <strong>${scoreText}</strong>
            </div>
            <div style="font-size:13px; color:#1f6f68; display:flex; justify-content:space-between;">
                <span>Rasio D/P:</span>
                <strong>${rasioText}</strong>
            </div>
        </div>
    `;

    layer.bindTooltip(tooltipContent, {
        sticky: true
    });
}

fetch("/static/data/indonesia-prov-real.geojson")
    .then(response => {
        if (!response.ok) {
            throw new Error("HTTP status " + response.status);
        }
        return response.json();
    })
    .then(data => {
        console.log("GeoJSON loaded:", data);

        const select = document.getElementById("provinsi-select");
        if (select && select.value) {
            currentSelectedProvince = normalizeProvinceName(select.value);
        } else {
            const firstProvince = Object.keys(provinceData)[0];
            currentSelectedProvince = firstProvince ? normalizeProvinceName(firstProvince) : "";
        }

        geojsonLayer = L.geoJSON(data, {
            style: styleFeature,
            onEachFeature: onEachFeature
        }).addTo(map);

        map.fitBounds(geojsonLayer.getBounds());

        if (currentSelectedProvince) {
            updateInfoPanel(currentSelectedProvince);
        }
    })
    .catch(error => {
        console.error("Gagal load GeoJSON:", error);
        document.getElementById("map-provinsi-title").textContent =
            "Gagal memuat peta: " + error.message;
    });