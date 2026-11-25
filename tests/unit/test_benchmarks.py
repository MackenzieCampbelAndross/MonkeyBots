"""
Unit tests for Kinematics Benchmark Runner
"""
import pytest
from core.monkeybots.benchmarks.kinematics_benchmark import KinematicsBenchmarkRunner


def test_benchmark_runner():
    runner = KinematicsBenchmarkRunner(iterations=100)
    res = runner.run_benchmark()
    assert res["iterations"] == 100
    assert res["dls_avg_us"] > 0
    assert res["analytical_avg_us"] < 25.0
    assert res["throughput_hz"] > 0
