import os


def compute_fixed_formula():
    formula = os.environ.get("FORMULA")
    print(f"received formula (not executed): {formula}")
    return eval("1 + 1")
