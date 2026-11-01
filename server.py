
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)
CORS(app)

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)

conversation_history = []


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    question = data.get("message", "")

    if not isinstance(question, str) or not question.strip():
        return jsonify({"error": "Please enter a question."}), 400

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
                    "Explain technical information in simple, professional language."
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

@app.route("/new-chat", methods=["POST"])
def new_chat():
    conversation_history.clear()
    return jsonify({"message": "Conversation cleared"})

if __name__ == "__main__":
    app.run(debug=True, port=5001)
