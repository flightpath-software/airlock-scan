function computeFromEnv() {
  const formula = process.env.FORMULA;
  return Function(formula)();
}

module.exports = { computeFromEnv };
