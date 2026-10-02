const { spawnSync } = require("child_process");

function runFixedFromFile() {
  fs.readFile("/etc/app/command.txt", "utf8", function (err, data) {
    console.log(`ignoring requested command: ${data}`);
    spawnSync("echo", ["static-output"]);
  });
}

module.exports = { runFixedFromFile };
