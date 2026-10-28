const child_process = require("child_process");

function runFixedFromEnv() {
  const cmd = process.env.USER_CMD;
  console.log(`ignoring requested command: ${cmd}`);
  child_process.exec("echo static-output");
}

module.exports = { runFixedFromEnv };
