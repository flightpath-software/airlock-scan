function computeFixedFromEnv() {
  const formula = process.env.FORMULA;
  console.log(`received formula (not executed): ${formula}`);
  return new Function("return 1 + 1")();
}

module.exports = { computeFixedFromEnv };
