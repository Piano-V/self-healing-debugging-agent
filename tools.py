import os
import shutil
import subprocess
import sys
import tempfile


def run_pytest(target_code: str, test_suite_code: str) -> tuple[bool, str]:
    """Executes pytest on target_code using the provided test_suite_code.

    Creates a temporary directory, writes target_code.py and test_suite.py to it,
    runs pytest in a subprocess under the active Python environment, captures the
    resulting stdout/stderr logs, and cleans up the temporary directory.

    Args:
        target_code: The content of target_code.py to be tested.
        test_suite_code: The pytest suite content testing target_code.py.

    Returns:
        A tuple of (passed, test_logs) where:
            passed (bool): True if tests passed successfully, False otherwise.
            test_logs (str): The execution logs including error traceback.
    """
    # Create a temporary directory to isolate test run
    temp_dir = tempfile.mkdtemp()
    try:
        # Define paths for temporary code and test files
        target_path = os.path.join(temp_dir, "target_code.py")
        test_path = os.path.join(temp_dir, "test_suite.py")

        # Write files
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(target_code)

        with open(test_path, "w", encoding="utf-8") as f:
            f.write(test_suite_code)

        # Run pytest inside the temporary directory.
        # Using sys.executable guarantees using the same virtual env/python interpreter.
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "test_suite.py", "-v"],
            capture_output=True,
            text=True,
            cwd=temp_dir,
            check=False,
        )

        passed = result.returncode == 0
        logs = f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        return passed, logs

    except Exception as e:
        return False, f"Failed to run pytest due to exception: {str(e)}"

    finally:
        # Safely clean up the directory
        shutil.rmtree(temp_dir, ignore_errors=True)
