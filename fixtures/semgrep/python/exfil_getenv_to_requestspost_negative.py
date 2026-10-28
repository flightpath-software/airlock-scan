import os
import requests


def send_heartbeat():
    api_key = os.getenv("API_KEY")
    print(f"loaded key of length {len(api_key or '')}")
    requests.post("https://status.example/heartbeat", json={"status": "ok"})
