import os
import time
import json
import threading
from flask import Flask, render_template_string, Response
from google.cloud import firestore

app = Flask(__name__)

# ── DATABASE SETUP ────────────────────────────────────────────────────────────
try:
    db = firestore.Client(database="cullowhee")
except Exception:
    db = firestore.Client()

latest_data = {}

# ── BACKGROUND WATCHER ────────────────────────────────────────────────────────
def watch_firestore():
    global latest_data
    col_query = (
        db.collection("noah_sensor_data")
        .order_by("timestamp", direction=firestore.Query.DESCENDING)
        .limit(1)
    )

    def on_snapshot(col_snapshot, changes, read_time):
        global latest_data
        for doc in col_snapshot:
            d = doc.to_dict()
            if "timestamp" in d:
                d["timestamp"] = d["timestamp"].isoformat()
            latest_data = d

    col_query.on_snapshot(on_snapshot)

threading.Thread(target=watch_firestore, daemon=True).start()

# ── HTML TEMPLATE ─────────────────────────────────────────────────────────────
HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>NOAH | Weather Station Dashboard</title>
  <link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&family=Share+Tech+Mono&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    html, body {
      background: #060C14;
      color: #E0E8F0;
      font-family: 'Rajdhani', sans-serif;
      min-height: 100vh;
    }

    body::before {
      content: "";
      position: fixed; inset: 0; z-index: 0; pointer-events: none;
      background:
        radial-gradient(ellipse at 20% 20%, rgba(0,80,160,0.15) 0%, transparent 60%),
        radial-gradient(ellipse at 80% 80%, rgba(0,40,80,0.20) 0%, transparent 60%);
    }

    .page { position: relative; z-index: 1; padding: 0 0 60px; }

    /* ── HEADER ── */
    .site-header {
      border-left: 6px solid #0088FF;
      padding: 14px 28px;
      margin: 0 0 28px;
      background: rgba(0,136,255,0.06);
      border-radius: 0 8px 8px 0;
      display: flex; align-items: center; justify-content: space-between;
      flex-wrap: wrap; gap: 10px;
    }
    .site-title {
      font-size: 2.2em; font-weight: 700; color: #fff;
      letter-spacing: 3px; line-height: 1;
    }
    .site-sub {
      font-family: 'Share Tech Mono', monospace;
      font-size: 0.85em; color: #7AACCC; text-transform: uppercase;
    }
    #sync-time {
      font-family: 'Share Tech Mono', monospace;
      font-size: 0.78em; color: #00FFCC;
      background: rgba(0,255,204,0.07);
      border: 1px solid rgba(0,255,204,0.2);
      border-radius: 20px; padding: 4px 14px;
    }

    /* ── PANELS ── */
    .panel {
      background: rgba(10,20,35,0.85);
      border: 1px solid rgba(0,136,255,0.2);
      border-radius: 10px; padding: 20px 24px; margin: 0 20px 20px;
    }
    .panel-title {
      font-family: 'Share Tech Mono', monospace;
      font-size: 0.78em; color: #0088FF;
      text-transform: uppercase; letter-spacing: 3px;
      margin-bottom: 18px;
      border-bottom: 1px solid rgba(0,136,255,0.2);
      padding-bottom: 8px;
    }

    /* ── GAUGE GRID ── */
    .gauge-row { display: grid; gap: 16px; }
    .gauge-row-4 { grid-template-columns: repeat(4, 1fr); }
    .gauge-row-3 { grid-template-columns: repeat(3, 1fr); }
    @media (max-width: 900px) {
      .gauge-row-4 { grid-template-columns: repeat(2, 1fr); }
      .gauge-row-3 { grid-template-columns: repeat(2, 1fr); }
    }
    @media (max-width: 520px) {
      .gauge-row-4, .gauge-row-3 { grid-template-columns: 1fr; }
    }

    /* ── GAUGE CARD ── */
    .gauge-card {
      background: rgba(6,12,20,0.9);
      border: 1px solid rgba(0,136,255,0.18);
      border-radius: 10px; padding: 16px 10px 12px;
      text-align: center;
      transition: border-color 0.4s;
    }
    .gauge-card:hover { border-color: rgba(0,136,255,0.5); }

    .gauge-title {
      font-family: 'Share Tech Mono', monospace;
      font-size: 0.65em; color: #7AACCC;
      text-transform: uppercase; letter-spacing: 2px;
      margin-bottom: 6px;
    }

    /* SVG arc gauge */
    .gauge-svg-wrap { position: relative; width: 160px; height: 90px; margin: 0 auto; }
    .gauge-svg-wrap svg { width: 100%; height: 100%; overflow: visible; }

    .gauge-value {
      font-family: 'Rajdhani', sans-serif;
      font-size: 1.55em; font-weight: 700; color: #fff;
      margin: 4px 0 2px;
    }
    .gauge-label {
      font-family: 'Rajdhani', sans-serif;
      font-size: 1.05em; font-weight: 700;
      margin-bottom: 2px;
    }
    .gauge-detail {
      font-family: 'Rajdhani', sans-serif;
      font-size: 0.82em; color: #7AACCC;
    }
    .gauge-source {
      font-family: 'Share Tech Mono', monospace;
      font-size: 0.58em; color: #2A6080;
      margin-top: 4px; text-transform: uppercase; letter-spacing: 1px;
    }

    /* ── STAT TILES ── */
    .tile-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
    @media (max-width: 700px) { .tile-row { grid-template-columns: repeat(2, 1fr); } }

    .tile-card {
      background: rgba(0,136,255,0.04);
      border: 1px solid rgba(0,136,255,0.14);
      border-radius: 10px; padding: 14px 16px;
    }
    .tile-label {
      font-family: 'Share Tech Mono', monospace;
      font-size: 0.68em; color: #7AACCC;
      text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px;
    }
    .tile-val {
      font-family: 'Rajdhani', sans-serif;
      font-size: 1.35em; font-weight: 700; color: #fff;
    }
    .tile-sub {
      font-family: 'Rajdhani', sans-serif;
      font-size: 0.82em; color: #7AACCC; margin-top: 2px;
    }
  </style>
