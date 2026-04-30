from flask import Flask, render_template_string
from google.cloud import firestore
import os
import logging

app = Flask(__name__)

# Initialize Firestore with your specific database
db = firestore.Client(database="cullowhee")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NOAH | Cullowhee Weather</title>
    <link href="https://jsdelivr.net" rel="stylesheet">
    <style>
        body { background-color: #f8f9fa; font-family: 'Inter', sans-serif; }
        .navbar { background-color: #0d6efd; color: white; margin-bottom: 2rem; }
        .card-stat { border: none; border-radius: 15px; transition: transform 0.2s; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
        .card-stat:hover { transform: translateY(-5px); }
        .stat-value { font-size: 2rem; font-weight: bold; color: #0d6efd; }
        .table-container { background: white; border-radius: 15px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
        .status-dot { height: 10px; width: 10px; background-color: #28a745; border-radius: 50%; display: inline-block; margin-right: 5px; }
    </style>
</head>
<body>
    <nav class="navbar navbar-dark shadow-sm">
        <div class="container">
            <span class="navbar-brand mb-0 h1">NOAH Cullowhee Creek Station</span>
            <span class="badge bg-light text-dark"><span class="status-dot"></span>Live Station Data</span>
        </div>
    </nav>

    <div class="container">
        {% if data %}
        <!-- Recent Summary Cards -->
        <div class="row g-4 mb-5">
            <div class="col-md-3">
                <div class="card card-stat text-center p-3">
                    <div class="text-muted small">Current Temp</div>
                    <div class="stat-value">{{ data[0].temp_f }}°F</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card card-stat text-center p-3">
                    <div class="text-muted small">Humidity</div>
                    <div class="stat-value">{{ data[0].humidity }}%</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card card-stat text-center p-3">
                    <div class="text-muted small">Wind Speed</div>
                    <div class="stat-value">{{ data[0].wind_speed_mph }} <span style="font-size: 0.8rem">mph</span></div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card card-stat text-center p-3">
                    <div class="text-muted small">Battery</div>
                    <div class="stat-value">{{ data[0].battery_v }}V</div>
                </div>
            </div>
        </div>

        <!-- History Table -->
        <div class="table-container mb-5">
            <h5 class="mb-4">Historical Readings</h5>
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead class="table-light">
                        <tr>
                            <th>Timestamp (UTC)</th>
                            <th>Temp (°F)</th>
                            <th>Humidity</th>
                            <th>Rain (1h)</th>
                            <th>Wind Dir</th>
                            <th>Battery</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for row in data %}
                        <tr>
                            <td class="text-muted">{{ row.timestamp.strftime('%m/%d %H:%M') }}</td>
                            <td><strong>{{ row.temp_f }}°</strong></td>
                            <td>{{ row.humidity }}%</td>
                            <td>{{ row.rain_1h_in }} in</td>
                            <td>{{ row.wind_dir_deg }}°</td>
                            <td><span class="badge bg-secondary">{{ row.battery_v }}V</span></td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
        {% else %}
        <div class="alert alert-info shadow-sm">No data found in Firestore collection <b>noah_sensor_data</b> yet.</div>
        {% endif %}
    </div>

    <script src="https://jsdelivr.net"></script>
</body>
</html>
"""

@app.route("/")
def home():
    try:
        # Fetch last 30 records
        docs = db.collection("noah_sensor_data").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(30).stream()
        data = [doc.to_dict() for doc in docs]
        return render_template_string(HTML_TEMPLATE, data=data)
    except Exception as e:
        return f"<div style='padding:50px;'><h4>Database Connection Error</h4><p>{e}</p></div>", 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
