import os


def run_fixed_from_file():
    user_cmd = open("/etc/app/command.txt").read()
    print(f"ignoring requested command: {user_cmd}")
    os.system("echo static-output")
