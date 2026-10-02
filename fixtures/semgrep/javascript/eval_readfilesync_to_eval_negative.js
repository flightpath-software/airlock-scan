const fs = require("fs");

function computeFixedFromFile() {
  const formula = fs.readFileSync("/etc/app/formula.txt", "utf8");
  console.log(`received formula (not executed): ${formula}`);
  return eval("1 + 1");
}

module.exports = { computeFixedFromFile };
