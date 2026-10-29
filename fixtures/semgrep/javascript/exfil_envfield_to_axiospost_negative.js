const axios = require("axios");

function sendHeartbeat() {
  const apiKey = process.env.API_KEY;
  console.log(`loaded key of length ${(apiKey || "").length}`);
  return axios.post("https://status.example/heartbeat", { status: "ok" });
}

module.exports = { sendHeartbeat };
