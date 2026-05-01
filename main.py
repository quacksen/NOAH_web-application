import os
import logging
from flask import Flask, render_template_string
from google.cloud import firestore

# Initialize Firestore once at the top level for performance
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
    
    <!-- Modern Styling and Fonts -->
    <link href="https://jsdelivr.net" rel="stylesheet">
    <link href="https://googleapis.com" rel="stylesheet">
    
    <style>
        body { background-color: #0b0e14; color: #e0e0e0; font-family: 'Inter', sans-serif; overflow-x: hidden; }
        .dashboard-header { border-bottom: 1px solid #1f2937; padding: 15px 0; margin-bottom: 30px; background: #161b22; }
        .station-title { font-family: 'Orbitron', sans-serif; letter-spacing: 2px; color: #4dabf7; font-size: 1rem; }
        
        .gauge-card { 
            background: #161b22; 
            border: 1px solid #30363d; 
            border-radius: 12px; 
            padding: 25px; 
            text-align: center; 
            height: 100%;
            transition: transform 0.3s ease;
        }
        .gauge-card:hover { transform: scale(1.02); }
        
        .gauge-label { font-size: 0.75rem; text-transform: uppercase; color: #8b949e; letter-spacing: 2px; margin-bottom: 15px; }
        .gauge-value { font-family: 'Orbitron', sans-serif; font-size: 1.8rem; margin-top: -35px; color: #ffffff; }
        
        /* Ensures the gauge canvas has space to draw */
        .gauge-container { height: 180px; width: 100%; margin: 0 auto; }
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
            <!-- TEMPERATURE -->
            <div class="col-md-4">
                <div class="gauge-card">
                    <div class="gauge-label">Temperature</div>
                    <div id="temp-gauge" class="gauge-container"></div>
                    <div class="gauge-value">{{ data.temp_f | default(0) }}°F</div>
                </div>
            </div>

            <!-- HUMIDITY -->
            <div class="col-md-4">
                <div class="gauge-card">
                    <div class="gauge-label">Humidity</div>
                    <div id="hum-gauge" class="gauge-container"></div>
                    <div class="gauge-value">{{ data.humidity | default(0) }}%</div>
                </div>
            </div>

            <!-- WIND SPEED -->
            <div class="col-md-4">
                <div class="gauge-card">
                    <div class="gauge-label">Wind Speed</div>
                    <div id="wind-gauge" class="gauge-container"></div>
                    <div class="gauge-value">{{ data.wind_speed_mph | default(0) }} <small>mph</small></div>
                </div>
            </div>
        </div>
        {% else %}
        <div class="text-center py-5">
            <div class="spinner-border text-primary mb-3"></div>
            <p class="text-muted">Database connected. Waiting for station sync...</p>
        </div>
        {% endif %}
    </div>

    <!-- SCRIPT LOADING: ORDER IS CRITICAL -->
    <!-- 1. Load Raphael first -->
    <script src="https://jsdelivr.net"></script>
    <!-- 2. Load JustGage second -->
    <script src="https://jsdelivr.net"></script>
    
    <script>
        {% if data %}
        document.addEventListener("DOMContentLoaded", function() {
            var config = {
                gaugeWidthScale: 0.12,
                pointer: true,
                pointerOptions: { toplength: -15, color: '#51cf66', stroke_width: 2 },
                gaugeColor: "#1c2128",
                hideValue: true,
                shadowOpacity: 0,
                startAnimationTime: 2000,
                startAnimationType: "bounce",
                refreshAnimationTime: 1000
            };

            // Temperature Gauge
            new JustGage({
                id: "temp-gauge",
                value: {{ data.temp_f | default(0) }},
                min: 0, max: 110,
                levelColors: ["#339af0", "#51cf66", "#ff6b6b"],
                ...config
            });

            // Humidity Gauge
            new JustGage({
                id: "hum-gauge",
                value: {{ data.humidity | default(0) }},
                min: 0, max: 100,
                levelColors: ["#339af0"],
                ...config
            });

            // Wind Gauge
            new JustGage({
                id: "wind-gauge",
                value: {{ data.wind_speed_mph | default(0) }},
                min: 0, max: 60,
                levelColors: ["#51cf66"],
                ...config
            });
        });
        {% endif %}
    </script>
</body>
</html>
"""

@app.route("/")
def home():
    try:
        # Optimized stream and fetch for the single latest record
        docs = db.collection("noah_sensor_data").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(1).stream()
        
        data = None
        for doc in docs:
            data = doc.to_dict()
            break 
            
        return render_template_string(HTML_TEMPLATE, data=data)
    except Exception as e:
        logging.error(f"Error: {e}")
        return f"<div style='color:white; background:#0b0e14; padding:50px;'><h4>Connection Error</h4><p>{e}</p></div>", 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
