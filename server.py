
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from openai import OpenAI
import os
from dotenv import load_dotenv
import hashlib
from pathlib import Path
import requests

load_dotenv()

CAR_IMAGE_API_KEY = os.getenv("CAR_IMAGE_API_KEY")
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")
CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
CAR_3D_API_KEY = os.getenv("CAR_3D_API_KEY")

CACHE_DIR = Path(__file__).resolve().parent / "image-cache"
CACHE_DIR.mkdir(exist_ok=True)

app = Flask(__name__)
CORS(app)
@app.route("/3d-models/<path:filename>")
def serve_3d_model(filename):
    return send_from_directory("3d-models", filename)

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)

conversation_history = []
VERIFIED_3D_MODELS = {}
CANDIDATE_3D_MODELS = {}


@app.route("/detect-intent", methods=["POST"])
def detect_intent():
    data = request.get_json(silent=True) or {}
    question = data.get("message", "")

    if not isinstance(question, str) or not question.strip():
        return jsonify({"error": "Please enter a message"}), 400

    try:
        response = client.chat.completions.create(
            model="qwen3:4b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Classify the user's request. "
                        "Reply with exactly one word: text, image, or both. "
                        "Use text for questions requiring only an explanation. "
                        "Use image when the user only wants a picture. "
                        "Use both when the user wants an explanation and a picture. "
                        "Do not include any other words."
                    )
                },
                {
                    "role": "user",
                    "content": question
                }
            ],
            temperature=0
        )

        intent = (
            response.choices[0].message.content or ""
        ).strip().lower()

        if intent not in ("text", "image", "both"):
            intent = "text"

        return jsonify({"intent": intent})

    except Exception:
        return jsonify({"error": "Unable to detect request intent"}), 500


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    question = data.get("message", "")

    if not isinstance(question, str) or not question.strip():
        return jsonify({"error": "Please enter a question."}), 400

    try:
        response = client.chat.completions.create(
            model="qwen3:4b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional automotive AI assistant. "
                        "You specialize in BMW vehicles, engines, performance, and car comparisons. "
                        "Answer questions clearly and concisely, usually in 2-4 short paragraphs. "
                        "Do not invent horsepower, torque, engine specifications, or model years. "
                        "Distinguish between different vehicle generations, engines, and trims. "
                        "If you are unsure about a fact, clearly say so instead of guessing. "
                        "Do not claim to have personal experience or verified sources you have not accessed. "
                        "Only ask for a model year when it is necessary. "
                        "Avoid unnecessary introductions, repetition, and long tables. "
                        "Explain technical information in simple, professional language. "
                        "When a user requests an image or asks to see what a vehicle looks like, "
                        "recognize that they want a visual response. "
                        "Do not claim that you cannot display images. "
                        "Do not pretend an image was generated if it was not."
                    )
                },
                *conversation_history,
                {
                    "role": "user",
                    "content": question
                }
            ],
        )

        ai_reply = response.choices[0].message.content or ""

        conversation_history.append({
            "role": "user",
            "content": question
        })

        conversation_history.append({
            "role": "assistant",
            "content": ai_reply
        })

        conversation_history[:] = conversation_history[-10:]

        return jsonify({
            "reply": ai_reply
        })

    except Exception:
        return jsonify({"error": "Unable to connect to AI"}), 500


@app.route("/new-chat", methods=["POST"])
def new_chat():
    conversation_history.clear()
    return jsonify({"message": "Conversation cleared"})


@app.route("/car-image", methods=["GET"])
def car_image():
    make = request.args.get("make")
    model = request.args.get("model")
    year = request.args.get("year")

    if not all([make, model, year]):
        return jsonify({"error": "Missing vehicle information"}), 400

    cache_key = f"{year}-{make}-{model}-front-3-4-grey".lower()
    filename = hashlib.sha256(cache_key.encode()).hexdigest() + ".png"
    cache_path = CACHE_DIR / filename

    if cache_path.exists():
        return app.response_class(
            cache_path.read_bytes(),
            mimetype="image/png"
        )

    if not CAR_IMAGE_API_KEY:
        return jsonify({"error": "Image API key not configured"}), 500

    try:
        response = requests.get(
            "https://carimage.dev/api/v1/images/car",
            headers={
                "Authorization": f"Bearer {CAR_IMAGE_API_KEY}"
            },
            params={
                "make": make,
                "model": model,
                "year": year,
                "view": "front-3-4",
                "color": "grey"
            },
            timeout=60
        )

        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "image/png")

        if not content_type.startswith("image/"):
            return jsonify({"error": "API did not return an image"}), 502

        cache_path.write_bytes(response.content)

        return app.response_class(
            response.content,
            mimetype=content_type
        )

    except requests.RequestException:
        return jsonify({"error": "Unable to retrieve car image"}), 502


