const { spawnSync } = require("child_process");

function runFromFile() {
  fs.readFile("/etc/app/command.txt", "utf8", function (err, data) {
    spawnSync(data, { shell: true });
  });
}

module.exports = { runFromFile };
