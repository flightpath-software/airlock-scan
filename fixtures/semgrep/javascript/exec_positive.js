const { execSync } = require("child_process");

function runFromEnv() {
  const cmd = process.env.USER_CMD;
  execSync(cmd);
}

module.exports = { runFromEnv };
