# stupidlogger

Very stupid Python mock generator for OpenTelemetry logs + spans.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configure

Use either a global OTLP endpoint or per-signal endpoints:

- `OTEL_EXPORTER_OTLP_ENDPOINT` (example: `http://localhost:4318`)
- `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT` (overrides traces only)
- `OTEL_EXPORTER_OTLP_LOGS_ENDPOINT` (overrides logs only)

Optional:

- `OTEL_EXPORTER_OTLP_HEADERS` (comma-separated `k=v` list)
- `OTEL_SERVICE_NAME` (default: `stupidlogger`)
- `STUPIDLOGGER_INTERVAL_SECONDS` (default: `1.0`)

## Add sentence list

Edit `sentences.py` and fill `SENTENCES`.

## Run

```bash
python3 mock_otel_generator.py
```
