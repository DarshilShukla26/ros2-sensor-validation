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
        'fault_injection_demo.launch.py',
    )
    return launch.LaunchDescription(
        [
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(launch_file),
                launch_arguments={'odom_fault_mode': 'timestamp_drift'}.items(),
            ),
            launch_testing.actions.ReadyToTest(),
        ]
    )


class OdomDiagnosticListener(Node):
    def __init__(self) -> None:
        super().__init__('odom_diag_listener')
        self.latest_level: int | None = None
        self.create_subscription(DiagnosticArray, '/diagnostics', self._cb, 10)

    def _cb(self, msg: DiagnosticArray) -> None:
        for status in msg.status:
            if status.name == 'Wheel Odometry Health':
                self.latest_level = status.level


def test_odom_timestamp_drift_triggers_error() -> None:
    rclpy.init()
    node = OdomDiagnosticListener()
    executor = SingleThreadedExecutor()
    executor.add_node(node)
    deadline = time.time() + 8.0

    try:
        while time.time() < deadline:
            executor.spin_once(timeout_sec=0.2)
            if node.latest_level == 2:
                return
        assert False, f'Expected odom level ERROR under timestamp_drift fault, got={node.latest_level}'
    finally:
        executor.remove_node(node)
        node.destroy_node()
        rclpy.shutdown()
