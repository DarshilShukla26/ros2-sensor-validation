from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description() -> LaunchDescription:
    thresholds_file = os.path.join(get_package_share_directory('robot_bringup'), 'config', 'thresholds.yaml')

    imu_fault_mode = LaunchConfiguration('imu_fault_mode')
    camera_fault_mode = LaunchConfiguration('camera_fault_mode')
    odom_fault_mode = LaunchConfiguration('odom_fault_mode')
    scenario = LaunchConfiguration('scenario')
    start_after_sec = LaunchConfiguration('start_after_sec')

    return LaunchDescription(
        [
            DeclareLaunchArgument('imu_fault_mode', default_value='none'),
            DeclareLaunchArgument('camera_fault_mode', default_value='none'),
            DeclareLaunchArgument('odom_fault_mode', default_value='none'),
            DeclareLaunchArgument('scenario', default_value='none'),
            DeclareLaunchArgument('start_after_sec', default_value='5.0'),
            Node(
                package='sensor_sim',
                executable='imu_publisher',
                name='imu_publisher',
                parameters=[{'fault_mode': imu_fault_mode}],
            ),
            Node(
                package='sensor_sim',
                executable='camera_heartbeat_publisher',
                name='camera_heartbeat_publisher',
                parameters=[{'fault_mode': camera_fault_mode}],
            ),
            Node(
                package='sensor_sim',
                executable='wheel_odom_publisher',
                name='wheel_odom_publisher',
                parameters=[{'fault_mode': odom_fault_mode}],
            ),
            Node(
                package='sensor_diagnostics',
                executable='sensor_health_monitor',
                name='sensor_health_monitor',
                parameters=[thresholds_file],
            ),
            Node(
                package='sensor_diagnostics',
                executable='fault_injector',
                name='fault_injector',
                parameters=[{'scenario': scenario, 'start_after_sec': start_after_sec}],
            ),
        ]
    )
