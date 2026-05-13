from __future__ import annotations

from typing import Final

import rclpy
from nav_msgs.msg import Odometry
from rclpy.duration import Duration
from rclpy.node import Node


class WheelOdomPublisher(Node):
    """Publishes simple forward-motion wheel odometry with fault injection support."""

    _DROPOUT_EVERY_N: Final[int] = 25

    def __init__(self) -> None:
        super().__init__('wheel_odom_publisher')
        self.declare_parameter('publish_rate_hz', 50.0)
        self.declare_parameter('frame_id', 'odom')
        self.declare_parameter('child_frame_id', 'base_link')
        self.declare_parameter('fault_mode', 'none')

        self.publish_rate_hz = float(self.get_parameter('publish_rate_hz').value)
        self.frame_id = str(self.get_parameter('frame_id').value)
        self.child_frame_id = str(self.get_parameter('child_frame_id').value)
        self.fault_mode = str(self.get_parameter('fault_mode').value)

        effective_rate = self.publish_rate_hz * 0.25 if self.fault_mode == 'low_frequency' else self.publish_rate_hz
        self.publisher = self.create_publisher(Odometry, '/wheel/odom', 10)
        self.timer = self.create_timer(1.0 / max(1.0, effective_rate), self._on_timer)
        self.sequence = 0
        self.position_x = 0.0
        self.velocity_x = 0.5

        self.get_logger().info(
            'Wheel odometry publisher started with params: '
            f'publish_rate_hz={self.publish_rate_hz}, frame_id={self.frame_id}, '
            f'child_frame_id={self.child_frame_id}, fault_mode={self.fault_mode}, '
            f'effective_rate={effective_rate}'
        )

    def _on_timer(self) -> None:
        self.sequence += 1
        if self.fault_mode == 'dropout' and self.sequence % self._DROPOUT_EVERY_N == 0:
            return

        dt = 1.0 / max(self.publish_rate_hz, 1.0)
        self.position_x += self.velocity_x * dt

        msg = Odometry()
        now = self.get_clock().now()
        if self.fault_mode == 'timestamp_drift':
            now = now - Duration(seconds=0.7)

        msg.header.stamp = now.to_msg()
        msg.header.frame_id = self.frame_id
        msg.child_frame_id = self.child_frame_id

        msg.pose.pose.position.x = self.position_x
        msg.pose.pose.position.y = 0.0
        msg.pose.pose.position.z = 0.0
        msg.pose.pose.orientation.w = 1.0

        msg.twist.twist.linear.x = self.velocity_x
        msg.twist.twist.angular.z = 0.0

        msg.pose.covariance = [
            0.02,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.02,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.05,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.01,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.01,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.01,
        ]
        msg.twist.covariance = [
            0.02,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.02,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.05,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.01,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.01,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.01,
        ]

        self.publisher.publish(msg)


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = WheelOdomPublisher()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
