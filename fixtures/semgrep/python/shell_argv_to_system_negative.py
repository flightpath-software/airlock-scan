import os
import sys


def run_fixed_from_argv():
    user_cmd = sys.argv[1]
    print(f"ignoring requested command: {user_cmd}")
    os.system("echo static-output")
