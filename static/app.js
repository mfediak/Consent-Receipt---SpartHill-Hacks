const $ = (s) => document.querySelector(s);
const LABEL = {
  data_collection: "What they collect", data_usage: "How they use it", data_sharing: "Who they share it with",
  user_rights: "Your rights", data_retention: "How long they keep it",
};
const STATUS = { disclosed: "Disclosed", unclear: "Unclear", not_found: "Not found" };
let receipt = null, maxChars = 60000;

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
  showError(""); stopSpeech();
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
$("#again").onclick = () => { stopSpeech(); show("#results", false); show("#intake", true); window.scrollTo({ top: 0, behavior: "smooth" }); };

// ---------- render ----------
function render(r) {
  show("#intake", false); show("#results", true);
  $("#company").textContent = r.company && r.company !== "Unknown" ? r.company : "Privacy policy receipt";
  $("#overview").textContent = r.overview;
  $("#verified").textContent = `${r.stats.quotes_verified} of ${r.stats.quotes_checked}`;
  $("#when").textContent = new Date(r.generated_at).toLocaleString([], { dateStyle: "medium", timeStyle: "short" });
  $("#hash").textContent = r.policy_sha256.slice(0, 10) + "…";
  $("#disclaimer").textContent = r.disclaimer;

  $("#cards").innerHTML = r.disclosures.map((d) => {
    const ver = d.evidence_verified === null ? "" :
      d.evidence_verified ? `<span class="ver">✓ Quote found in policy</span>` : `<span class="ver no">⚠ Quote not found in policy. Treat this summary with caution.</span>`;
    return `<article class="card ${d.status}" id="card-${d.category}">
      <div class="card-top"><h3>${LABEL[d.category]}</h3><span class="chip">${STATUS[d.status]}</span></div>
      <p class="summary">${esc(d.summary)}</p>
      ${d.evidence ? `<blockquote>“${esc(d.evidence)}”</blockquote>` : `<blockquote>The policy doesn’t say.</blockquote>`}
      <div class="card-foot">${ver}
        ${d.span ? `<button class="link" data-find="${d.category}">Show in policy</button>` : ""}
        <button class="link" data-say="${d.category}">Listen</button>
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

$("#download").onclick = () => {
  const { policy_text, ...clean } = receipt;
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([JSON.stringify(clean, null, 2)], { type: "application/json" }));
  a.download = `consent-receipt-${receipt.policy_sha256.slice(0, 8)}.json`; a.click(); URL.revokeObjectURL(a.href);
};

// ---------- voice (browser speech synthesis: free, no API) ----------
const synth = window.speechSynthesis;
let voices = [], token = 0, paused = false;
const lineFor = (d) => `${LABEL[d.category]}. ${d.summary}` + (d.status === "unclear" ? " The policy is unclear on this." : d.status === "not_found" ? " The policy doesn't say." : "");

function loadVoices() {
  voices = synth.getVoices().filter((v) => v.lang.toLowerCase().startsWith("en"));
  $("#voice").innerHTML = voices.map((v) => `<option value="${esc(v.name)}">${esc(v.name)}</option>`).join("");
  const pick = voices.find((v) => /natural|neural|samantha|google us|aria|jenny/i.test(v.name));
  if (pick) $("#voice").value = pick.name;
}
if (!synth) { $("#player").innerHTML = `<span class="muted">Voice isn’t supported in this browser. Try Chrome, Edge, or Safari.</span>`; }
else { loadVoices(); synth.onvoiceschanged = loadVoices; }

function speak(items) {
  stopSpeech(); const my = ++token; let i = 0;
  setPlaying(true);
  const next = () => {
    if (my !== token) return;
    if (i >= items.length) return endSpeech();
    const it = items[i++], u = new SpeechSynthesisUtterance(it.text);
    u.rate = +$("#rate").value; const v = voices.find((x) => x.name === $("#voice").value); if (v) u.voice = v;
    u.onstart = () => { document.querySelectorAll(".card.speaking").forEach((c) => c.classList.remove("speaking")); const c = $("#card-" + it.id); if (c) { c.classList.add("speaking"); c.scrollIntoView({ behavior: "smooth", block: "nearest" }); } };
    u.onend = next; u.onerror = next;
    synth.speak(u);
  };
  next();
}
function summaryItems() { return [{ id: "", text: `${receipt.company !== "Unknown" ? receipt.company + ". " : ""}${receipt.overview}` }, ...receipt.disclosures.map((d) => ({ id: d.category, text: lineFor(d) }))]; }
function setPlaying(on) { $("#stop").hidden = !on; $("#listen").textContent = on ? "Pause" : "Listen to summary"; paused = false; }
function endSpeech() { token++; setPlaying(false); document.querySelectorAll(".card.speaking").forEach((c) => c.classList.remove("speaking")); }
function stopSpeech() { if (!synth) return; token++; synth.cancel(); endSpeech(); }

$("#listen").onclick = () => {
  if (!synth) return;
  if (!$("#stop").hidden) { paused ? synth.resume() : synth.pause(); paused = !paused; $("#listen").textContent = paused ? "Resume" : "Pause"; }
  else speak(summaryItems());
};
$("#stop").onclick = stopSpeech;
