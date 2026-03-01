"""Configuration for stupidlogger."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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


def _resolve_signal_endpoint(
    signal_name: str, specific: str | None, base: str | None
) -> str:
    if specific:
        return specific
    if base:
        return f"{base.rstrip('/')}/v1/{signal_name.lower()}"
    return f"http://localhost:4318/v1/{signal_name.lower()}"


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables."""

    model_config = SettingsConfigDict(populate_by_name=True, extra="ignore")

    service_name: str = Field(default="stupidlogger", alias="OTEL_SERVICE_NAME")
    interval_seconds: float = Field(default=1.0, alias="STUPIDLOGGER_INTERVAL_SECONDS")
    interval_jitter_ratio: float = Field(
        default=0.2, alias="STUPIDLOGGER_INTERVAL_JITTER_RATIO"
    )
    log_output: Literal["otlp", "stdout", "both"] = Field(
        default="otlp", alias="STUPIDLOGGER_LOG_OUTPUT"
    )
    trace_output: Literal["otlp", "stdout", "both", "none"] | None = Field(
        default=None, alias="STUPIDLOGGER_TRACE_OUTPUT"
    )

    otlp_endpoint: str | None = Field(default=None, alias="OTEL_EXPORTER_OTLP_ENDPOINT")
    otlp_traces_endpoint: str | None = Field(
        default=None, alias="OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"
    )
    otlp_logs_endpoint: str | None = Field(
        default=None, alias="OTEL_EXPORTER_OTLP_LOGS_ENDPOINT"
    )
    otlp_headers_raw: str | None = Field(default=None, alias="OTEL_EXPORTER_OTLP_HEADERS")
    headers: dict[str, str] = Field(default_factory=dict)

    @field_validator("interval_seconds")
    @classmethod
    def _validate_interval(cls, value: float) -> float:
        return max(value, 0.1)

    @field_validator("interval_jitter_ratio")
    @classmethod
    def _validate_interval_jitter_ratio(cls, value: float) -> float:
        return max(value, 0.0)

    @field_validator("log_output", "trace_output", mode="before")
    @classmethod
    def _normalize_output_modes(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip().lower()

    @model_validator(mode="after")
    def _finalize(self) -> "Settings":
        self.headers = _parse_headers(self.otlp_headers_raw)

        if self.log_output == "stdout":
            # Force spans off so stdout logs remain easy to parse by line readers.
            self.trace_output = "none"
        elif self.trace_output is None:
            self.trace_output = "otlp"

        return self

    @property
    def trace_endpoint(self) -> str:
        return _resolve_signal_endpoint(
            "TRACES", self.otlp_traces_endpoint, self.otlp_endpoint
        )

    @property
    def log_endpoint(self) -> str:
        return _resolve_signal_endpoint("LOGS", self.otlp_logs_endpoint, self.otlp_endpoint)
