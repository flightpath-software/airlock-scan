import os


def run_from_env():
    code = os.getenv("CODE")
    exec(code)
