import os
import time
import json
import logging
from datetime import datetime
from flask import Flask, render_template_string, Response
from google.cloud import firestore
import threading

# Initialize Flask
app = Flask(__name__)

# Configure Firestore - explicitly pointing to your 'cullowhee' database
try:
    db = firestore.Client(database="cullowhee")
except Exception as e:
    logging.error(f"Firestore Init Error: {e}")
    db = firestore.Client()

# Global variable to store the latest data for the stream
latest_data = {}

# --- BACKGROUND LISTENER ---
# This runs on the server to catch new data the moment it hits Firestore
def watch_firestore():
    global latest_data
    logging.info("Starting Firestore Watcher...")
    
    # Listen to the most recent document in your collection
    col_query = db.collection("noah_sensor_data").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(1)
    
    def on_snapshot(col_snapshot, changes, read_time):
        global latest_data
        for doc in col_snapshot:
            d = doc.to_dict()
            # Convert timestamp to string so JSON can handle it
            if "timestamp" in d:
                d["timestamp"] = d["timestamp"].isoformat()
            latest_data = d
            logging.info(f"New data detected: {latest_data.get('device_id')}")

    # Watch the collection forever
    col_query.on_snapshot(on_snapshot)

# Start the background thread so it doesn't block the web server
threading.Thread(target=watch_firestore, daemon=True).start()

