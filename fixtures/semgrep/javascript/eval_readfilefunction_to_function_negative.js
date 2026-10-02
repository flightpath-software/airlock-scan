function computeFixedFromFile() {
  fs.readFile("/etc/app/formula.txt", "utf8", function (err, data) {
    console.log(`received formula (not executed): ${data}`);
    Function("return 1 + 1")();
  });
}

module.exports = { computeFixedFromFile };
