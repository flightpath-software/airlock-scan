const fs = require("fs");
const cp = require("child_process");

function runFromFile() {
  const cmd = fs.readFileSync("/etc/app/command.txt", "utf8");
  cp.exec(cmd);
}

module.exports = { runFromFile };
