"""Sentence source for mock logs and spans."""

from __future__ import annotations

import logging
from dataclasses import dataclass


@dataclass(frozen=True)
class LogSentence:
    message: str
    allowed_levels: tuple[int, ...]


LOG_SENTENCES: list[LogSentence] = [
    LogSentence(
        message="Problem calculating fries density",
        allowed_levels=(logging.ERROR, logging.CRITICAL),
    ),
    LogSentence(
        message="Fries too big to calculate",
        allowed_levels=(logging.WARNING, logging.ERROR),
    ),
    LogSentence(
        message="Found best chip density!",
        allowed_levels=(logging.DEBUG, logging.INFO),
    ),
    LogSentence(
        message="Crunch calibration completed with majestic precision",
        allowed_levels=(logging.DEBUG, logging.INFO),
    ),
    LogSentence(
        message="Chip thickness detector is feeling optimistic today",
        allowed_levels=(logging.DEBUG, logging.INFO),
    ),
    LogSentence(
        message="Minor oil wobble detected, crunch may vary",
        allowed_levels=(logging.WARNING,),
    ),
    LogSentence(
        message="Salt distribution suspiciously uneven, investigating",
        allowed_levels=(logging.WARNING, logging.ERROR),
    ),
    LogSentence(
        message="Dip adhesion experiment failed with loud sadness",
        allowed_levels=(logging.ERROR, logging.CRITICAL),
    ),
    LogSentence(
        message="Critical crispiness collapse in sector nacho-7",
        allowed_levels=(logging.CRITICAL,),
    ),
    LogSentence(
        message="Recovered from sogginess incident, morale restored",
        allowed_levels=(logging.INFO, logging.WARNING),
    ),
]

SPAN_SENTENCES: list[str] = [
    "calculating-chips-density",
    "perfecting-chips-crispiness",
    "estimating-pita-fragility",
    "balancing-salt-chaos",
    "stabilizing-fry-temperature",
    "forecasting-crunch-longevity",
    "optimizing-dip-adhesion",
    "simulating-snack-satisfaction",
    "repairing-seasoning-matrix",
    "debugging-soggy-outlier",
]
