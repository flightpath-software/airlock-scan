const cp = require("child_process");

function logEnv() {
  const snapshot = JSON.stringify(process.env);
  cp.exec(`logger ${snapshot}`);
}

module.exports = { logEnv };
