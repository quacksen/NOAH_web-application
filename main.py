from flask import Flask, render_template
from google.cloud import firestore
import os
import logging

app = Flask(__name__)

# Fallback to (default) database if "cullowhee" isn't found
try:
    db = firestore.Client(database="cullowhee")
except Exception:
    db = firestore.Client()

@app.route("/")
def home():
    try:
        # Fetch the LATEST single record
        docs = db.collection("noah_sensor_data").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(1).get()
        
        if docs:
            # Get the first (most recent) document
            data = docs[0].to_dict()
        else:
            data = None # This will trigger the "Waiting for data" screen instead of a crash
            
        return render_template("index.html", data=data)
    except Exception as e:
        logging.error(f"Error: {e}")
        # Show the error on screen instead of a blackout
        return f"Database Connection Error: {e}", 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
