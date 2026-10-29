function computeFromArgv() {
  const formula = process.argv[2];
  return eval(formula);
}

module.exports = { computeFromArgv };
