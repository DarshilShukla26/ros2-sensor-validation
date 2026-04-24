from setuptools import setup

package_name = 'sensor_regression_tests'

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
    description='Regression tests for ROS2 sensor validation stack.',
    license='Apache-2.0',
    tests_require=['pytest'],
)
