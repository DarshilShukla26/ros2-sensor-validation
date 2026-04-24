from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description() -> LaunchDescription:
    thresholds_file = os.path.join(get_package_share_directory('robot_bringup'), 'config', 'thresholds.yaml')

    return LaunchDescription(
        [
            Node(package='sensor_sim', executable='imu_publisher', name='imu_publisher', parameters=[{'fault_mode': 'none'}]),
            Node(
                package='sensor_sim',
                executable='camera_heartbeat_publisher',
                name='camera_heartbeat_publisher',
                parameters=[{'fault_mode': 'none'}],
            ),
            Node(
                package='sensor_sim',
                executable='wheel_odom_publisher',
                name='wheel_odom_publisher',
                parameters=[{'fault_mode': 'none'}],
            ),
            Node(
                package='sensor_diagnostics',
                executable='sensor_health_monitor',
                name='sensor_health_monitor',
                parameters=[thresholds_file],
            ),
        ]
    )
