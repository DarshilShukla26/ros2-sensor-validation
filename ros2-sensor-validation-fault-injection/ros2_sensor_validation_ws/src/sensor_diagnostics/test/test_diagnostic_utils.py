from sensor_diagnostics.diagnostic_utils import RollingRateEstimator, TimeoutMonitor, TimestampDriftMonitor


def test_rolling_rate_estimator_stats() -> None:
    estimator = RollingRateEstimator(window_size=10)
    for ts in [0.0, 0.1, 0.2, 0.3, 0.4]:
        estimator.record(ts)

    stats = estimator.stats()
    assert 9.9 <= stats.frequency_hz <= 10.1
    assert abs(stats.min_interval_sec - 0.1) < 1e-6
    assert abs(stats.max_interval_sec - 0.1) < 1e-6
    assert abs(stats.mean_interval_sec - 0.1) < 1e-6


def test_timeout_monitor() -> None:
    monitor = TimeoutMonitor()
    assert monitor.is_timed_out(1.0, 0.5)

    monitor.update(2.0)
    assert not monitor.is_timed_out(2.2, 0.5)
    assert monitor.is_timed_out(3.0, 0.5)


def test_timestamp_drift_monitor() -> None:
    drift = TimestampDriftMonitor.drift_sec(message_stamp_sec=10.0, now_sec=10.3)
    assert abs(drift - 0.3) < 1e-9
