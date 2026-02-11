# ============================================
# JEEVIKA – Advanced Women-Centered AI Core
# Rule-Based Intelligence + HF Enhancement
# ============================================

import requests
import os

# ============================================
# 🔐 Hugging Face Configuration (Secure)
# ============================================

HF_API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-large"
HF_API_KEY = os.environ.get("HF_API_KEY")

HEADERS = {}
if HF_API_KEY:
    HEADERS = {
        "Authorization": f"Bearer {HF_API_KEY}"
    }

# ============================================
# 🚨 CRISIS DETECTION (HIGHEST PRIORITY)
# ============================================

def crisis_detection(text):
    text = text.lower()

    crisis_words = [
        "kill myself",
        "suicide",
        "end my life",
        "self harm",
        "cut myself",
        "i don't want to live",
        "i want to die"
    ]

    if any(w in text for w in crisis_words):
        return (
            "I’m really concerned about you 🤍\n\n"
            "You deserve immediate support and care.\n"
            "If you're in danger, please contact local emergency services right now.\n\n"
            "If you're in India: Call 9152987821 (Kiran Mental Health Helpline)\n"
            "You are not alone in this."
        )

    return None


# ============================================
# 🔥 EMOTIONAL SEVERITY DETECTION
# ============================================

def detect_severity(text):
    text = text.lower()

    severe_words = ["hopeless", "worthless", "broken", "empty inside"]
    moderate_words = ["very sad", "really stressed", "crying a lot"]
    mild_words = ["sad", "tired", "low"]

    if any(w in text for w in severe_words):
        return "severe"
    elif any(w in text for w in moderate_words):
        return "moderate"
    elif any(w in text for w in mild_words):
        return "mild"

    return "normal"


# ============================================
# 🌙 CYCLE PHASE INTELLIGENCE + NUTRITION
# ============================================

def cycle_phase_guidance(text):
    text = text.lower()

    if "cycle day" in text:
        day_digits = ''.join(filter(str.isdigit, text))

        if day_digits:
            day = int(day_digits)

            if 1 <= day <= 5:
                return (
                    "🌊 Menstrual Phase\n"
                    "• Iron-rich foods (spinach, lentils)\n"
                    "• Warm meals & proper rest\n"
                    "• Gentle stretching\n\n"
                    "Your body is restoring energy 🤍"
                )

            elif 6 <= day <= 13:
                return (
                    "🌱 Follicular Phase\n"
                    "• Fresh vegetables & fermented foods\n"
                    "• Light cardio or new projects\n\n"
                    "Energy and creativity may rise 🌸"
                )

            elif 14 <= day <= 16:
                return (
                    "🌼 Ovulation Phase\n"
                    "• Antioxidants (berries, citrus)\n"
                    "• Zinc-rich foods\n\n"
                    "Confidence and communication often peak 🤍"
                )

            elif 17 <= day <= 28:
                return (
                    "🍂 Luteal Phase\n"
                    "• Magnesium-rich foods\n"
                    "• Complex carbs\n"
                    "• Reduce caffeine\n\n"
                    "Emotions may feel stronger — be gentle 🌿"
                )

    return None


# ============================================
# 🌸 PCOS MODE
# ============================================

def pcos_guidance(text):
    text = text.lower()

    if any(w in text for w in ["pcos", "polycystic", "insulin resistance"]):
        return (
            "PCOS often links to insulin resistance 🌸\n\n"
            "Diet focus:\n"
            "• High-protein meals\n"
            "• Low glycemic carbs\n"
            "• Healthy fats (nuts, seeds)\n"
            "• Reduce sugar & refined flour\n\n"
            "Lifestyle:\n"
            "• Strength training 3x/week\n"
            "• Daily walking\n"
            "• Stress regulation\n\n"
            "Would you like a simple PCOS-friendly meal plan?"
        )

    return None


# ============================================
# 💜 HORMONAL + EMOTIONAL SYNC
# ============================================

def hormonal_emotion_sync(text):
    text = text.lower()

    if any(w in text for w in ["mood swings", "pms anger", "cry before period"]):
        return (
            "Pre-period mood shifts are often progesterone-related 🤍\n\n"
            "Support ideas:\n"
            "• Magnesium-rich foods\n"
            "• Reduce caffeine\n"
            "• Gentle movement\n"
            "• Emotional journaling\n\n"
            "Would calming techniques help right now?"
        )

    return None


# ============================================
# 🌿 THERAPIST-STYLE EMOTIONAL SUPPORT
# ============================================

def emotional_support(text):
    text = text.lower()

    if any(w in text for w in ["sad", "lonely", "alone", "depressed"]):
        severity = detect_severity(text)

        if severity == "severe":
            return (
                "That sounds deeply painful 🤍\n"
                "I’m really glad you shared this.\n"
                "What feels most overwhelming right now?"
            )

        return (
            "That sounds really heavy 🤍\n"
            "When you say you're feeling this way, what feels the hardest?"
        )

    if any(w in text for w in ["cheated", "betrayed"]):
        return (
            "Being betrayed can shake your sense of safety 🤍\n"
            "What part of that hurt you the most?"
        )

    if any(w in text for w in ["anxious", "stressed", "overwhelmed"]):
        return (
            "It sounds like your nervous system is under pressure 🤍\n"
            "What feels most out of control right now?"
        )

    if any(w in text for w in ["worthless", "not enough"]):
        return (
            "I hear how painful that belief feels 🤍\n"
            "What made you start feeling that way?"
        )

    return None


# ============================================
# 🤖 HUGGING FACE FALLBACK
# ============================================

def hf_reply(user_input):

    if not HF_API_KEY:
        return "I’m here 🤍 Tell me a little more."

    payload = {
        "inputs": f"Respond with empathy and clarity: {user_input}",
        "parameters": {
            "max_new_tokens": 120,
            "temperature": 0.7
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

    return "I’m here 🤍 Tell me a little more."


# ============================================
# 🌿 MAIN ENTRY FUNCTION
# ============================================

def get_jeevika_response(user_input):

    crisis = crisis_detection(user_input)
    if crisis:
        return crisis

    cycle = cycle_phase_guidance(user_input)
    if cycle:
        return cycle

    pcos = pcos_guidance(user_input)
    if pcos:
        return pcos

    hormone = hormonal_emotion_sync(user_input)
    if hormone:
        return hormone

    emotional = emotional_support(user_input)
    if emotional:
        return emotional

    return hf_reply(user_input)
