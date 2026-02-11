# ============================================
# JEEVIKA PRO – Clinical Intelligent Engine v7
# Stable • Smart Emotional Engine • Production Ready
# ============================================

import requests
import os
from datetime import datetime

# ============================================
# SAFE TEXTBLOB IMPORT
# ============================================

try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except:
    TEXTBLOB_AVAILABLE = False


HF_API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-large"
HF_API_KEY = os.environ.get("HF_API_KEY")
HEADERS = {"Authorization": f"Bearer {HF_API_KEY}"} if HF_API_KEY else {}


# ============================================
# 🧠 MEMORY INITIALIZER
# ============================================

def initialize_memory(memory):

    if not memory:
        memory = {}

    defaults = {
        "symptoms": [],
        "symptom_timeline": [],
        "pcos_score": 0,
        "pain_score": 0,
        "iron_score": 0,
        "estrogen_percent": 0.0,
        "progesterone_percent": 0.0,
        "emotional_depth_level": 0,
        "last_topic": None,
        "sentiment_history": [],
        "clinical_risk_level": "LOW"
    }

    for key, value in defaults.items():
        if key not in memory or memory[key] is None:
            memory[key] = [] if isinstance(value, list) else value

    return memory


# ============================================
# 📊 SENTIMENT ENGINE
# ============================================

def sentiment_engine(memory, text):

    polarity = 0

    if TEXTBLOB_AVAILABLE:
        try:
            polarity = TextBlob(text).sentiment.polarity
        except:
            polarity = 0

    memory["sentiment_history"].append(round(polarity, 3))
    memory["sentiment_history"] = memory["sentiment_history"][-50:]

    return memory


# ============================================
# 🚨 CRISIS DETECTION
# ============================================

def crisis_detection(text):
    text = text.lower()

    crisis_words = [
        "kill myself", "suicide",
        "end my life", "self harm",
        "i want to die"
    ]

    if any(w in text for w in crisis_words):
        return (
            "I’m really concerned about you 🤍\n\n"
            "You deserve immediate support.\n"
            "India: 📞 9152987821 (Kiran Mental Health Helpline)\n"
            "Please reach out right now."
        )

    return None


# ============================================
# 🩺 RED FLAG DETECTION
# ============================================

def red_flag_detection(text):
    text = text.lower()

    red_flags = [
        "sharp right lower pain",
        "severe one sided pelvic pain",
        "sudden severe abdominal pain",
        "fainting with pain",
        "vomiting with severe pain"
    ]

    if any(r in text for r in red_flags):
        return (
            "⚠️ This may require urgent medical care.\n"
            "Please seek emergency attention immediately."
        )

    return None


# ============================================
# 📈 PAIN ENGINE
# ============================================

def pain_engine(memory, text):
    text = text.lower()

    levels = {
        "unbearable": 9,
        "very severe": 8,
        "severe": 7,
        "moderate": 5,
        "mild": 3
    }

    for word, score in levels.items():
        if word in text:
            memory["pain_score"] = max(memory["pain_score"], score)

    return memory


# ============================================
# 📊 PCOS ENGINE
# ============================================

def update_pcos(memory, text):
    text = text.lower()

    symptom_map = {
        "irregular periods": 2,
        "missed period": 2,
        "hair fall": 1,
        "acne": 1,
        "weight gain": 1,
        "belly fat": 1,
        "mood swings": 1
    }

    for symptom, value in symptom_map.items():
        if symptom in text and symptom not in memory["symptoms"]:

            memory["symptoms"].append(symptom)
            memory["pcos_score"] += value

            memory["symptom_timeline"].append({
                "symptom": symptom,
                "timestamp": datetime.utcnow().isoformat()
            })

    memory["symptom_timeline"] = memory["symptom_timeline"][-50:]

    return memory


def evaluate_pcos(score):
    if score >= 5:
        return "HIGH"
    elif score >= 3:
        return "MODERATE"
    return "LOW"


# ============================================
# 🧬 IRON ENGINE
# ============================================

def iron_engine(memory, text):
    text = text.lower()

    iron_symptoms = [
        "fatigue",
        "tired all the time",
        "pale skin",
        "dizziness"
    ]

    for s in iron_symptoms:
        if s in text:
            memory["iron_score"] = min(memory["iron_score"] + 1, 5)

    if memory["iron_score"] >= 3:
        return (
            "Your symptoms may suggest possible iron deficiency 🤍\n"
            "Consider checking hemoglobin and ferritin levels."
        )

    return None


