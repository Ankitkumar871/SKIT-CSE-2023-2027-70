from flask import Flask, render_template, request, jsonify
from chatbot.engine import ChatbotEngine
from database import (
    initialize_database,
    save_conversation,
    get_conversations,
    save_feedback,
    get_statistics,
    clear_conversations
)

app = Flask(__name__)

engine = ChatbotEngine.from_file("chatbot/intents.json")

initialize_database()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}

    message = str(data.get("message", "")).strip()

    if not message:
        return jsonify({
            "success": False,
            "error": "Please enter a message."
        }), 400

    result = engine.reply(message)

    language = detect_language(message)

    conversation_id = save_conversation(
        user_message=message,
        bot_response=result["reply"],
        source=result.get("source", "unknown"),
        tag=result.get("tag", "unknown"),
        confidence=result.get("confidence", 0),
        language=language
    )

    return jsonify({
        "success": True,
        "id": conversation_id,
        "reply": result["reply"],
        "source": result.get("source"),
        "tag": result.get("tag"),
        "confidence": result.get("confidence"),
        "language": language
    })


@app.route("/api/history", methods=["GET"])
def history():
    limit = request.args.get("limit", 20, type=int)
    limit = max(1, min(limit, 100))

    return jsonify({
        "success": True,
        "count": len(get_conversations(limit)),
        "history": get_conversations(limit)
    })


@app.route("/api/feedback", methods=["POST"])
def feedback():
    data = request.get_json(silent=True) or {}

    conversation_id = data.get("conversation_id")
    value = data.get("feedback")

    if not conversation_id:
        return jsonify({
            "success": False,
            "error": "Conversation ID is required."
        }), 400

    if value not in [0, 1]:
        return jsonify({
            "success": False,
            "error": "Feedback must be 0 or 1."
        }), 400

    if not save_feedback(conversation_id, value):
        return jsonify({
            "success": False,
            "error": "Conversation not found."
        }), 404

    return jsonify({
        "success": True,
        "message": "Feedback saved."
    })


@app.route("/api/statistics", methods=["GET"])
def statistics():
    return jsonify({
        "success": True,
        "statistics": get_statistics()
    })


@app.route("/api/history/clear", methods=["DELETE"])
def clear_history():
    clear_conversations()

    return jsonify({
        "success": True,
        "message": "Conversation history cleared."
    })


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "online",
        "service": "AI Linguistic Chatbot",
        "chatbot": "ready"
    })


def detect_language(message):
    text = message.lower()

    hindi_chars = sum(
        "\u0900" <= char <= "\u097f"
        for char in message
    )

    if hindi_chars > 0:
        return "Hindi"

    spanish_words = {
        "hola", "gracias", "cómo", "que", "qué", "por", "favor"
    }

    french_words = {
        "bonjour", "merci", "comment", "avec", "pour"
    }

    german_words = {
        "hallo", "danke", "wie", "und", "bitte"
    }

    tokens = set(text.split())

    if tokens & spanish_words:
        return "Spanish"

    if tokens & french_words:
        return "French"

    if tokens & german_words:
        return "German"

    return "English"


if __name__ == "__main__":
    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )