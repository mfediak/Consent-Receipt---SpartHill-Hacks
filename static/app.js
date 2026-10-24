const $ = (s) => document.querySelector(s);
const LABEL = {
  data_collection: "What they collect", data_usage: "How they use it", data_sharing: "Who they share it with",
  user_rights: "Your rights", data_retention: "How long they keep it",
};
const STATUS = { disclosed: "Disclosed", unclear: "Unclear", not_found: "Not found" };
const UI_LABELS = {
  language: "Language", listen: "Listen to summary", listenOne: "Listen", pause: "Pause", resume: "Resume", stop: "Stop",
  voice: "Voice", speed: "Speed", quotesVerified: "Quotes verified", generated: "Generated",
  fingerprint: "Policy fingerprint", analysisModel: "Analysis model", originalPolicy: "Original policy", privacyReceipt: "Privacy policy receipt",
  quoteFound: "Quote found in policy", quoteNotFound: "Quote not found in policy. Treat this summary with caution.",
  showInPolicy: "Show in policy", noEvidence: "The policy doesn’t say.", unclearSpoken: "The policy is unclear on this.",
  notFoundSpoken: "The policy doesn’t say.", download: "Download report (PDF)", preparingPdf: "Preparing PDF…",
  again: "Analyze another policy", important: "Important", quoteVerified: "Verified quote",
  quoteUnverified: "Quote not verified", noQuote: "No supporting quote was found in the policy.",
  voiceFallback: "No voice is installed for this language; playback will request the selected language.",
};
const LANGUAGE_LOCALES = { en: "en-US", es: "es-ES", fr: "fr-FR", hi: "hi-IN", ar: "ar-SA", "zh-CN": "zh-CN", pt: "pt-BR", de: "de-DE" };
let receipt = null, maxChars = 60000, currentLanguage = "en", activeTranslation = null, translationCache = {};

const esc = (t) => t.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const show = (id, on) => ($(id).hidden = !on);
function showError(msg) { const e = $("#error"); e.textContent = msg; e.hidden = !msg; }
async function readApiJson(response) {
  const text = await response.text();
  let data;
  try {
    data = JSON.parse(text);
  } catch {
    throw new Error(`Server returned an invalid response (HTTP ${response.status}). Check the uvicorn terminal and restart the server.`);
  }
  if (!response.ok) throw new Error(data.detail || `Request failed (HTTP ${response.status}).`);
  return data;
}

// ---------- input ----------
$("#policy").addEventListener("input", () => {
  $("#count").textContent = `${$("#policy").value.length.toLocaleString()} / ${maxChars.toLocaleString()}`;
});
$("#policyFile").addEventListener("change", async () => {
  const file = $("#policyFile").files[0];
  if (!file) return;
  showError(""); $("#fileStatus").textContent = `Reading ${file.name}…`;
  const form = new FormData(); form.append("file", file);
  try {
    const response = await fetch("/api/extract", { method: "POST", body: form });
    const data = await readApiJson(response);
    $("#policy").value = data.policy_text; $("#policy").dispatchEvent(new Event("input"));
    $("#fileStatus").textContent = `${data.file_name} loaded`;
  } catch (e) {
    $("#fileStatus").textContent = "Choose a policy file";
    showError(e.message);
  }
});
$("#sample").onclick = async () => {
  try {
    const r = await fetch("/api/sample");
    const j = await readApiJson(r);
    $("#policy").value = j.policy_text; $("#policy").dispatchEvent(new Event("input"));
  } catch (e) {
    showError(e.message === "Failed to fetch" ? "Can't reach the server. Is it running?" : e.message);
  }
};
fetch("/api/health").then(readApiJson).then((h) => {
  maxChars = h.max_chars; $("#policy").dispatchEvent(new Event("input"));
  if (!h.key_configured) showError("No valid Groq API key found. Replace the example GROQ_API_KEY in your .env file and restart the server.");
}).catch((e) => showError(e.message === "Failed to fetch" ? "Can't reach the server. Is it running?" : e.message));

$("#go").onclick = async () => {
  showError(""); stopSpeech(); resetLanguage();
  const text = $("#policy").value.trim();
  if (text.length < 200) return showError("Paste the full privacy policy (at least a few paragraphs).");
  $("#go").disabled = true; $("#go").textContent = "Analyzing…";
  show("#loading", true); show("#results", false);
  try {
    const r = await fetch("/api/analyze", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ policy_text: text }) });
    const j = await readApiJson(r);
    receipt = j; render(j);
  } catch (e) { showError(e.message); show("#intake", true); }
  finally { show("#loading", false); $("#go").disabled = false; $("#go").textContent = "Generate receipt"; }
};
$("#again").onclick = () => { stopSpeech(); resetLanguage(); show("#results", false); show("#intake", true); window.scrollTo({ top: 0, behavior: "smooth" }); };

function resetLanguage() {
  currentLanguage = "en"; activeTranslation = null; translationCache = {};
  $("#language").value = "en"; $("#languageStatus").textContent = "";
  document.documentElement.lang = LANGUAGE_LOCALES.en;
}

$("#language").addEventListener("change", async () => {
  if (!receipt) return;
  const language = $("#language").value;
  stopSpeech(); currentLanguage = language;
  if (language === "en") {
    activeTranslation = null; render(receipt); updateVoiceOptions(); return;
  }
  if (translationCache[language]) {
    activeTranslation = translationCache[language]; render(receipt, activeTranslation); updateVoiceOptions(); return;
  }

  const selector = $("#language"), status = $("#languageStatus");
  selector.disabled = true; status.textContent = "Translating results…";
  try {
    const payload = {
      language,
      overview: receipt.overview,
      disclaimer: receipt.disclaimer,
      category_labels: LABEL,
      status_labels: STATUS,
      ui_labels: UI_LABELS,
      disclosures: receipt.disclosures.map(({ category, summary }) => ({ category, summary })),
    };
    const response = await fetch("/api/translate", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload),
    });
    const translated = await readApiJson(response);
    translationCache[language] = translated;
    activeTranslation = translated;
    render(receipt, translated);
    updateVoiceOptions();
    status.textContent = "";
  } catch (e) {
    currentLanguage = "en"; selector.value = "en"; activeTranslation = null; render(receipt);
    status.textContent = "Translation unavailable; showing English.";
    showError(e.message);
    updateVoiceOptions();
  } finally {
    selector.disabled = false;
  }
});

// ---------- render ----------
function render(r, translation = null) {
  activeTranslation = translation;
  const ui = translation?.ui_labels || UI_LABELS;
  show("#intake", false); show("#results", true);
  $("#company").textContent = r.company && r.company !== "Unknown" ? r.company : (translation?.ui_labels.privacyReceipt || "Privacy policy receipt");
  $("#overview").textContent = translation?.overview || r.overview;
  $("#verified").textContent = `${r.stats.quotes_verified} of ${r.stats.quotes_checked}`;
  $("#when").textContent = new Date(r.generated_at).toLocaleString(currentLanguage, { dateStyle: "medium", timeStyle: "short" });
  $("#hash").textContent = r.policy_sha256.slice(0, 10) + "…";
  $("#disclaimer").textContent = translation?.disclaimer || r.disclaimer;
  $("#languageLabel").textContent = ui.language;
  $("#verifiedLabel").textContent = ui.quotesVerified;
  $("#generatedLabel").textContent = ui.generated;
  $("#fingerprintLabel").textContent = ui.fingerprint;
  $("#policyLabel").textContent = ui.originalPolicy;
  $("#listen").textContent = ui.listen;
  $("#stop").textContent = ui.stop;
  $("#voiceLabel").textContent = ui.voice;
  $("#speedLabel").textContent = ui.speed;
  $("#download").textContent = ui.download;
  $("#again").textContent = ui.again;
  $("#results").dir = currentLanguage === "ar" ? "rtl" : "ltr";
  $("#policyView").dir = "ltr";
  document.documentElement.lang = LANGUAGE_LOCALES[currentLanguage];

  $("#cards").innerHTML = r.disclosures.map((d) => {
    const category = translation?.category_labels[d.category] || LABEL[d.category];
    const status = translation?.status_labels[d.status] || STATUS[d.status];
    const ver = d.evidence_verified === null ? "" :
      d.evidence_verified ? `<span class="ver">✓ ${esc(ui.quoteFound)}</span>` : `<span class="ver no">⚠ ${esc(ui.quoteNotFound)}</span>`;
    return `<article class="card ${d.status}" id="card-${d.category}">
      <div class="card-top"><h3>${esc(category)}</h3><span class="chip">${esc(status)}</span></div>
      <p class="summary">${esc(translation?.disclosures.find((item) => item.category === d.category)?.summary || d.summary)}</p>
      ${d.evidence ? `<blockquote>“${esc(d.evidence)}”</blockquote>` : `<blockquote>${esc(ui.noEvidence)}</blockquote>`}
      <div class="card-foot">${ver}
        ${d.span ? `<button class="link" data-find="${d.category}">${esc(ui.showInPolicy)}</button>` : ""}
        <button class="link" data-say="${d.category}">${esc(ui.listenOne)}</button>
      </div></article>`;
  }).join("");

  // original policy with verified quotes highlighted
  const spans = r.disclosures.filter((d) => d.span).map((d) => ({ s: d.span[0], e: d.span[1], id: d.category })).sort((a, b) => a.s - b.s);
  let html = "", pos = 0; const t = r.policy_text;
  for (const sp of spans) { if (sp.s < pos) continue; html += esc(t.slice(pos, sp.s)) + `<mark id="mk-${sp.id}">${esc(t.slice(sp.s, sp.e))}</mark>`; pos = sp.e; }
  $("#policyView").innerHTML = html + esc(t.slice(pos));
  window.scrollTo({ top: 0, behavior: "smooth" });
}

$("#cards").addEventListener("click", (e) => {
  const find = e.target.dataset.find, say = e.target.dataset.say;
  if (find) { const m = $("#mk-" + find); if (m) { m.scrollIntoView({ behavior: "smooth", block: "center" }); m.classList.remove("flash"); void m.offsetWidth; m.classList.add("flash"); } }
  if (say) { const d = receipt.disclosures.find((x) => x.category === say); speak([{ id: say, text: lineFor(d) }]); }
});

$("#download").onclick = async () => {
  const button = $("#download"), ui = activeTranslation?.ui_labels || UI_LABELS; button.disabled = true; button.textContent = ui.preparingPdf;
  try {
    const { policy_text, ...report } = receipt;
    if (activeTranslation) {
      report.overview = activeTranslation.overview;
      report.disclaimer = activeTranslation.disclaimer;
      report.ui_labels = activeTranslation.ui_labels;
      report.disclosures = receipt.disclosures.map((d) => ({
        ...d,
        summary: activeTranslation.disclosures.find((item) => item.category === d.category)?.summary || d.summary,
        category_label: activeTranslation.category_labels[d.category],
        status_label: activeTranslation.status_labels[d.status],
      }));
    }
    const response = await fetch("/api/report", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(report),
    });
    if (!response.ok) await readApiJson(response);
    const url = URL.createObjectURL(await response.blob());
    const a = document.createElement("a"); a.href = url;
    a.download = `consent-receipt-${receipt.policy_sha256.slice(0, 8)}.pdf`; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  } catch (e) { showError(e.message); }
  finally { button.disabled = false; button.textContent = (activeTranslation?.ui_labels || UI_LABELS).download; }
};

