import subprocess


def run_fixed_from_prompt():
    user_cmd = input("Enter command (ignored): ")
    print(f"ignoring requested command: {user_cmd}")
    subprocess.call(["echo", "static-output"])
