# Mock Client / CLI Consumer

Consumes the mock server's SSE stream, buffers the last **N** ticks
(default 10), and exports them to JSON or CSV.

## Run

```powershell
cd mock\client-dashboard
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Example: collect 8 ticks across two symbols, write JSON
python client.py --tickers ACME,GLOBEX --buffer 8 --out ..\..\integration\out\ticks.json
```

The mock server (`mock/server/app.py`) must already be running on
`http://127.0.0.1:5050`.

## Buffer

Rolling deque of size `--buffer` (default 10). When `--duration` is 0
the client stops as soon as the buffer is full; otherwise it keeps
reading for the requested number of seconds and the deque drops the
oldest entries.

## Formats

- `--format json` (default) — pretty-printed list of tick objects.
- `--format csv` — header row + one row per tick; fields:
  `ticker,price,ts,trader_email,operator_name,comment`.
