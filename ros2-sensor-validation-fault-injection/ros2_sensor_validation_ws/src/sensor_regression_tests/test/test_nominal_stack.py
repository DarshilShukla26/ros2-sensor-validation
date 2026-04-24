from __future__ import annotations

import os
import time

from ament_index_python.packages import get_package_share_directory
import launch
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
import launch_testing.actions
import pytest
import rclpy
from diagnostic_msgs.msg import DiagnosticArray
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node


@pytest.mark.launch_test
def generate_test_description():
    launch_file = os.path.join(
        get_package_share_directory('robot_bringup'),
        'launch',
        'validation_stack.launch.py',
    )
    return launch.LaunchDescription(
        [
            IncludeLaunchDescription(PythonLaunchDescriptionSource(launch_file)),
            launch_testing.actions.ReadyToTest(),
        ]
    )


class DiagnosticListener(Node):
    def __init__(self) -> None:
        super().__init__('nominal_diag_listener')
        self.latest_levels: dict[str, int] = {}
        self.subscription = self.create_subscription(DiagnosticArray, '/diagnostics', self._cb, 10)

    def _cb(self, msg: DiagnosticArray) -> None:
        for status in msg.status:
            self.latest_levels[status.name] = status.level


def test_nominal_stack_reports_ok() -> None:
    rclpy.init()
    node = DiagnosticListener()
    executor = SingleThreadedExecutor()
    executor.add_node(node)
    deadline = time.time() + 7.0

    try:
        required = [
            'IMU Topic Health',
            'Camera Heartbeat Health',
            'Wheel Odometry Health',
            'System Startup Readiness',
        ]
        while time.time() < deadline:
            executor.spin_once(timeout_sec=0.2)
            if all(node.latest_levels.get(name) == 0 for name in required):
                return
        assert False, f'Expected all diagnostics OK within timeout, got={node.latest_levels}'
    finally:
        executor.remove_node(node)
        node.destroy_node()
        rclpy.shutdown()
