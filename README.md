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
- `STUPIDLOGGER_LOG_OUTPUT` (`otlp`, `stdout`, or `both`; default: `otlp`)
- `STUPIDLOGGER_TRACE_OUTPUT` (`otlp`, `stdout`, `both`, or `none`)

If `STUPIDLOGGER_LOG_OUTPUT=stdout`, logs are printed to stdout instead of being sent to the OTEL collector.
When `STUPIDLOGGER_LOG_OUTPUT=stdout`, span creation/export is forcibly disabled (`trace_output=none`) to keep stdout log lines parse-friendly.

## Add sentence list

Edit `sentences.py` and fill `SENTENCES`.

## Run

```bash
python3 mock_otel_generator.py
```
