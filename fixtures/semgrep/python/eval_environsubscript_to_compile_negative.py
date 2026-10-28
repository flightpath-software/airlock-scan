import os


def compile_fixed_from_env_subscript():
    code = os.environ["CODE"]
    print(f"received code (not executed): {code}")
    return compile("pass", "<static>", "exec")
