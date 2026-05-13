from __future__ import annotations

from typing import Final

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class CameraHeartbeatPublisher(Node):
    """Publishes lightweight heartbeat status for camera availability checks."""

    _DROPOUT_EVERY_N: Final[int] = 15
    _STOPPED_AFTER_SEC: Final[float] = 3.0

    def __init__(self) -> None:
        super().__init__('camera_heartbeat_publisher')
        self.declare_parameter('publish_rate_hz', 10.0)
        self.declare_parameter('camera_name', 'front_camera')
        self.declare_parameter('fault_mode', 'none')

        self.publish_rate_hz = float(self.get_parameter('publish_rate_hz').value)
        self.camera_name = str(self.get_parameter('camera_name').value)
        self.fault_mode = str(self.get_parameter('fault_mode').value)

        effective_rate = self.publish_rate_hz * 0.3 if self.fault_mode == 'low_frequency' else self.publish_rate_hz
        self.publisher = self.create_publisher(String, '/camera/heartbeat', 10)
        self.timer = self.create_timer(1.0 / max(1.0, effective_rate), self._on_timer)
        self.sequence = 0
        self.start_time = self.get_clock().now()
        self._has_reported_stop = False

        self.get_logger().info(
            'Camera heartbeat publisher started with params: '
            f'publish_rate_hz={self.publish_rate_hz}, camera_name={self.camera_name}, '
            f'fault_mode={self.fault_mode}, effective_rate={effective_rate}'
        )

    def _on_timer(self) -> None:
        elapsed = (self.get_clock().now() - self.start_time).nanoseconds / 1e9
        if self.fault_mode == 'stopped_after_startup' and elapsed >= self._STOPPED_AFTER_SEC:
            if not self._has_reported_stop:
                self._has_reported_stop = True
                self.get_logger().warn('Fault transition: camera heartbeat stopped after startup phase.')
            return

        self.sequence += 1
        if self.fault_mode == 'dropout' and self.sequence % self._DROPOUT_EVERY_N == 0:
            if self.sequence % (self._DROPOUT_EVERY_N * 3) == 0:
                self.get_logger().warn('Fault state: camera heartbeat dropout event triggered.')
            return

        msg = String()
        msg.data = f'{self.camera_name}:alive:{self.sequence}'
        self.publisher.publish(msg)


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = CameraHeartbeatPublisher()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
