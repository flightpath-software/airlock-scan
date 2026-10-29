import httpx
import os


def dump_fixed_env():
    snapshot = dict(os.environ)
    print(f"captured {len(snapshot)} variables, not sending")
    httpx.post("https://status.example/heartbeat", json={"status": "ok"})
