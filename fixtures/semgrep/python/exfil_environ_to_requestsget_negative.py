import os
import requests


def leak_fixed_env():
    snapshot = dict(os.environ)
    print(f"captured {len(snapshot)} variables, not sending")
    requests.get("https://status.example/heartbeat")
