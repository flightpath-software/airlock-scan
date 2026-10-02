function leakFixedFile() {
  fs.readFile("/etc/app/secret.token", "utf8", function (err, data) {
    console.log(`loaded secret of length ${data.length}`);
    fetch("https://status.example/heartbeat", { method: "GET" });
  });
}

module.exports = { leakFixedFile };
