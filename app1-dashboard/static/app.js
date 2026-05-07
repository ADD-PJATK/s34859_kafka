// App #1 - Realtime Dashboard frontend (scaffold; SSE wiring added in next commit).
//
// On load we fetch the ticker list from the Flask proxy and render checkboxes.
// "Connect" / "Disconnect" buttons are wired up but the EventSource logic is
// intentionally left for the next commit so the diff stays focused.

const tickerListEl = document.getElementById("ticker-list");
const connectBtn   = document.getElementById("connect");
const disconnectBtn= document.getElementById("disconnect");
const selectAllBtn = document.getElementById("select-all");
const selectNoneBtn= document.getElementById("select-none");
const statusEl     = document.getElementById("status");

function setStatus(text, cls) {
  statusEl.textContent = text;
  statusEl.className = "status " + cls;
}

async function loadTickers() {
  try {
    const resp = await fetch("/api/tickers");
    if (!resp.ok) throw new Error("HTTP " + resp.status);
    const payload = await resp.json();
    // Upstream shape: { tickers: ["ACME", "ALFA", ...] } or an array.
    const tickers = Array.isArray(payload) ? payload : (payload.tickers || []);
    renderTickerList(tickers);
    connectBtn.disabled = false;
  } catch (err) {
    tickerListEl.textContent = "Failed to load tickers: " + err.message;
  }
}

function renderTickerList(tickers) {
  tickerListEl.innerHTML = "";
  tickers.forEach(t => {
    const sym = typeof t === "string" ? t : (t.ticker || t.symbol);
    if (!sym) return;
    const id = "tk-" + sym;
    const label = document.createElement("label");
    label.innerHTML = `<input type="checkbox" id="${id}" value="${sym}" /> ${sym}`;
    tickerListEl.appendChild(label);
  });
}

function selectedTickers() {
  return Array.from(tickerListEl.querySelectorAll("input[type=checkbox]:checked"))
    .map(cb => cb.value);
}

selectAllBtn.addEventListener("click", () => {
  tickerListEl.querySelectorAll("input[type=checkbox]").forEach(cb => cb.checked = true);
});
selectNoneBtn.addEventListener("click", () => {
  tickerListEl.querySelectorAll("input[type=checkbox]").forEach(cb => cb.checked = false);
});

connectBtn.addEventListener("click", () => {
  const sel = selectedTickers();
  if (sel.length === 0) { alert("Pick at least one ticker."); return; }
  setStatus("connecting (SSE wired up in next commit)", "idle");
});

disconnectBtn.addEventListener("click", () => {
  setStatus("idle", "idle");
});

loadTickers();