</head>
<body>
<div class="page">

  <!-- HEADER -->
  <div class="site-header">
    <div>
      <div class="site-title">✦ NOAH</div>
      <div class="site-sub">Real-Time Weather Station · Cullowhee, NC</div>
    </div>
    <div id="sync-time">STATION INITIALIZING…</div>
  </div>

  <!-- ATMOSPHERICS PANEL -->
  <div class="panel">
    <div class="panel-title">⚡ Atmospherics</div>
    <div class="gauge-row gauge-row-4">

      <!-- TEMPERATURE -->
      <div class="gauge-card">
        <div class="gauge-title">Air Temperature</div>
        <div class="gauge-svg-wrap">
          <svg viewBox="0 0 160 90">
            <!-- threshold bands (0–110°F scale mapped to 180° arc) -->
            <path d="M 10 80 A 70 70 0 0 1 42 17" fill="none" stroke="rgba(90,200,250,0.18)" stroke-width="10" stroke-linecap="butt"/>
            <path d="M 42 17 A 70 70 0 0 1 80 10" fill="none" stroke="rgba(0,255,255,0.18)" stroke-width="10" stroke-linecap="butt"/>
            <path d="M 80 10 A 70 70 0 0 1 118 17" fill="none" stroke="rgba(0,255,156,0.18)" stroke-width="10" stroke-linecap="butt"/>
            <path d="M 118 17 A 70 70 0 0 1 143 47" fill="none" stroke="rgba(255,215,0,0.18)" stroke-width="10" stroke-linecap="butt"/>
            <path d="M 143 47 A 70 70 0 0 1 150 80" fill="none" stroke="rgba(255,140,0,0.18)" stroke-width="10" stroke-linecap="butt"/>
            <!-- track -->
            <path id="temp-track" d="M 10 80 A 70 70 0 0 1 150 80" fill="none" stroke="rgba(0,136,255,0.12)" stroke-width="5"/>
            <!-- fill arc -->
            <path id="temp-arc" d="M 10 80 A 70 70 0 0 1 150 80" fill="none" stroke="#ff6b6b" stroke-width="5" stroke-linecap="round"
                  stroke-dasharray="0 220"/>
            <!-- needle -->
            <circle id="temp-dot" cx="10" cy="80" r="5" fill="#ff6b6b" opacity="0"/>
          </svg>
        </div>
        <div id="temp-val" class="gauge-value">--°F</div>
        <div id="temp-label" class="gauge-label" style="color:#ff6b6b;">--</div>
        <div class="gauge-detail">Station sensor</div>
        <div class="gauge-source">SRC: NOAH FIRESTORE</div>
      </div>

      <!-- HUMIDITY -->
      <div class="gauge-card">
        <div class="gauge-title">Relative Humidity</div>
        <div class="gauge-svg-wrap">
          <svg viewBox="0 0 160 90">
            <path d="M 10 80 A 70 70 0 0 1 55 14" fill="none" stroke="rgba(90,200,250,0.18)" stroke-width="10"/>
            <path d="M 55 14 A 70 70 0 0 1 105 14" fill="none" stroke="rgba(0,255,156,0.18)" stroke-width="10"/>
            <path d="M 105 14 A 70 70 0 0 1 135 38" fill="none" stroke="rgba(255,215,0,0.18)" stroke-width="10"/>
            <path d="M 135 38 A 70 70 0 0 1 150 80" fill="none" stroke="rgba(255,140,0,0.18)" stroke-width="10"/>
            <path d="M 10 80 A 70 70 0 0 1 150 80" fill="none" stroke="rgba(0,136,255,0.12)" stroke-width="5"/>
            <path id="hum-arc" d="M 10 80 A 70 70 0 0 1 150 80" fill="none" stroke="#339af0" stroke-width="5" stroke-linecap="round"
                  stroke-dasharray="0 220"/>
          </svg>
        </div>
        <div id="hum-val" class="gauge-value">--%</div>
        <div id="hum-label" class="gauge-label" style="color:#339af0;">--</div>
        <div id="hum-detail" class="gauge-detail">Dewpoint: --</div>
        <div class="gauge-source">SRC: NOAH FIRESTORE</div>
      </div>

      <!-- WIND -->
      <div class="gauge-card">
        <div class="gauge-title">Wind Speed</div>
        <div class="gauge-svg-wrap">
          <svg viewBox="0 0 160 90">
            <path d="M 10 80 A 70 70 0 0 1 80 10" fill="none" stroke="rgba(0,255,156,0.18)" stroke-width="10"/>
            <path d="M 80 10 A 70 70 0 0 1 127 25" fill="none" stroke="rgba(255,215,0,0.18)" stroke-width="10"/>
            <path d="M 127 25 A 70 70 0 0 1 148 65" fill="none" stroke="rgba(255,140,0,0.18)" stroke-width="10"/>
            <path d="M 148 65 A 70 70 0 0 1 150 80" fill="none" stroke="rgba(255,51,51,0.18)" stroke-width="10"/>
            <path d="M 10 80 A 70 70 0 0 1 150 80" fill="none" stroke="rgba(0,136,255,0.12)" stroke-width="5"/>
            <path id="wind-arc" d="M 10 80 A 70 70 0 0 1 150 80" fill="none" stroke="#51cf66" stroke-width="5" stroke-linecap="round"
                  stroke-dasharray="0 220"/>
          </svg>
        </div>
        <div id="wind-val" class="gauge-value">-- mph</div>
        <div id="wind-label" class="gauge-label" style="color:#51cf66;">--</div>
        <div id="wind-detail" class="gauge-detail">Gust: --</div>
        <div class="gauge-source">SRC: NOAH FIRESTORE</div>
      </div>

      <!-- RAIN 1h -->
      <div class="gauge-card">
        <div class="gauge-title">Rain (1-hour)</div>
        <div class="gauge-svg-wrap">
          <svg viewBox="0 0 160 90">
            <path d="M 10 80 A 70 70 0 0 1 80 10" fill="none" stroke="rgba(0,255,156,0.18)" stroke-width="10"/>
            <path d="M 80 10 A 70 70 0 0 1 130 30" fill="none" stroke="rgba(255,215,0,0.18)" stroke-width="10"/>
            <path d="M 130 30 A 70 70 0 0 1 148 65" fill="none" stroke="rgba(255,140,0,0.18)" stroke-width="10"/>
            <path d="M 148 65 A 70 70 0 0 1 150 80" fill="none" stroke="rgba(255,51,51,0.18)" stroke-width="10"/>
            <path d="M 10 80 A 70 70 0 0 1 150 80" fill="none" stroke="rgba(0,136,255,0.12)" stroke-width="5"/>
            <path id="rain-arc" d="M 10 80 A 70 70 0 0 1 150 80" fill="none" stroke="#a5d8ff" stroke-width="5" stroke-linecap="round"
                  stroke-dasharray="0 220"/>
          </svg>
        </div>
        <div id="rain-val" class="gauge-value">-- in</div>
        <div id="rain-label" class="gauge-label" style="color:#a5d8ff;">--</div>
        <div class="gauge-detail">1-hour accumulation</div>
        <div class="gauge-source">SRC: NOAH FIRESTORE</div>
      </div>

    </div><!-- /gauge-row-4 -->
  </div><!-- /atmospherics panel -->

  <!-- PRESSURE & LIGHTNING PANEL -->
  <div class="panel">
    <div class="panel-title">📡 Station Health & Environment</div>
    <div class="gauge-row gauge-row-3">

      <!-- PRESSURE -->
      <div class="gauge-card">
        <div class="gauge-title">Barometric Pressure</div>
        <div class="gauge-svg-wrap">
          <svg viewBox="0 0 160 90">
            <path d="M 10 80 A 70 70 0 0 1 35 20" fill="none" stroke="rgba(255,51,51,0.18)" stroke-width="10"/>
            <path d="M 35 20 A 70 70 0 0 1 80 10" fill="none" stroke="rgba(255,140,0,0.18)" stroke-width="10"/>
            <path d="M 80 10 A 70 70 0 0 1 125 20" fill="none" stroke="rgba(0,255,156,0.18)" stroke-width="10"/>
            <path d="M 125 20 A 70 70 0 0 1 150 80" fill="none" stroke="rgba(90,200,250,0.18)" stroke-width="10"/>
            <path d="M 10 80 A 70 70 0 0 1 150 80" fill="none" stroke="rgba(0,136,255,0.12)" stroke-width="5"/>
            <path id="press-arc" d="M 10 80 A 70 70 0 0 1 150 80" fill="none" stroke="#00FFFF" stroke-width="5" stroke-linecap="round"
                  stroke-dasharray="0 220"/>
          </svg>
        </div>
        <div id="press-val" class="gauge-value">-- inHg</div>
        <div id="press-label" class="gauge-label" style="color:#00FFFF;">BAROMETRIC</div>
        <div class="gauge-detail">28–32 inHg normal range</div>
        <div class="gauge-source">SRC: NOAH FIRESTORE</div>
      </div>

      <!-- LIGHTNING -->
      <div class="gauge-card">
        <div class="gauge-title">Lightning Count</div>
        <div class="gauge-svg-wrap">
          <svg viewBox="0 0 160 90">
            <path d="M 10 80 A 70 70 0 0 1 80 10" fill="none" stroke="rgba(0,255,156,0.18)" stroke-width="10"/>
            <path d="M 80 10 A 70 70 0 0 1 125 20" fill="none" stroke="rgba(255,215,0,0.18)" stroke-width="10"/>
            <path d="M 125 20 A 70 70 0 0 1 148 60" fill="none" stroke="rgba(255,140,0,0.18)" stroke-width="10"/>
            <path d="M 148 60 A 70 70 0 0 1 150 80" fill="none" stroke="rgba(255,51,51,0.18)" stroke-width="10"/>
            <path d="M 10 80 A 70 70 0 0 1 150 80" fill="none" stroke="rgba(0,136,255,0.12)" stroke-width="5"/>
            <path id="light-arc" d="M 10 80 A 70 70 0 0 1 150 80" fill="none" stroke="#FFD700" stroke-width="5" stroke-linecap="round"
                  stroke-dasharray="0 220"/>
          </svg>
        </div>
        <div id="light-val" class="gauge-value">0</div>
        <div id="light-label" class="gauge-label" style="color:#FFD700;">CLEAR</div>
        <div class="gauge-detail">Strikes detected</div>
        <div class="gauge-source">SRC: NOAH FIRESTORE</div>
      </div>

      <!-- BATTERY -->
      <div class="gauge-card">
        <div class="gauge-title">Battery Voltage</div>
        <div class="gauge-svg-wrap">
          <svg viewBox="0 0 160 90">
            <path d="M 10 80 A 70 70 0 0 1 40 18" fill="none" stroke="rgba(255,51,51,0.18)" stroke-width="10"/>
            <path d="M 40 18 A 70 70 0 0 1 80 10" fill="none" stroke="rgba(255,215,0,0.18)" stroke-width="10"/>
            <path d="M 80 10 A 70 70 0 0 1 150 80" fill="none" stroke="rgba(0,255,156,0.18)" stroke-width="10"/>
            <path d="M 10 80 A 70 70 0 0 1 150 80" fill="none" stroke="rgba(0,136,255,0.12)" stroke-width="5"/>
            <path id="batt-arc" d="M 10 80 A 70 70 0 0 1 150 80" fill="none" stroke="#51cf66" stroke-width="5" stroke-linecap="round"
                  stroke-dasharray="0 220"/>
          </svg>
        </div>
        <div id="batt-val" class="gauge-value">-- V</div>
        <div id="batt-label" class="gauge-label" style="color:#51cf66;">--</div>
        <div id="batt-detail" class="gauge-detail">--</div>
        <div class="gauge-source">SRC: NOAH FIRESTORE</div>
      </div>

    </div><!-- /gauge-row-3 -->
  </div><!-- /station health panel -->

  <!-- SNAPSHOT TILES -->
  <div class="panel">
    <div class="panel-title">📋 Sensor Snapshot</div>
    <div class="tile-row">
      <div class="tile-card">
        <div class="tile-label">Device ID</div>
        <div id="dev-val" class="tile-val" style="font-size:1em; word-break:break-all;">--</div>
      </div>
      <div class="tile-card">
        <div class="tile-label">Wind Direction</div>
        <div id="wdir-val" class="tile-val">--°</div>
        <div id="wdir-label" class="tile-sub">--</div>
      </div>
      <div class="tile-card">
        <div class="tile-label">Pressure</div>
        <div id="press-tile" class="tile-val">-- inHg</div>
      </div>
      <div class="tile-card">
        <div class="tile-label">Last Updated</div>
        <div id="ts-val" class="tile-val" style="font-size:0.9em;">--</div>
      </div>
    </div>
  </div>

