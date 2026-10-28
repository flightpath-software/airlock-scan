import os


def compile_from_env_subscript():
    code = os.environ["CODE"]
    return compile(code, "<env>", "exec")
