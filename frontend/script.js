/* =============================================
   NWI Dashboard — Interactive Logic
   Chart.js · Leaflet Choropleth · Suggestion Form
   Scroll-Driven Watch Animation · Live Clock
   ============================================= */

// ---- Country code mappings ----
const ALPHA2_TO_NUMERIC = {
    "AF": "004", "AL": "008", "DZ": "012", "AS": "016", "AD": "020", "AO": "024", "AG": "028",
    "AR": "032", "AM": "051", "AU": "036", "AT": "040", "AZ": "031", "BS": "044", "BH": "048",
    "BD": "050", "BB": "052", "BY": "112", "BE": "056", "BZ": "084", "BJ": "204", "BT": "064",
    "BO": "068", "BA": "070", "BW": "072", "BR": "076", "BN": "096", "BG": "100", "BF": "854",
    "BI": "108", "CV": "132", "KH": "116", "CM": "120", "CA": "124", "CF": "140", "TD": "148",
    "CL": "152", "CN": "156", "CO": "170", "KM": "174", "CD": "180", "CG": "178", "CR": "188",
    "CI": "384", "HR": "191", "CU": "192", "CY": "196", "CZ": "203", "DK": "208", "DJ": "262",
    "DM": "212", "DO": "214", "EC": "218", "EG": "818", "SV": "222", "GQ": "226", "ER": "232",
    "EE": "233", "SZ": "748", "ET": "231", "FJ": "242", "FI": "246", "FR": "250", "GA": "266",
    "GM": "270", "GE": "268", "DE": "276", "GH": "288", "GR": "300", "GD": "308", "GT": "320",
    "GN": "324", "GW": "624", "GY": "328", "HT": "332", "HN": "340", "HU": "348", "IS": "352",
    "IN": "356", "ID": "360", "IR": "364", "IQ": "368", "IE": "372", "IL": "376", "IT": "380",
    "JM": "388", "JP": "392", "JO": "400", "KZ": "398", "KE": "404", "KI": "296", "KP": "408",
    "KR": "410", "KW": "414", "KG": "417", "LA": "418", "LV": "428", "LB": "422", "LS": "426",
    "LR": "430", "LY": "434", "LI": "438", "LT": "440", "LU": "442", "MG": "450", "MW": "454",
    "MY": "458", "MV": "462", "ML": "466", "MT": "470", "MH": "584", "MR": "478", "MU": "480",
    "MX": "484", "FM": "583", "MD": "498", "MC": "492", "MN": "496", "ME": "499", "MA": "504",
    "MZ": "508", "MM": "104", "NA": "516", "NR": "520", "NP": "524", "NL": "528", "NZ": "554",
    "NI": "558", "NE": "562", "NG": "566", "MK": "807", "NO": "578", "OM": "512", "PK": "586",
    "PW": "585", "PA": "591", "PG": "598", "PY": "600", "PE": "604", "PH": "608", "PL": "616",
    "PT": "620", "QA": "634", "RO": "642", "RU": "643", "RW": "646", "KN": "659", "LC": "662",
    "VC": "670", "WS": "882", "SM": "674", "ST": "678", "SA": "682", "SN": "686", "RS": "688",
    "SC": "690", "SL": "694", "SG": "702", "SK": "703", "SI": "705", "SB": "090", "SO": "706",
    "ZA": "710", "SS": "728", "ES": "724", "LK": "144", "SD": "729", "SR": "740", "SE": "752",
    "CH": "756", "SY": "760", "TW": "158", "TJ": "762", "TZ": "834", "TH": "764", "TL": "626",
    "TG": "768", "TO": "776", "TT": "780", "TN": "788", "TR": "792", "TM": "795", "TV": "798",
    "UG": "800", "UA": "804", "AE": "784", "GB": "826", "US": "840", "UY": "858", "UZ": "860",
    "VU": "548", "VE": "862", "VN": "704", "YE": "887", "ZM": "894", "ZW": "716",
    "XK": "383", "PS": "275", "EH": "732", "TF": "260", "GL": "304", "NC": "540", "PR": "630",
    "FK": "238", "GF": "254", "PF": "258", "HK": "344", "MO": "446"
};

