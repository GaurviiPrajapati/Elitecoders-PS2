# SME Telegram Bot

A small Telegram bot that routes user queries to a domain-specific Subject Matter Expert (SME) prompt and interacts with Google's Gemini (Generative AI) via the `google.genai` client.

**Files:**
- [bot.py](bot.py) : Main Telegram bot entrypoint. Reads environment variables, classifies incoming messages into domains, creates/maintains chat sessions, and forwards messages to the Gemini chat session.
- [sme_engine.py](sme_engine.py) : `SMEEngine` class for loading domain JSON files and building the system prompt used for each chat session.
- `domains/` : Directory containing JSON domain descriptors (e.g., [domains/general.json](domains/general.json)).

**Environment**
- Python 3.10+ recommended.
- Required environment variables:
  - `TELEGRAM_TOKEN` — your Telegram Bot API token.
  - `GEMINI_API_KEY` — API key for Google's Generative AI (Gemini) client.

On Windows PowerShell you can set them for the session with:

```
$env:TELEGRAM_TOKEN = "<your-telegram-token>"
$env:GEMINI_API_KEY = "<your-gemini-api-key>"
```

On Windows CMD:

```
set TELEGRAM_TOKEN=<your-telegram-token>
set GEMINI_API_KEY=<your-gemini-api-key>
```

**Install dependencies**
- Create a virtual environment and install dependencies (example packages shown — adjust if you use different client libraries):

```
python -m venv .venv
.\.venv\Scripts\activate
pip install python-telegram-bot google-genai
```

Note: The project uses `google.genai` in `bot.py`. Ensure you have the appropriate Google Generative AI library installed and configured for your environment.

**Run**
- Start the bot:

```
python bot.py
```

The bot logs to `bot.log` (created in the working directory).

**How it works (high level)**
- `bot.py` receives incoming Telegram text messages, uses an LLM prompt-based classifier to pick one of the domain JSONs in `domains/`, and then uses `SMEEngine` to build a system prompt for Gemini.
- For each Telegram user the bot maintains a chat session (per-domain). If a user switches domains, a new chat session with updated system prompt is created.

**Domain JSON structure (example fields)**
- `domain_name` — friendly name used in the system prompt.
- `persona` — short persona description the model should adopt.
- `scope` — array of topic strings describing what's in-scope.
- `decision_tree` — optional list of decision steps to include in the system prompt.
- `citation_rules` — optional object (e.g., `{ "required": true, "format": "..." }`).
- `output_format` — optional object describing required output structure.
- `out_of_scope_response` — message to return when queries are outside scope.

**Output Personas / Modes**
Users can customize the response style using the `/mode <MODE_NAME>` command. 
Available modes are:
- `TECHNICAL` — precise jargon, detailed, code/equations where applicable
- `EXECUTIVE` — high-level summaries, ROI, strategic impact
- `AUDIT` — objective focus on compliance, risks, and evidence
- `CLIENT` — accessible language, benefits, and practical implications

For example, type `/mode EXECUTIVE` in the Telegram chat to switch to Executive mode.

To add or customize a domain, create a new JSON file under `domains/` following the same keys found in the existing files.

**Extending or customizing**
- To change the classifier behavior, edit the `classify_domain` function in [bot.py](bot.py).
- To change system prompt construction, edit `SMEEngine.build_system_prompt()` in [sme_engine.py](sme_engine.py).
- To use a different Gemini/LLM model, update the model names used in `client.models.generate_content` and `client.chats.create` in `bot.py`.

**Troubleshooting**
- If the bot immediately raises "Missing TELEGRAM_TOKEN or GEMINI_API_KEY", verify your environment variables are set.
- Check `bot.log` for runtime errors and stack traces.
- If domain classification seems wrong, inspect responses from the Gemini classifier call and refine the classification prompt.

**Notes**
- This repository contains only the bot logic and domain JSONs. Add appropriate dependency lists (e.g., `requirements.txt`) as desired.

**License**
- Use or add a license file as appropriate for your project.
