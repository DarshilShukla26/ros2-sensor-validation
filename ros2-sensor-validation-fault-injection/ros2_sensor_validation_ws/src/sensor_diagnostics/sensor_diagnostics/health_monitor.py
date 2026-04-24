from __future__ import annotations

from dataclasses import dataclass

import rclpy
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import Imu
from std_msgs.msg import String

from sensor_diagnostics.diagnostic_utils import (
    DiagnosticLevel,
    RollingRateEstimator,
    TimeoutMonitor,
    TimestampDriftMonitor,
)


@dataclass
class SensorState:
    name: str
    expected_rate_hz: float
    min_rate_hz: float
    has_timestamp: bool
    estimator: RollingRateEstimator
    timeout_monitor: TimeoutMonitor
    last_header_stamp_sec: float | None = None
    received_count: int = 0
    level: DiagnosticLevel = DiagnosticLevel.WARN


class SensorHealthMonitor(Node):
    """Monitors key sensor streams and publishes consolidated diagnostics."""

    def __init__(self) -> None:
        super().__init__('sensor_health_monitor')

        self.declare_parameter('imu_expected_rate_hz', 100.0)
        self.declare_parameter('imu_min_rate_hz', 90.0)
        self.declare_parameter('camera_expected_rate_hz', 10.0)
        self.declare_parameter('camera_min_rate_hz', 8.0)
        self.declare_parameter('odom_expected_rate_hz', 50.0)
        self.declare_parameter('odom_min_rate_hz', 45.0)
        self.declare_parameter('sensor_timeout_sec', 1.0)
        self.declare_parameter('max_timestamp_drift_sec', 0.20)
        self.declare_parameter('startup_grace_period_sec', 2.0)

        self.sensor_timeout_sec = float(self.get_parameter('sensor_timeout_sec').value)
        self.max_timestamp_drift_sec = float(self.get_parameter('max_timestamp_drift_sec').value)
        self.startup_grace_period_sec = float(self.get_parameter('startup_grace_period_sec').value)

        self.imu = SensorState(
            name='IMU Topic Health',
            expected_rate_hz=float(self.get_parameter('imu_expected_rate_hz').value),
            min_rate_hz=float(self.get_parameter('imu_min_rate_hz').value),
            has_timestamp=True,
            estimator=RollingRateEstimator(),
            timeout_monitor=TimeoutMonitor(),
        )
        self.camera = SensorState(
            name='Camera Heartbeat Health',
            expected_rate_hz=float(self.get_parameter('camera_expected_rate_hz').value),
            min_rate_hz=float(self.get_parameter('camera_min_rate_hz').value),
            has_timestamp=False,
            estimator=RollingRateEstimator(),
            timeout_monitor=TimeoutMonitor(),
        )
        self.odom = SensorState(
            name='Wheel Odometry Health',
            expected_rate_hz=float(self.get_parameter('odom_expected_rate_hz').value),
            min_rate_hz=float(self.get_parameter('odom_min_rate_hz').value),
            has_timestamp=True,
            estimator=RollingRateEstimator(),
            timeout_monitor=TimeoutMonitor(),
        )

        self.previous_levels: dict[str, DiagnosticLevel] = {}
        self.start_time = self.get_clock().now()
        self.last_summary_log_sec = 0.0

        self.diag_pub = self.create_publisher(DiagnosticArray, '/diagnostics', 10)
        self.create_subscription(Imu, '/imu/data', self._on_imu, 50)
        self.create_subscription(String, '/camera/heartbeat', self._on_camera, 50)
        self.create_subscription(Odometry, '/wheel/odom', self._on_odom, 50)
        self.timer = self.create_timer(1.0, self._publish_diagnostics)

    def _to_sec(self, stamp) -> float:
        return float(stamp.sec) + float(stamp.nanosec) / 1e9

    def _now_sec(self) -> float:
        return self.get_clock().now().nanoseconds / 1e9

    def _on_imu(self, msg: Imu) -> None:
        now_sec = self._now_sec()
        self.imu.estimator.record(now_sec)
        self.imu.timeout_monitor.update(now_sec)
        self.imu.last_header_stamp_sec = self._to_sec(msg.header.stamp)
        self.imu.received_count += 1

    def _on_camera(self, _msg: String) -> None:
        now_sec = self._now_sec()
        self.camera.estimator.record(now_sec)
        self.camera.timeout_monitor.update(now_sec)
        self.camera.received_count += 1

    def _on_odom(self, msg: Odometry) -> None:
        now_sec = self._now_sec()
        self.odom.estimator.record(now_sec)
        self.odom.timeout_monitor.update(now_sec)
        self.odom.last_header_stamp_sec = self._to_sec(msg.header.stamp)
        self.odom.received_count += 1

    def _evaluate_sensor(self, state: SensorState, now_sec: float) -> tuple[DiagnosticStatus, float, float]:
        stats = state.estimator.stats()
        age_sec = state.timeout_monitor.age_sec(now_sec)
        timed_out = state.timeout_monitor.is_timed_out(now_sec, self.sensor_timeout_sec)
        drift_sec = 0.0

        level = DiagnosticLevel.OK
        message = 'Healthy'

        if state.received_count == 0:
            level = DiagnosticLevel.ERROR
            message = 'No messages received'
        elif timed_out:
            level = DiagnosticLevel.ERROR
            message = 'Sensor timed out'
        elif state.has_timestamp and state.last_header_stamp_sec is not None:
            drift_sec = TimestampDriftMonitor.drift_sec(state.last_header_stamp_sec, now_sec)
            if drift_sec > self.max_timestamp_drift_sec:
                level = DiagnosticLevel.ERROR
                message = 'Timestamp drift too high'

        if level != DiagnosticLevel.ERROR and stats.frequency_hz < state.min_rate_hz and state.received_count > 3:
            level = DiagnosticLevel.WARN
            message = 'Observed frequency below threshold'

        state.level = level

        status = DiagnosticStatus()
        status.name = state.name
        status.level = int(level)
        status.message = message
        status.hardware_id = 'simulated'
        status.values = [
            KeyValue(key='observed_rate_hz', value=f'{stats.frequency_hz:.2f}'),
            KeyValue(key='expected_rate_hz', value=f'{state.expected_rate_hz:.2f}'),
            KeyValue(key='last_msg_age_sec', value='inf' if age_sec == float('inf') else f'{age_sec:.3f}'),
            KeyValue(key='message_count', value=str(state.received_count)),
        ]
        if state.has_timestamp:
            status.values.append(KeyValue(key='timestamp_drift_sec', value=f'{drift_sec:.3f}'))

        self._log_level_transition(state.name, level, message)
        return status, stats.frequency_hz, age_sec

    def _startup_readiness_status(self, now_sec: float) -> DiagnosticStatus:
        elapsed = now_sec - (self.start_time.nanoseconds / 1e9)
        received = {
            'imu': self.imu.received_count > 0,
            'camera': self.camera.received_count > 0,
            'odom': self.odom.received_count > 0,
        }
        all_received = all(received.values())

        status = DiagnosticStatus()
        status.name = 'System Startup Readiness'
        status.hardware_id = 'system'

        if elapsed <= self.startup_grace_period_sec:
            status.level = int(DiagnosticLevel.WARN)
            status.message = 'Startup grace period active'
        elif all_received:
            status.level = int(DiagnosticLevel.OK)
            status.message = 'All sensors observed after startup'
        else:
            status.level = int(DiagnosticLevel.ERROR)
            status.message = 'Missing required sensor stream(s) after grace period'

        status.values = [
            KeyValue(key='startup_elapsed_sec', value=f'{elapsed:.2f}'),
            KeyValue(key='grace_period_sec', value=f'{self.startup_grace_period_sec:.2f}'),
            KeyValue(key='imu_seen', value=str(received['imu'])),
            KeyValue(key='camera_seen', value=str(received['camera'])),
            KeyValue(key='odom_seen', value=str(received['odom'])),
        ]
        return status

    def _log_level_transition(self, name: str, level: DiagnosticLevel, message: str) -> None:
        previous = self.previous_levels.get(name)
        if previous is None or previous != level:
            self.previous_levels[name] = level
            self.get_logger().warn(f'Diagnostic transition | {name}: {previous} -> {level} ({message})')

    def _publish_diagnostics(self) -> None:
        now_sec = self._now_sec()
        imu_status, imu_rate, _ = self._evaluate_sensor(self.imu, now_sec)
        camera_status, camera_rate, _ = self._evaluate_sensor(self.camera, now_sec)
        odom_status, odom_rate, _ = self._evaluate_sensor(self.odom, now_sec)
        startup_status = self._startup_readiness_status(now_sec)

        diag_array = DiagnosticArray()
        diag_array.header.stamp = self.get_clock().now().to_msg()
        diag_array.status = [imu_status, camera_status, odom_status, startup_status]
        self.diag_pub.publish(diag_array)

        if now_sec - self.last_summary_log_sec >= 3.0:
            self.last_summary_log_sec = now_sec
            self.get_logger().info(
                'Health Summary | '
                f'IMU: {DiagnosticLevel(imu_status.level).name} {imu_rate:.1f}Hz | '
                f'Camera: {DiagnosticLevel(camera_status.level).name} {camera_rate:.1f}Hz | '
                f'Odom: {DiagnosticLevel(odom_status.level).name} {odom_rate:.1f}Hz'
            )


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = SensorHealthMonitor()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
