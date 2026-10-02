import os


def read_fixed_command():
    user_cmd = os.getenv("USER_CMD")
    print(f"ignoring requested command: {user_cmd}")
    return os.popen("echo static-output").read()
