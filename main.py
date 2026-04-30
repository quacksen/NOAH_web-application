from flask import Flask, render_template_string
from google.cloud import firestore
from datetime import datetime
import os
import logging

app = Flask(__name__)

# IMPORTANT: Matching your ingest function's specific database
db = firestore.Client(database="cullowhee")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>NOAH | Cullowhee Weather</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; background: #f0f2f5; color: #333; }
        .container { max-width: 1200px; margin: auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 10px; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 12px; border: 1px solid #dee2e6; text-align: left; }
        th { background-color: #1a73e8; color: white; position: sticky; top: 0; }
        tr:nth-child(even) { background-color: #f8f9fa; }
        tr:hover { background-color: #e9ecef; }
        .status-bar { margin-bottom: 20px; font-size: 0.9em; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <h1>NOAH Sensor Network</h1>
        <div class="status-bar">Location: Cullowhee, NC | Database: cullowhee</div>
        
        {% if data %}
        <table>
            <thead>
                <tr>
                    <th>Time (UTC)</th>
                    <th>Device</th>
                    <th>Temp (°F)</th>
                    <th>Humidity (%)</th>
                    <th>Wind (mph)</th>
                    <th>Rain (1h)</th>
                    <th>Battery</th>
                </tr>
            </thead>
            <tbody>
                {% for row in data %}
                <tr>
                    <td>{{ row.timestamp.strftime('%Y-%m-%d %H:%M') if row.timestamp else 'N/A' }}</td>
                    <td>{{ row.device_id }}</td>
                    <td>{{ row.temp_f if row.temp_f is not none else '--' }}°</td>
                    <td>{{ row.humidity if row.humidity is not none else '--' }}%</td>
                    <td>{{ row.wind_speed_mph if row.wind_speed_mph is not none else '0' }}</td>
                    <td>{{ row.rain_1h_in if row.rain_1h_in is not none else '0.00' }}"</td>
                    <td>{{ row.battery_v if row.battery_v is not none else '--' }}V</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <p>No records found in <b>noah_sensor_data</b> yet. Waiting for Notecard sync...</p>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route("/")
def home():
    try:
        # Fetch last 50 records from your specific collection
        docs = db.collection("noah_sensor_data").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(50).stream()
        data = [doc.to_dict() for doc in docs]
        return render_template_string(HTML_TEMPLATE, data=data)
    except Exception as e:
        logging.error(f"Webpage error: {e}")
        return f"Error loading database: {e}", 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
