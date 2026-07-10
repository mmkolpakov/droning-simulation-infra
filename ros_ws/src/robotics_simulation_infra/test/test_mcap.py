from __future__ import annotations

import os
import re
import signal
import subprocess
import tempfile
import threading
import time
import unittest
from pathlib import Path

import launch
import launch_testing.actions
import launch_testing.markers
import rclpy
from rclpy.executors import SingleThreadedExecutor
from std_msgs.msg import String


@launch_testing.markers.keep_alive
def generate_test_description() -> launch.LaunchDescription:
    return launch.LaunchDescription([launch_testing.actions.ReadyToTest()])


def stop_process(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    os.killpg(process.pid, signal.SIGINT)
    try:
        process.wait(timeout=15)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=5)


class TestMcap(unittest.TestCase):
    def test_record_info_and_replay(self) -> None:
        rclpy.init()
        publisher_node = rclpy.create_node("mcap_probe_publisher")
        publisher = publisher_node.create_publisher(String, "/mcap_probe", 10)
        publisher_node.create_timer(0.05, lambda: publisher.publish(String(data="probe")))
        executor = SingleThreadedExecutor()
        executor.add_node(publisher_node)
        spin_thread = threading.Thread(target=executor.spin, daemon=True)
        spin_thread.start()

        with tempfile.TemporaryDirectory(prefix="robotics-mcap-") as temporary:
            bag = Path(temporary) / "probe"
            recorder = subprocess.Popen(
                [
                    "ros2",
                    "bag",
                    "record",
                    "--storage",
                    "mcap",
                    "--output",
                    str(bag),
                    "--topics",
                    "/mcap_probe",
                ],
                text=True,
                start_new_session=True,
            )
            try:
                time.sleep(4)
            finally:
                stop_process(recorder)

            executor.shutdown(timeout_sec=5)
            spin_thread.join(timeout=5)
            publisher_node.destroy_node()
            info = subprocess.run(
                ["ros2", "bag", "info", str(bag)],
                check=True,
                capture_output=True,
                text=True,
            ).stdout
            self.assertIn("mcap", info.lower())
            self.assertIn("/mcap_probe", info)
            match = re.search(r"Messages:\s+(\d+)", info)
            self.assertIsNotNone(match)
            self.assertGreater(int(match.group(1)), 0)

            replay_node = rclpy.create_node("mcap_probe_replay")
            received: list[String] = []
            replay_node.create_subscription(String, "/mcap_probe", received.append, 10)
            playback = subprocess.Popen(
                ["ros2", "bag", "play", str(bag)],
                text=True,
                start_new_session=True,
            )
            deadline = time.monotonic() + 30
            try:
                while not received and time.monotonic() < deadline:
                    rclpy.spin_once(replay_node, timeout_sec=0.5)
                self.assertTrue(received)
                self.assertEqual(received[-1].data, "probe")
            finally:
                stop_process(playback)
                replay_node.destroy_node()
                rclpy.shutdown()
