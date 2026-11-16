const form = document.getElementById("audit-form");
const tabs = document.querySelectorAll(".tab");
const pastePanel = document.getElementById("paste-panel");
const uploadPanel = document.getElementById("upload-panel");
const textArea = document.getElementById("contract-text");
const pdfInput = document.getElementById("pdf-file");
const count = document.getElementById("char-count");
const errorBox = document.getElementById("form-error");
const loading = document.getElementById("loading");
const results = document.getElementById("results");
let activeTab = "paste";

tabs.forEach((tab) => tab.addEventListener("click", () => {
  activeTab = tab.dataset.tab;
  tabs.forEach((item) => item.classList.toggle("active", item === tab));
  pastePanel.classList.toggle("hidden", activeTab !== "paste");
  uploadPanel.classList.toggle("hidden", activeTab !== "upload");
  errorBox.textContent = "";
}));
textArea.addEventListener("input", () => {
  count.textContent = textArea.value.length.toLocaleString() + " / 30,000";
});
pdfInput.addEventListener("change", () => {
  document.getElementById("file-name").textContent = pdfInput.files[0]?.name || "No file selected";
});
function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[char]);
}
function showError(message) { errorBox.textContent = message; }
function renderResults(data) {
  const clauses = Array.isArray(data.clauses) ? data.clauses : [];
  const counts = { HIGH: 0, MEDIUM: 0, LOW: 0 };
  clauses.forEach((clause) => { if (counts[clause.risk_level] !== undefined) counts[clause.risk_level]++; });
  const cards = clauses.map((clause, index) => {
    const risk = ["HIGH", "MEDIUM", "LOW"].includes(clause.risk_level) ? clause.risk_level : "MEDIUM";
    const label = risk === "HIGH" ? "High priority" : risk === "MEDIUM" ? "Review" : "Lower concern";
    return '<article class="clause-card"><div class="clause-head"><b>' + (index + 1) + '. ' + escapeHtml(clause.clause_title || "Contract clause") + '</b><span class="risk-tag risk-' + risk.toLowerCase() + '">' + label + '</span></div><div class="clause-body"><p class="quote">“' + escapeHtml(clause.original_text) + '”</p><p><strong>What it means</strong><br>' + escapeHtml(clause.plain_language_explanation) + '</p><p><strong>Why it matters</strong><br>' + escapeHtml(clause.why_it_matters) + '</p><p><strong>Suggested next step</strong><br>' + escapeHtml(clause.negotiation_tip) + '</p><p><strong>Possible balanced wording</strong><br>' + escapeHtml(clause.suggested_revision) + '</p><p><strong>AI confidence:</strong> ' + escapeHtml(clause.confidence || "Not specified") + '</p></div></article>';
  }).join("");
  const limitations = (data.limitations || []).map((item) => '<li>' + escapeHtml(item) + '</li>').join("");
  results.innerHTML = '<h3>Your contract review</h3><p class="summary">' + escapeHtml(data.overall_summary || "Review completed. Read each finding carefully.") + '</p><div class="risk-counts"><span class="risk-high">' + counts.HIGH + ' HIGH PRIORITY</span><span class="risk-medium">' + counts.MEDIUM + ' REVIEW</span><span class="risk-low">' + counts.LOW + ' LOWER CONCERN</span></div>' + (cards || "<p class='summary'>No specific clauses were flagged. This does not mean the contract is risk-free.</p>") + '<div class="limitations"><b>Important limitations</b><ul>' + limitations + '</ul></div><div class="result-actions"><button class="secondary-button" id="copy-report">Copy review summary</button><button class="secondary-button" id="new-review">Start a new review</button></div>';
  results.classList.remove("hidden");
  document.getElementById("copy-report").addEventListener("click", async () => {
    const lines = ["CONTRACTGUARDIAN REVIEW", data.overall_summary || ""];
    clauses.forEach((c, i) => lines.push("\n" + (i + 1) + ". " + c.clause_title + " [" + c.risk_level + "]\nEvidence: " + c.original_text + "\nMeaning: " + c.plain_language_explanation + "\nWhy it matters: " + c.why_it_matters + "\nSuggested next step: " + c.negotiation_tip + "\nPossible wording: " + c.suggested_revision));
    lines.push("\nLIMITATIONS", ...(data.limitations || []));
    try { await navigator.clipboard.writeText(lines.join("\n")); document.getElementById("copy-report").textContent = "Copied"; }
    catch { document.getElementById("copy-report").textContent = "Copy unavailable"; }
  });
  document.getElementById("new-review").addEventListener("click", () => {
    results.classList.add("hidden"); form.scrollIntoView({ behavior: "smooth" });
  });
}
form.addEventListener("submit", async (event) => {
  event.preventDefault();
  showError("");
  results.classList.add("hidden");
  const jurisdiction = document.getElementById("jurisdiction").value.trim() || "Not specified";
  const contractType = document.getElementById("contract-type").value;
  let endpoint, options;
  if (activeTab === "paste") {
    const contractText = textArea.value.trim();
    if (contractText.length < 50) return showError("Please enter at least 50 characters of contract text.");
    if (contractText.length > 30000) return showError("The text exceeds the 30,000-character limit.");
    endpoint = "/api/analyze";
    options = { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ contract_text: contractText, jurisdiction, contract_type: contractType }) };
  } else {
    const file = pdfInput.files[0];
    if (!file) return showError("Please choose a PDF file.");
    if (file.size > 8 * 1024 * 1024) return showError("The PDF must be 8 MB or smaller.");
    if (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf")) return showError("Please choose a PDF file.");
    const body = new FormData();
    body.append("file", file); body.append("jurisdiction", jurisdiction); body.append("contract_type", contractType);
    endpoint = "/api/analyze-pdf"; options = { method: "POST", body };
  }
  const button = document.getElementById("submit-button");
  button.disabled = true; button.textContent = "Analyzing…"; loading.classList.remove("hidden");
  try {
    const response = await fetch(endpoint, options);
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload.detail || "The review could not be completed.");
    renderResults(payload); results.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    showError(error.message || "Something went wrong. Please try again.");
  } finally {
    loading.classList.add("hidden"); button.disabled = false; button.innerHTML = 'Analyze contract <span>↗</span>';
  }
});
