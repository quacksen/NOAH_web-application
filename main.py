import os
from flask import Flask, render_template_string
from google.cloud import firestore

# Initialize Firestore
try:
    db = firestore.Client(database="cullowhee")
except Exception:
    db = firestore.Client()

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NOAH | Real-Time Dashboard</title>
    <link href="https://jsdelivr.net" rel="stylesheet">
    <link href="https://googleapis.com" rel="stylesheet">
    
    <!-- Include Firebase SDK for Real-time Snapshots -->
    <script src="https://gstatic.com"></script>
    <script src="https://gstatic.com"></script>

    <style>
        body { background-color: #0b0e14; color: #e0e0e0; font-family: 'Inter', sans-serif; padding-bottom: 50px; }
        .dashboard-header { border-bottom: 1px solid #1f2937; padding: 15px 0; margin-bottom: 30px; background: #161b22; }
        .station-title { font-family: 'Orbitron', sans-serif; color: #4dabf7; font-size: 1rem; }
        .gauge-card { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 20px; text-align: center; }
        .gauge-svg { width: 100%; height: 120px; transform: rotate(-90deg); }
        .gauge-bg { fill: none; stroke: #1c2128; stroke-width: 3; }
        .gauge-fill { fill: none; stroke-width: 3; stroke-linecap: round; transition: stroke-dasharray 1s ease-in-out; }
        .gauge-val { font-family: 'Orbitron', sans-serif; font-size: 1.4rem; color: #fff; margin-top: 5px; }
        .tile-card { background: #0d1117; border: 1px solid #30363d; border-radius: 8px; padding: 15px; height: 100%; }
        .tile-label { font-size: 0.65rem; text-transform: uppercase; color: #8b949e; letter-spacing: 1px; }
        .tile-val { font-family: 'Orbitron', sans-serif; font-size: 1.1rem; color: #51cf66; }
        .section-header { border-left: 4px solid #4dabf7; padding-left: 10px; margin: 30px 0 15px 0; font-weight: bold; font-size: 0.9rem; color: #8b949e; }
    </style>
</head>
<body>
    <div class="dashboard-header">
        <div class="container d-flex justify-content-between align-items-center">
            <div class="station-title">✦ NOAH REAL-TIME NETWORK</div>
            <div id="sync-time" class="small text-info">SYNCING...</div>
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

        <div class="section-header">STORM & FLOOD</div>
        <div class="row g-2">
            <div class="col-6 col-md-2"><div class="tile-card"><div class="tile-label">Pressure</div><div id="press-val" class="tile-val">--</div></div></div>
            <div class="col-6 col-md-2"><div class="tile-card"><div class="tile-label">Stage (ft)</div><div id="stage-val" class="tile-val">--</div></div></div>
            <div class="col-6 col-md-2"><div class="tile-card"><div class="tile-label">Lightning</div><div id="light-val" class="tile-val">--</div></div></div>
            <div class="col-6 col-md-2"><div class="tile-card"><div class="tile-label">L-Dist (km)</div><div id="ldist-val" class="tile-val">--</div></div></div>
            <div class="col-6 col-md-2"><div class="tile-card"><div class="tile-label">Velocity</div><div id="vel-val" class="tile-val">--</div></div></div>
            <div class="col-6 col-md-2"><div class="tile-card"><div class="tile-label">Battery</div><div id="batt-val" class="tile-val" style="color:#4dabf7">--V</div></div></div>
        </div>
    </div>

    <script>
        // Use Firebase Client SDK to listen for changes
        // Since we are on Cloud Run, we use the Project ID and Database name
        const firebaseConfig = { projectId: "ee-dashboard-477704" };
        firebase.initializeApp(firebaseConfig);
        const db = firebase.firestore();

        // Listen to the 'cullowhee' database and the 'noah_sensor_data' collection
        // Note: Real-time listener detects NEW records instantly
        db.collection("noah_sensor_data")
          .orderBy("timestamp", "desc")
          .limit(1)
          .onSnapshot((snapshot) => {
              snapshot.forEach((doc) => {
                  const d = doc.data();
                  
                  // LOCAL TIME CONVERSION
                  const date = d.timestamp.toDate(); 
                  const localTime = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
                  document.getElementById('sync-time').innerText = 'LIVE SYNC: ' + localTime + ' (Local)';

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
                  document.getElementById('stage-val').innerText = d.stage_ft || '--';
                  document.getElementById('light-val').innerText = d.lightning_count || '0';
                  document.getElementById('batt-val').innerText = d.battery_v + 'V';
              });
          });
    </script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
