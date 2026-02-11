from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime
from sqlalchemy.dialects.sqlite import JSON

db = SQLAlchemy()
bcrypt = Bcrypt()

# ==========================================
# 👩 USER MODEL
# ==========================================

class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(200), nullable=False)
    verified = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sessions = db.relationship(
        "ChatSession",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan"
    )

    health = db.relationship(
        "HealthData",
        backref="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    # 🔐 Password Handling
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.email}>"


# ==========================================
# 💬 CHAT SESSION MODEL
# ==========================================

class ChatSession(db.Model):
    __tablename__ = "chat_session"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    messages = db.relationship(
        "Message",
        backref="session",
        lazy=True,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<ChatSession {self.id}>"


# ==========================================
# 📨 MESSAGE MODEL
# ==========================================

class Message(db.Model):
    __tablename__ = "message"

    id = db.Column(db.Integer, primary_key=True)

    session_id = db.Column(
        db.Integer,
        db.ForeignKey("chat_session.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    role = db.Column(db.String(10), nullable=False)  # user / bot
    text = db.Column(db.Text, nullable=False)

    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<Message {self.role} @ {self.timestamp}>"


# ==========================================
# 🧬 HEALTH DATA MODEL (ENTERPRISE SAFE)
# ==========================================

class HealthData(db.Model):
    __tablename__ = "health_data"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )

    # 📊 Clinical Scores
    pcos_score = db.Column(db.Integer, default=0)
    pain_score = db.Column(db.Integer, default=0)
    iron_score = db.Column(db.Integer, default=0)

    # 🧬 Hormone Percentages (Float — correct for charts)
    estrogen_percent = db.Column(db.Float, default=0.0)
    progesterone_percent = db.Column(db.Float, default=0.0)

    # 🏥 Clinical Risk
    clinical_risk = db.Column(db.String(50), default="LOW")

    # 📈 JSON Data (SAFE DEFAULT FACTORIES)
    symptoms = db.Column(JSON, default=lambda: [])
    symptom_timeline = db.Column(JSON, default=lambda: [])
    sentiment_history = db.Column(JSON, default=lambda: [])

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    def __repr__(self):
        return f"<HealthData user_id={self.user_id} risk={self.clinical_risk}>"
