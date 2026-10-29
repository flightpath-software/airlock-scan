const fs = require("fs");

function leakFixedConfig() {
  const secrets = fs.readFileSync("/etc/app/config.json", "utf8");
  console.log(`loaded config of length ${secrets.length}`);
  return fetch("https://collector.example/ingest", {
    method: "POST",
    body: "static-payload",
  });
}

module.exports = { leakFixedConfig };
