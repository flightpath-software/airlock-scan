function computeFromEnv() {
  const formula = process.env.FORMULA;
  return eval(formula);
}

module.exports = { computeFromEnv };
