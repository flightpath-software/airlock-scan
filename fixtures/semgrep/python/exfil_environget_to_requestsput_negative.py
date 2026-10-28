import os
import requests


def leak_fixed_api_key():
    api_key = os.environ.get("API_KEY")
    print(f"loaded key of length {len(api_key or '')}")
    requests.put("https://status.example/heartbeat", data="ok")
