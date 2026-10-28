const axios = require("axios");

function leakFixedEnv() {
  const secret = process.env.API_KEY;
  console.log(`loaded key of length ${(secret || "").length}`);
  return axios.get("https://status.example/heartbeat");
}

module.exports = { leakFixedEnv };
