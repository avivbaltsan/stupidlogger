#!/usr/bin/env python3
"""Generate intentionally dumb random OpenTelemetry logs and spans."""

from __future__ import annotations

import logging
import os
import random
import signal
import time
from dataclasses import dataclass

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
)

from sentences import SENTENCES


SEVERITY_LEVELS = [
    logging.DEBUG,
    logging.INFO,
    logging.WARNING,
    logging.ERROR,
    logging.CRITICAL,
]

SPAN_NAMES = [
    "calculating-chips-density",
    "perfecting-chips-crispiness",
    "estimating-pita-fragility",
    "balancing-salt-chaos",
    "stabilizing-fry-temperature",
    "forecasting-crunch-longevity",
    "optimizing-dip-adhesion",
    "simulating-snack-satisfaction",
]

LOG_OUTPUT_MODES = {"otlp", "stdout", "both"}
TRACE_OUTPUT_MODES = {"otlp", "stdout", "both", "none"}


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
    log_output: str
    trace_output: str

    @staticmethod
    def load_from_env() -> "Settings":
        service_name = os.getenv("OTEL_SERVICE_NAME", "stupidlogger")
        interval_seconds = float(os.getenv("STUPIDLOGGER_INTERVAL_SECONDS", "1.0"))
        headers = _parse_headers(os.getenv("OTEL_EXPORTER_OTLP_HEADERS"))
        log_output = os.getenv("STUPIDLOGGER_LOG_OUTPUT", "otlp").strip().lower()
        if log_output not in LOG_OUTPUT_MODES:
            log_output = "otlp"
        default_trace_output = "none" if log_output == "stdout" else "otlp"
        trace_output = (
            os.getenv("STUPIDLOGGER_TRACE_OUTPUT", default_trace_output).strip().lower()
        )
        if trace_output not in TRACE_OUTPUT_MODES:
            trace_output = default_trace_output
        if log_output == "stdout":
            trace_output = "none"
        return Settings(
            service_name=service_name,
            interval_seconds=max(interval_seconds, 0.1),
            trace_endpoint=_resolve_signal_endpoint("TRACES"),
            log_endpoint=_resolve_signal_endpoint("LOGS"),
            headers=headers,
            log_output=log_output,
            trace_output=trace_output,
        )


def main() -> None:
    settings = Settings.load_from_env()

    resource = Resource.create({"service.name": settings.service_name})

    spans_enabled = settings.trace_output != "none"

    tracer_provider = TracerProvider(resource=resource)
    if settings.trace_output in {"otlp", "both"}:
        tracer_provider.add_span_processor(
            BatchSpanProcessor(
                OTLPSpanExporter(endpoint=settings.trace_endpoint, headers=settings.headers)
            )
        )
    if settings.trace_output in {"stdout", "both"}:
        tracer_provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(tracer_provider)
    tracer = trace.get_tracer("stupidlogger.mock")

    logger_provider: LoggerProvider | None = None

    app_logger = logging.getLogger("stupidlogger.mock")
    app_logger.setLevel(logging.DEBUG)
    app_logger.handlers = []
    app_logger.propagate = False

    if settings.log_output in {"otlp", "both"}:
        logger_provider = LoggerProvider(resource=resource)
        logger_provider.add_log_record_processor(
            BatchLogRecordProcessor(
                OTLPLogExporter(endpoint=settings.log_endpoint, headers=settings.headers)
            )
        )
        app_logger.addHandler(
            LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)
        )
    if settings.log_output in {"stdout", "both"}:
        stdout_handler = logging.StreamHandler()
        stdout_handler.setLevel(logging.DEBUG)
        stdout_handler.setFormatter(
            logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
        )
        app_logger.addHandler(stdout_handler)

    running = True

    def _stop(*_: object) -> None:
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    print(f"service.name={settings.service_name}")
    if settings.trace_output in {"otlp", "both"}:
        print(f"traces endpoint={settings.trace_endpoint}")
    print(f"trace output={settings.trace_output}")
    if settings.log_output in {"otlp", "both"}:
        print(f"logs endpoint={settings.log_endpoint}")
    print(f"log output={settings.log_output}")
    print(f"interval={settings.interval_seconds}s")
    print("press Ctrl+C to stop")

    while running:
        log_level = random.choice(SEVERITY_LEVELS)
        message = (
            random.choice(SENTENCES)
            if SENTENCES
            else "placeholder sentence: populate SENTENCES in sentences.py"
        )

        if spans_enabled:
            with tracer.start_as_current_span(random.choice(SPAN_NAMES)) as span:
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
        else:
            app_logger.log(
                log_level,
                message,
                extra={
                    "stupidlogger.level": logging.getLevelName(log_level),
                    "stupidlogger.mock": True,
                },
            )

        time.sleep(settings.interval_seconds)

    if logger_provider is not None:
        logger_provider.shutdown()
    tracer_provider.shutdown()


if __name__ == "__main__":
    main()
