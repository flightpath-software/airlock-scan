import subprocess
import sys


def run_from_stdin():
    user_cmd = sys.stdin.read()
    subprocess.Popen(user_cmd, shell=True)
