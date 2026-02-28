import os
import logging
import json
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    filters,
    ContextTypes,
)
from telegram.constants import ChatAction
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
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
# Governance Rules for Anti-Jailbreak Protection
# ==============================
def load_governance_rules():
    """Load governance rules from security/governance_rules.json"""
    try:
        with open("security/governance_rules.json", "r") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Failed to load governance rules: {str(e)}")
        return {
            "override_triggers": [],
            "response_message": "🛡 Governance Override Attempt Detected.\nRequest denied.",
            "log_severity": "HIGH"
        }

governance_rules = load_governance_rules()
OVERRIDE_TRIGGERS = governance_rules.get("override_triggers", [])
GOVERNANCE_RESPONSE = governance_rules.get("response_message", "🛡 Governance Override Attempt Detected.\nRequest denied.")

# ==============================
# Environment Variables
# ==============================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    raise ValueError("Missing TELEGRAM_TOKEN or GEMINI_API_KEY.")

# ==============================
# LangChain LLM Client
# ==============================
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=GEMINI_API_KEY
)

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
# Anti-Jailbreak Protection
# ==============================
def check_override_attempt(user_text):
    """
    Check if user is attempting to override or jailbreak the governance.
    
    Returns: (is_override, trigger_found)
    """
    user_text_lower = user_text.lower()
    
    for trigger in OVERRIDE_TRIGGERS:
        if trigger.lower() in user_text_lower:
            return True, trigger
    
    return False, None

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

    response = llm.invoke(classification_prompt)

    raw_output = response.content.strip().lower()

    # Extract valid domain from response safely
    for key in AVAILABLE_DOMAINS.keys():
        if key in raw_output:
            return key

    return "general"
# ==============================
# Commands
# ==============================
async def set_mode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if not context.args:
        await update.message.reply_text("Please specify a mode: TECHNICAL, EXECUTIVE, AUDIT, CLIENT")
        return
        
    requested_mode = context.args[0].upper()
    mode_map = {
        "TECHNICAL": "TECHNICAL MODE",
        "EXECUTIVE": "EXECUTIVE MODE",
        "AUDIT": "AUDIT MODE", 
        "CLIENT": "CLIENT SUMMARY MODE"
    }
    
    if requested_mode in mode_map:
        mode_full = mode_map[requested_mode]
        if user_id not in user_sessions:
            user_sessions[user_id] = {"domain": "general", "output_mode": "DEFAULT"}
        
        user_sessions[user_id]["output_mode"] = mode_full
        
        # Remove messages so it reinitializes with the new system prompt
        if "messages" in user_sessions[user_id]:
            del user_sessions[user_id]["messages"]
            
        await update.message.reply_text(f"✅ Output mode updated to: {mode_full}")
    else:
        await update.message.reply_text("❌ Invalid mode. Available: TECHNICAL, EXECUTIVE, AUDIT, CLIENT")

# ==============================
# Message Handler
# ==============================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_text = update.message.text

    logging.info(f"User {user_id}: {user_text}")

    # ==============================
    # Check for Override/Jailbreak Attempts
    # ==============================
    is_override, trigger = check_override_attempt(user_text)
    if is_override:
        logging.warning(f"🚨 SECURITY ALERT: User {user_id} attempted override with trigger: '{trigger}'")
        await update.message.reply_text(GOVERNANCE_RESPONSE)
        return

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )
    detected_domain = classify_domain(user_text)
    print(f"Detected domain: {detected_domain}")
    try:
        detected_domain = classify_domain(user_text)

        # Create new session if new user OR domain changed / missing chat
        if user_id not in user_sessions:
            user_sessions[user_id] = {"domain": detected_domain, "output_mode": "DEFAULT"}
            needs_new_chat = True
        else:
            needs_new_chat = (
                user_sessions[user_id]["domain"] != detected_domain or
                "messages" not in user_sessions[user_id]
            )
            if user_sessions[user_id]["domain"] != detected_domain:
                user_sessions[user_id]["domain"] = detected_domain

        if needs_new_chat:
            sme_engine.switch_domain(AVAILABLE_DOMAINS[detected_domain])

            # Apply the user's output mode
            current_mode = user_sessions[user_id].get("output_mode", "DEFAULT")
            sme_engine.set_output_mode(current_mode)

            system_prompt = sme_engine.build_system_prompt()
            
            user_sessions[user_id]["messages"] = [
                SystemMessage(content=system_prompt)
            ]

        messages = user_sessions[user_id]["messages"]
        messages.append(HumanMessage(content=user_text))
        
        response = llm.invoke(messages)
        messages.append(response)

        reply = getattr(response, "content", None)
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
    
    app.add_handler(CommandHandler("mode", set_mode_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 SME Telegram Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()