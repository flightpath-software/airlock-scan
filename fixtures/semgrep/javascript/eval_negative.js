function computeFixedFormula() {
  const formula = process.env.FORMULA;
  console.log(`received formula (not executed): ${formula}`);
  return eval("1 + 1");
}

module.exports = { computeFixedFormula };
