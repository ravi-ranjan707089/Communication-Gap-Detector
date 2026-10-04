from flask import Flask, request, jsonify, render_template
from analyzer import analyze_conversation

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():

    data = request.get_json()

    if not data or "conversation" not in data:
        return jsonify({
            "error": "Conversation text is required."
        }), 400

    conversation = data["conversation"]

    if not conversation.strip():
        return jsonify({
            "error": "Conversation cannot be empty."
        }), 400

    result = analyze_conversation(conversation)

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True, port=5001)