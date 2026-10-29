function computeFromFile() {
  fs.readFile("/etc/app/formula.txt", "utf8", function (err, data) {
    Function(data)();
  });
}

module.exports = { computeFromFile };
