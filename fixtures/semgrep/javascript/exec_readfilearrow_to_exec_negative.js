const { exec } = require("child_process");

function runFixedFromFile() {
  fs.readFile("/etc/app/command.txt", "utf8", (err, data) => {
    console.log(`ignoring requested command: ${data}`);
    exec("echo static-output");
  });
}

module.exports = { runFixedFromFile };
