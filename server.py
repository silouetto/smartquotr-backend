# server.py
from flask import Flask, request, jsonify, send_from_directory
import requests
import os

app = Flask(__name__, static_folder="www")
UPLOAD_FOLDER = os.path.join(app.static_folder, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/")
def serve_index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory(app.static_folder, path)

@app.route("/pdf/<pdf_id>")
def proxy_pdf(pdf_id):
    try:
        # Proxy to FastAPI
        resp = requests.get(f"https://localhost:8000/pdf/{pdf_id}", stream=True)
        return (resp.content, resp.status_code, resp.headers.items())
    except Exception as e:
        print("❌ PDF proxy error:", e)
        return "PDF not found", 404


@app.route("/steps", methods=["POST"])
def proxy_steps():
    try:
        resp = requests.post("https://localhost:8000/steps", json=request.get_json())
        return jsonify(resp.json())
    except Exception as e:
        print("❌ Steps proxy error:", e)
        return jsonify(error="Failed to get steps"), 500

@app.route("/helpbot", methods=["POST"])
def proxy_helpbot():
    try:
        # 🔁 Forward the JSON to FastAPI /helpbot
        resp = requests.post("https://localhost:8000/helpbot", json=request.get_json())
        return jsonify(resp.json())
    except Exception as e:
        print("❌ HelpBot proxy error:", e)
        return jsonify(error="HelpBot unavailable"), 500


@app.route("/analyze", methods=["POST"])
def proxy_analyze():
    if "file" not in request.files:
        return jsonify(error="Missing image file"), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify(error="No selected file"), 400

    # Forward form and file to FastAPI
    form_data = {
        "intent": request.form.get("intent", ""),
        "description": request.form.get("description", ""),
        "project_type": request.form.get("project_type", ""),
        "steps": request.form.get("steps", "off"),
        "include_sketch": request.form.get("include_sketch", "off"),
        "include_coupons": request.form.get("include_coupons", "off")
    }

    files = {
        "file": (file.filename, file.stream, file.mimetype)
    }

    try:
        # 🔁 Forward to FastAPI at localhost:8000
        response = requests.post("https://localhost:8000/analyze", data=form_data, files=files)
        return jsonify(response.json())
    except Exception as e:
        print("❌ Error proxying to FastAPI:", e)
        return jsonify(error="Server proxy error"), 500

if __name__ == "__main__":
    app.run(debug=True)

