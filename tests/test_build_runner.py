"""Integration tests for Build Runner Docker image."""

import subprocess
import tempfile
from pathlib import Path

def test_build_runner_image_builds():
    """Test that the Docker image builds successfully."""
    result = subprocess.run(
        ["docker", "build", "-t", "build-runner", "-f", "build-runner/Dockerfile", "."],
        capture_output=True,
        text=True,
        timeout=60
    )
    assert result.returncode == 0, f"Build failed: {result.stderr}"

def test_zephyr_blinky_build():
    """Smoke test: build official blinky sample."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Copy minimal project structure (or use volume in real CI)
        subprocess.run(["west", "init", "-m", "https://github.com/zephyrproject-rtos/zephyr", "--mr", "v4.0.0", str(tmp_path / "zephyrproject")], check=True)
        
        result = subprocess.run([
            "docker", "run", "--rm",
            "-v", f"{tmp_path}:/workspace/app",
            "build-runner",
            "build", "-b", "esp32_devkitc_wroom/esp32/procpu", "samples/basic/blinky"
        ], capture_output=True, text=True, timeout=300)
        
        assert result.returncode == 0, f"Build failed: {result.stderr}"
        assert (tmp_path / "zephyrproject/zephyr/build/zephyr/zephyr.bin").exists()