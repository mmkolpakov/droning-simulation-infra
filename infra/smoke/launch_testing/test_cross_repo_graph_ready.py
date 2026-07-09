#!/usr/bin/env python3
"""Cross-repo integration graph readiness check.

Replaces `ros_graph_observer.py` (a bespoke rclpy polling script run as a
sidecar container) with `launch_testing_ros.WaitForTopics` used directly:
the ROS graph under test is started by the sibling `cross-repo-simulation`
compose service (`launch/simulation_smoke.launch.py`), not by this test, so
this only needs `WaitForTopics`' "attach to an already-running graph" mode
-- no `generate_test_description`/`launch_test` decorator required.

Run with:
    source /etc/profile.d/robotics_ros_setup.sh
    python3 -m pytest infra/smoke/launch_testing/test_cross_repo_graph_ready.py \
        --junitxml=<report>.xml
"""

from __future__ import annotations

import os

from launch_testing_ros import WaitForTopics
from rosgraph_msgs.msg import Clock


def test_clock_topic_is_ready() -> None:
    timeout_sec = float(os.environ.get("SMOKE_TIMEOUT_SECONDS", "60"))
    with WaitForTopics([("/clock", Clock)], timeout=timeout_sec):
        pass