# ============================================
# 🧬 HORMONE PROBABILITY
# ============================================

def hormone_probability(memory):

    estrogen = 0
    progesterone = 0
    s = memory["symptoms"]

    if "weight gain" in s: estrogen += 2
    if "belly fat" in s: estrogen += 2
    if "acne" in s: estrogen += 1

    if "irregular periods" in s: progesterone += 2
    if "mood swings" in s: progesterone += 1

    total = estrogen + progesterone

    if total == 0:
        memory["estrogen_percent"] = 0.0
        memory["progesterone_percent"] = 0.0
    else:
        memory["estrogen_percent"] = round((estrogen / total) * 100, 1)
        memory["progesterone_percent"] = round((progesterone / total) * 100, 1)

    return memory


# ============================================
# 🏥 CLINICAL RISK
# ============================================

def clinical_risk(memory):

    score = (
        memory["pcos_score"] * 2 +
        memory["pain_score"] +
        memory["iron_score"]
    )

    if score >= 15:
        memory["clinical_risk_level"] = "HIGH"
    elif score >= 8:
        memory["clinical_risk_level"] = "MODERATE"
    else:
        memory["clinical_risk_level"] = "LOW"

    return memory


# ============================================
# 🧠 THERAPIST DEEPENING (UPGRADED)
# ============================================

def therapist_deepening(memory, text):

    text = text.lower()

    if memory["emotional_depth_level"] < 10:
        memory["emotional_depth_level"] += 1

    if "stress" in text or "stressed" in text:
        memory["last_topic"] = "stress"
        return "Stress can feel overwhelming 🤍 What’s causing the most pressure right now?"

    if "anxiety" in text or "anxious" in text:
        memory["last_topic"] = "anxiety"
        return "Anxiety can make everything feel urgent 🤍 What thoughts are racing?"

    if "alone" in text or "lonely" in text:
        memory["last_topic"] = "lonely"
        return "Feeling alone can feel heavy 🤍 What feels most isolating right now?"

    if "sad" in text:
        memory["last_topic"] = "sad"
        return "What thought keeps replaying when you feel this sadness?"

    if memory["emotional_depth_level"] >= 4 and memory["last_topic"]:
        return (
            "Let’s gently question that belief 🤍\n"
            "What evidence supports it — and what challenges it?"
        )

    return None


# ============================================
# 🤖 HF AI FALLBACK
# ============================================

def hf_reply(user_input):

    if not HF_API_KEY:
        return (
            "I'm here with you 🤍\n\n"
            "Can you tell me a little more about what you're experiencing?"
        )

    prompt = (
        "You are JEEVIKA, a calm, empathetic women's health AI.\n"
        "Be supportive, short, and human.\n\n"
        f"User: {user_input}"
    )

    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 120, "temperature": 0.6}
    }

    try:
        response = requests.post(
            HF_API_URL,
            headers=HEADERS,
            json=payload,
            timeout=30
        )
        result = response.json()

        if isinstance(result, list) and "generated_text" in result[0]:
            return result[0]["generated_text"].strip()

    except:
        pass

    return "Tell me more about that 🤍"


# ============================================
# 🌿 MAIN ROUTER
# ============================================

def get_jeevika_response(user_input, memory):

    memory = initialize_memory(memory)

    memory = sentiment_engine(memory, user_input)

    crisis = crisis_detection(user_input)
    if crisis:
        return crisis, memory

    emergency = red_flag_detection(user_input)
    if emergency:
        return emergency, memory

    memory = pain_engine(memory, user_input)
    if memory["pain_score"] >= 8:
        return "That pain sounds severe 🤍 Please seek urgent care.", memory

    memory = update_pcos(memory, user_input)

    iron = iron_engine(memory, user_input)
    if iron:
        return iron, memory

    memory = hormone_probability(memory)
    memory = clinical_risk(memory)

    emotional = therapist_deepening(memory, user_input)
    if emotional:
        return emotional, memory

    if memory["pcos_score"] >= 3:
        return (
            f"PCOS Risk: {evaluate_pcos(memory['pcos_score'])}\n\n"
            f"Estrogen: {memory['estrogen_percent']}%\n"
            f"Progesterone: {memory['progesterone_percent']}%\n\n"
            f"Clinical Risk: {memory['clinical_risk_level']}\n\n"
            "Would you like a structured hormone-support plan?"
        ), memory

    return hf_reply(user_input), memory
