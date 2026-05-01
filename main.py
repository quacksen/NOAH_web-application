import os
import logging
from flask import Flask, render_template_string
from google.cloud import firestore

# 1. Initialize once at the top level to keep the connection "warm"
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
    
    <!-- Using fast Cloudflare/Google CDNs -->
    <link href="https://cloudflare.com" rel="stylesheet">
    <link href="https://googleapis.com" rel="stylesheet">
    
    <style>
        body { background-color: #0b0e14; color: #e0e0e0; font-family: 'Inter', sans-serif; overflow-x: hidden; }
        .dashboard-header { border-bottom: 1px solid #1f2937; padding: 15px 0; margin-bottom: 25px; background: #161b22; }
        .station-title { font-family: 'Orbitron', sans-serif; letter-spacing: 2px; color: #4dabf7; font-size: 1rem; }
        .gauge-card { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 20px; text-align: center; transition: 0.3s; }
        .gauge-label { font-size: 0.7rem; text-transform: uppercase; color: #8b949e; letter-spacing: 2px; margin-bottom: 10px; }
        .gauge-value { font-family: 'Orbitron', sans-serif; font-size: 1.6rem; margin-top: -30px; color: #ffffff; }
    </style>
</head>
<body>
    <div class="dashboard-header">
        <div class="container d-flex justify-content-between align-items-center">
            <div class="station-title">✦ NOAH NETWORK</div>
            <div class="small text-muted">{{ data.timestamp.strftime('%H:%M:%S') if data else '' }} UTC</div>
        </div>
    </div>

    <div class="container">
        {% if data %}
        <div class="row g-4">
            <div class="col-md-4">
                <div class="gauge-card">
                    <div class="gauge-label">Temperature</div>
                    <div id="temp-gauge" style="height: 150px;"></div>
                    <div class="gauge-value">{{ data.temp_f | default(0) }}°F</div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="gauge-card">
                    <div class="gauge-label">Humidity</div>
                    <div id="hum-gauge" style="height: 150px;"></div>
                    <div class="gauge-value">{{ data.humidity | default(0) }}%</div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="gauge-card">
                    <div class="gauge-label">Wind</div>
                    <div id="wind-gauge" style="height: 150px;"></div>
                    <div class="gauge-value">{{ data.wind_speed_mph | default(0) }} <small>mph</small></div>
                </div>
            </div>
        </div>
        {% else %}
        <div class="text-center py-5">Loading sensor data...</div>
        {% endif %}
    </div>

    <script src="https://cloudflare.com"></script>
    <script src="https://cloudflare.com"></script>
    <script>
        {% if data %}
        document.addEventListener("DOMContentLoaded", function() {
            var config = {
                gaugeWidthScale: 0.12, pointer: true, gaugeColor: "#1c2128",
                hideValue: true, shadowOpacity: 0,
                pointerOptions: { toplength: -15, color: '#51cf66', stroke_width: 2 },
                startAnimationTime: 1000, startAnimationType: "bounce"
            };
            new JustGage({ id: "temp-gauge", value: {{ data.temp_f | default(0) }}, min: 0, max: 110, levelColors: ["#339af0", "#51cf66", "#ff6b6b"], ...config });
            new JustGage({ id: "hum-gauge", value: {{ data.humidity | default(0) }}, min: 0, max: 100, levelColors: ["#339af0"], ...config });
            new JustGage({ id: "wind-gauge", value: {{ data.wind_speed_mph | default(0) }}, min: 0, max: 60, levelColors: ["#51cf66"], ...config });
        });
        {% endif %}
    </script>
</body>
</html>
"""

@app.route("/")
def home():
    try:
        # Use stream() and next() for the absolute fastest single-record pull
        docs = db.collection("noah_sensor_data").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(1).stream()
        
        # Generator to dict
        data = None
        for doc in docs:
            data = doc.to_dict()
            break 
            
        return render_template_string(HTML_TEMPLATE, data=data)
    except Exception as e:
        return f"Error: {e}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
import os
import logging
from flask import Flask, render_template_string
from google.cloud import firestore

# 1. Initialize once at the top level to keep the connection "warm"
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
    
    <!-- Using fast Cloudflare/Google CDNs -->
    <link href="https://cloudflare.com" rel="stylesheet">
    <link href="https://googleapis.com" rel="stylesheet">
    
    <style>
        body { background-color: #0b0e14; color: #e0e0e0; font-family: 'Inter', sans-serif; overflow-x: hidden; }
        .dashboard-header { border-bottom: 1px solid #1f2937; padding: 15px 0; margin-bottom: 25px; background: #161b22; }
        .station-title { font-family: 'Orbitron', sans-serif; letter-spacing: 2px; color: #4dabf7; font-size: 1rem; }
        .gauge-card { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 20px; text-align: center; transition: 0.3s; }
        .gauge-label { font-size: 0.7rem; text-transform: uppercase; color: #8b949e; letter-spacing: 2px; margin-bottom: 10px; }
        .gauge-value { font-family: 'Orbitron', sans-serif; font-size: 1.6rem; margin-top: -30px; color: #ffffff; }
    </style>
</head>
<body>
    <div class="dashboard-header">
        <div class="container d-flex justify-content-between align-items-center">
            <div class="station-title">✦ NOAH NETWORK</div>
            <div class="small text-muted">{{ data.timestamp.strftime('%H:%M:%S') if data else '' }} UTC</div>
        </div>
    </div>

    <div class="container">
        {% if data %}
        <div class="row g-4">
            <div class="col-md-4">
                <div class="gauge-card">
                    <div class="gauge-label">Temperature</div>
                    <div id="temp-gauge" style="height: 150px;"></div>
                    <div class="gauge-value">{{ data.temp_f | default(0) }}°F</div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="gauge-card">
                    <div class="gauge-label">Humidity</div>
                    <div id="hum-gauge" style="height: 150px;"></div>
                    <div class="gauge-value">{{ data.humidity | default(0) }}%</div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="gauge-card">
                    <div class="gauge-label">Wind</div>
                    <div id="wind-gauge" style="height: 150px;"></div>
                    <div class="gauge-value">{{ data.wind_speed_mph | default(0) }} <small>mph</small></div>
                </div>
            </div>
        </div>
        {% else %}
        <div class="text-center py-5">Loading sensor data...</div>
        {% endif %}
    </div>

    <script src="https://cloudflare.com"></script>
    <script src="https://cloudflare.com"></script>
    <script>
        {% if data %}
        document.addEventListener("DOMContentLoaded", function() {
            var config = {
                gaugeWidthScale: 0.12, pointer: true, gaugeColor: "#1c2128",
                hideValue: true, shadowOpacity: 0,
                pointerOptions: { toplength: -15, color: '#51cf66', stroke_width: 2 },
                startAnimationTime: 1000, startAnimationType: "bounce"
            };
            new JustGage({ id: "temp-gauge", value: {{ data.temp_f | default(0) }}, min: 0, max: 110, levelColors: ["#339af0", "#51cf66", "#ff6b6b"], ...config });
            new JustGage({ id: "hum-gauge", value: {{ data.humidity | default(0) }}, min: 0, max: 100, levelColors: ["#339af0"], ...config });
            new JustGage({ id: "wind-gauge", value: {{ data.wind_speed_mph | default(0) }}, min: 0, max: 60, levelColors: ["#51cf66"], ...config });
        });
        {% endif %}
    </script>
</body>
</html>
"""

@app.route("/")
def home():
    try:
        # Use stream() and next() for the absolute fastest single-record pull
        docs = db.collection("noah_sensor_data").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(1).stream()
        
        # Generator to dict
        data = None
        for doc in docs:
            data = doc.to_dict()
            break 
            
        return render_template_string(HTML_TEMPLATE, data=data)
    except Exception as e:
        return f"Error: {e}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
