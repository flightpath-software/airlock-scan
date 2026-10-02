const { spawn } = require("child_process");

function runFromArgv() {
  const cmd = process.argv[2];
  spawn(cmd, { shell: true });
}

module.exports = { runFromArgv };
