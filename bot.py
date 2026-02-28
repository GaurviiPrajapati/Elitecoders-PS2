# bot.py

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

from sme_engine import SMEEngine
from agent import AgentFactory

logging.basicConfig(
    filename="bot.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

AVAILABLE_DOMAINS = {
    "legal_compliance": "domains/legal_compliance.json",
    "financial_analysis": "domains/financial_analysis.json",
    "cybersecurity": "domains/cybersecurity.json",
    "general": "domains/general.json"
}

sme_engine = SMEEngine("domains/general.json")
agent_factory = AgentFactory()

user_agents = {}

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


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_text = update.message.text

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )

    try:
        llm = agent_factory.llm
        detected_domain = classify_domain(user_text, llm)

        # Recreate agent if domain changed
        if user_id not in user_agents:
            sme_engine.switch_domain(AVAILABLE_DOMAINS[detected_domain])
            system_prompt = sme_engine.build_system_prompt()
            agent = agent_factory.create_agent(system_prompt)
            user_agents[user_id] = {
                "agent": agent,
                "domain": detected_domain
            }
        else:
            if user_agents[user_id]["domain"] != detected_domain:
                sme_engine.switch_domain(AVAILABLE_DOMAINS[detected_domain])
                system_prompt = sme_engine.build_system_prompt()
                agent = agent_factory.create_agent(system_prompt)
                user_agents[user_id] = {
                    "agent": agent,
                    "domain": detected_domain
                }

        agent = user_agents[user_id]["agent"]

        response = agent.invoke(
            {"input": user_text},
            config={"configurable": {"session_id": str(user_id)}}
        )

        reply = response["output"]

    except Exception as e:
        reply = f"⚠️ Error: {str(e)}"
        logging.error(str(e))

    await update.message.reply_text(reply)


def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Clean SME Agent running...")
    app.run_polling()


if __name__ == "__main__":
    main()