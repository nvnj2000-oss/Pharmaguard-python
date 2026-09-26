"""
flask_app.py
------------
A VERY simple Flask API for PharmaGuard.

What it does:
- Has one endpoint: /analyze
- You POST a CSV file to it
- It runs the same analysis.py pipeline used by Streamlit
- It returns the results as JSON

Why Flask is here:
This is just to demonstrate how a backend API works separately from
the website (Streamlit). In a real company, Flask might run on a
server and many different apps (mobile, web, etc.) could all send
data to it and get JSON back. Streamlit does NOT need this file to
run - it works fine on its own using analysis.py directly.

How to run:
    python flask_app.py

Then test it (in a NEW terminal window) with:
    curl -X POST -F "file=@medicines.csv" http://127.0.0.1:5000/analyze
"""

from flask import Flask, request, jsonify
from analysis import load_data, process_dataframe, get_dashboard_summary

app = Flask(__name__)


@app.route("/")
def home():
    return "PharmaGuard Flask API is running. POST a CSV file to /analyze."


@app.route("/analyze", methods=["POST"])
def analyze():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded. Use form field name 'file'."}), 400

    file = request.files["file"]
    df = load_data(file)
    df = process_dataframe(df)
    summary = get_dashboard_summary(df)

    return jsonify({
        "summary": summary,
        "medicines": df.to_dict(orient="records")
    })


if __name__ == "__main__":
    app.run(debug=True)