// ---------- voice (browser speech synthesis: free, no API) ----------
const synth = window.speechSynthesis;
let voices = [], token = 0, paused = false;
const lineFor = (d) => {
  const translation = activeTranslation, ui = translation?.ui_labels || UI_LABELS;
  const category = translation?.category_labels[d.category] || LABEL[d.category];
  const summary = translation?.disclosures.find((item) => item.category === d.category)?.summary || d.summary;
  const ending = d.status === "unclear" ? ui.unclearSpoken : d.status === "not_found" ? ui.notFoundSpoken : "";
  return `${category}. ${summary}${ending ? ` ${ending}` : ""}`;
};

function updateVoiceOptions() {
  if (!synth) return;
  voices = synth.getVoices();
  const locale = LANGUAGE_LOCALES[currentLanguage].toLowerCase();
  const primary = locale.split("-")[0];
  const matching = voices.filter((v) => v.lang.toLowerCase().startsWith(primary));
  $("#voice").innerHTML = matching.length
    ? matching.map((v) => `<option value="${esc(v.name)}">${esc(v.name)} (${esc(v.lang)})</option>`).join("")
    : `<option value="">System voice (${esc(locale)})</option>`;
  const pick = matching.find((v) => /natural|neural|samantha|google|aria|jenny/i.test(v.name)) || matching[0];
  if (pick) $("#voice").value = pick.name;
  $("#voiceStatus").textContent = currentLanguage !== "en" && !matching.length
    ? (activeTranslation?.ui_labels.voiceFallback || UI_LABELS.voiceFallback) : "";
}
if (!synth) {
  $("#listen").disabled = true; $("#voice").disabled = true; $("#rate").disabled = true;
  $("#voiceStatus").textContent = "Voice isn’t supported in this browser. Try Chrome, Edge, or Safari.";
}
else { updateVoiceOptions(); synth.onvoiceschanged = updateVoiceOptions; }

function speak(items) {
  stopSpeech(); const my = ++token; let i = 0;
  setPlaying(true);
  const next = () => {
    if (my !== token) return;
    if (i >= items.length) return endSpeech();
    const it = items[i++], u = new SpeechSynthesisUtterance(it.text);
    u.rate = +$("#rate").value; u.lang = LANGUAGE_LOCALES[currentLanguage];
    const v = voices.find((x) => x.name === $("#voice").value); if (v) u.voice = v;
    u.onstart = () => { document.querySelectorAll(".card.speaking").forEach((c) => c.classList.remove("speaking")); const c = $("#card-" + it.id); if (c) { c.classList.add("speaking"); c.scrollIntoView({ behavior: "smooth", block: "nearest" }); } };
    u.onend = next; u.onerror = next;
    synth.speak(u);
  };
  next();
}
function summaryItems() { return [{ id: "", text: `${receipt.company !== "Unknown" ? receipt.company + ". " : ""}${activeTranslation?.overview || receipt.overview}` }, ...receipt.disclosures.map((d) => ({ id: d.category, text: lineFor(d) }))]; }
function setPlaying(on) { const ui = activeTranslation?.ui_labels || UI_LABELS; $("#stop").hidden = !on; $("#listen").textContent = on ? ui.pause : ui.listen; paused = false; }
function endSpeech() { token++; setPlaying(false); document.querySelectorAll(".card.speaking").forEach((c) => c.classList.remove("speaking")); }
function stopSpeech() { if (!synth) return; token++; synth.cancel(); endSpeech(); }

$("#listen").onclick = () => {
  if (!synth) return;
  if (!$("#stop").hidden) { paused ? synth.resume() : synth.pause(); paused = !paused; $("#listen").textContent = paused ? (activeTranslation?.ui_labels.resume || UI_LABELS.resume) : (activeTranslation?.ui_labels.pause || UI_LABELS.pause); }
  else speak(summaryItems());
};
$("#stop").onclick = stopSpeech;
