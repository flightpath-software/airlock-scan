import sys


def load_fixed_from_argv():
    module_name = sys.argv[1]
    print(f"ignoring requested module: {module_name}")
    return __import__("os")
