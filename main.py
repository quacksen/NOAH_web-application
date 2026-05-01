import os
import logging
from flask import Flask, render_template_string
from google.cloud import firestore

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
    <meta http-equiv="refresh" content="60">
    <title>NOAH | Live Dashboard</title>
    <link href="https://jsdelivr.net" rel="stylesheet">
    <link href="https://googleapis.com" rel="stylesheet">
    
    <style>
        body { background-color: #0b0e14; color: #e0e0e0; font-family: 'Inter', sans-serif; }
        .dashboard-header { border-bottom: 1px solid #1f2937; padding: 15px 0; margin-bottom: 30px; background: #161b22; }
        .station-title { font-family: 'Orbitron', sans-serif; letter-spacing: 2px; color: #4dabf7; font-size: 1rem; }
        
        .gauge-card { 
            background: #161b22; 
            border: 1px solid #30363d; 
            border-radius: 12px; 
            padding: 25px; 
            text-align: center; 
            height: 100%;
        }
        
        /* SVG Gauge CSS */
        .gauge-svg { width: 100%; height: 140px; transform: rotate(-90deg); }
        .gauge-bg { fill: none; stroke: #1c2128; stroke-width: 3; }
        .gauge-fill { 
            fill: none; 
            stroke: #51cf66; 
            stroke-width: 3; 
            stroke-linecap: round; 
            transition: stroke-dasharray 2s ease-in-out;
        }
        
        .gauge-label { font-size: 0.75rem; text-transform: uppercase; color: #8b949e; letter-spacing: 2px; margin-bottom: 10px; }
        .gauge-value { font-family: 'Orbitron', sans-serif; font-size: 1.8rem; color: #ffffff; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="dashboard-header">
        <div class="container d-flex justify-content-between align-items-center">
            <div class="station-title">✦ NOAH WEATHER STATION</div>
            <div class="text-end small text-muted">
                SYNC: {{ data.timestamp.strftime('%H:%M:%S') if data else 'N/A' }} UTC
            </div>
        </div>
    </div>

    <div class="container">
        {% if data %}
        <div class="row g-4">
            <!-- TEMPERATURE GAUGE -->
            <div class="col-md-4">
                <div class="gauge-card">
                    <div class="gauge-label">Temperature</div>
                    <svg class="gauge-svg" viewBox="0 0 36 36">
                        <path class="gauge-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" stroke-dasharray="50, 100"/>
                        <!-- Logic: (Value / Max) * 50 to fill the top half circle -->
                        <path class="gauge-fill" style="stroke: #ff6b6b;" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" 
                              stroke-dasharray="{{ (data.temp_f / 110) * 50 }}, 100"/>
                    </svg>
                    <div class="gauge-value">{{ data.temp_f | default(0) }}°F</div>
                </div>
            </div>

            <!-- HUMIDITY GAUGE -->
            <div class="col-md-4">
                <div class="gauge-card">
                    <div class="gauge-label">Humidity</div>
                    <svg class="gauge-svg" viewBox="0 0 36 36">
                        <path class="gauge-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" stroke-dasharray="50, 100"/>
                        <path class="gauge-fill" style="stroke: #339af0;" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" 
                              stroke-dasharray="{{ (data.humidity / 100) * 50 }}, 100"/>
                    </svg>
                    <div class="gauge-value">{{ data.humidity | default(0) }}%</div>
                </div>
            </div>

            <!-- WIND SPEED GAUGE -->
            <div class="col-md-4">
                <div class="gauge-card">
                    <div class="gauge-label">Wind Speed</div>
                    <svg class="gauge-svg" viewBox="0 0 36 36">
                        <path class="gauge-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" stroke-dasharray="50, 100"/>
                        <path class="gauge-fill" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" 
                              stroke-dasharray="{{ (data.wind_speed_mph / 60) * 50 }}, 100"/>
                    </svg>
                    <div class="gauge-value">{{ data.wind_speed_mph | default(0) }} <small>mph</small></div>
                </div>
            </div>
        </div>
        {% else %}
        <div class="text-center py-5">
            <div class="spinner-border text-primary mb-3"></div>
            <p class="text-muted">Database connected. Waiting for sync...</p>
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route("/")
def home():
    try:
        docs = db.collection("noah_sensor_data").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(1).stream()
        data = None
        for doc in docs:
            data = doc.to_dict()
            break 
        return render_template_string(HTML_TEMPLATE, data=data)
    except Exception as e:
        return f"Error: {e}", 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