# --- HTML TEMPLATE ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NOAH | Live Stream Dashboard</title>
    <link href="https://jsdelivr.net" rel="stylesheet">
    <link href="https://googleapis.com" rel="stylesheet">
    <style>
        body { background-color: #0b0e14; color: #e0e0e0; font-family: 'Inter', sans-serif; padding-bottom: 50px; }
        .dashboard-header { border-bottom: 1px solid #1f2937; padding: 15px 0; margin-bottom: 30px; background: #161b22; }
        .station-title { font-family: 'Orbitron', sans-serif; color: #4dabf7; font-size: 1rem; }
        .gauge-card { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 20px; text-align: center; }
        .gauge-svg { width: 100%; height: 120px; transform: rotate(-90deg); }
        .gauge-bg { fill: none; stroke: #1c2128; stroke-width: 3; }
        .gauge-fill { fill: none; stroke-width: 3; stroke-linecap: round; transition: stroke-dasharray 1.2s ease-in-out; }
        .gauge-val { font-family: 'Orbitron', sans-serif; font-size: 1.4rem; color: #fff; margin-top: 5px; }
        .tile-card { background: #0d1117; border: 1px solid #30363d; border-radius: 8px; padding: 15px; height: 100%; }
        .tile-label { font-size: 0.65rem; text-transform: uppercase; color: #8b949e; letter-spacing: 1px; }
        .tile-val { font-family: 'Orbitron', sans-serif; font-size: 1.1rem; color: #51cf66; }
        .section-header { border-left: 4px solid #4dabf7; padding-left: 10px; margin: 30px 0 15px 0; font-weight: bold; font-size: 0.9rem; color: #8b949e; }
        .stream-status { font-size: 0.8rem; color: #4dabf7; }
    </style>
</head>
<body>
    <div class="dashboard-header">
        <div class="container d-flex justify-content-between align-items-center">
            <div class="station-title">✦ NOAH LIVE STREAM</div>
            <div id="sync-time" class="stream-status">CONNECTING TO DATA STREAM...</div>
        </div>
    </div>

    <div class="container">
        <div class="section-header">ATMOSPHERICS</div>
        <div class="row g-3">
            <div class="col-md-3"><div class="gauge-card"><div class="tile-label">Temperature</div><svg class="gauge-svg" viewBox="0 0 36 36"><path class="gauge-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" stroke-dasharray="50, 100"/><path id="temp-arc" class="gauge-fill" style="stroke: #ff6b6b;" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"/></svg><div id="temp-val" class="gauge-val">--°F</div></div></div>
            <div class="col-md-3"><div class="gauge-card"><div class="tile-label">Humidity</div><svg class="gauge-svg" viewBox="0 0 36 36"><path class="gauge-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" stroke-dasharray="50, 100"/><path id="hum-arc" class="gauge-fill" style="stroke: #339af0;" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"/></svg><div id="hum-val" class="gauge-val">--%</div></div></div>
            <div class="col-md-3"><div class="gauge-card"><div class="tile-label">Wind Speed</div><svg class="gauge-svg" viewBox="0 0 36 36"><path class="gauge-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" stroke-dasharray="50, 100"/><path id="wind-arc" class="gauge-fill" style="stroke: #51cf66;" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"/></svg><div id="wind-val" class="gauge-val">-- mph</div></div></div>
            <div class="col-md-3"><div class="gauge-card"><div class="tile-label">Rain (1h)</div><svg class="gauge-svg" viewBox="0 0 36 36"><path class="gauge-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" stroke-dasharray="50, 100"/><path id="rain-arc" class="gauge-fill" style="stroke: #a5d8ff;" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"/></svg><div id="rain-val" class="gauge-val">-- in</div></div></div>
        </div>

        <div class="section-header">STORM & SYSTEM</div>
        <div class="row g-2">
            <div class="col-6 col-md-3"><div class="tile-card"><div class="tile-label">Pressure</div><div id="press-val" class="tile-val">--</div></div></div>
            <div class="col-6 col-md-3"><div class="tile-card"><div class="tile-label">Lightning</div><div id="light-val" class="tile-val">--</div></div></div>
            <div class="col-6 col-md-3"><div class="tile-card"><div class="tile-label">Battery</div><div id="batt-val" class="tile-val">--V</div></div></div>
            <div class="col-6 col-md-3"><div class="tile-card"><div class="tile-label">Device ID</div><div id="device-val" class="tile-val" style="font-size:0.7rem; color:#8b949e;">--</div></div></div>
        </div>
    </div>

    <script>
        // Use browser EventSource to listen to the Python /stream route
        const source = new EventSource("/stream");

        source.onmessage = function(event) {
            const d = JSON.parse(event.data);
            
            // LOCAL TIME CONVERSION
            const localTime = new Date().toLocaleTimeString();
            document.getElementById('sync-time').innerText = 'LIVE STREAM: ' + localTime + ' (Local)';

            // UPDATE GAUGE ARCS
            document.getElementById('temp-arc').setAttribute('stroke-dasharray', `${(d.temp_f / 110) * 50}, 100`);
            document.getElementById('hum-arc').setAttribute('stroke-dasharray', `${(d.humidity / 100) * 50}, 100`);
            document.getElementById('wind-arc').setAttribute('stroke-dasharray', `${(d.wind_speed_mph / 60) * 50}, 100`);
            document.getElementById('rain-arc').setAttribute('stroke-dasharray', `${((d.rain_1h_in || 0) / 2) * 50}, 100`);

            // UPDATE VALUES
            document.getElementById('temp-val').innerText = d.temp_f + '°F';
            document.getElementById('hum-val').innerText = d.humidity + '%';
            document.getElementById('wind-val').innerText = d.wind_speed_mph + ' mph';
            document.getElementById('rain-val').innerText = (d.rain_1h_in || 0) + ' in';
            document.getElementById('press-val').innerText = d.pressure_inhg || '--';
            document.getElementById('light-val').innerText = d.lightning_count || '0';
            document.getElementById('batt-val').innerText = d.battery_v + 'V';
            document.getElementById('device-val').innerText = d.device_id;
        };

        source.onerror = function() {
            document.getElementById('sync-time').innerText = 'STREAM DISCONNECTED. RECONNECTING...';
        };
    </script>
</body>
</html>
"""

# --- ROUTES ---

@app.route("/stream")
def stream():
    def event_stream():
        last_sent_time = None
        while True:
            # Check if we have new data compared to what was last sent
            if latest_data:
                current_time = latest_data.get('timestamp')
                if current_time != last_sent_time:
                    yield f"data: {json.dumps(latest_data)}\\n\\n"
                    last_sent_time = current_time
            time.sleep(1) # Frequency of check
            
    return Response(event_stream(), mimetype="text/event-stream")

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

if __name__ == "__main__":
    # Gunicorn is used in production, but this works for testing
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
