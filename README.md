# ConsentReceipt

Paste a privacy policy and get a **consent receipt**: five plain-English disclosures (what's collected, how it's used, who it's shared with, your rights, how long it's kept). Every disclosure is backed by an exact quote that the app **verifies against the original text**, and you can **listen to the summary** read aloud.

- **AI (free):** Groq
- **Backend:** Python + FastAPI. **Frontend:** plain HTML/CSS/JS (no build step)
- **Voice:** your browser's built-in text-to-speech (free, no extra API)

---

## Step-by-step setup (Windows + VS Code)

### 1. Prerequisites
Python 3.10 or newer (`python --version`) and Chrome, Edge, or Safari.

> **Tip:** put the project in a simple folder like `C:\dev\consent-receipt`, not inside OneDrive. OneDrive syncing can break virtual environments.

### 2. Get a free AI key (Groq is the easiest)
1. Go to <https://console.groq.com/keys> and sign in.
2. Click **Create API Key**, name it, and copy the `gsk_...` key (it's shown only once).

### 3. Open the folder in VS Code
**File > Open Folder**, choose `consent-receipt` (the folder that contains `requirements.txt`). Open a terminal with **Ctrl+`**.

### 4. Create a virtual environment
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```
(Mac/Linux: `python3 -m venv .venv` then `source .venv/bin/activate`.) If PowerShell blocks it, run `Set-ExecutionPolicy -Scope Process Bypass` first. You should see `(.venv)` in the prompt. Activate it again whenever you open a new terminal.

### 5. Install dependencies
```powershell
python -m pip install -r requirements.txt
```

### 6. Create your `.env` file
Copy `.env.example` to a new file named exactly `.env` and paste your Groq key:
```
GROQ_API_KEY=gsk_your_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```
No quotes, no spaces around the key.

### 7. Check that your key works
```powershell
python -m scripts.check_providers
```
You want at least one `OK` line. If every line says FAIL, the message tells you why (bad key, rate limit, and so on).

### 8. Run it
```powershell
uvicorn app.main:app --reload
```
Open <http://127.0.0.1:8000>. Check <http://127.0.0.1:8000/api/health>: it should list Groq when the key is configured.

### 9. Try it
1. Click **Use sample policy**, then **Generate receipt**.
2. Click **Show in policy** on a card to jump to the highlighted source passage.
3. Click **Listen to summary** (or **Listen** on one card). Choose a voice and speed.
4. Click **Download receipt (JSON)**.

### 10. Tests and evaluation
```powershell
pytest
python -m scripts.evaluate
```
`evaluate` runs 4 labeled fictional policies in `eval/` and prints status accuracy, citation validity, the "we do not sell" check, and speed. The expected labels are author-written, so have a teammate review them.

---

## How Groq requests work
The app sends requests to Groq using `GROQ_MODEL`. If Groq is rate-limited or overloaded, the app retries once. The receipt records the model used; if the request still fails, the error box shows the reason.

| Provider | Key | Notes |
|---|---|---|
| groq | `GROQ_API_KEY` | Fast, free tier. Per-minute token caps may reject very long policies |

Free tiers and model names change often. Run `python -m scripts.check_providers` before the event.

## How it works
1. The policy goes to the AI with a strict prompt asking for five categories in a fixed JSON shape.
2. `app/verification.py` searches the **original policy** for each returned quote (ignoring case, spacing, curly quotes). Missing quotes get a warning in the UI.
3. `app/receipt.py` builds the receipt: five categories, a SHA-256 policy fingerprint, timestamp, verification stats.
4. The browser highlights verified quotes and reads the summary with the Web Speech API.

**Honest limits:** "verified" means the quote exists in the policy, not that the summary reads it correctly. This is not legal advice or a legal certification. Pasted text is sent to the AI provider you configure.

## Project structure
```
consent-receipt/
├── app/            main.py (routes), analyzer.py (Groq), models.py, verification.py, receipt.py
├── static/         index.html, style.css, app.js
├── eval/           labeled policies + cases.json
├── scripts/        check_providers.py, evaluate.py
├── samples/sample_policy.txt
├── tests/
└── requirements.txt  .env.example  .gitignore
```

## Troubleshooting
| Problem | Fix |
|---|---|
| `No module named ...` | Activate the venv (step 4) and rerun step 5 |
| "No Groq API key found" | `.env` must be named exactly `.env`, sit next to `requirements.txt`, and contain `GROQ_API_KEY`. Restart uvicorn after editing |
| "Groq request failed" | Read the reason in the message. 429 = rate limit (wait a minute). 401 = bad key |
| Voice silent or no voices | Use Chrome/Edge/Safari and check system volume |

## 2-minute demo script
1. Paste the sample policy and generate the receipt.
2. Show **Who they share it with**: "We do not sell" is summarized correctly and the vague ad-partner sharing is flagged.
3. Click **Show in policy** to prove the quote is real.
4. Play the voice summary.
5. Show the **Unclear** retention card: the tool says what the policy *doesn't* say.
