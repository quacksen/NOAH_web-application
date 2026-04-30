from flask import Flask, render_template_string
from 
google.cloud
 import firestore
import os

app = Flask(__name__)
db = firestore.Client()

# Basic HTML template as a string
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><title>Weather Station</title></head>
<body>
    <h1>Cullowhee Weather Data</h1>
    <table border="1">
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
</body>
</html>
"""

@app.route("/")
def home():
    # Fetch last 50 records from Firestore
    docs = db.collection('weather_data').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(50).stream()
    data = [doc.to_dict() for doc in docs]
    return render_template_string(HTML_TEMPLATE, data=data)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
