// App #2 - History Downloader / Viewer frontend.
//
// Workflow:
//   1. Pick tickers + a window in minutes (1/2/5/10).
//   2. Click "Start polling": every 10s we GET /api/latest?ticker=... for the
//      selected tickers and append any new ticks (deduped by ticker+seq).
//   3. The table and chart render the current window (last N minutes).
//   4. "Download CSV" / "Download JSON" save the current window to a file.
//
// Important constraint: the upstream API only retains data for ~10 minutes,
// so the window is built up by polling forward in time -- it cannot reach
// into the past. This is documented in the README.

const tickerListEl  = document.getElementById("ticker-list");
const startBtn      = document.getElementById("start");
const stopBtn       = document.getElementById("stop");
const selectAllBtn  = document.getElementById("select-all");
const selectNoneBtn = document.getElementById("select-none");
const statusEl      = document.getElementById("status");
const minutesEl     = document.getElementById("minutes");
const dlCsvBtn      = document.getElementById("dl-csv");
const dlJsonBtn     = document.getElementById("dl-json");
const tableBodyEl   = document.querySelector("#ticks-table tbody");

const POLL_MS = 10_000;

let pollTimer  = null;
let chart      = null;
let pollCount  = 0;
const ticks    = [];           // {ticker, ts, price, currency, volume, seq}
const seen     = new Set();    // "TICKER#seq" dedupe keys
const palette  = ["#38bdf8", "#34d399", "#f87171", "#fbbf24", "#a78bfa",
                  "#f472b6", "#fb923c", "#22d3ee", "#facc15", "#4ade80"];
const colorOf  = {};

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

function selectedTickers() {
  return Array.from(tickerListEl.querySelectorAll("input[type=checkbox]:checked"))
    .map(cb => cb.value);
}

function windowedTicks() {
  const minutes = parseInt(minutesEl.value, 10);
  const cutoff  = Date.now() - minutes * 60_000;
  return ticks.filter(t => Date.parse(t.ts) >= cutoff);
}

function ensureChart() {
  if (chart) return chart;
  const ctx = document.getElementById("chart").getContext("2d");
  chart = new Chart(ctx, {
    type: "line",
    data: { labels: [], datasets: [] },
    options: {
      animation: false,
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { ticks: { color: "#94a3b8", maxTicksLimit: 12 }, grid: { color: "#334155" } },
        y: { ticks: { color: "#94a3b8" }, grid: { color: "#334155" } },
      },
      plugins: { legend: { labels: { color: "#e2e8f0" } } },
    },
  });
  return chart;
}

function colorFor(ticker) {
  if (!colorOf[ticker]) {
    colorOf[ticker] = palette[Object.keys(colorOf).length % palette.length];
  }
  return colorOf[ticker];
}

function renderChart(visible) {
  ensureChart();
  // Group ticks by ticker and sort each by timestamp.
  const byTicker = {};
  visible.forEach(t => {
    (byTicker[t.ticker] = byTicker[t.ticker] || []).push(t);
  });
  Object.values(byTicker).forEach(arr => arr.sort((a, b) => Date.parse(a.ts) - Date.parse(b.ts)));

  // Build a unified, sorted timestamp axis across all tickers.
  const allTs = Array.from(new Set(visible.map(t => t.ts))).sort();
  chart.data.labels = allTs.map(s => new Date(s).toLocaleTimeString());

  chart.data.datasets = Object.entries(byTicker).map(([ticker, arr]) => {
    const byTs = Object.fromEntries(arr.map(t => [t.ts, t.price]));
    return {
      label: ticker,
      data: allTs.map(t => byTs[t] ?? null),
      borderColor: colorFor(ticker),
      backgroundColor: colorFor(ticker) + "33",
      tension: 0.25,
      pointRadius: 2,
      spanGaps: true,
    };
  });
  chart.update("none");
}

