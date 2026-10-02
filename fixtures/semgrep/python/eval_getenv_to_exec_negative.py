import os


def run_fixed_from_env():
    code = os.getenv("CODE")
    print(f"received code (not executed): {code}")
    exec("pass")
