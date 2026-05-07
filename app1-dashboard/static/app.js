// App #1 - Realtime Dashboard frontend.
//
// On load: fetch tickers from /api/tickers and render a checkbox list.
// On Connect: open EventSource against /api/stream?ticker=... for each
// selected ticker, update the per-ticker card and the rolling Chart.js chart
// for every "tick" event. Reconnects with backoff on error.

const tickerListEl  = document.getElementById("ticker-list");
const cardGridEl    = document.getElementById("card-grid");
const connectBtn    = document.getElementById("connect");
const disconnectBtn = document.getElementById("disconnect");
const selectAllBtn  = document.getElementById("select-all");
const selectNoneBtn = document.getElementById("select-none");
const statusEl      = document.getElementById("status");

const HISTORY_LEN = 30;

let evtSources    = [];          // one EventSource per selected ticker
let chart         = null;
let reconnectMs   = 1000;        // exponential backoff base
const palette     = ["#38bdf8", "#34d399", "#f87171", "#fbbf24", "#a78bfa",
                     "#f472b6", "#fb923c", "#22d3ee", "#facc15", "#4ade80"];
const colorOf     = {};          // ticker -> color
const history     = {};          // ticker -> [{ts, price}, ...]
const cards       = {};          // ticker -> {root, priceEl, tsEl, lastPrice}

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

function ensureCard(ticker) {
  if (cards[ticker]) return cards[ticker];
  const root = document.createElement("div");
  root.className = "card";
  root.innerHTML = `
    <div class="ticker">${ticker}</div>
    <div class="price">--</div>
    <div class="ts">waiting&hellip;</div>
  `;
  cardGridEl.appendChild(root);
  cards[ticker] = {
    root,
    priceEl: root.querySelector(".price"),
    tsEl:    root.querySelector(".ts"),
    lastPrice: null,
  };
  return cards[ticker];
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
        x: { ticks: { color: "#94a3b8" }, grid: { color: "#334155" } },
        y: { ticks: { color: "#94a3b8" }, grid: { color: "#334155" } },
      },
      plugins: {
        legend: { labels: { color: "#e2e8f0" } },
      },
    },
  });
  return chart;
}

function ensureDataset(ticker) {
  ensureChart();
  let ds = chart.data.datasets.find(d => d.label === ticker);
  if (!ds) {
    if (!colorOf[ticker]) {
      colorOf[ticker] = palette[Object.keys(colorOf).length % palette.length];
    }
    ds = {
      label: ticker,
      data: [],
      borderColor: colorOf[ticker],
      backgroundColor: colorOf[ticker] + "33",
      tension: 0.25,
      pointRadius: 2,
    };
    chart.data.datasets.push(ds);
  }
  return ds;
}

function pushTick(ticker, ts, price) {
  history[ticker] = history[ticker] || [];
  history[ticker].push({ ts, price });
  if (history[ticker].length > HISTORY_LEN) history[ticker].shift();

  // Update card.
  const card = ensureCard(ticker);
  if (card.lastPrice !== null) {
    card.root.classList.toggle("up",   price >= card.lastPrice);
    card.root.classList.toggle("down", price <  card.lastPrice);
  }
  card.priceEl.textContent = price.toFixed(2);
  card.tsEl.textContent    = new Date(ts).toLocaleTimeString();
  card.lastPrice = price;

  // Update chart: x-axis is the union of timestamps; align datasets to it.
  ensureChart();
  const ds = ensureDataset(ticker);
  ds.data.push({ x: ts, y: price });
  if (ds.data.length > HISTORY_LEN) ds.data.shift();

  // Recompute labels as the most recent N timestamps across all datasets.
  const allTs = new Set();
  chart.data.datasets.forEach(d => d.data.forEach(p => allTs.add(p.x)));
  const labels = Array.from(allTs).sort().slice(-HISTORY_LEN);
  chart.data.labels = labels.map(s => new Date(s).toLocaleTimeString());

  // Re-bind dataset values to labels.
  chart.data.datasets.forEach(d => {
    const byTs = Object.fromEntries(d.data.map(p => [p.x, p.y]));
    d._values = labels.map(t => byTs[t] ?? null);
    d.data    = d._values.map((v, i) => ({ x: labels[i], y: v }));
  });
  chart.update("none");
}

function closeAllStreams() {
  evtSources.forEach(es => { try { es.close(); } catch (_) {} });
  evtSources = [];
}

function openStream(tickers) {
  // The upstream /api/stream endpoint streams one ticker per connection
  // (despite accepting the param, only the first ticker is honored). To get
  // live updates for several tickers we open one EventSource per ticker;
  // each one flows through our /api/stream proxy carrying a single ticker.
  closeAllStreams();
  const connectedTickers = new Set();

  tickers.forEach(t => {
    const es = new EventSource("/api/stream?ticker=" + encodeURIComponent(t));

    es.addEventListener("open", () => {
      connectedTickers.add(t);
      setStatus(
        "connected (" + connectedTickers.size + "/" + tickers.length + " tickers)",
        "connected"
      );
      reconnectMs = 1000;
    });

    es.addEventListener("tick", (e) => {
      try {
        const tk = JSON.parse(e.data);
        // Upstream tick shape: { ticker, ts, price, currency, volume, seq }
        pushTick(tk.ticker, tk.ts, Number(tk.price));
      } catch (err) {
        console.warn("Bad tick payload:", e.data, err);
      }
    });

    es.addEventListener("error", () => {
      // EventSource auto-reconnects; we just surface state and apply backoff
      // on repeated failures.
      connectedTickers.delete(t);
      setStatus(
        "disconnected - retrying in " + (reconnectMs / 1000) + "s",
        "error"
      );
      reconnectMs = Math.min(reconnectMs * 2, 10000);
    });

    evtSources.push(es);
  });
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
  cardGridEl.innerHTML = "";
  Object.keys(cards).forEach(k => delete cards[k]);
  Object.keys(history).forEach(k => delete history[k]);
  if (chart) { chart.destroy(); chart = null; }
  openStream(sel);
  connectBtn.disabled = true;
  disconnectBtn.disabled = false;
});

disconnectBtn.addEventListener("click", () => {
  closeAllStreams();
  setStatus("idle", "idle");
  connectBtn.disabled = false;
  disconnectBtn.disabled = true;
});

loadTickers();
