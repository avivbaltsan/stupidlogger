#!/usr/bin/env python3
"""Generate intentionally dumb random OpenTelemetry logs and spans."""

from __future__ import annotations

import logging
import random
import signal
import time

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

from settings import Settings
from sentences import LOG_SENTENCES, SPAN_SENTENCES

def main() -> None:
    settings = Settings()

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
    print(f"interval jitter ratio={settings.interval_jitter_ratio}")
    print("press Ctrl+C to stop")

    while running:
        if LOG_SENTENCES:
            sentence = random.choice(LOG_SENTENCES)
            message = sentence.message
            log_level = random.choice(sentence.allowed_levels)
        else:
            message = "placeholder sentence: populate LOG_SENTENCES in sentences.py"
            log_level = logging.INFO

        if spans_enabled:
            span_name = (
                random.choice(SPAN_SENTENCES) if SPAN_SENTENCES else "calculating-chips-density"
            )
            with tracer.start_as_current_span(span_name) as span:
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

        jitter = random.uniform(
            -settings.interval_jitter_ratio, settings.interval_jitter_ratio
        )
        sleep_seconds = max(0.01, settings.interval_seconds * (1.0 + jitter))
        time.sleep(sleep_seconds)

    if logger_provider is not None:
        logger_provider.shutdown()
    tracer_provider.shutdown()


if __name__ == "__main__":
    main()