const COUNTRY_NAMES = {
    "AF": "Afghanistan", "AL": "Albania", "DZ": "Algeria", "AD": "Andorra", "AO": "Angola",
    "AG": "Antigua & Barbuda", "AR": "Argentina", "AM": "Armenia", "AU": "Australia",
    "AT": "Austria", "AZ": "Azerbaijan", "BS": "Bahamas", "BH": "Bahrain", "BD": "Bangladesh",
    "BB": "Barbados", "BY": "Belarus", "BE": "Belgium", "BZ": "Belize", "BJ": "Benin",
    "BT": "Bhutan", "BO": "Bolivia", "BA": "Bosnia & Herz.", "BW": "Botswana", "BR": "Brazil",
    "BN": "Brunei", "BG": "Bulgaria", "BF": "Burkina Faso", "BI": "Burundi", "CV": "Cabo Verde",
    "KH": "Cambodia", "CM": "Cameroon", "CA": "Canada", "CF": "Central African Rep.", "TD": "Chad",
    "CL": "Chile", "CN": "China", "CO": "Colombia", "KM": "Comoros", "CD": "DR Congo",
    "CG": "Congo", "CR": "Costa Rica", "CI": "Côte d'Ivoire", "HR": "Croatia", "CU": "Cuba",
    "CY": "Cyprus", "CZ": "Czechia", "DK": "Denmark", "DJ": "Djibouti", "DM": "Dominica",
    "DO": "Dominican Rep.", "EC": "Ecuador", "EG": "Egypt", "SV": "El Salvador",
    "GQ": "Eq. Guinea", "ER": "Eritrea", "EE": "Estonia", "SZ": "Eswatini", "ET": "Ethiopia",
    "FJ": "Fiji", "FI": "Finland", "FR": "France", "GA": "Gabon", "GM": "Gambia", "GE": "Georgia",
    "DE": "Germany", "GH": "Ghana", "GR": "Greece", "GD": "Grenada", "GT": "Guatemala",
    "GN": "Guinea", "GW": "Guinea-Bissau", "GY": "Guyana", "HT": "Haiti", "HN": "Honduras",
    "HU": "Hungary", "IS": "Iceland", "IN": "India", "ID": "Indonesia", "IR": "Iran", "IQ": "Iraq",
    "IE": "Ireland", "IL": "Israel", "IT": "Italy", "JM": "Jamaica", "JP": "Japan", "JO": "Jordan",
    "KZ": "Kazakhstan", "KE": "Kenya", "KI": "Kiribati", "KP": "North Korea", "KR": "South Korea",
    "KW": "Kuwait", "KG": "Kyrgyzstan", "LA": "Laos", "LV": "Latvia", "LB": "Lebanon",
    "LS": "Lesotho", "LR": "Liberia", "LY": "Libya", "LI": "Liechtenstein", "LT": "Lithuania",
    "LU": "Luxembourg", "MG": "Madagascar", "MW": "Malawi", "MY": "Malaysia", "MV": "Maldives",
    "ML": "Mali", "MT": "Malta", "MH": "Marshall Is.", "MR": "Mauritania", "MU": "Mauritius",
    "MX": "Mexico", "FM": "Micronesia", "MD": "Moldova", "MC": "Monaco", "MN": "Mongolia",
    "ME": "Montenegro", "MA": "Morocco", "MZ": "Mozambique", "MM": "Myanmar", "NA": "Namibia",
    "NR": "Nauru", "NP": "Nepal", "NL": "Netherlands", "NZ": "New Zealand", "NI": "Nicaragua",
    "NE": "Niger", "NG": "Nigeria", "MK": "North Macedonia", "NO": "Norway", "OM": "Oman",
    "PK": "Pakistan", "PW": "Palau", "PA": "Panama", "PG": "Papua New Guinea", "PY": "Paraguay",
    "PE": "Peru", "PH": "Philippines", "PL": "Poland", "PT": "Portugal", "QA": "Qatar",
    "RO": "Romania", "RU": "Russia", "RW": "Rwanda", "KN": "St. Kitts & Nevis", "LC": "St. Lucia",
    "VC": "St. Vincent", "WS": "Samoa", "SM": "San Marino", "ST": "São Tomé & Príncipe",
    "SA": "Saudi Arabia", "SN": "Senegal", "RS": "Serbia", "SC": "Seychelles", "SL": "Sierra Leone",
    "SG": "Singapore", "SK": "Slovakia", "SI": "Slovenia", "SB": "Solomon Is.", "SO": "Somalia",
    "ZA": "South Africa", "SS": "South Sudan", "ES": "Spain", "LK": "Sri Lanka", "SD": "Sudan",
    "SR": "Suriname", "SE": "Sweden", "CH": "Switzerland", "SY": "Syria", "TW": "Taiwan",
    "TJ": "Tajikistan", "TZ": "Tanzania", "TH": "Thailand", "TL": "Timor-Leste", "TG": "Togo",
    "TO": "Tonga", "TT": "Trinidad & Tobago", "TN": "Tunisia", "TR": "Türkiye", "TM": "Turkmenistan",
    "TV": "Tuvalu", "UG": "Uganda", "UA": "Ukraine", "AE": "UAE", "GB": "United Kingdom",
    "US": "United States", "UY": "Uruguay", "UZ": "Uzbekistan", "VU": "Vanuatu", "VE": "Venezuela",
    "VN": "Vietnam", "YE": "Yemen", "ZM": "Zambia", "ZW": "Zimbabwe", "XX": "Unknown"
};

