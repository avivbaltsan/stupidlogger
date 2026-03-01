#!/usr/bin/env python3
"""Generate intentionally dumb random OpenTelemetry logs and spans."""

from __future__ import annotations

import logging
import os
import random
import signal
import time
import uuid
from dataclasses import dataclass

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from sentences import SENTENCES


SEVERITY_LEVELS = [
    logging.DEBUG,
    logging.INFO,
    logging.WARNING,
    logging.ERROR,
    logging.CRITICAL,
]


def _parse_headers(raw_headers: str | None) -> dict[str, str]:
    if not raw_headers:
        return {}
    parsed: dict[str, str] = {}
    for item in raw_headers.split(","):
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        key = key.strip()
        value = value.strip()
        if key:
            parsed[key] = value
    return parsed


def _resolve_signal_endpoint(signal_name: str) -> str:
    specific = os.getenv(f"OTEL_EXPORTER_OTLP_{signal_name}_ENDPOINT")
    if specific:
        return specific

    base = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if base:
        return f"{base.rstrip('/')}/v1/{signal_name.lower()}"

    return f"http://localhost:4318/v1/{signal_name.lower()}"


@dataclass
class Settings:
    service_name: str
    interval_seconds: float
    trace_endpoint: str
    log_endpoint: str
    headers: dict[str, str]

    @staticmethod
    def load_from_env() -> "Settings":
        service_name = os.getenv("OTEL_SERVICE_NAME", "stupidlogger")
        interval_seconds = float(os.getenv("STUPIDLOGGER_INTERVAL_SECONDS", "1.0"))
        headers = _parse_headers(os.getenv("OTEL_EXPORTER_OTLP_HEADERS"))
        return Settings(
            service_name=service_name,
            interval_seconds=max(interval_seconds, 0.1),
            trace_endpoint=_resolve_signal_endpoint("TRACES"),
            log_endpoint=_resolve_signal_endpoint("LOGS"),
            headers=headers,
        )


def main() -> None:
    settings = Settings.load_from_env()

    resource = Resource.create({"service.name": settings.service_name})

    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(endpoint=settings.trace_endpoint, headers=settings.headers)
        )
    )
    trace.set_tracer_provider(tracer_provider)
    tracer = trace.get_tracer("stupidlogger.mock")

    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(
        BatchLogRecordProcessor(
            OTLPLogExporter(endpoint=settings.log_endpoint, headers=settings.headers)
        )
    )

    app_logger = logging.getLogger("stupidlogger.mock")
    app_logger.setLevel(logging.DEBUG)
    app_logger.handlers = [LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)]
    app_logger.propagate = False

    running = True

    def _stop(*_: object) -> None:
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    print(f"service.name={settings.service_name}")
    print(f"traces endpoint={settings.trace_endpoint}")
    print(f"logs endpoint={settings.log_endpoint}")
    print(f"interval={settings.interval_seconds}s")
    print("press Ctrl+C to stop")

    while running:
        log_level = random.choice(SEVERITY_LEVELS)
        message = (
            random.choice(SENTENCES)
            if SENTENCES
            else "placeholder sentence: populate SENTENCES in sentences.py"
        )

        with tracer.start_as_current_span(f"stupid-span-{uuid.uuid4().hex[:8]}") as span:
            span.set_attribute("stupidlogger.mock", True)
            span.set_attribute("stupidlogger.interval_seconds", settings.interval_seconds)
            span.set_attribute("stupidlogger.log_level", logging.getLevelName(log_level))
            span.add_event("generated.log")

            app_logger.log(
                log_level,
                message,
                extra={
                    "stupidlogger.level": logging.getLevelName(log_level),
                    "stupidlogger.mock": True,
                },
            )

        time.sleep(settings.interval_seconds)

    logger_provider.shutdown()
    tracer_provider.shutdown()


if __name__ == "__main__":
    main()