</div><!-- /page -->

<script>
// ── ARC MATH ──────────────────────────────────────────────────────────────────
// Semi-circle arc: starts at left (180°), sweeps clockwise 180° to right.
// Arc path: M 10 80  A 70 70 0 0 1  150 80  → total arc length ≈ 220
const ARC_LEN = 220;

function arcDash(value, min, max) {
  const pct = Math.max(0, Math.min(1, (value - min) / (max - min)));
  const fill = pct * ARC_LEN;
  return `${fill.toFixed(1)} ${ARC_LEN}`;
}

// ── COLOR HELPERS ─────────────────────────────────────────────────────────────
function tempColor(f) {
  if (f < 32)  return "#5AC8FA";
  if (f < 50)  return "#00FFFF";
  if (f < 80)  return "#51cf66";
  if (f < 95)  return "#FFD700";
  if (f < 105) return "#FF8C00";
  return "#FF3333";
}
function tempLabel(f) {
  if (f < 32)  return "FREEZING";
  if (f < 50)  return "COLD";
  if (f < 70)  return "COOL";
  if (f < 80)  return "COMFORTABLE";
  if (f < 90)  return "WARM";
  if (f < 100) return "HOT";
  return "EXTREME";
}
function humLabel(h) {
  if (h < 30)  return "DRY";
  if (h < 60)  return "COMFORTABLE";
  if (h < 80)  return "HUMID";
  return "VERY HUMID";
}
function windColor(w) {
  if (w < 15)  return "#51cf66";
  if (w < 25)  return "#FFD700";
  if (w < 35)  return "#FF8C00";
  return "#FF3333";
}
function windLabel(w) {
  if (w < 15)  return "CALM";
  if (w < 25)  return "BREEZY";
  if (w < 35)  return "STRONG";
  return "DANGEROUS";
}
function rainLabel(r) {
  if (r < 0.1)  return "NONE";
  if (r < 0.25) return "LIGHT";
  if (r < 1.0)  return "MODERATE";
  if (r < 2.0)  return "HEAVY";
  return "SIGNIFICANT";
}
function pressLabel(p) {
  if (p < 29.0)  return "VERY LOW";
  if (p < 29.8)  return "LOW";
  if (p < 30.3)  return "NORMAL";
  return "HIGH";
}
function lightLabel(n) {
  if (n === 0) return "CLEAR";
  if (n < 5)   return "DISTANT";
  if (n < 15)  return "NEARBY";
  return "CLOSE!";
}
function battColor(v) {
  if (v >= 3.7) return "#51cf66";
  if (v >= 3.5) return "#FFD700";
  return "#FF3333";
}
function battLabel(v) {
  if (v >= 3.7) return "GOOD";
  if (v >= 3.5) return "LOW";
  return "CRITICAL";
}
function windDirLabel(deg) {
  const dirs = ["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"];
  return dirs[Math.round(deg / 22.5) % 16];
}