// Build reverse lookup (numeric → alpha-2)
const NUMERIC_TO_ALPHA2 = {};
for (const [a2, num] of Object.entries(ALPHA2_TO_NUMERIC)) {
    NUMERIC_TO_ALPHA2[num] = a2;
}

// Country flag emoji from alpha-2 code
function countryFlag(code) {
    if (!code || code === "XX" || code.length !== 2) return "🌍";
    const offset = 127397;
    return String.fromCodePoint(code.charCodeAt(0) + offset, code.charCodeAt(1) + offset);
}

// ---- Data fetching ----
let summaryData = null;
let aggregatedCountries = {};  // { "NL": 35, "DE": 5, ... }
let totalUsers = 0;
let totalUniqueUsers = 0;

async function fetchSummary() {
    try {
        const [resSummary, resTotal] = await Promise.all([
            fetch("/api/summary"),
            fetch("/api/total_users").catch(() => null)
        ]);

        if (resSummary.ok) {
            summaryData = await resSummary.json();

            const sortedDates = Object.keys(summaryData).sort((a, b) => b.localeCompare(a));
            const recentDates = sortedDates.slice(0, 2);

            let bestDate = null;
            totalUsers = -1;

            for (const date of recentDates) {
                const users = summaryData[date].unique_users || 0;
                if (users > totalUsers) {
                    totalUsers = users;
                    bestDate = date;
                }
            }

            if (totalUsers === -1) totalUsers = 0;
            aggregatedCountries = bestDate && summaryData[bestDate].countries ? { ...summaryData[bestDate].countries } : {};
        }

        if (resTotal && resTotal.ok) {
            const data = await resTotal.json();
            totalUniqueUsers = data.total_users || 0;
        }

        return summaryData;
    } catch (err) {
        console.warn("Failed to fetch data:", err);
        return null;
    }
}

// ---- Hero Stats ----
function updateHeroStats() {
    document.getElementById("totalUsers").textContent = totalUsers.toLocaleString();

    const uniqueEl = document.getElementById("totalUniqueUsers");
    if (uniqueEl) uniqueEl.textContent = totalUniqueUsers.toLocaleString();

    const uniqueCountries = Object.keys(aggregatedCountries).filter(c => c !== "XX").length;
    document.getElementById("totalCountries").textContent = uniqueCountries.toString();
}

