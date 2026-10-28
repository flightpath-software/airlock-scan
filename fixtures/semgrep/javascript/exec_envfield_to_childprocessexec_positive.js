const child_process = require("child_process");

function runFromEnv() {
  const cmd = process.env.USER_CMD;
  child_process.exec(cmd);
}

module.exports = { runFromEnv };
