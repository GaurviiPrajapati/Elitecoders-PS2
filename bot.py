import os
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    filters,
    ContextTypes,
)
from telegram.constants import ChatAction
from google import genai
from sme_engine import SMEEngine

# ==============================
# Logging
# ==============================
logging.basicConfig(
    filename="bot.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ==============================
# Environment Variables
# ==============================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    raise ValueError("Missing TELEGRAM_TOKEN or GEMINI_API_KEY.")

# ==============================
# Gemini Client
# ==============================
client = genai.Client(api_key=GEMINI_API_KEY)

# ==============================
# Domain Setup
# ==============================
AVAILABLE_DOMAINS = {
    "structural_engineer": "domains/structural_engineer.json",
    "legal_analyst": "domains/legal_analyst.json",
    "financial_advisor": "domains/financial_advisor.json",
    "cybersecurity": "domains/cybersecurity.json",
    "medical_advisory": "domains/medical_advisory.json",
    "software_architecture": "domains/software_architecture.json",
    "general": "domains/general.json"
}

# Default SME engine
sme_engine = SMEEngine("domains/general.json")

# Store user sessions
user_sessions = {}

MAX_LENGTH = 4000

# ==============================
# Domain Classifier
# ============================== 
def classify_domain(user_text):
    classification_prompt = f"""
Classify the following user query into one of these domains:

- general
- structural_engineer
- legal_analyst
- financial_advisor
- cybersecurity
- medical_advisory
- software_architecture

Rules:
- Greetings, casual talk, or unclear queries → general
- Only choose a specialized domain if the query clearly requires domain expertise.

Respond with ONLY the domain name.

User Query:
{user_text}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=classification_prompt
    )

    raw_output = response.text.strip().lower()

    # Extract valid domain from response safely
    for key in AVAILABLE_DOMAINS.keys():
        if key in raw_output:
            return key

    return "general"
# ==============================
# Message Handler
# ==============================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_text = update.message.text

    logging.info(f"User {user_id}: {user_text}")

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )
    detected_domain = classify_domain(user_text)
    print(f"Detected domain: {detected_domain}")
    try:
        detected_domain = classify_domain(user_text)

        # Create new session if new user OR domain changed
        if (
            user_id not in user_sessions or
            user_sessions[user_id]["domain"] != detected_domain
        ):
            sme_engine.switch_domain(AVAILABLE_DOMAINS[detected_domain])

            chat = client.chats.create(
                model="gemini-2.5-flash"
            )

            system_prompt = sme_engine.build_system_prompt()
            chat.send_message(system_prompt)

            user_sessions[user_id] = {
                "chat": chat,
                "domain": detected_domain
            }

        chat_session = user_sessions[user_id]["chat"]

        response = chat_session.send_message(user_text)

        reply = getattr(response, "text", None)
        if not reply:
            reply = str(response)

    except Exception as e:
        reply = f"⚠️ Error: {str(e)}"
        logging.error(f"Error for user {user_id}: {str(e)}")

    logging.info(f"Bot response to {user_id}: {reply}")

    for i in range(0, len(reply), MAX_LENGTH):
        await update.message.reply_text(reply[i:i + MAX_LENGTH])

# ==============================
# Main
# ==============================
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 SME Telegram Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()