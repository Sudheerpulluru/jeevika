# ============================================
# JEEVIKA – Intelligent Women Health System
# Context Memory + PCOS Scoring + Hormone Engine
# ============================================

import requests
import os

# ============================================
# 🔐 Hugging Face Configuration
# ============================================

HF_API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-large"
HF_API_KEY = os.environ.get("HF_API_KEY")

HEADERS = {}
if HF_API_KEY:
    HEADERS = {"Authorization": f"Bearer {HF_API_KEY}"}

# ============================================
# 🧠 SIMPLE SESSION CONTEXT MEMORY
# (Works safely with Flask session later)
# ============================================

user_context = {
    "symptoms": set(),
    "emotional_state": None,
    "pcos_score": 0
}

# ============================================
# 🚨 CRISIS DETECTION (TOP PRIORITY)
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
            "Please seek immediate support.\n"
            "India: 📞 9152987821 (Kiran Mental Health Helpline)\n"
            "You matter more than you know."
        )

    return None


# ============================================
# 🔥 GREETING HANDLER
# ============================================

def greeting_handler(text):
    text = text.lower()

    if any(w in text for w in ["hi", "hello", "hey", "hii", "heyy"]):
        return "Hi 🤍 I’m here with you. What’s been on your mind lately?"

    if len(text.strip()) <= 3:
        return "I’m here 🤍 Tell me what’s going on."

    return None


# ============================================
# 📊 PCOS SYMPTOM SCORING SYSTEM
# ============================================

def update_pcos_score(text):
    text = text.lower()
    score = 0

    symptom_map = {
        "irregular": 2,
        "missed period": 2,
        "hair fall": 1,
        "hair loss": 1,
        "weight gain": 1,
        "belly fat": 1,
        "acne": 1,
        "mood swings": 1
    }

    for symptom, value in symptom_map.items():
        if symptom in text:
            user_context["symptoms"].add(symptom)
            score += value

    user_context["pcos_score"] += score
    return user_context["pcos_score"]


def evaluate_pcos_risk(score):
    if score >= 4:
        return "HIGH"
    elif score >= 2:
        return "MODERATE"
    else:
        return "LOW"


# ============================================
# 🧬 HORMONE PATTERN ENGINE
# ============================================

def hormone_pattern_analysis():
    symptoms = user_context["symptoms"]

    if "weight gain" in symptoms and "irregular" in symptoms:
        return "This may reflect an insulin resistance pattern 🤍"

    if "mood swings" in symptoms and "irregular" in symptoms:
        return "This may reflect progesterone imbalance 🤍"

    if "hair fall" in symptoms and "acne" in symptoms:
        return "This may reflect androgen excess pattern 🤍"

    return None


# ============================================
# 🌙 CYCLE PHASE INTELLIGENCE
# ============================================

def cycle_phase_guidance(text):
    text = text.lower()

    if "cycle day" in text:
        digits = ''.join(filter(str.isdigit, text))
        if digits:
            day = int(digits)

            if 1 <= day <= 5:
                return "🌊 Menstrual Phase — Prioritize rest, iron-rich foods, and warmth 🤍"

            elif 6 <= day <= 13:
                return "🌱 Follicular Phase — Energy may rise. Great time for new plans 🌸"

            elif 14 <= day <= 16:
                return "🌼 Ovulation Phase — Communication and confidence may peak 🤍"

            elif 17 <= day <= 28:
                return "🍂 Luteal Phase — Reduce caffeine, add magnesium, protect energy 🌿"

    return None


# ============================================
# 💬 THERAPIST-STYLE FLOW
# ============================================

def therapist_flow(text):
    text = text.lower()

    if "alone" in text or "lonely" in text:
        user_context["emotional_state"] = "lonely"
        return (
            "Feeling alone can feel deeply heavy 🤍\n"
            "Is it emotional loneliness or lack of support around you?"
        )

    if "sad" in text or "depressed" in text:
        user_context["emotional_state"] = "sad"
        return (
            "I hear that sadness 🤍\n"
            "What has been weighing on you the most lately?"
        )

    if "anxious" in text or "stressed" in text:
        user_context["emotional_state"] = "anxious"
        return (
            "It sounds like your nervous system is overloaded 🤍\n"
            "What feels most out of control right now?"
        )

    if "hate my body" in text or "feel ugly" in text:
        return (
            "Body image struggles can hurt deeply 🤍\n"
            "When did you start feeling this way about yourself?"
        )

    return None


# ============================================
# 🥗 SMART DIET ROUTER
# ============================================

def diet_mode(text):
    if "diet" in text.lower():
        return (
            "Before suggesting anything 🤍\n"
            "What is your main goal?\n\n"
            "• PCOS management\n"
            "• Weight loss\n"
            "• Energy improvement\n"
            "• Hormone balance\n\n"
            "Tell me your goal."
        )
    return None


# ============================================
# 🤖 HUGGING FACE FALLBACK
# ============================================

def hf_reply(user_input):

    if not HF_API_KEY:
        return (
            "I want to understand better 🤍\n"
            "Can you describe your symptoms in a bit more detail?"
        )

    payload = {
        "inputs": f"Respond with empathy and women’s health awareness: {user_input}",
        "parameters": {
            "max_new_tokens": 120,
            "temperature": 0.6
        }
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

    except Exception:
        pass

    return "Tell me a little more 🤍"


# ============================================
# 🌿 MAIN ROUTER
# ============================================

def get_jeevika_response(user_input):

    # 1️⃣ Crisis first
    crisis = crisis_detection(user_input)
    if crisis:
        return crisis

    # 2️⃣ Greeting
    greet = greeting_handler(user_input)
    if greet:
        return greet

    # 3️⃣ Update PCOS score
    score = update_pcos_score(user_input)
    if score > 0:
        risk = evaluate_pcos_risk(score)
        hormone = hormone_pattern_analysis()

        response = (
            f"Based on what you're describing 🤍\n"
            f"PCOS Risk Level: {risk}\n\n"
        )

        if hormone:
            response += hormone + "\n\n"

        response += "Would you like a structured plan to improve this?"
        return response

    # 4️⃣ Cycle phase
    cycle = cycle_phase_guidance(user_input)
    if cycle:
        return cycle

    # 5️⃣ Therapist mode
    emotional = therapist_flow(user_input)
    if emotional:
        return emotional

    # 6️⃣ Diet
    diet = diet_mode(user_input)
    if diet:
        return diet

    # 7️⃣ HF fallback
    return hf_reply(user_input)
