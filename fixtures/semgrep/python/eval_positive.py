import os


def compute_from_env():
    formula = os.environ.get("FORMULA")
    return eval(formula)