function renderTable(visible) {
  // Newest first.
  const sorted = [...visible].sort((a, b) => Date.parse(b.ts) - Date.parse(a.ts));
  tableBodyEl.innerHTML = sorted.map((t, i) => `
    <tr>
      <td>${i + 1}</td>
      <td>${t.ticker}</td>
      <td>${Number(t.price).toFixed(2)}</td>
      <td>${t.currency || ""}</td>
      <td>${t.volume ?? ""}</td>
      <td>${new Date(t.ts).toLocaleString()}</td>
      <td>${t.seq ?? ""}</td>
    </tr>
  `).join("");
}

function refreshViews() {
  const visible = windowedTicks();
  renderChart(visible);
  renderTable(visible);
  const haveData = visible.length > 0;
  dlCsvBtn.disabled  = !haveData;
  dlJsonBtn.disabled = !haveData;
}

async function pollOnce(tickers) {
  const qs = tickers.map(t => "ticker=" + encodeURIComponent(t)).join("&");
  const resp = await fetch("/api/latest?" + qs);
  if (!resp.ok) throw new Error("HTTP " + resp.status);
  const payload = await resp.json();
  const rows = Array.isArray(payload) ? payload : (payload.data || []);
  let added = 0;
  rows.forEach(r => {
    const key = `${r.ticker}#${r.seq}`;
    if (seen.has(key)) return;
    seen.add(key);
    ticks.push(r);
    added++;
  });
  pollCount++;
  setStatus(
    `polling (poll #${pollCount}, +${added} new, ${ticks.length} total)`,
    "polling"
  );
  refreshViews();
}

async function startPolling() {
  const sel = selectedTickers();
  if (sel.length === 0) { alert("Pick at least one ticker."); return; }
  startBtn.disabled = true;
  stopBtn.disabled = false;
  setStatus("polling (poll #1)...", "polling");

  try { await pollOnce(sel); }
  catch (e) { setStatus("error: " + e.message, "error"); }

  pollTimer = setInterval(async () => {
    try { await pollOnce(sel); }
    catch (e) { setStatus("error: " + e.message, "error"); }
  }, POLL_MS);
}

function stopPolling() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
  startBtn.disabled = false;
  stopBtn.disabled = true;
  setStatus("stopped (" + ticks.length + " ticks captured)", "idle");
}

function downloadBlob(filename, content, mime) {
  const blob = new Blob([content], { type: mime });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function csvEscape(v) {
  if (v == null) return "";
  const s = String(v);
  return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

function buildCsv(rows) {
  const headers = ["ticker", "ts", "price", "currency", "volume", "seq"];
  const lines = [headers.join(",")];
  rows.forEach(r => lines.push(headers.map(h => csvEscape(r[h])).join(",")));
  return lines.join("\n") + "\n";
}

function timestampSlug() {
  const d = new Date();
  const pad = n => String(n).padStart(2, "0");
  return `${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}-${pad(d.getHours())}${pad(d.getMinutes())}${pad(d.getSeconds())}`;
}

dlCsvBtn.addEventListener("click", () => {
  const visible = windowedTicks();
  if (!visible.length) return;
  downloadBlob(`stocks-${timestampSlug()}.csv`, buildCsv(visible), "text/csv");
});

dlJsonBtn.addEventListener("click", () => {
  const visible = windowedTicks();
  if (!visible.length) return;
  downloadBlob(
    `stocks-${timestampSlug()}.json`,
    JSON.stringify(visible, null, 2),
    "application/json"
  );
});

selectAllBtn.addEventListener("click", () => {
  tickerListEl.querySelectorAll("input[type=checkbox]").forEach(cb => cb.checked = true);
});
selectNoneBtn.addEventListener("click", () => {
  tickerListEl.querySelectorAll("input[type=checkbox]").forEach(cb => cb.checked = false);
});

startBtn.addEventListener("click", startPolling);
stopBtn.addEventListener("click", stopPolling);

minutesEl.addEventListener("change", refreshViews);

loadTickers();
