#!/usr/bin/env python3
"""Headless Gazebo joint motion smoke.

Metrics are recorded as `<property>` tags on the JUnit XML report via
pytest's `record_property`, replacing the old bespoke
`run-metrics.v1`-shaped JSON file (`SMOKE_JOINT_METRICS_PATH`).

Run with:
    source /etc/profile.d/robotics_ros_setup.sh
    python3 -m pytest infra/smoke/launch_testing/test_joint_motion.py \
        --junitxml=<report>.xml
"""

from __future__ import annotations

import os
import re
import subprocess
import time
from typing import Any

ERROR_RE = re.compile(r"(error|failed|exception)", re.IGNORECASE)


def test_joint_motion_completes_without_errors(record_property: Any) -> None:
    world_path = os.environ.get(
        "SMOKE_JOINT_WORLD_PATH", "/workspace/infra/smoke/worlds/joint_motion.sdf"
    )
    iterations = int(os.environ.get("SMOKE_JOINT_ITERATIONS", "200"))

    started = time.monotonic()
    completed = subprocess.run(
        [
            "bash",
            "-lc",
            (
                "source /etc/profile.d/robotics_ros_setup.sh && "
                f"gz sim -s -r -v 3 --iterations {iterations} {world_path}"
            ),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    duration_s = time.monotonic() - started
    output = completed.stdout + completed.stderr

    record_property("iterations", iterations)
    record_property("duration_s", round(duration_s, 3))
    record_property("returncode", completed.returncode)

    failed = completed.returncode != 0 or bool(ERROR_RE.search(output))
    assert not failed, output[-2000:]
