import os
import sys


def run_from_argv():
    user_cmd = sys.argv[1]
    os.system(user_cmd)
