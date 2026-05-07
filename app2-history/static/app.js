// App #2 - History viewer frontend (scaffold; polling + table + export wired
// in the next commit). Loads tickers and lets the user pick a window.

const tickerListEl  = document.getElementById("ticker-list");
const startBtn      = document.getElementById("start");
const stopBtn       = document.getElementById("stop");
const selectAllBtn  = document.getElementById("select-all");
const selectNoneBtn = document.getElementById("select-none");
const statusEl      = document.getElementById("status");

function setStatus(text, cls) {
  statusEl.textContent = text;
  statusEl.className = "status " + cls;
}

async function loadTickers() {
  try {
    const resp = await fetch("/api/tickers");
    if (!resp.ok) throw new Error("HTTP " + resp.status);
    const payload = await resp.json();
    const tickers = Array.isArray(payload) ? payload : (payload.tickers || []);
    renderTickerList(tickers);
    startBtn.disabled = false;
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

selectAllBtn.addEventListener("click", () => {
  tickerListEl.querySelectorAll("input[type=checkbox]").forEach(cb => cb.checked = true);
});
selectNoneBtn.addEventListener("click", () => {
  tickerListEl.querySelectorAll("input[type=checkbox]").forEach(cb => cb.checked = false);
});

startBtn.addEventListener("click", () => {
  setStatus("polling (handler wired in next commit)", "idle");
});
stopBtn.addEventListener("click", () => {
  setStatus("idle", "idle");
});

loadTickers();
