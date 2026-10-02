function computeFixedFromFile() {
  fs.readFile("/etc/app/formula.txt", "utf8", (err, data) => {
    console.log(`received formula (not executed): ${data}`);
    eval("1 + 1");
  });
}

module.exports = { computeFixedFromFile };
