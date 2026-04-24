from __future__ import annotations

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class FaultInjector(Node):
    """Publishes fault orchestration events for demonstration and observability.

    The active fault behavior is intentionally applied via launch-time parameters on
    sensor publisher nodes. This node provides a timeline marker topic (`/fault_events`)
    so integration tests and operators can observe when a scenario is expected to start.
    """

    def __init__(self) -> None:
        super().__init__('fault_injector')
        self.declare_parameter('scenario', 'none')
        self.declare_parameter('start_after_sec', 5.0)

        self.scenario = str(self.get_parameter('scenario').value)
        self.start_after_sec = float(self.get_parameter('start_after_sec').value)

        self.publisher = self.create_publisher(String, '/fault_events', 10)
        self.timer = self.create_timer(0.5, self._tick)
        self.start_time = self.get_clock().now()
        self.triggered = False

        self.get_logger().info(
            f'Fault injector armed with scenario={self.scenario}, start_after_sec={self.start_after_sec}'
        )

    def _tick(self) -> None:
        if self.triggered:
            return
        elapsed = (self.get_clock().now() - self.start_time).nanoseconds / 1e9
        if elapsed < self.start_after_sec:
            return

        event = String()
        event.data = f'fault_scenario_started:{self.scenario}:t={elapsed:.2f}'
        self.publisher.publish(event)
        self.get_logger().warn(f'Fault scenario marker published: {event.data}')
        self.triggered = True


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = FaultInjector()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
