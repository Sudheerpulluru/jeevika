from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
from jeevika import get_jeevika_response
from models import db, bcrypt, User, ChatSession, Message, HealthData
import os
import razorpay
from datetime import datetime, timedelta

app = Flask(__name__)

# =====================================================
# 🔐 CONFIG
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
# 💳 RAZORPAY CONFIG
# =====================================================

RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET")

# Initialize Razorpay safely
razorpay_client = None
if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
    razorpay_client = razorpay.Client(
        auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)
    )

PRO_PRICE = 49900  # ₹499.00 in paise

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

        return redirect(url_for("dashboard"))

    return render_template("login.html")

# =====================================================
# 💳 CREATE RAZORPAY ORDER
# =====================================================

@app.route("/create-order", methods=["POST"])
def create_order():

    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    if not razorpay_client:
        return jsonify({"error": "Payment system not configured"}), 500

    try:
        order = razorpay_client.order.create({
            "amount": PRO_PRICE,
            "currency": "INR",
            "payment_capture": 1
        })

        return jsonify({
            "order_id": order["id"],
            "razorpay_key": RAZORPAY_KEY_ID,
            "amount": PRO_PRICE
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =====================================================
# ✅ VERIFY PAYMENT
# =====================================================

@app.route("/verify-payment", methods=["POST"])
def verify_payment():

    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    if not razorpay_client:
        return jsonify({"error": "Payment system not configured"}), 500

    data = request.json

    try:
        razorpay_client.utility.verify_payment_signature({
            "razorpay_order_id": data["razorpay_order_id"],
            "razorpay_payment_id": data["razorpay_payment_id"],
            "razorpay_signature": data["razorpay_signature"]
        })

        user = db.session.get(User, session["user_id"])

        user.plan = "PRO"
        user.subscription_status = "ACTIVE"
        user.subscription_start = datetime.utcnow()
        user.subscription_end = datetime.utcnow() + timedelta(days=30)
        user.razorpay_payment_id = data["razorpay_payment_id"]

        db.session.commit()

        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

# =====================================================
# 💬 DASHBOARD
# =====================================================

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user = db.session.get(User, session["user_id"])

    chat_session = ChatSession.query.filter_by(user_id=user.id).first()

    if not chat_session:
        chat_session = ChatSession(user_id=user.id)
        db.session.add(chat_session)
        db.session.commit()

    health = HealthData.query.filter_by(user_id=user.id).first()

    if not health:
        health = HealthData(user_id=user.id)
        db.session.add(health)
        db.session.commit()

    if request.method == "POST":

        user_input = request.form.get("message").strip()

        db.session.add(Message(
            session_id=chat_session.id,
            role="user",
            text=user_input
        ))
        db.session.commit()

        memory = {
            "symptoms": health.symptoms or [],
            "pcos_score": health.pcos_score,
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

    messages = [{
        "role": m.role,
        "text": m.text,
        "emotion": EMOJI_MAP.get(detect_simple_emotion(m.text), "🤍")
    } for m in db_messages]

    return render_template(
        "dashboard.html",
        messages=messages,
        memory=health,
        is_pro=user.is_pro(),
        razorpay_key=RAZORPAY_KEY_ID
    )

# =====================================================
# 🔓 LOGOUT
# =====================================================

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))

# =====================================================
# HEALTH CHECK
# =====================================================

@app.route("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
