# ConsentReceipt

Paste a privacy policy. Get five plain-English findings, each tied to the exact words it came from, a list of what the policy leaves unclear, and a downloadable receipt.

The model never gets the last word. Every quote Gemini returns is searched for in the pasted policy, and any finding whose quote can't be found is marked **Verification failed**.

## Run it

```powershell
# Windows PowerShell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env      # then put your Gemini API key in .env
streamlit run app.py
```

macOS or Linux: `source .venv/bin/activate` and `cp .env.example .env`.

Get a key in Google AI Studio. You can also leave `.env` empty and paste the key into the app's sidebar.

`GEMINI_MODEL` defaults to `gemini-3.8-flash`. Google retires model names often, so if you see a "model not found" error, set it to a current one (also editable in the sidebar).

Run the tests with `pytest`. They don't call the network.

## Files

```
app.py                  Streamlit interface: input, results tabs, export
src/render.py           Frontend: CSS and HTML for the hero, receipt sheet, and source view
src/analyzer.py         Gemini extraction (google-genai, structured output)
src/models.py           Pydantic schema Gemini must follow
src/verification.py     Paragraph labels, quote matching, final status
src/receipt.py          Receipt object, JSON and text export
src/constants.py        Categories, statuses, receipt notice
tests/                  Verification, receipt, and rendering tests
samples/                Three policies: ad-supported, "we do not sell" wording, a policy that says little
```

## How a receipt is made

1. You paste the policy (40,000 characters max).
2. The text is normalized and split into labeled paragraphs.
3. Gemini returns five disclosures, each with a copied quote, a summary, and a status.
4. Each quote is searched for in the policy. Matching ignores line breaks and curly-versus-straight quotes, but every word must match. Quotes shorter than 12 characters are rejected.
5. Each finding ends as **Disclosed**, **Unclear**, **Not found**, or **Verification failed**. The paragraph and character range come from our own search, not from the model.
6. The receipt is shown on screen and can be downloaded as JSON or text.

## Limits to state out loud

- A found quote proves the words exist in the policy. It does not prove the summary interprets them correctly. The interface says so, and the quote is always shown next to the summary.
- The receipt is not legal advice and does not record consent.
- The pasted text is sent to Google's Gemini API. This app doesn't store or log it, but check Google's data-use terms for your API tier before pasting anything non-public.
- The sampling parameters (`temperature`, `top_p`, `top_k`) are deprecated for current Gemini models, so they are not set. Consistency comes from the schema and the verification step.
- Not built: PDF upload, URL scraping, accounts, a database.
