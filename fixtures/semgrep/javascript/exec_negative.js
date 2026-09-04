const { execSync } = require("child_process");

function runFixedCommand() {
  const cmd = process.env.USER_CMD;
  console.log(`ignoring requested command: ${cmd}`);
  execSync("echo static-output");
}

module.exports = { runFixedCommand };
