from flask import Flask, render_template_string
from google.cloud import firestore
import os
import logging

app = Flask(__name__)

# Initialize Firestore
# Note: On Cloud Run, it automatically finds credentials if the service account has permission
try:
    db = firestore.Client()
except Exception as e:
    logging.error(f"Error connecting to Firestore: {e}")
    db = None

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Cullowhee Weather</title>
    <style>
        body { font-family: sans-serif; margin: 40px; background: #f4f4f9; }
        table { width: 100%; border-collapse: collapse; background: white; }
        th, td { padding: 12px; border: 1px solid #ddd; text-align: left; }
        th { background-color: #007bff; color: white; }
        tr:nth-child(even) { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <h1>Cullowhee Weather Data</h1>
    {% if data %}
    <table>
        <tr><th>Time</th><th>Device</th><th>Temp</th><th>Voltage</th></tr>
        {% for row in data %}
        <tr>
            <td>{{ row.timestamp }}</td>
            <td>{{ row.device }}</td>
            <td>{{ row.temp }}°C</td>
            <td>{{ row.voltage }}V</td>
        </tr>
        {% endfor %}
    </table>
    {% else %}
    <p>No data found in Firestore collection 'weather_data'. Check your ingestion function!</p>
    {% endif %}
</body>
</html>
"""

@app.route("/")
def home():
    if not db:
        return "Database connection failed", 500
    
    try:
        # Fetch last 50 records
        docs = db.collection('weather_data').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(50).stream()
        data = [doc.to_dict() for doc in docs]
        return render_template_string(HTML_TEMPLATE, data=data)
    except Exception as e:
        logging.error(f"Error fetching data: {e}")
        return f"Error fetching data: {e}", 500

if __name__ == "__main__":
    # This part is used for LOCAL testing; Cloud Run uses the Entrypoint command
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
