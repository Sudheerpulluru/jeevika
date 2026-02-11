from flask import Flask, render_template, request, session, redirect, url_for
from jeevika import get_jeevika_response
import uuid
import os

app = Flask(__name__)

# 🔐 Production-Ready Secret Key
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev_secret_change_this")

# ======================================
# Emoji Mapping (UI Layer Only)
# ======================================
EMOJI_MAP = {
    "sad": "😔",
    "lonely": "🥺",
    "alone": "🥺",
    "heartbroken": "💔",
    "anxious": "😟",
    "stressed": "😣",
    "depressed": "😔",
    "happy": "😊",
    "calm": "😌",
    "neutral": "🤍"
}

def detect_simple_emotion(text):
    text = text.lower()
    for key in EMOJI_MAP:
        if key in text:
            return key
    return "neutral"

# ======================================
# Session-Based Message Storage
# ======================================

def initialize_session():
    if "user_id" not in session:
        session["user_id"] = str(uuid.uuid4())

    if "messages" not in session:
        session["messages"] = []

    if "emotion_log" not in session:
        session["emotion_log"] = []

def get_user_messages():
    initialize_session()
    return session["messages"]

# ======================================
# Emotional Logging (Future Analytics)
# ======================================

def log_emotion(reply_text):
    emotion = detect_simple_emotion(reply_text)

    session["emotion_log"].append({
        "emotion": emotion
    })

    session.modified = True

# ======================================
# Flask Route
# ======================================

@app.route("/", methods=["GET", "POST"])
def home():

    initialize_session()
    messages = session["messages"]

    if request.method == "POST":
        user_input = request.form.get("message", "").strip()

        if user_input:
            # Save user message
            messages.append({
                "role": "user",
                "text": user_input
            })

            # Get AI reply
            reply = get_jeevika_response(user_input)

            emotion = detect_simple_emotion(reply)

            messages.append({
                "role": "bot",
                "text": reply,
                "emotion": EMOJI_MAP.get(emotion, "🤍")
            })

            log_emotion(reply)

            session["messages"] = messages
            session.modified = True

    return render_template("index.html", messages=messages)

# ======================================
# Clear Chat Route
# ======================================

@app.route("/clear")
def clear_chat():
    session.clear()
    return redirect(url_for("home"))

# ======================================
# Health Check Route (For Deployment)
# ======================================

@app.route("/health")
def health():
    return {"status": "ok"}

# ======================================
# App Runner
# ======================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

