from flask import Flask, render_template
from google.cloud import firestore
import os

app = Flask(__name__)
db = firestore.Client(database="cullowhee")

@app.route("/")
def home():
    try:
        # Fetch the latest record
        docs = db.collection("noah_sensor_data").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(1).stream()
        data = [doc.to_dict() for doc in docs]
        
        # This now looks for templates/index.html automatically
        return render_template("index.html", data=data)
    except Exception as e:
        return f"Database Error: {e}", 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
