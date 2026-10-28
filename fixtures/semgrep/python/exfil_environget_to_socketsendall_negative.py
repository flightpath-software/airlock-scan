import os
import socket


def leak_fixed_via_socket():
    api_key = os.environ.get("API_KEY")
    print(f"loaded key of length {len(api_key or '')}")
    socket.socket().sendall(b"static-output")
