import os
import time
import json
import logging
from flask import Flask, render_template_string, Response
from google.cloud import firestore
import threading

app = Flask(__name__)

# 1. DATABASE SETUP
try:
    db = firestore.Client(database="cullowhee")
except Exception:
    db = firestore.Client()

latest_data = {}

# 2. BACKGROUND WATCHER (Listens for new database entries)
def watch_firestore():
    global latest_data
    col_query = db.collection("noah_sensor_data").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(1)
    
    def on_snapshot(col_snapshot, changes, read_time):
        global latest_data
        for doc in col_snapshot:
            d = doc.to_dict()
            if "timestamp" in d:
                d["timestamp"] = d["timestamp"].isoformat()
            latest_data = d

    col_query.on_snapshot(on_snapshot)

threading.Thread(target=watch_firestore, daemon=True).start()

# 3. DASHBOARD LAYOUT
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NOAH | Real-Time Dashboard</title>
    <link href="https://jsdelivr.net" rel="stylesheet">
    <link href="https://googleapis.com" rel="stylesheet">
    <style>
        body { background-color: #0b0e14; color: #e0e0e0; font-family: 'Inter', sans-serif; padding-bottom: 50px; }
        .dashboard-header { border-bottom: 1px solid #1f2937; padding: 15px 0; margin-bottom: 30px; background: #161b22; }
        .station-title { font-family: 'Orbitron', sans-serif; color: #4dabf7; font-size: 1rem; letter-spacing: 2px; }
        .gauge-card { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 20px; text-align: center; height: 100%; }
        .gauge-svg { width: 100%; height: 120px; transform: rotate(-90deg); }
        .gauge-bg { fill: none; stroke: #1c2128; stroke-width: 3; }
        .gauge-fill { fill: none; stroke-width: 3; stroke-linecap: round; transition: stroke-dasharray 1.5s ease-in-out; }
        .gauge-val { font-family: 'Orbitron', sans-serif; font-size: 1.4rem; color: #fff; margin-top: 5px; }
        .tile-card { background: #0d1117; border: 1px solid #30363d; border-radius: 8px; padding: 15px; height: 100%; }
        .tile-label { font-size: 0.65rem; text-transform: uppercase; color: #8b949e; letter-spacing: 1px; }
        .tile-val { font-family: 'Orbitron', sans-serif; font-size: 1.1rem; color: #51cf66; }
        .section-header { border-left: 4px solid #4dabf7; padding-left: 10px; margin: 30px 0 10px 0; font-weight: bold; font-size: 0.8rem; color: #8b949e; text-transform: uppercase; }
    </style>
</head>
<body>
    <div class="dashboard-header">
        <div class="container d-flex justify-content-between align-items-center">
            <div class="station-title">✦ NOAH WEATHER STATION</div>
            <div id="sync-time" class="small text-info">STATION INITIALIZING...</div>
        </div>
    </div>

    <div class="container">
        <div class="section-header">Atmospherics</div>
        <div class="row g-3">
            <!-- TEMPERATURE -->
            <div class="col-md-3">
                <div class="gauge-card">
                    <div class="tile-label">Temperature</div>
                    <svg class="gauge-svg" viewBox="0 0 36 36">
                        <path class="gauge-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" stroke-dasharray="50, 100"/>
                        <path id="temp-arc" class="gauge-fill" style="stroke: #ff6b6b;" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" stroke-dasharray="{{ (pre_data.temp_f / 110) * 50 if pre_data else 0 }}, 100"/>
                    </svg>
                    <div id="temp-val" class="gauge-val">{{ pre_data.temp_f if pre_data else '--' }}°F</div>
                </div>
            </div>
            <!-- HUMIDITY -->
            <div class="col-md-3">
                <div class="gauge-card">
                    <div class="tile-label">Humidity</div>
                    <svg class="gauge-svg" viewBox="0 0 36 36">
                        <path class="gauge-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" stroke-dasharray="50, 100"/>
                        <path id="hum-arc" class="gauge-fill" style="stroke: #339af0;" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" stroke-dasharray="{{ (pre_data.humidity / 100) * 50 if pre_data else 0 }}, 100"/>
                    </svg>
                    <div id="hum-val" class="gauge-val">{{ pre_data.humidity if pre_data else '--' }}%</div>
                </div>
            </div>
            <!-- WIND -->
            <div class="col-md-3">
                <div class="gauge-card">
                    <div class="tile-label">Wind Speed</div>
                    <svg class="gauge-svg" viewBox="0 0 36 36">
                        <path class="gauge-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" stroke-dasharray="50, 100"/>
                        <path id="wind-arc" class="gauge-fill" style="stroke: #51cf66;" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" stroke-dasharray="{{ (pre_data.wind_speed_mph / 60) * 50 if pre_data else 0 }}, 100"/>
                    </svg>
                    <div id="wind-val" class="gauge-val">{{ pre_data.wind_speed_mph if pre_data else '--' }} mph</div>
                </div>
            </div>
            <!-- RAIN -->
            <div class="col-md-3">
                <div class="gauge-card">
                    <div class="tile-label">Rain (1h)</div>
                    <svg class="gauge-svg" viewBox="0 0 36 36">
                        <path class="gauge-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" stroke-dasharray="50, 100"/>
                        <path id="rain-arc" class="gauge-fill" style="stroke: #a5d8ff;" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" stroke-dasharray="{{ (pre_data.rain_1h_in / 2) * 50 if pre_data else 0 }}, 100"/>
                    </svg>
                    <div id="rain-val" class="gauge-val">{{ pre_data.rain_1h_in if pre_data else '--' }} in</div>
                </div>
            </div>
        </div>

        <div class="section-header">Station Health & Environment</div>
        <div class="row g-2">
            <div class="col-6 col-md-3"><div class="tile-card"><div class="tile-label">Pressure</div><div id="press-val" class="tile-val">{{ pre_data.pressure_inhg if pre_data else '--' }}</div></div></div>
            <div class="col-6 col-md-3"><div class="tile-card"><div class="tile-label">Lightning</div><div id="light-val" class="tile-val">{{ pre_data.lightning_count if pre_data else '0' }}</div></div></div>
            <div class="col-6 col-md-3"><div class="tile-card"><div class="tile-label">Battery</div><div id="batt-val" class="tile-val">{{ pre_data.battery_v if pre_data else '--' }}V</div></div></div>
            <div class="col-6 col-md-3"><div class="tile-card"><div class="tile-label">Source</div><div id="dev-val" class="tile-val" style="font-size:0.7rem; color:#8b949e;">{{ pre_data.device_id if pre_data else '--' }}</div></div></div>
        </div>
    </div>

    <script>
        const source = new EventSource("/stream");
        source.onmessage = function(event) {
            const d = JSON.parse(event.data);
            const now = new Date().toLocaleTimeString();
            document.getElementById('sync-time').innerText = 'LIVE STREAM: ' + now + ' (Local)';

            // Update Gauges (Arcs)
            document.getElementById('temp-arc').setAttribute('stroke-dasharray', `${(d.temp_f / 110) * 50}, 100`);
            document.getElementById('hum-arc').setAttribute('stroke-dasharray', `${(d.humidity / 100) * 50}, 100`);
            document.getElementById('wind-arc').setAttribute('stroke-dasharray', `${(d.wind_speed_mph / 60) * 50}, 100`);
            document.getElementById('rain-arc').setAttribute('stroke-dasharray', `${((d.rain_1h_in || 0) / 2) * 50}, 100`);

            // Update Text Values
            document.getElementById('temp-val').innerText = d.temp_f + '°F';
            document.getElementById('hum-val').innerText = d.humidity + '%';
            document.getElementById('wind-val').innerText = (d.wind_speed_mph || 0) + ' mph';
            document.getElementById('rain-val').innerText = (d.rain_1h_in || 0) + ' in';
            document.getElementById('press-val').innerText = d.pressure_inhg || '--';
            document.getElementById('light-val').innerText = d.lightning_count || '0';
            document.getElementById('batt-val').innerText = d.battery_v + 'V';
            document.getElementById('dev-val').innerText = d.device_id;
        };
        source.onerror = function() { document.getElementById('sync-time').innerText = 'RECONNECTING TO STATION...'; };
    </script>
</body>
</html>
"""

# --- ROUTES ---

@app.route("/stream")
def stream():
    def event_stream():
        last_sent = None
        while True:
            if latest_data and latest_data != last_sent:
                yield f"data: {json.dumps(latest_data)}\\n\\n"
                last_sent = latest_data.copy()
            time.sleep(1)
    return Response(event_stream(), mimetype="text/event-stream")

@app.route("/")
def index():
    # PRE-LOAD: Grab the absolute latest record so the page isn't blank on load
    docs = db.collection("noah_sensor_data").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(1).stream()
    pre_data = next((doc.to_dict() for doc in docs), None)
    return render_template_string(HTML_TEMPLATE, pre_data=pre_data)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