// ---- Daily Users Chart (Chart.js) ----
function renderDailyChart() {
    if (!summaryData) return;

    const dates = Object.keys(summaryData).sort();
    const counts = dates.map(d => summaryData[d].unique_users || 0);

    const ctx = document.getElementById("dailyChart").getContext("2d");

    const gradient = ctx.createLinearGradient(0, 0, 0, 360);
    gradient.addColorStop(0, "rgba(14, 165, 233, 0.35)");
    gradient.addColorStop(1, "rgba(14, 165, 233, 0.0)");

    new Chart(ctx, {
        type: "line",
        data: {
            labels: dates.map(d => {
                const dt = new Date(d + "T00:00:00");
                return dt.toLocaleDateString("en-GB", { day: "numeric", month: "short" });
            }),
            datasets: [{
                label: "Unique Users",
                data: counts,
                fill: true,
                backgroundColor: gradient,
                borderColor: "#0ea5e9",
                borderWidth: 2.5,
                pointBackgroundColor: "#0ea5e9",
                pointBorderColor: "#030712",
                pointBorderWidth: 2,
                pointRadius: counts.length > 30 ? 0 : 4,
                pointHoverRadius: 6,
                tension: 0.35
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: "index"
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: "rgba(15, 23, 42, 0.9)",
                    titleColor: "#94a3b8",
                    bodyColor: "#f1f5f9",
                    borderColor: "rgba(255,255,255,0.08)",
                    borderWidth: 1,
                    cornerRadius: 8,
                    padding: 12,
                    displayColors: false,
                    callbacks: {
                        label: ctx => `${ctx.parsed.y} users`
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: "rgba(255,255,255,0.04)" },
                    ticks: { color: "#64748b", maxRotation: 45, font: { size: 11 } },
                    border: { display: false }
                },
                y: {
                    beginAtZero: true,
                    grid: { color: "rgba(255,255,255,0.04)" },
                    ticks: {
                        color: "#64748b",
                        font: { size: 11 },
                        stepSize: 1,
                        callback: val => Number.isInteger(val) ? val : null
                    },
                    border: { display: false }
                }
            }
        }
    });
}

