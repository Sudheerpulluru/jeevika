from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
from jeevika import get_jeevika_response
from models import db, bcrypt, User, ChatSession, Message, HealthData
import os
import stripe

app = Flask(__name__)

# =====================================================
# 🔐 PRODUCTION CONFIGURATION
# =====================================================

app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev_secret_change_this")

database_url = os.environ.get("DATABASE_URL")

if database_url:
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

# =====================================================
# 💳 STRIPE CONFIG
# =====================================================

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
STRIPE_PUBLIC_KEY = os.environ.get("STRIPE_PUBLIC_KEY")
STRIPE_PRICE_ID = os.environ.get("STRIPE_PRICE_ID")

# =====================================================
# 🎭 EMOJI MAP
# =====================================================

EMOJI_MAP = {
    "sad": "😔",
    "lonely": "🥺",
    "alone": "🥺",
    "heartbroken": "💔",
    "anxious": "😟",
    "stress": "😣",
    "stressed": "😣",
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

# =====================================================
# 🏠 LANDING
# =====================================================

@app.route("/")
def landing():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("landing.html")

# =====================================================
# 🔐 REGISTER
# =====================================================

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
            flash("Account already exists.", "danger")
            return render_template("register.html")

        new_user = User(name=name, email=email)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        flash("Account created successfully. Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

# =====================================================
# 🔐 LOGIN
# =====================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if not user:
            flash("No account found with this email.", "danger")
            return render_template("login.html")

        if not user.check_password(password):
            flash("Incorrect password.", "danger")
            return render_template("login.html")

        session.clear()
        session["user_id"] = user.id

        chat_session = ChatSession(user_id=user.id)
        db.session.add(chat_session)
        db.session.commit()

        session["chat_session_id"] = chat_session.id

        return redirect(url_for("dashboard"))

    return render_template("login.html")

# =====================================================
# 💳 STRIPE CHECKOUT
# =====================================================

@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():

    if "user_id" not in session:
        return redirect(url_for("login"))

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="subscription",
            line_items=[{
                "price": STRIPE_PRICE_ID,
                "quantity": 1,
            }],
            success_url=url_for("payment_success", _external=True),
            cancel_url=url_for("dashboard", _external=True),
        )

        return redirect(checkout_session.url)

    except Exception as e:
        return str(e)

# =====================================================
# ✅ PAYMENT SUCCESS
# =====================================================

@app.route("/payment-success")
def payment_success():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user = db.session.get(User, session["user_id"])

    # Mark user as premium
    user.verified = True  # using verified as premium flag
    db.session.commit()

    flash("🎉 You are now a Premium Member!", "success")

    return redirect(url_for("dashboard"))

# =====================================================
# 🔓 LOGOUT
# =====================================================

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))

# =====================================================
# 💬 DASHBOARD
# =====================================================

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user = db.session.get(User, session["user_id"])

    if not user:
        session.clear()
        return redirect(url_for("login"))

    chat_session = None

    if "chat_session_id" in session:
        chat_session = db.session.get(ChatSession, session["chat_session_id"])

    if not chat_session:
        chat_session = ChatSession(user_id=user.id)
        db.session.add(chat_session)
        db.session.commit()
        session["chat_session_id"] = chat_session.id

    health = HealthData.query.filter_by(user_id=user.id).first()

    if not health:
        health = HealthData(user_id=user.id)
        db.session.add(health)
        db.session.commit()

    # MESSAGE HANDLING
    if request.method == "POST":

        user_input = request.form.get("message", "").strip()

        if user_input:

            db.session.add(Message(
                session_id=chat_session.id,
                role="user",
                text=user_input
            ))
            db.session.commit()

            memory = {
                "symptoms": health.symptoms or [],
                "symptom_timeline": health.symptom_timeline or [],
                "sentiment_history": health.sentiment_history or [],
                "pcos_score": health.pcos_score,
                "pain_score": health.pain_score,
                "iron_score": health.iron_score,
                "estrogen_percent": health.estrogen_percent,
                "progesterone_percent": health.progesterone_percent,
                "clinical_risk_level": health.clinical_risk
            }

            reply, updated_memory = get_jeevika_response(user_input, memory)

            health.pcos_score = updated_memory.get("pcos_score", 0)
            health.clinical_risk = updated_memory.get("clinical_risk_level", "LOW")
            db.session.commit()

            db.session.add(Message(
                session_id=chat_session.id,
                role="bot",
                text=reply
            ))
            db.session.commit()

        return redirect(url_for("dashboard"))

    db_messages = Message.query.filter_by(
        session_id=chat_session.id
    ).order_by(Message.id.asc()).all()

    messages = []

    for m in db_messages:
        emotion = detect_simple_emotion(m.text)
        messages.append({
            "role": m.role,
            "text": m.text,
            "emotion": EMOJI_MAP.get(emotion, "🤍")
        })

    return render_template(
        "dashboard.html",
        messages=messages,
        memory=health,
        is_premium=user.verified,
        stripe_public_key=STRIPE_PUBLIC_KEY
    )

# =====================================================
# 🗑 CLEAR CHAT
# =====================================================

@app.route("/clear")
def clear_chat():
    if "chat_session_id" in session:
        Message.query.filter_by(
            session_id=session["chat_session_id"]
        ).delete()
        db.session.commit()

    return redirect(url_for("dashboard"))

# =====================================================
# 🏥 HEALTH CHECK
# =====================================================

@app.route("/health")
def health_check():
    return {"status": "ok"}

# =====================================================
# RUN
# =====================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
