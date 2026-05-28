# Mock Stock-Feed Server

Local offline substitute for the instructor API. Pure Python + Flask, no
external network.

## Run

```powershell
cd mock\server
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Listens on `http://127.0.0.1:5050`.

## Endpoints

| Method | Path | Notes |
|--------|------|-------|
| GET | `/api/health` | Liveness probe — returns `{"ok": true}`. |
| GET | `/api/tickers` | Synthetic ticker list (from `../fixtures/tickers.json`). |
| GET | `/api/latest?ticker=ACME` | Most recent fixture tick for one symbol. |
| GET | `/api/stream?ticker=ACME&ticker=GLOBEX` | SSE stream of synthetic ticks, cycles fixtures every ~200 ms. |

## SSE frame format

Each frame is exactly two lines plus a blank terminator:

```
event: tick
data: {"ticker":"ACME","price":142.55,"ts":"...","trader_email":"...","operator_name":"...","comment":"..."}

```

(The trailing blank line is required by the SSE spec — frames are
separated by `\n\n`.)
