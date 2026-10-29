const fs = require("fs");
const cp = require("child_process");

function runFixedFromFile() {
  const cmd = fs.readFileSync("/etc/app/command.txt", "utf8");
  console.log(`ignoring requested command: ${cmd}`);
  cp.exec("echo static-output");
}

module.exports = { runFixedFromFile };