// ── SET ARC COLOR ─────────────────────────────────────────────────────────────
function setArc(id, dasharray, color) {
  const el = document.getElementById(id);
  if (!el) return;
  el.setAttribute("stroke-dasharray", dasharray);
  el.setAttribute("stroke", color);
}

// ── UPDATE DISPLAY ────────────────────────────────────────────────────────────
function updateDash(d) {
  const now = new Date().toLocaleTimeString();
  document.getElementById("sync-time").textContent = "LIVE  ·  " + now;

  // TEMPERATURE
  const tempF = parseFloat(d.temp_f) || 0;
  const tc = tempColor(tempF);
  setArc("temp-arc", arcDash(tempF, 0, 110), tc);
  document.getElementById("temp-val").textContent   = (d.temp_f ?? "--") + "°F";
  document.getElementById("temp-label").textContent = d.temp_f != null ? tempLabel(tempF) : "--";
  document.getElementById("temp-label").style.color = tc;

  // HUMIDITY
  const hum = parseFloat(d.humidity) || 0;
  setArc("hum-arc", arcDash(hum, 0, 100), "#339af0");
  document.getElementById("hum-val").textContent    = (d.humidity ?? "--") + "%";
  document.getElementById("hum-label").textContent  = d.humidity != null ? humLabel(hum) : "--";
  // dewpoint approx
  const dp = (d.temp_f != null && d.humidity != null)
    ? (parseFloat(d.temp_f) - ((100 - hum) / 5)).toFixed(1)
    : null;
  document.getElementById("hum-detail").textContent = dp != null ? "Dewpoint: " + dp + "°F" : "Dewpoint: --";

  // WIND
  const wspd = parseFloat(d.wind_speed_mph) || 0;
  const wc = windColor(wspd);
  setArc("wind-arc", arcDash(wspd, 0, 60), wc);
  document.getElementById("wind-val").textContent   = (d.wind_speed_mph ?? "--") + " mph";
  document.getElementById("wind-label").textContent = d.wind_speed_mph != null ? windLabel(wspd) : "--";
  document.getElementById("wind-label").style.color = wc;
  document.getElementById("wind-detail").textContent =
    d.wind_gust_mph != null ? "Gust: " + d.wind_gust_mph + " mph" : "Gust: --";

  // RAIN
  const rain = parseFloat(d.rain_1h_in) || 0;
  const rainC = rain < 0.1 ? "#51cf66" : rain < 1 ? "#FFD700" : rain < 2 ? "#FF8C00" : "#FF3333";
  setArc("rain-arc", arcDash(rain, 0, 2), rainC);
  document.getElementById("rain-val").textContent   = (d.rain_1h_in ?? "--") + " in";
  document.getElementById("rain-label").textContent = d.rain_1h_in != null ? rainLabel(rain) : "--";
  document.getElementById("rain-label").style.color = rainC;

  // PRESSURE
  const press = parseFloat(d.pressure_inhg) || 0;
  const pressC = press < 29.0 ? "#FF3333" : press < 29.8 ? "#FF8C00" : press < 30.3 ? "#51cf66" : "#5AC8FA";
  setArc("press-arc", arcDash(press, 28, 32), pressC);
  document.getElementById("press-val").textContent   = (d.pressure_inhg ?? "--") + " inHg";
  document.getElementById("press-label").style.color = pressC;
  document.getElementById("press-tile").textContent  = (d.pressure_inhg ?? "--") + " inHg";

  // LIGHTNING
  const lcount = parseInt(d.lightning_count) || 0;
  const lc = lcount === 0 ? "#51cf66" : lcount < 5 ? "#FFD700" : lcount < 15 ? "#FF8C00" : "#FF3333";
  setArc("light-arc", arcDash(lcount, 0, 25), lc);
  document.getElementById("light-val").textContent   = lcount;
  document.getElementById("light-label").textContent = lightLabel(lcount);
  document.getElementById("light-label").style.color = lc;

  // BATTERY
  const bv = parseFloat(d.battery_v) || 0;
  const bc = battColor(bv);
  setArc("batt-arc", arcDash(bv, 3.0, 4.2), bc);
  document.getElementById("batt-val").textContent    = (d.battery_v ?? "--") + " V";
  document.getElementById("batt-label").textContent  = d.battery_v != null ? battLabel(bv) : "--";
  document.getElementById("batt-label").style.color  = bc;
  document.getElementById("batt-detail").textContent =
    bv >= 3.7 ? "Fully charged" : bv >= 3.5 ? "Recharge soon" : "Low — check station";

  // SNAPSHOT TILES
  document.getElementById("dev-val").textContent  = d.device_id ?? "--";
  const wdir = d.wind_dir ?? d.wind_direction;
  document.getElementById("wdir-val").textContent   = wdir != null ? wdir + "°" : "--°";
  document.getElementById("wdir-label").textContent = wdir != null ? windDirLabel(parseFloat(wdir)) : "--";
  document.getElementById("ts-val").textContent     = d.timestamp
    ? new Date(d.timestamp).toLocaleTimeString() : "--";
}