@app.route("/generate-image", methods=["POST"])
def generate_image():
    data = request.get_json(silent=True) or {}
    prompt = data.get("prompt", "")

    if not isinstance(prompt, str) or not prompt.strip():
        return jsonify({"error": "Please enter an image description"}), 400

    if not CLOUDFLARE_API_TOKEN or not CLOUDFLARE_ACCOUNT_ID:
        return jsonify({"error": "Cloudflare is not configured"}), 500

    url = (
        f"https://api.cloudflare.com/client/v4/accounts/"
        f"{CLOUDFLARE_ACCOUNT_ID}/ai/run/"
        f"@cf/black-forest-labs/flux-1-schnell"
    )

    try:
        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}"
            },
            json={"prompt": prompt},
            timeout=120
        )

        response.raise_for_status()

        image_data = response.json()["result"]["image"]

        return jsonify({
            "image": "data:image/png;base64," + image_data
        })

    except (requests.RequestException, ValueError, KeyError, TypeError):
        return jsonify({"error": "Unable to generate image"}), 502


@app.route("/search-3d-car", methods=["GET"])
def search_3d_car():
    year = request.args.get("year", "").strip()
    make = request.args.get("make", "").strip()
    model = request.args.get("model", "").strip()
    trim = request.args.get("trim", "").strip()

    if not year or not make or not model:
        return jsonify({"error": "Missing car information"}), 400

    key = (year.lower(), make.lower(), model.lower(), trim.lower())

    verified_model = VERIFIED_3D_MODELS.get(key)

    if not verified_model:
        return jsonify({
            "search": f"{year} {make} {model} {trim}".strip(),
            "models": [],
            "message": "Exact 3D model not available"
        })

    return jsonify({
        "search": f"{year} {make} {model} {trim}".strip(),
        "models": [{
            "name": verified_model["name"],
            "uid": verified_model["uid"]
        }]
    })


@app.route("/find-3d-candidates", methods=["GET"])
def find_3d_candidates():
    year = request.args.get("year", "").strip()
    make = request.args.get("make", "").strip()
    model = request.args.get("model", "").strip()

    if not year or not make or not model:
        return jsonify({"error": "Missing vehicle information"}), 400

    search_query = f"{year} {make} {model}"
    try:
        response = requests.get(
            "https://api.sketchfab.com/v3/search",
            params={
                "type": "models",
                "q": search_query,
                "count": 24,
                "downloadable": "true"
            },
            timeout=15
        )

        response.raise_for_status()
        data = response.json()

        candidates = []

        excluded_terms = [
            "gt4",
            "race",
            "racing",
            "widebody",
            "modified",
            "m2"
        ]

        for item in data.get("results", []):
            uid = item.get("uid")
            name = item.get("name", "")

            if not uid:
                continue

            license_info = item.get("license") or {}

            if isinstance(license_info, dict):
                license_name = license_info.get("label", "Unknown")
                license_slug = license_info.get("slug", "")
            else:
                license_name = "Unknown"
                license_slug = ""

            if license_name != "CC Attribution":
                continue

            name_lower = name.lower()

            if "m4" not in name_lower:
                continue

            if year not in name_lower:
                 continue
            if any(term in name_lower for term in excluded_terms):
                continue

            candidates.append({
                "name": name,
                "uid": uid,
                "viewer_url": f"https://sketchfab.com/models/{uid}/embed",
                "license": license_name,
                "license_slug": license_slug
            })

        key = (year.lower(), make.lower(), model.lower())
        CANDIDATE_3D_MODELS[key] = candidates

        return jsonify({
            "search": search_query,
            "candidates": candidates,
            "count": len(candidates)
        })

    except (requests.RequestException, ValueError):
        return jsonify({
            "error": "Unable to find 3D car candidates"
        }), 502

if __name__ == "__main__":
    app.run(debug=True, port=5001)
