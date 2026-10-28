import subprocess
import sys


def run_fixed_from_stdin():
    user_cmd = sys.stdin.read()
    print(f"ignoring requested command: {user_cmd}")
    subprocess.Popen(["echo", "static-output"])