// ── INITIAL PAINT FROM SERVER DATA ────────────────────────────────────────────
{% if pre_data %}
(function() {
  const d = {{ pre_data | tojson }};
  if (d) updateDash(d);
})();
{% endif %}

// ── LIVE STREAM ───────────────────────────────────────────────────────────────
const source = new EventSource("/stream");
source.onmessage = function(event) {
  const d = JSON.parse(event.data);
  updateDash(d);
};
source.onerror = function() {
  document.getElementById("sync-time").textContent = "RECONNECTING TO STATION…";
};
</script>
</body>
</html>
"""

# ── ROUTES ────────────────────────────────────────────────────────────────────

@app.route("/stream")
def stream():
    def event_stream():
        last_sent = None
        while True:
            if latest_data and latest_data != last_sent:
                yield f"data: {json.dumps(latest_data)}\n\n"
                last_sent = latest_data.copy()
            time.sleep(1)
    return Response(event_stream(), mimetype="text/event-stream")

@app.route("/")
def index():
    try:
        docs = (
            db.collection("noah_sensor_data")
            .order_by("timestamp", direction=firestore.Query.DESCENDING)
            .limit(1)
            .stream()
        )
        pre_data = next((doc.to_dict() for doc in docs), None)
        if pre_data and "timestamp" in pre_data:
            pre_data["timestamp"] = pre_data["timestamp"].isoformat()
    except Exception:
        pre_data = None
    return render_template_string(HTML_TEMPLATE, pre_data=pre_data)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
