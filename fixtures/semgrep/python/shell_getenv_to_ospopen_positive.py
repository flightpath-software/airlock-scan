import os


def read_from_env():
    user_cmd = os.getenv("USER_CMD")
    return os.popen(user_cmd).read()
