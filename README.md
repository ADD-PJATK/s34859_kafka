# s34859_kafka — Real-time Stock Data (Kafka / SSE)

Course assignment for **ADD** (PJATK). Two small Python/Flask apps that consume a
live stream of fictitious stock prices for 50 companies, served by the
instructor's HTTP/SSE facade in front of a Kafka broker:
**`https://add.piotrkojalowicz.dev`**.

## Apps

| Folder | What it does |
|---|---|
| [`app1-dashboard/`](app1-dashboard/) | Realtime dashboard — connects to `/api/stream` (SSE), shows live ticker / price / timestamp + a rolling Chart.js line chart for the selected tickers. |
| [`app2-history/`](app2-history/) | History downloader / viewer — polls `/api/latest` every 10 s for the selected tickers, accumulates a window of up to ~10 minutes, displays a table + chart, and exports as CSV or JSON. |

Each app folder has its own `README.md` with full prerequisites / installation /
configuration / run instructions.

## API key

Get one at <https://add.piotrkojalowicz.dev/> (class password: `[REDACTED]`).

The key is read from the `ADD_API_KEY` environment variable, loaded from a local
`.env` file (see `.env.example`). `.env` is gitignored — **the key is never
committed**.

## Screenshots

See [`screenshots/`](screenshots/):

- `app1-dashboard.png` — App #1 with live updates for ≥2 tickers and the chart.
- `app2-history-table.png` — App #2 showing the populated table for a chosen range.
- `app2-history-download.png` — A downloaded CSV with real rows.

## Conversation transcript

The full Claude Code session that produced this repo is exported to
[`chat-transcript.md`](chat-transcript.md).
