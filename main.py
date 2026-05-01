import os
import logging
from flask import Flask, render_template_string
from google.cloud import firestore

# Initialize Flask
app = Flask(__name__)

# Configure Firestore - Tries your custom DB first, then falls back to default
try:
    db = firestore.Client(database="cullowhee")
except Exception:
    db = firestore.Client()

# DASHBOARD HTML & CSS & JAVASCRIPT
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="60">
    <title>NOAH | Cullowhee Dashboard</title>
    
    <!-- Bootstrap and Modern Fonts -->
    <link href="https://jsdelivr.net" rel="stylesheet">
    <link href="https://googleapis.com" rel="stylesheet">
    
    <style>
        body { background-color: #0b0e14; color: #e0e0e0; font-family: 'Inter', sans-serif; overflow-x: hidden; }
        
        .dashboard-header { 
            border-bottom: 1px solid #1f2937; 
            padding: 20px 0; 
            margin-bottom: 30px; 
            background: linear-gradient(180deg, #161b22 0%, #0b0e14 100%);
        }
        
        .station-title { 
            font-family: 'Orbitron', sans-serif; 
            letter-spacing: 2px; 
            color: #4dabf7; 
            font-size: 1.1rem; 
            font-weight: 700;
        }

        /* Animated Pulse Dot */
        .status-dot {
            height: 10px; width: 10px; background-color: #28a745; border-radius: 50%; display: inline-block;
            box-shadow: 0 0 8px #28a745;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(40, 167, 69, 0.7); }
            70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(40, 167, 69, 0); }
            100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(40, 167, 69, 0); }
        }
        
        .gauge-card { 
            background: #161b22; 
            border: 1px solid #30363d; 
            border-radius: 12px; 
            padding: 25px; 
            text-align: center;
            height: 100%;
            transition: transform 0.3s ease, border-color 0.3s ease;
        }
        .gauge-card:hover { transform: scale(1.03); border-color: #4dabf7; }
        
        .gauge-label { 
            font-size: 0.75rem; 
            text-transform: uppercase; 
            color: #8b949e; 
            letter-spacing: 2px; 
            margin-bottom: 15px; 
            font-weight: 600;
        }
        
        .gauge-value { 
            font-family: 'Orbitron', sans-serif; 
            font-size: 1.8rem; 
            margin-top: -35px; 
            color: #ffffff;
        }
        
        .gauge-desc { font-size: 0.85rem; font-weight: 700; margin-top: 5px; letter-spacing: 1px; }
        .text-cyan { color: #339af0; }
        .text-green { color: #51cf66; }
    </style>
</head>
<body>

    <div class="dashboard-header">
        <div class="container d-flex justify-content-between align-items-center">
            <div class="station-title">✦ NOAH ATMOSPHERIC NETWORK</div>
            <div class="text-end">
                <span class="status-dot me-2"></span>
                <span class="small text-muted">SYNC: {{ data.timestamp.strftime('%H:%M:%S') if data else 'N/A' }} UTC</span>
            </div>
        </div>
    </div>

    <div class="container">
        {% if data %}
        <div class="row g-4">
            <!-- TEMPERATURE -->
            <div class="col-md-4">
                <div class="gauge-card">
                    <div class="gauge-label">Air Temperature</div>
                    <div id="temp-gauge" style="height: 180px;"></div>
                    <div class="gauge-value">{{ data.temp_f | default(0) }}°F</div>
                    <div class="gauge-desc text-green">MILD</div>
                </div>
            </div>

            <!-- HUMIDITY -->
            <div class="col-md-4">
                <div class="gauge-card">
                    <div class="gauge-label">Humidity</div>
                    <div id="hum-gauge" style="height: 180px;"></div>
                    <div class="gauge-value">{{ data.humidity | default(0) }}%</div>
                    <div class="gauge-desc text-cyan">STABLE</div>
                </div>
            </div>

            <!-- WIND SPEED -->
            <div class="col-md-4">
                <div class="gauge-card">
                    <div class="gauge-label">Wind Speed</div>
                    <div id="wind-gauge" style="height: 180px;"></div>
                    <div class="gauge-value">{{ data.wind_speed_mph | default(0) }} <small>mph</small></div>
                    <div class="gauge-desc text-green">CALM</div>
                </div>
            </div>
        </div>
        {% else %}
        <div class="text-center py-5">
            <div class="spinner-border text-primary mb-3"></div>
            <h4 class="text-muted">Scanning for Sensor Data...</h4>
            <p class="small text-muted">Verify collection 'noah_sensor_data' in database 'cullowhee'.</p>
        </div>
        {% endif %}
    </div>

    <!-- Gauge Engine Scripts -->
    <script src="https://cloudflare.com"></script>
    <script src="https://cloudflare.com"></script>
    
    <script>
        {% if data %}
        document.addEventListener("DOMContentLoaded", function() {
            var config = {
                gaugeWidthScale: 0.12,
                pointer: true,
                pointerOptions: { toplength: -15, color: '#51cf66', stroke: '#0b0e14', stroke_width: 2 },
                gaugeColor: "#1c2128",
                hideValue: true,
                shadowOpacity: 0,
                // Animation Logic
                startAnimationTime: 2000,
                startAnimationType: "bounce",
                refreshAnimationTime: 1000,
                refreshAnimationType: "bounce"
            };

            new JustGage({
                id: "temp-gauge",
                value: {{ data.temp_f | default(0) }},
                min: 0, max: 110,
                levelColors: ["#339af0", "#51cf66", "#fcc419", "#ff6b6b"],
                ...config
            });

            new JustGage({
                id: "hum-gauge",
                value: {{ data.humidity | default(0) }},
                min: 0, max: 100,
                levelColors: ["#339af0"],
                ...config
            });

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
        # Fetch the MOST RECENT single record
        query = db.collection("noah_sensor_data").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(1).get()
        
        data = None
        if query:
            # We take the first result from the list of returned documents
            data = query[0].to_dict()
            
        return render_template_string(HTML_TEMPLATE, data=data)
    except Exception as e:
        logging.error(f"Firestore Error: {e}")
        return f"<div style='color:white; background:#0b0e14; padding:50px; height:100vh;'><h4>Database Error</h4><p>{e}</p></div>", 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
