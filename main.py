import os
import logging
from flask import Flask, render_template_string, jsonify
from google.cloud import firestore

# Initialize Firestore
try:
    db = firestore.Client(database="cullowhee")
except Exception:
    db = firestore.Client()

app = Flask(__name__)

# THE HTML & CSS & JAVASCRIPT
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NOAH | Live Atmospheric Dashboard</title>
    <link href="https://jsdelivr.net" rel="stylesheet">
    <link href="https://googleapis.com" rel="stylesheet">
    
    <style>
        body { background-color: #0b0e14; color: #e0e0e0; font-family: 'Inter', sans-serif; overflow-x: hidden; }
        .dashboard-header { border-bottom: 1px solid #1f2937; padding: 15px 0; margin-bottom: 30px; background: #161b22; }
        .station-title { font-family: 'Orbitron', sans-serif; letter-spacing: 2px; color: #4dabf7; font-size: 0.9rem; }
        
        .gauge-card { 
            background: #161b22; 
            border: 1px solid #30363d; 
            border-radius: 12px; 
            padding: 25px; 
            text-align: center; 
            height: 100%;
        }
        
        /* SVG Gauge CSS */
        .gauge-svg { width: 100%; height: 160px; transform: rotate(-90deg); }
        .gauge-bg { fill: none; stroke: #1c2128; stroke-width: 2.5; }
        .gauge-fill { 
            fill: none; 
            stroke-width: 2.5; 
            stroke-linecap: round; 
            transition: stroke-dasharray 2s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .gauge-label { font-size: 0.75rem; text-transform: uppercase; color: #8b949e; letter-spacing: 2px; margin-bottom: 10px; }
        .gauge-value { font-family: 'Orbitron', sans-serif; font-size: 1.8rem; color: #ffffff; margin-top: 5px; }
        
        .status-pulse {
            height: 8px; width: 8px; background-color: #28a745; border-radius: 50%; display: inline-block;
            box-shadow: 0 0 8px #28a745; margin-right: 8px;
        }
    </style>
</head>
<body>
    <div class="dashboard-header">
        <div class="container d-flex justify-content-between align-items-center">
            <div class="station-title">✦ NOAH WEATHER STATION</div>
            <div class="text-end small text-muted">
                <span class="status-pulse"></span>
                <span id="sync-time">SYNC: {{ data.timestamp.strftime('%H:%M:%S') if data else 'N/A' }} UTC</span>
            </div>
        </div>
    </div>

    <div class="container">
        {% if data %}
        <div class="row g-4">
            <!-- TEMPERATURE -->
            <div class="col-md-4">
                <div class="gauge-card">
                    <div class="gauge-label">Temperature</div>
                    <svg class="gauge-svg" viewBox="0 0 36 36">
                        <path class="gauge-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" stroke-dasharray="50, 100"/>
                        <path id="temp-arc" class="gauge-fill" style="stroke: #ff6b6b;" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" 
                              stroke-dasharray="{{ (data.temp_f / 110) * 50 }}, 100"/>
                    </svg>
                    <div id="temp-val" class="gauge-value">{{ data.temp_f | default(0) }}°F</div>
                </div>
            </div>

            <!-- HUMIDITY -->
            <div class="col-md-4">
                <div class="gauge-card">
                    <div class="gauge-label">Humidity</div>
                    <svg class="gauge-svg" viewBox="0 0 36 36">
                        <path class="gauge-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" stroke-dasharray="50, 100"/>
                        <path id="hum-arc" class="gauge-fill" style="stroke: #339af0;" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" 
                              stroke-dasharray="{{ (data.humidity / 100) * 50 }}, 100"/>
                    </svg>
                    <div id="hum-val" class="gauge-value">{{ data.humidity | default(0) }}%</div>
                </div>
            </div>

            <!-- WIND SPEED -->
            <div class="col-md-4">
                <div class="gauge-card">
                    <div class="gauge-label">Wind Speed</div>
                    <svg class="gauge-svg" viewBox="0 0 36 36">
                        <path class="gauge-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" stroke-dasharray="50, 100"/>
                        <path id="wind-arc" class="gauge-fill" style="stroke: #51cf66;" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" 
                              stroke-dasharray="{{ (data.wind_speed_mph / 60) * 50 }}, 100"/>
                    </svg>
                    <div id="wind-val" class="gauge-value">{{ data.wind_speed_mph | default(0) }} <small style="font-size:0.8rem">mph</small></div>
                </div>
            </div>
        </div>
        {% else %}
        <div class="text-center py-5">
            <div class="spinner-border text-primary mb-3"></div>
            <p class="text-muted">Waiting for sensor synchronization...</p>
        </div>
        {% endif %}
    </div>

    <script>
        async function updateDashboard() {
            try {
                const response = await fetch('/api/data');
                const data = await response.json();
                
                if (data && !data.error) {
                    // Update Time
                    document.getElementById('sync-time').innerText = 'SYNC: ' + data.timestamp + ' UTC';
                    
                    // Update Values
                    document.getElementById('temp-val').innerText = data.temp_f + '°F';
                    document.getElementById('hum-val').innerText = data.humidity + '%';
                    document.getElementById('wind-val').innerHTML = data.wind_speed_mph + ' <small style="font-size:0.8rem">mph</small>';

                    // Update SVG Arcs (Value / Max * 50)
                    document.getElementById('temp-arc').setAttribute('stroke-dasharray', `${(data.temp_f / 110) * 50}, 100`);
                    document.getElementById('hum-arc').setAttribute('stroke-dasharray', `${(data.humidity / 100) * 50}, 100`);
                    document.getElementById('wind-arc').setAttribute('stroke-dasharray', `${(data.wind_speed_mph / 60) * 50}, 100`);
                }
            } catch (err) {
                console.log('Live update failed:', err);
            }
        }

        // Check for new data every 30 seconds
        setInterval(updateDashboard, 30000);
    </script>
</body>
</html>
"""

@app.route("/api/data")
def get_data_api():
    try:
        # Fetch the absolute latest record
        docs = db.collection("noah_sensor_data").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(1).stream()
        data = None
        for doc in docs:
            data = doc.to_dict()
            if "timestamp" in data:
                data["timestamp"] = data["timestamp"].strftime('%H:%M:%S')
            break
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/")
def home():
    try:
        docs = db.collection("noah_sensor_data").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(1).stream()
        data = next((doc.to_dict() for doc in docs), None)
        return render_template_string(HTML_TEMPLATE, data=data)
    except Exception as e:
        return f"Database Error: {e}", 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
