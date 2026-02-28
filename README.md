# 🧠 Expertease

![License](https://img.shields.io/badge/license-MIT-green) 
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Telegram](https://img.shields.io/badge/telegram-bot-blue)

**Subject‑Matter‑Expert (SME) AI Assistant Suite**

A polished web UI and Telegram bot that route user questions to domain‑specific SME prompts, powered by Google’s Gemini LLM. Built with Gemini CLI, LangChain, and a splash of Auto‑GPT.

![Expertease UI](path/to/your/screenshot.png)

---

## 🚀 Features

- **Four expert domains**
  - General, Cyber‑security, Financial advisory, Legal analyst
- **Dual interface**
  - Telegram chatbot
  - Dedicated vanilla‑JS web UI (Expertease)
- **Modular JSON domains** with persona, scope, decision trees, etc.
- **Mode switching**: /mode TECHNICAL | EXECUTIVE | AUDIT | CLIENT
- **Jailbreak/security filters** from security/governance_rules.json

---

## 🗂️ Repo Structure

`
agent.py
bot.py              # Telegram bot entrypoint
sme_engine.py       # builds system prompts
tools.py

domains/
  general.json
  cybersecurity.json
  financial_advisor.json
  legal_analyst.json

logs/
  bot.log

security/
  governance_rules.json

ui/                 # frontend HTML/CSS/JS (if present)
`

---

## 🛠️ Setup & Run

### Requirements

- Python 3.10+
- Virtualenv or venv
- Env vars: TELEGRAM_TOKEN, GEMINI_API_KEY

Setting them:

**PowerShell**
`powershell
 = "<your-telegram-token>"
   = "<your-gemini-api-key>"
`

**CMD**
`cmd
set TELEGRAM_TOKEN=<your-telegram-token>
set GEMINI_API_KEY=<your-gemini-api-key>
`

### Install

`ash
python -m venv .venv
.venv\Scripts\activate
pip install python-telegram-bot google-genai
`

### Run

`ash
python bot.py
`

Access via Telegram or open the Expertease web UI (e.g., http://localhost:PORT).

---

## 🔍 How It Works

1. Incoming message → ot.py classifies domain via LLM prompt.
2. SMEEngine loads JSON & constructs system prompt.
3. Session maintained per user/domain; domain switch resets prompt.
4. Gemini API generates response; bot returns it to user.

---

## 📁 Domain JSON Example

`json
{
  "domain_name": "Cyber‑Security",
  "persona": "Seasoned infosec analyst",
  "scope": ["vulnerabilities", "threat intel"],
  "decision_tree": [...],
  "citation_rules": { "required": true, "format": "APA" },
  "output_format": { "type": "markdown" },
  "out_of_scope_response": "I'm not able to answer that."
}
`

> Add new domains by creating a JSON file in domains/ using this schema.

---

## 🧩 Customization

- Modify classify_domain() in ot.py.
- Update SMEEngine.build_system_prompt() for prompt logic.
- Swap LLM models in client.models.generate_content / client.chats.create.
- Edit frontend in ui/ for UI tweaks.

---

## 🛡️ Security

- Governance rules in security/governance_rules.json prevent jailbreaks.
- All user input is screened before hitting Gemini.

---

## 📦 Notes

- Backend logic & domains included; feel free to add equirements.txt, tests, CI.
- Web UI (Expertease) is separate but bundled for showcase.

---

## 📜 License

This project is licensed under the **MIT License**.  
See [LICENSE](LICENSE) for details.

---

### 🎯 Hackathon Tips

Demonstrate:
- Slick UI vs Telegram interaction
- Adding a domain in seconds
- Mode switching & safe responses

---
