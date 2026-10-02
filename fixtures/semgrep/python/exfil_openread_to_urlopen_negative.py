import urllib.request


def leak_fixed_file():
    secrets = open("/etc/app/config.json").read()
    print(f"loaded config of length {len(secrets)}")
    urllib.request.urlopen("https://status.example/heartbeat")
