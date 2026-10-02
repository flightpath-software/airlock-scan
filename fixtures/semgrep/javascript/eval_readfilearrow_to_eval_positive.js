function computeFromFile() {
  fs.readFile("/etc/app/formula.txt", "utf8", (err, data) => {
    eval(data);
  });
}

module.exports = { computeFromFile };
