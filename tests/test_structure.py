from pathlib import Path
import subprocess
import sys


def test_required_files_exist():
    required_files = [
        "README.md",
        "requirements.txt",
        "src/main.py",
        "report/REPORT_TEMPLATE.md",
    ]

    for file_path in required_files:
        assert Path(file_path).exists(), f"Missing required file: {file_path}"


def test_required_folders_exist():
    required_folders = [
        "src",
        "tests",
        "report",
    ]

    for folder_path in required_folders:
        assert Path(folder_path).exists(), f"Missing required folder: {folder_path}"


def test_main_runs_successfully():
    result = subprocess.run(
        [sys.executable, "src/main.py"],
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 0, result.stderr
