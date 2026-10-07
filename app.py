from flask import Flask, render_template, request, jsonify
from chatbot.engine import ChatbotEngine

app = Flask(__name__)

engine = ChatbotEngine.from_file("chatbot/intents.json")


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"reply": "Please enter a message."})

    result = engine.reply(message)
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
