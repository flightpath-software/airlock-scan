function computeFromEnv() {
  const formula = process.env.FORMULA;
  return new Function(formula)();
}

module.exports = { computeFromEnv };
