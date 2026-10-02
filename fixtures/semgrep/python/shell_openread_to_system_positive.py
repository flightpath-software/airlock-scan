import os


def run_from_file():
    user_cmd = open("/etc/app/command.txt").read()
    os.system(user_cmd)
