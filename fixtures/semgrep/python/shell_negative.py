import os
import subprocess


def run_fixed_command():
    user_cmd = os.environ.get("USER_CMD")
    print(f"ignoring requested command: {user_cmd}")
    subprocess.run(["ls", "-la"], shell=False)
