const map = L.map('map').setView([-2.5, 118], 5);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

function normalizeProvinceName(name) {
    if (!name) return "";

    const mapping = {
        "DAERAH ISTIMEWA YOGYAKARTA": "DI YOGYAKARTA",
        "YOGYAKARTA": "DI YOGYAKARTA",
        "JAKARTA": "DKI JAKARTA",
        "DKI JAKARTA": "DKI JAKARTA",
        "NUSA TENGGARA BARAT": "NUSA TENGGARA BARAT",
        "NUSA TENGGARA TIMUR": "NUSA TENGGARA TIMUR",
        "PAPUA BARAT DAYA": "PAPUA BARAT DAYA",
        "PAPUA BARAT": "PAPUA BARAT",
        "PAPUA TENGAH": "PAPUA TENGAH",
        "PAPUA SELATAN": "PAPUA SELATAN",
        "PAPUA PEGUNUNGAN": "PAPUA PEGUNUNGAN",
        "PAPUA": "PAPUA"
    };

    const upper = name.toUpperCase().trim();
    return mapping[upper] || upper;
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
    const provinsi =
        normalizeProvinceName(
            feature.properties.name ||
            feature.properties.NAME_1 ||
            feature.properties.Provinsi ||
            "Unknown"
        );

    const isSelected = provinsi === currentSelectedProvince;

    return {
        fillColor: isSelected ? "#f2a51a" : "#1f6f68",
        weight: isSelected ? 2.5 : 1.2,
        opacity: 1,
        color: "#ffffff",
        fillOpacity: isSelected ? 0.9 : 0.75
    };
}

function highlightFeature(e) {
    const layer = e.target;
    layer.setStyle({
        weight: 2,
        color: "#f2a51a",
        fillOpacity: 0.9
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
    const provinsi =
        feature.properties.name ||
        feature.properties.NAME_1 ||
        feature.properties.Provinsi ||
        "Unknown";

    const normalized = normalizeProvinceName(provinsi);

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

    layer.bindTooltip(normalized, {
        sticky: true
    });
}

fetch("/static/data/indonesia-prov.geojson")
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