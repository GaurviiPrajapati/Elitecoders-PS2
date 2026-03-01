# 🧠 Expertease

![License](https://img.shields.io/badge/license-MIT-green) 
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Telegram](https://img.shields.io/badge/telegram-bot-blue)

**Subject-Matter-Expert (SME) AI Assistant Suite**

A polished web UI and Telegram bot that route user questions to domain-specific SME prompts, powered by Google's Gemini LLM. Built with the Gemini SDK, LangChain, and a splash of Auto-GPT concepts.

![Expertease UI](path/to/your/screenshot.png)

---

## 🚀 Features

- **Four Expert Domains**
  - General, Cyber-security, Financial Advisory, Legal Analyst
- **Dual Interface**
  - Interactive Telegram Chatbot
  - Dedicated vanilla JS Web UI (Expertease)
- **Modular JSON Domains**
  - Customizable personas, scopes, decision trees, and formatting rules
- **Mode Switching**
  - Role-based responses: `/mode TECHNICAL | EXECUTIVE | AUDIT | CLIENT`
- **Robust Security**
  - Jailbreak and prompt injection filters governed by `security/governance_rules.json`

---

## 🗂️ Repository Structure

Elitecoders-PS2/
│
├── .run/                      # Runtime configs / IDE run configurations
│
├── AI_Backend/                # Core AI logic (LangChain, AutoGPT, domain logic)
│
├── backend_server/            # Backend server implementation
│
├── conversations/             # Stored conversation logs / memory
│
├── sme_env/                   # SME environment configurations
│
├── sme-ui/                    # Frontend (HTML, CSS, JS)
│   ├── auth.js                # Authentication logic
│   ├── chat.html              # Chat interface
│   ├── index.html             # Landing page
│   ├── login.html             # Login page
│   ├── logo.png               # Project logo
│   ├── script.js              # Frontend interaction logic
│   └── style.css              # Styling
│
├── .gitignore                 # Git ignored files
├── bot.log                    # Runtime logs
├── LICENSE                    # Project license
├── README.md                  # Project documentation
├── run_all.ps1                # PowerShell script to run full system
├── run_server.ps1             # PowerShell script to run backend
├── server.pid                 # Server process ID
└── test_bot.py                # Bot testing script

## 🛠️ Setup & Run

### Prerequisites

- Python 3.10+
- Virtualenv or venv
- API Keys: `TELEGRAM_TOKEN`, `GEMINI_API_KEY`

### 1. Set Environment Variables

**PowerShell**
```powershell
$env:TELEGRAM_TOKEN = "<your-telegram-token>"
$env:GEMINI_API_KEY = "<your-gemini-api-key>"
```

**CMD**
```cmd
set TELEGRAM_TOKEN=<your-telegram-token>
set GEMINI_API_KEY=<your-gemini-api-key>
```

**Linux/macOS**
```bash
export TELEGRAM_TOKEN="<your-telegram-token>"
export GEMINI_API_KEY="<your-gemini-api-key>"
```

### 2. Install Dependencies

```bash
python -m venv .venv

# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install python-telegram-bot google-genai
```

### 3. Run the Bot

```bash
python bot.py
```

Access the bot via Telegram or open the Expertease web UI (e.g., `http://localhost:PORT`).

---

## 🔍 How It Works

1. **Classification:** Incoming message → `bot.py` classifies the domain via an LLM prompt.
2. **Prompt Construction:** `SMEEngine` loads the relevant JSON config and constructs the system prompt.
3. **Session Management:** Sessions are maintained per user/domain. Switching domains resets the prompt context.
4. **Response Generation:** The Gemini API generates the response, and the bot returns it securely to the user.

---

## 📁 Domain JSON Configuration

Adding new domains is as simple as creating a new JSON file in the `domains/` directory using this schema:

```json
{
  "domain_name": "Cyber-Security",
  "persona": "Seasoned infosec analyst",
  "scope": ["vulnerabilities", "threat intel"],
  "decision_tree": [...],
  "citation_rules": { "required": true, "format": "APA" },
  "output_format": { "type": "markdown" },
  "out_of_scope_response": "I'm not able to answer that."
}
```

> **Tip:** Add a new domain by copying an existing JSON file and tweaking the schema attributes.

---

## 🧩 Customization

- Modify `classify_domain()` in `bot.py` to add new routing logic.
- Update `SMEEngine.build_system_prompt()` for advanced prompt engineering.
- Edit the frontend files in `ui/` for custom styling and web components.
- Swap LLM models or tweak generation params directly in the API client calls.

---

## 🛡️ Security & Governance

- Configurable rules in `security/governance_rules.json` prevent LLM jailbreaks.
- All user inputs are sanitized and screened before content generation.

---

## 📦 Additional Notes

- Core backend logic and initial domains are included. Feel free to extend this project by adding a `requirements.txt`, unit tests, or a CI/CD pipeline.
- The web UI (Expertease) is separate but bundled for showcase purposes.

---

## 📜 License

This project is licensed under the **MIT License**.  
See [LICENSE](LICENSE) for details.

---

### 🎯 Hackathon Tips

If presenting this project, demonstrate:
- The slick UI compared to the standard Telegram interaction.
- How easy it is to drop in a new expert domain in seconds.
- Seamless mode switching and secure, filtered responses.
