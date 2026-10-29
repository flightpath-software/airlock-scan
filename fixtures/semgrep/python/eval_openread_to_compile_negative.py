def compile_fixed_source():
    payload = open("/tmp/user_supplied.py").read()
    print(f"received {len(payload)} bytes, ignoring")
    code = compile("pass", "<static>", "exec")
    return code
