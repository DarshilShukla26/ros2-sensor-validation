from __future__ import annotations

import math
import random
from typing import Final

import rclpy
from rclpy.duration import Duration
from rclpy.node import Node
from sensor_msgs.msg import Imu


class ImuPublisher(Node):
    """Publishes synthetic IMU data with configurable fault modes."""

    _DROPOUT_EVERY_N: Final[int] = 20

    def __init__(self) -> None:
        super().__init__('imu_publisher')
        self.declare_parameter('publish_rate_hz', 100.0)
        self.declare_parameter('frame_id', 'imu_link')
        self.declare_parameter('noise_stddev', 0.01)
        self.declare_parameter('fault_mode', 'none')

        self.publish_rate_hz = float(self.get_parameter('publish_rate_hz').value)
        self.frame_id = str(self.get_parameter('frame_id').value)
        self.noise_stddev = float(self.get_parameter('noise_stddev').value)
        self.fault_mode = str(self.get_parameter('fault_mode').value)

        effective_rate = self.publish_rate_hz * 0.2 if self.fault_mode == 'low_frequency' else self.publish_rate_hz
        self.publisher = self.create_publisher(Imu, '/imu/data', 10)
        self.timer = self.create_timer(1.0 / max(1.0, effective_rate), self._on_timer)
        self.sequence = 0

        self.get_logger().info(
            'IMU publisher started with params: '
            f'publish_rate_hz={self.publish_rate_hz}, frame_id={self.frame_id}, '
            f'noise_stddev={self.noise_stddev}, fault_mode={self.fault_mode}, '
            f'effective_rate={effective_rate}'
        )

    def _on_timer(self) -> None:
        self.sequence += 1
        if self.fault_mode == 'dropout' and self.sequence % self._DROPOUT_EVERY_N == 0:
            return

        msg = Imu()
        now = self.get_clock().now()
        if self.fault_mode == 'stale_timestamp':
            now = now - Duration(seconds=0.8)

        msg.header.stamp = now.to_msg()
        msg.header.frame_id = self.frame_id

        t = self.sequence / max(self.publish_rate_hz, 1.0)
        msg.angular_velocity.x = random.gauss(0.0, self.noise_stddev)
        msg.angular_velocity.y = random.gauss(0.0, self.noise_stddev)
        msg.angular_velocity.z = math.sin(0.5 * t) * 0.1 + random.gauss(0.0, self.noise_stddev)

        msg.linear_acceleration.x = random.gauss(0.0, self.noise_stddev)
        msg.linear_acceleration.y = random.gauss(0.0, self.noise_stddev)
        msg.linear_acceleration.z = 9.81 + random.gauss(0.0, self.noise_stddev)

        msg.orientation_covariance = [0.01, 0.0, 0.0, 0.0, 0.01, 0.0, 0.0, 0.0, 0.01]
        msg.angular_velocity_covariance = [
            self.noise_stddev**2,
            0.0,
            0.0,
            0.0,
            self.noise_stddev**2,
            0.0,
            0.0,
            0.0,
            self.noise_stddev**2,
        ]
        msg.linear_acceleration_covariance = [
            self.noise_stddev**2,
            0.0,
            0.0,
            0.0,
            self.noise_stddev**2,
            0.0,
            0.0,
            0.0,
            self.noise_stddev**2,
        ]

        self.publisher.publish(msg)


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = ImuPublisher()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
