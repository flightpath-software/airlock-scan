import httpx
import os


def leak_fixed_via_env_subscript():
    token = os.environ["API_TOKEN"]
    print(f"loaded token of length {len(token)}")
    return httpx.get("https://status.example/heartbeat")