// ---- World Map (Leaflet + TopoJSON Choropleth) ----
async function renderWorldMap() {
    const map = L.map("worldMap", {
        center: [30, 10],
        zoom: 2,
        minZoom: 2,
        maxZoom: 6,
        worldCopyJump: true,
        zoomControl: true
    });

    L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png", {
        attribution: '&copy; <a href="https://carto.com/">CARTO</a>',
        subdomains: "abcd",
        maxZoom: 19
    }).addTo(map);

    let topoData;
    try {
        const res = await fetch("https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json");
        topoData = await res.json();
    } catch (err) {
        console.warn("Failed to load world map data:", err);
        return;
    }

    const geoJson = topojson.feature(topoData, topoData.objects.countries);

    geoJson.features.forEach(feature => {
        if (feature.id === "643" || feature.id === "242" || feature.id === "010") {
            if (feature.geometry.type === "Polygon") {
                feature.geometry.coordinates.forEach(ring => {
                    ring.forEach(coord => { if (coord[0] < 0) coord[0] += 360; });
                });
            } else if (feature.geometry.type === "MultiPolygon") {
                feature.geometry.coordinates.forEach(poly => {
                    poly.forEach(ring => {
                        ring.forEach(coord => { if (coord[0] < 0) coord[0] += 360; });
                    });
                });
            }
        }
        if (feature.id === "840") {
            if (feature.geometry.type === "Polygon") {
                feature.geometry.coordinates.forEach(ring => {
                    ring.forEach(coord => { if (coord[0] > 0) coord[0] -= 360; });
                });
            } else if (feature.geometry.type === "MultiPolygon") {
                feature.geometry.coordinates.forEach(poly => {
                    poly.forEach(ring => {
                        ring.forEach(coord => { if (coord[0] > 0) coord[0] -= 360; });
                    });
                });
            }
        }
    });

    const maxCount = Math.max(1, ...Object.values(aggregatedCountries));

    function getColor(count) {
        if (!count || count === 0) return "rgba(255,255,255,0.03)";
        const ratio = count / maxCount;
        if (ratio > 0.8) return "#991b1b";
        if (ratio > 0.6) return "#b91c1c";
        if (ratio > 0.4) return "#dc2626";
        if (ratio > 0.2) return "#ef4444";
        if (ratio > 0.05) return "#f87171";
        return "#fca5a5";
    }

    function getCountryCount(numericId) {
        const alpha2 = NUMERIC_TO_ALPHA2[numericId] || NUMERIC_TO_ALPHA2[String(parseInt(numericId))];
        if (!alpha2) return 0;
        return aggregatedCountries[alpha2] || 0;
    }

    function getCountryName(numericId) {
        const alpha2 = NUMERIC_TO_ALPHA2[numericId] || NUMERIC_TO_ALPHA2[String(parseInt(numericId))];
        if (!alpha2) return "Unknown";
        return COUNTRY_NAMES[alpha2] || alpha2;
    }

    L.geoJSON(geoJson, {
        style: function (feature) {
            const count = getCountryCount(feature.id);
            return {
                fillColor: getColor(count),
                fillOpacity: count > 0 ? 0.85 : 0.15,
                weight: 0.5,
                color: "rgba(255,255,255,0.12)",
                opacity: 1
            };
        },
        onEachFeature: function (feature, layer) {
            const count = getCountryCount(feature.id);
            const name = getCountryName(feature.id);
            const alpha2 = NUMERIC_TO_ALPHA2[feature.id] || NUMERIC_TO_ALPHA2[String(parseInt(feature.id))];
            const flag = countryFlag(alpha2);

            layer.bindTooltip(
                `${flag} <strong>${name}</strong><br><span class="tooltip-count">${count}</span> user${count !== 1 ? "s" : ""}`,
                { className: "country-tooltip", sticky: true }
            );

            layer.on("mouseover", function () {
                this.setStyle({ weight: 2, color: "#0ea5e9", fillOpacity: 0.95 });
                this.bringToFront();
            });
            layer.on("mouseout", function () {
                this.setStyle({
                    weight: 0.5,
                    color: "rgba(255,255,255,0.12)",
                    fillOpacity: count > 0 ? 0.85 : 0.15
                });
            });
        }
    }).addTo(map);
}

// ---- Country List ----
function renderCountryList() {
    const grid = document.getElementById("countryGrid");
    grid.innerHTML = "";

    const entries = Object.entries(aggregatedCountries)
        .filter(([code]) => code !== "XX")
        .sort((a, b) => b[1] - a[1]);

    if (entries.length === 0) {
        grid.innerHTML = '<div class="country-loading">No country data yet.</div>';
        return;
    }

    const maxCount = entries[0][1];

    entries.forEach(([code, count], index) => {
        const card = document.createElement("div");
        card.className = "country-card";
        card.style.animationDelay = `${index * 0.06}s`;

        const pct = Math.round((count / maxCount) * 100);
        card.innerHTML = `
            <div class="country-flag">${countryFlag(code)}</div>
            <div class="country-info">
                <div class="country-name">${COUNTRY_NAMES[code] || code}</div>
                <div class="country-count">${count} user${count !== 1 ? "s" : ""}</div>
                <div class="country-bar-bg">
                    <div class="country-bar" style="width: ${pct}%"></div>
                </div>
            </div>
        `;
        grid.appendChild(card);
    });
}

// ---- Garmin Embed Fallback ----
function setupGarminEmbed() {
    const iframe = document.getElementById("garminIframe");
    const fallback = document.getElementById("appFallback");
    if (!iframe || !fallback) return;

    let loaded = false;
    iframe.addEventListener("load", () => { loaded = true; });

    setTimeout(() => {
        if (!loaded) {
            iframe.style.display = "none";
            fallback.classList.add("visible");
        }
    }, 3000);

    iframe.addEventListener("error", () => {
        iframe.style.display = "none";
        fallback.classList.add("visible");
    });
}

