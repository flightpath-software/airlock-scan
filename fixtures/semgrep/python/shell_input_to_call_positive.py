import subprocess


def run_from_prompt():
    user_cmd = input("Enter command: ")
    subprocess.call(user_cmd, shell=True)
