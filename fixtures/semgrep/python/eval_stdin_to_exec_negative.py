import sys


def exec_fixed_from_stdin():
    payload = sys.stdin.read()
    print(f"received {len(payload)} bytes, ignoring")
    exec("pass")
