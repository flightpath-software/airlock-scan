import os
import subprocess


def run_from_env_subscript():
    user_cmd = os.environ["USER_CMD"]
    subprocess.check_output(user_cmd, shell=True)
