import os
import subprocess


def run_user_command():
    user_cmd = os.environ.get("USER_CMD")
    subprocess.run(user_cmd, shell=True)
