# bot.py

import os
import logging
import asyncio
from telegram.ext import CommandHandler
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    filters,
    ContextTypes,
)
from telegram.constants import ChatAction

from sme_engine import SMEEngine
from agent import AgentFactory

logging.basicConfig(
    filename="bot.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

if not TELEGRAM_TOKEN:
    raise ValueError("Missing TELEGRAM_TOKEN")

AVAILABLE_DOMAINS = {
    "legal_compliance": "domains/legal_compliance.json",
    "financial_analysis": "domains/financial_advisor.json",
    "cybersecurity": "domains/cybersecurity.json",
    "general": "domains/general.json"
}

sme_engine = SMEEngine("domains/general.json")
agent_factory = AgentFactory()

user_agents = {}
user_modes = {}

def classify_domain(user_text, llm):
    prompt = f"""
Classify into:
- general
- legal_compliance
- financial_analysis
- cybersecurity

Respond ONLY with domain name.

User Query:
{user_text}
"""
    response = llm.invoke(prompt)
    raw = response.content.strip().lower()

    for key in AVAILABLE_DOMAINS:
        if key in raw:
            return key

    return "general"

async def mode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    if not context.args:
        await update.message.reply_text(
            "Available modes: TECHNICAL, EXECUTIVE, AUDIT, CLIENT"
        )
        return
    
    mode = context.args[0].upper()
    
    if mode not in ["TECHNICAL", "EXECUTIVE", "AUDIT", "CLIENT"]:
        await update.message.reply_text("Invalid mode.")
        return
    
    user_modes[user_id] = mode
    
    # Reset agent to rebuild prompt
    if user_id in user_agents:
        del user_agents[user_id]
    
    await update.message.reply_text(f"Mode set to {mode}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_text = update.message.text

    # Typing indicator
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )

    try:
        llm = agent_factory.llm
        detected_domain = classify_domain(user_text, llm)

        # Create or refresh agent if needed
        if (
            user_id not in user_agents
            or user_agents[user_id]["domain"] != detected_domain
        ):
            sme_engine.switch_domain(AVAILABLE_DOMAINS[detected_domain])
            system_prompt = sme_engine.build_system_prompt()

            # Apply output mode
            mode = user_modes.get(user_id, "TECHNICAL")

            mode_instruction = {
                "TECHNICAL": "Use deep technical analysis and structured reasoning.",
                "EXECUTIVE": "Provide concise strategic summaries.",
                "AUDIT": "Focus strictly on compliance, risk, and verification.",
                "CLIENT": "Use simple, accessible language."
            }[mode]

            system_prompt = f"{system_prompt}\n\nOUTPUT MODE:\n{mode_instruction}"

            agent = agent_factory.create_agent(system_prompt)

            user_agents[user_id] = {
                "agent": agent,
                "domain": detected_domain
            }

        agent = user_agents[user_id]["agent"]
        print("Invoking agent...")
        response = agent.invoke({
            "messages": [
                {"role": "user", "content": user_text}
            ]
        })

        last_message = response["messages"][-1]

        reply = ""

        if hasattr(last_message, "content"):
            if isinstance(last_message.content, list):
                text_parts = [
                    block.get("text", "")
                    for block in last_message.content
                    if isinstance(block, dict) and block.get("type") == "text"
                ]
                reply = "\n".join(text_parts)
            else:
                reply = str(last_message.content)

        # Fallback protection
        if not reply.strip():
            reply = "⚠️ No response generated."

        # 🔒 Hard length cap for Telegram
        reply = reply[:4000]

    except Exception as e:
        reply = f"⚠️ Error: {str(e)}"
        logging.error(str(e))

    await update.message.reply_text(reply)


def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("mode", mode_command))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    print("🤖 Clean SME Agent running...")
    app.run_polling()


if __name__ == "__main__":
    main()