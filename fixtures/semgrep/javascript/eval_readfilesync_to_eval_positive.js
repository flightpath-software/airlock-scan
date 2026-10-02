const fs = require("fs");

function computeFromFile() {
  const formula = fs.readFileSync("/etc/app/formula.txt", "utf8");
  return eval(formula);
}

module.exports = { computeFromFile };
