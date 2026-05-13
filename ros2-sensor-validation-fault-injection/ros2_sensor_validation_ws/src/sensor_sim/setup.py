from setuptools import setup

package_name = 'sensor_sim'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ROS2 Sensor Validation',
    maintainer_email='dev@example.com',
    description='Simulated robotics sensor publishers with configurable fault modes.',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'imu_publisher = sensor_sim.imu_publisher:main',
            'camera_heartbeat_publisher = sensor_sim.camera_heartbeat_publisher:main',
            'wheel_odom_publisher = sensor_sim.wheel_odom_publisher:main',
        ],
    },
)
