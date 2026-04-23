const map = L.map('map').setView([-2.5, 118], 5);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

function normalizeProvinceName(name) {
    if (!name) return "";

    const mapping = {
        "DAERAH ISTIMEWA YOGYAKARTA": "DI YOGYAKARTA",
        "YOGYAKARTA": "DI YOGYAKARTA",
        "JAKARTA": "DKI JAKARTA"
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

function styleFeature() {
    return {
        fillColor: "#1f6f68",
        weight: 1.2,
        opacity: 1,
        color: "#ffffff",
        fillOpacity: 0.75
    };
}

function highlightFeature(e) {
    const layer = e.target;
    layer.setStyle({
        weight: 2,
        color: "#f2a51a",
        fillOpacity: 0.9
    });
    layer.bringToFront();
}

let geojsonLayer;

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

    layer.on({
        mouseover: highlightFeature,
        mouseout: resetHighlight,
        click: function() {
            updateInfoPanel(provinsi);
        }
    });

    layer.bindTooltip(provinsi, {
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

        geojsonLayer = L.geoJSON(data, {
            style: styleFeature,
            onEachFeature: onEachFeature
        }).addTo(map);

        map.fitBounds(geojsonLayer.getBounds());

        const firstProvince = Object.keys(provinceData)[0];
        if (firstProvince) {
            updateInfoPanel(firstProvince);
        }
    })
    .catch(error => {
        console.error("Gagal load GeoJSON:", error);
        document.getElementById("map-provinsi-title").textContent =
            "Gagal memuat peta: " + error.message;
    });