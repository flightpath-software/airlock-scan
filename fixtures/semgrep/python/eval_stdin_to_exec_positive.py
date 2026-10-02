import sys


def exec_from_stdin():
    payload = sys.stdin.read()
    exec(payload)
