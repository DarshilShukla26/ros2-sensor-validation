# ROS2 Sensor Validation and Fault Injection Framework

`ros2-sensor-validation-fault-injection` is a practical ROS2 Humble project for validating upstream sensor stream health before perception and localization pipelines consume data. It simulates common robot streams (IMU, camera heartbeat, wheel odometry), evaluates runtime quality signals (frequency, timeout, timestamp drift, startup readiness), and provides fault injection + regression tests to catch integration regressions early.

## Why this project exists

Autonomous systems depend on stable sensor timing and availability. This project validates sensor stream health before downstream perception/localization modules consume data.

## Architecture (ASCII)

```text
IMU Publisher ----\
Camera Heartbeat --> Health Monitor --> /diagnostics
Wheel Odometry ---/
                       ^
                       |
                Fault Injection Demo
```

## Features

- Simulated IMU, camera heartbeat, and wheel odometry streams
- Topic frequency monitoring with rolling estimators
- Sensor timeout detection
- Timestamp drift detection for timestamped sensors
- Startup readiness validation across required streams
- Fault injection scenarios for degraded and failure modes
- Automated regression tests with pytest/launch_testing structure

## Requirements

- Ubuntu 22.04
- ROS2 Humble
- Python 3

## Repository layout

```text
ros2-sensor-validation-fault-injection/
├── README.md
├── .gitignore
├── requirements.txt
└── ros2_sensor_validation_ws/
    └── src/
        ├── sensor_sim/
        ├── sensor_diagnostics/
        ├── robot_bringup/
        └── sensor_regression_tests/
```

## Installation

```bash
source /opt/ros/humble/setup.bash
cd ros2-sensor-validation-fault-injection/ros2_sensor_validation_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build
source install/setup.bash
```

## Run nominal stack

```bash
ros2 launch robot_bringup validation_stack.launch.py
```

## Inspect topics

```bash
ros2 topic list
ros2 topic echo /diagnostics
ros2 topic hz /imu/data
ros2 topic hz /camera/heartbeat
ros2 topic hz /wheel/odom
```

## Run fault demos

```bash
ros2 launch robot_bringup fault_injection_demo.launch.py imu_fault_mode:=low_frequency
ros2 launch robot_bringup fault_injection_demo.launch.py camera_fault_mode:=stopped_after_startup
ros2 launch robot_bringup fault_injection_demo.launch.py odom_fault_mode:=timestamp_drift
```

## Run tests

```bash
cd ros2-sensor-validation-fault-injection/ros2_sensor_validation_ws
colcon test
colcon test-result --verbose

# Package-focused run
colcon test --packages-select sensor_regression_tests
colcon test-result --verbose
```

## Expected diagnostic behavior

| Scenario | Expected Diagnostic |
|---|---|
| Nominal | all OK |
| IMU low frequency | IMU WARN/ERROR |
| Camera stopped | Camera ERROR |
| Odom timestamp drift | Odom ERROR |

## Engineering decisions

- **Heartbeat separate from image data**: image topics are high-bandwidth and expensive to deserialize only for liveness checks; a heartbeat isolates availability from data-heavy payload transport.
- **Timestamp drift monitoring**: even when frequency is high, stale/future timestamps can break sensor fusion and state estimation.
- **Frequency as a regression signal**: rate degradation often surfaces CPU contention, QoS mismatch, and scheduling problems early.
- **Fault injection in bringup**: launch-controlled fault modes provide repeatable integration scenarios for CI and pre-deployment checks.

## Troubleshooting

- **ROS2 not sourced**: run `source /opt/ros/humble/setup.bash` and `source install/setup.bash` in each shell.
- **Package not found**: confirm build succeeded and you sourced the workspace overlay from `ros2_sensor_validation_ws/install/setup.bash`.
- **Diagnostics not publishing**: verify publishers are up (`ros2 node list`) and check `/diagnostics` subscription counts with `ros2 topic info /diagnostics`.
- **colcon build failure**: run `rosdep install --from-paths src --ignore-src -r -y`, then rebuild from a clean tree (`rm -rf build install log`).
- **Topic frequency lower than expected on slow laptops**: reduce publish rates or thresholds in `robot_bringup/config/thresholds.yaml` to match platform constraints.

## Future improvements

- Integrate rosbag replay for replay-driven validation
- Add TF tree validation and frame consistency checks
- Integrate `diagnostic_aggregator` for dashboard-friendly summaries
- Add real hardware serial bridge adapters
- Add GitHub Actions CI for build + regression automation

## Resume bullet

```text
\resumeProjectHeading
{ROS2 Sensor Validation and Fault Injection Framework}
{Python, C++, ROS2, Linux, PyTest}
\resumeItemListStart
\resumeItem{Built a ROS2-based validation framework for robotic sensor streams, integrating simulated IMU, camera heartbeat, and wheel odometry publishers with launch files, startup checks, and structured diagnostic reporting.}
\resumeItem{Implemented fault injection for sensor dropout, timestamp drift, degraded publish frequency, and missing heartbeat signals to evaluate robustness before downstream perception or localization modules consume data.}
\resumeItem{Developed automated regression tests for topic frequency, message timeout, startup readiness, and timestamp consistency, enabling repeatable validation of robotic software integration changes.}
\resumeItemListEnd
```