// ---- Suggestion Form ----
function setupSuggestionForm() {
    const form = document.getElementById("suggestionForm");
    const thankYou = document.getElementById("thankYou");
    const submitBtn = document.getElementById("submitBtn");

    if (!form) return;

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        submitBtn.disabled = true;

        const name = document.getElementById("sugName").value.trim();
        const suggestion = document.getElementById("sugText").value.trim();

        if (!suggestion) {
            submitBtn.disabled = false;
            return;
        }

        try {
            const res = await fetch("/api/suggestions", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name, suggestion })
            });

            if (!res.ok) throw new Error(`HTTP ${res.status}`);

            thankYou.classList.add("active");

            setTimeout(() => {
                thankYou.classList.remove("active");
                form.reset();
                submitBtn.disabled = false;
            }, 3500);

        } catch (err) {
            console.error("Suggestion submission failed:", err);
            alert("Failed to submit suggestion. Please try again.");
            submitBtn.disabled = false;
        }
    });
}

// ---- Scroll Reveal ----
function setupScrollReveal() {
    const sections = document.querySelectorAll(".section");
    sections.forEach(s => s.classList.add("reveal"));

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add("visible");
            }
        });
    }, { threshold: 0.1, rootMargin: "0px 0px -50px 0px" });

    sections.forEach(s => observer.observe(s));
}

// ---- Expiry Disclaimer ----
function setupDisclaimer() {
    const disclaimer = document.getElementById("versionDisclaimer");
    if (!disclaimer) return;

    const expiryDate = new Date("2026-03-03T23:59:59Z");
    if (new Date() < expiryDate) {
        disclaimer.textContent = "(The number of unique users is lower than current users because people with v1.4 installed cannot be counted right now)";
        disclaimer.style.display = "block";
    }
}

// ====================================================================
//  SCROLL-DRIVEN WATCH SHOWCASE — Apple-style animation
// ====================================================================

// The time when the page loaded — this is the "target" (real) time.
// The animation starts at (loadTime - 60s) and interpolates to loadTime.
let pageLoadTime = Date.now();

// Format helpers
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const DAYS = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"];

function formatTime(date) {
    const h = String(date.getHours()).padStart(2, "0");
    const m = String(date.getMinutes()).padStart(2, "0");
    return `${h}:${m}`;
}

function formatDate(date) {
    return `${date.getDate()} ${MONTHS[date.getMonth()]}`;
}

function formatDay(date) {
    return DAYS[date.getDay()];
}

/**
 * Interpolate between two timestamps.
 * progress: 0 → startMs, 1 → endMs
 */
function interpolateTime(startMs, endMs, progress) {
    const clamped = Math.max(0, Math.min(1, progress));
    return startMs + (endMs - startMs) * clamped;
}

