function evalEnv() {
  const snapshot = JSON.stringify(process.env);
  return eval(snapshot);
}

module.exports = { evalEnv };
