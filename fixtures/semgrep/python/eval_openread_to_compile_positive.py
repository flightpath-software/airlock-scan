def compile_from_file():
    payload = open("/tmp/user_supplied.py").read()
    code = compile(payload, "<user>", "exec")
    return code