function setupWatchShowcase() {
    const showcase = document.getElementById("watchShowcase");
    const container = document.getElementById("watchContainer");
    const overlay = document.getElementById("clockOverlay");
    const caption = document.getElementById("watchCaption");
    const clockTime = document.getElementById("clockTime");
    const clockDate = document.getElementById("clockDate");
    const clockDay = document.getElementById("clockDay");

    if (!showcase || !container) return;

    // Ease function for a smoother feel (ease-out cubic)
    function easeOutCubic(t) {
        return 1 - Math.pow(1 - t, 3);
    }

    let ticking = false;

    function onScroll() {
        if (ticking) return;
        ticking = true;
        requestAnimationFrame(() => {
            updateWatch();
            ticking = false;
        });
    }

    function updateWatch() {
        const rect = showcase.getBoundingClientRect();
        const showcaseHeight = showcase.offsetHeight;
        const viewportHeight = window.innerHeight;

        // How far we have scrolled into the showcase section
        // rect.top starts positive (below viewport) → goes negative (scrolled past)
        // progress: 0 = showcase just entering viewport, 1 = fully scrolled through
        const scrolled = -rect.top;
        const totalScrollable = showcaseHeight - viewportHeight;
        const rawProgress = scrolled / totalScrollable;
        const progress = Math.max(0, Math.min(1, rawProgress));

        // ---- Watch scale & opacity ----
        // Phase 1 (0 → 0.4): fade in and scale up
        // Phase 2 (0.4 → 0.7): fully visible, time animates
        // Phase 3 (0.7 → 1.0): still visible, caption fades in
        const scaleProgress = easeOutCubic(Math.min(1, progress / 0.4));
        const scale = 0.4 + scaleProgress * 0.6; // 0.4 → 1.0
        const opacity = Math.min(1, progress / 0.25); // fade in during first 25%

        container.style.transform = `scale(${scale})`;
        container.style.opacity = opacity;

        // ---- Clock overlay ----
        const clockFadeStart = 0.2;
        const clockFadeEnd = 0.35;
        const clockOpacity = Math.max(0, Math.min(1, (progress - clockFadeStart) / (clockFadeEnd - clockFadeStart)));
        if (clockOpacity > 0) {
            overlay.classList.add("visible");
            overlay.style.opacity = clockOpacity;
        } else {
            overlay.classList.remove("visible");
            overlay.style.opacity = 0;
        }

        // ---- Time interpolation ----
        // Time range: from (now - 60s) to (now)
        // The "now" updates in real time so the clock is always live once fully scrolled
        const now = Date.now();
        const startTime = now - 60000; // 1 minute ago
        const endTime = now;

        // Map the progress (with a focus on the 0.2 → 0.8 range for the time animation)
        const timeProgress = Math.max(0, Math.min(1, (progress - 0.2) / 0.6));
        const easedTimeProgress = easeOutCubic(timeProgress);
        const displayMs = interpolateTime(startTime, endTime, easedTimeProgress);
        const displayDate = new Date(displayMs);

        clockTime.textContent = formatTime(displayDate);
        clockDate.textContent = formatDate(displayDate);
        clockDay.textContent = formatDay(displayDate);

        // ---- Caption ----
        if (progress > 0.7) {
            caption.classList.add("visible");
        } else {
            caption.classList.remove("visible");
        }

        // ---- Watch glow effect based on progress ----
        const glowIntensity = Math.min(1, progress / 0.5);
        const face = document.getElementById("watchFace");
        if (face) {
            face.style.boxShadow = `
                0 0 ${80 * glowIntensity}px rgba(14, 165, 233, ${0.15 * glowIntensity}),
                0 ${20 * glowIntensity}px ${60 * glowIntensity}px rgba(0, 0, 0, ${0.5 * glowIntensity}),
                0 0 0 1px rgba(255, 255, 255, ${0.06 * glowIntensity})
            `;
        }
    }

    window.addEventListener("scroll", onScroll, { passive: true });
    // Initial call
    updateWatch();
}

// ---- Cover Image Observer ----
function setupCoverSection() {
    const cover = document.getElementById("coverSection");
    if (!cover) return;

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                cover.classList.add("in-view");
            }
        });
    }, { threshold: 0.2 });

    observer.observe(cover);
}

// ---- Live Clock Ticker (updates every second for smooth clock) ----
function setupLiveClock() {
    // The scroll handler already updates the clock in real time based on Date.now(),
    // but we need to trigger re-renders even when the user isn't scrolling.
    // This fires a synthetic scroll-update every second.
    setInterval(() => {
        const showcase = document.getElementById("watchShowcase");
        if (!showcase) return;

        const rect = showcase.getBoundingClientRect();
        // Only update if the watch showcase is currently in view
        if (rect.top < window.innerHeight && rect.bottom > 0) {
            // Trigger the scroll handler
            window.dispatchEvent(new Event("scroll"));
        }
    }, 1000);
}

// ---- Initialization ----
document.addEventListener("DOMContentLoaded", async () => {
    setupScrollReveal();
    setupGarminEmbed();
    setupSuggestionForm();
    setupDisclaimer();
    setupWatchShowcase();
    setupCoverSection();
    setupLiveClock();

    await fetchSummary();
    updateHeroStats();
    renderDailyChart();
    renderCountryList();
    await renderWorldMap();
});
