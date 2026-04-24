from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from enum import IntEnum
from typing import Deque


class DiagnosticLevel(IntEnum):
    OK = 0
    WARN = 1
    ERROR = 2


@dataclass
class RollingRateStats:
    frequency_hz: float
    min_interval_sec: float
    max_interval_sec: float
    mean_interval_sec: float
    message_count: int


class RollingRateEstimator:
    """Estimate observed publish rate by tracking recent receive timestamps."""

    def __init__(self, window_size: int = 200) -> None:
        self._timestamps: Deque[float] = deque(maxlen=window_size)

    def record(self, timestamp_sec: float) -> None:
        self._timestamps.append(timestamp_sec)

    def stats(self) -> RollingRateStats:
        if len(self._timestamps) < 2:
            return RollingRateStats(0.0, 0.0, 0.0, 0.0, len(self._timestamps))

        intervals = [
            self._timestamps[idx] - self._timestamps[idx - 1]
            for idx in range(1, len(self._timestamps))
            if self._timestamps[idx] - self._timestamps[idx - 1] > 0.0
        ]
        if not intervals:
            return RollingRateStats(0.0, 0.0, 0.0, 0.0, len(self._timestamps))

        mean_interval = sum(intervals) / len(intervals)
        frequency = 1.0 / mean_interval if mean_interval > 0.0 else 0.0
        return RollingRateStats(
            frequency_hz=frequency,
            min_interval_sec=min(intervals),
            max_interval_sec=max(intervals),
            mean_interval_sec=mean_interval,
            message_count=len(self._timestamps),
        )


class TimeoutMonitor:
    """Track last receive time and determine if the stream timed out."""

    def __init__(self) -> None:
        self._last_message_time_sec: float | None = None

    def update(self, now_sec: float) -> None:
        self._last_message_time_sec = now_sec

    def age_sec(self, now_sec: float) -> float:
        if self._last_message_time_sec is None:
            return float('inf')
        return max(0.0, now_sec - self._last_message_time_sec)

    def is_timed_out(self, now_sec: float, timeout_sec: float) -> bool:
        return self.age_sec(now_sec) > timeout_sec


class TimestampDriftMonitor:
    """Compute absolute drift between message header stamp and local ROS time."""

    @staticmethod
    def drift_sec(message_stamp_sec: float, now_sec: float) -> float:
        return abs(now_sec - message_stamp_sec)
