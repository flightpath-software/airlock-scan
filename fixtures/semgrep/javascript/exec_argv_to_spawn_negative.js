const { spawn } = require("child_process");

function runFixedFromArgv() {
  const cmd = process.argv[2];
  console.log(`ignoring requested command: ${cmd}`);
  spawn("echo", ["static-output"]);
}

module.exports = { runFixedFromArgv };
