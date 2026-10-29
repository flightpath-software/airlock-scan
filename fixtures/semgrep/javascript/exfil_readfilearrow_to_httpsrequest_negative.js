const https = require("https");

function leakFixedFile() {
  fs.readFile("/etc/app/secret.token", "utf8", (err, data) => {
    console.log(`loaded secret of length ${data.length}`);
    https.request("https://status.example/heartbeat", { method: "GET" });
  });
}

module.exports = { leakFixedFile };
