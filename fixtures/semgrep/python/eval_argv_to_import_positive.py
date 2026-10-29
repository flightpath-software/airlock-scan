import sys


def load_from_argv():
    module_name = sys.argv[1]
    return __import__(module_name)
