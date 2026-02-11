from flask import Flask, render_template, request, session, redirect, url_for, flash
from jeevika import get_jeevika_response
from models import db, bcrypt, User, ChatSession, Message, HealthData
import os

app = Flask(__name__)

# ======================================
# 🔐 PRODUCTION CONFIGURATION
# ======================================

app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev_secret_change_this")

# -----------------------------
# 🗄 DATABASE CONFIG
# -----------------------------

DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    # Render gives postgres:// — SQLAlchemy needs postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
else:
    # Local development fallback
    database_url = os.environ.get("DATABASE_URL")

if database_url:
    # Render gives postgres:// but SQLAlchemy needs postgresql://
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///jeevika.db"


app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
bcrypt.init_app(app)

with app.app_context():
    db.create_all()

# ======================================
# 🎭 EMOJI MAP
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
# 🔐 AUTH ROUTES
# ======================================

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        if not name or not email or not password:
            flash("All fields are required.", "danger")
            return render_template("register.html")

        if User.query.filter_by(email=email).first():
            flash("User already exists.", "danger")
            return render_template("register.html")

        new_user = User(name=name, email=email)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        flash("Account created successfully. Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            session.clear()
            session["user_id"] = user.id

            # Always create new chat session
            chat_session = ChatSession(user_id=user.id)
            db.session.add(chat_session)
            db.session.commit()

            session["chat_session_id"] = chat_session.id

            return redirect(url_for("home"))

        flash("Invalid email or password.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("login"))

# ======================================
# 🏠 MAIN CHAT ROUTE
# ======================================

@app.route("/", methods=["GET", "POST"])
def home():

    # Must be logged in
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = db.session.get(User, session["user_id"])

    if not user:
        session.clear()
        return redirect(url_for("login"))

    # -----------------------------
    # 🔒 SAFE CHAT SESSION
    # -----------------------------
    chat_session = None

    if "chat_session_id" in session:
        chat_session = db.session.get(ChatSession, session["chat_session_id"])

    if not chat_session:
        chat_session = ChatSession(user_id=user.id)
        db.session.add(chat_session)
        db.session.commit()
        session["chat_session_id"] = chat_session.id

    # -----------------------------
    # 🔒 SAFE HEALTH RECORD
    # -----------------------------
    health = HealthData.query.filter_by(user_id=user.id).first()

    if not health:
        health = HealthData(
            user_id=user.id,
            pcos_score=0,
            pain_score=0,
            iron_score=0,
            estrogen_percent=0.0,
            progesterone_percent=0.0,
            clinical_risk="LOW",
            symptoms=[],
            symptom_timeline=[],
            sentiment_history=[]
        )
        db.session.add(health)
        db.session.commit()

    # -----------------------------
    # 🧠 HANDLE MESSAGE
    # -----------------------------
    if request.method == "POST":

        user_input = request.form.get("message", "").strip()

        if user_input:

            # Save user message
            db.session.add(Message(
                session_id=chat_session.id,
                role="user",
                text=user_input
            ))

            # Map DB → memory
            memory = {
                "symptoms": health.symptoms or [],
                "symptom_timeline": health.symptom_timeline or [],
                "sentiment_history": health.sentiment_history or [],
                "pcos_score": health.pcos_score,
                "pain_score": health.pain_score,
                "iron_score": health.iron_score,
                "estrogen_percent": health.estrogen_percent,
                "progesterone_percent": health.progesterone_percent,
                "emotional_depth_level": 0,
                "last_topic": None,
                "clinical_risk_level": health.clinical_risk
            }

            reply, updated_memory = get_jeevika_response(user_input, memory)

            # Update health
            health.pcos_score = updated_memory.get("pcos_score", 0)
            health.pain_score = updated_memory.get("pain_score", 0)
            health.iron_score = updated_memory.get("iron_score", 0)
            health.estrogen_percent = updated_memory.get("estrogen_percent", 0.0)
            health.progesterone_percent = updated_memory.get("progesterone_percent", 0.0)
            health.clinical_risk = updated_memory.get("clinical_risk_level", "LOW")
            health.symptoms = updated_memory.get("symptoms", [])
            health.symptom_timeline = updated_memory.get("symptom_timeline", [])
            health.sentiment_history = updated_memory.get("sentiment_history", [])

            db.session.commit()

            # Save bot reply
            db.session.add(Message(
                session_id=chat_session.id,
                role="bot",
                text=reply
            ))

            db.session.commit()

    # -----------------------------
    # 📩 FETCH MESSAGES
    # -----------------------------
    db_messages = Message.query.filter_by(session_id=chat_session.id).all()

    messages = []
    for m in db_messages:
        emotion = detect_simple_emotion(m.text)
        messages.append({
            "role": m.role,
            "text": m.text,
            "emotion": EMOJI_MAP.get(emotion, "🤍")
        })

    return render_template(
        "index.html",
        messages=messages,
        memory=health,
        sentiment=health.sentiment_history or [],
        timeline=health.symptom_timeline or []
    )

# ======================================
# 🗑 CLEAR CHAT
# ======================================

@app.route("/clear")
def clear_chat():
    if "chat_session_id" in session:
        Message.query.filter_by(
            session_id=session["chat_session_id"]
        ).delete()
        db.session.commit()

    flash("Chat cleared.", "success")
    return redirect(url_for("home"))

# ======================================
# 🏥 HEALTH CHECK
# ======================================

@app.route("/health")
def health_check():
    return {"status": "ok"}

# ======================================
# RUN
# ======================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
