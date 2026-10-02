const { exec } = require("child_process");

function runFromFile() {
  fs.readFile("/etc/app/command.txt", "utf8", (err, data) => {
    exec(data);
  });
}

module.exports = { runFromFile };
