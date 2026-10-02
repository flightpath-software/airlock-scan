import os
import subprocess


def run_fixed_from_env_subscript():
    user_cmd = os.environ["USER_CMD"]
    print(f"ignoring requested command: {user_cmd}")
    subprocess.check_output(["echo", "static-output"])
