function computeFixedFromArgv() {
  const formula = process.argv[2];
  console.log(`received formula (not executed): ${formula}`);
  return eval("1 + 1");
}

module.exports = { computeFixedFromArgv };
