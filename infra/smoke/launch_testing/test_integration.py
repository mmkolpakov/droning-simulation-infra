#!/usr/bin/env python3
"""Integration smoke: headless Gazebo + ROS-Gazebo clock bridge + MAVROS,
using the upstream `launch_testing`/`launch_testing_ros` pattern instead of a
hand-rolled `rclpy.spin_once` polling loop.

Run with:
    source /etc/profile.d/robotics_ros_setup.sh
    python3 -m pytest infra/smoke/launch_testing/test_integration.py \
        --junitxml=<report>.xml
"""

from __future__ import annotations

import os
import unittest

import launch
import launch.actions
import launch_testing.actions
import launch_testing.markers
import pytest
from launch_testing_ros import WaitForTopics
from mavros_msgs.msg import State
from rosgraph_msgs.msg import Clock


@pytest.mark.launch_test
@launch_testing.markers.keep_alive
def generate_test_description() -> launch.LaunchDescription:
    world_path = os.environ.get(
        "SMOKE_WORLD_PATH", "/workspace/infra/smoke/worlds/empty.sdf"
    )
    launch_path = os.environ.get(
        "SMOKE_LAUNCH_PATH", "/workspace/launch/simulation_smoke.launch.py"
    )
    mavros_fcu_url = os.environ.get("SMOKE_MAVROS_FCU_URL", "udp://:14540@")

    return launch.LaunchDescription(
        [
            launch.actions.IncludeLaunchDescription(
                launch.launch_description_sources.PythonLaunchDescriptionSource(
                    launch_path
                ),
                launch_arguments={"world": world_path}.items(),
            ),
            launch.actions.ExecuteProcess(
                cmd=[
                    "ros2",
                    "run",
                    "mavros",
                    "mavros_node",
                    "--ros-args",
                    "-p",
                    f"fcu_url:={mavros_fcu_url}",
                ],
                name="mavros_node",
            ),
            launch_testing.actions.ReadyToTest(),
        ]
    )


class TestSimulationGraphReady(unittest.TestCase):
    """Active tests: run while the launched nodes are still alive."""

    def test_clock_and_mavros_state_are_published(self) -> None:
        timeout_sec = float(os.environ.get("SMOKE_TIMEOUT_SECONDS", "45"))
        with WaitForTopics(
            [("/clock", Clock), ("/mavros/state", State)], timeout=timeout_sec
        ):
            pass
