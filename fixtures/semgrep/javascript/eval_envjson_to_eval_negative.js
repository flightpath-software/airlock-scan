function evalFixedEnv() {
  const snapshot = JSON.stringify(process.env);
  console.log(`captured ${snapshot.length} bytes, not evaluated`);
  return eval("1 + 1");
}

module.exports = { evalFixedEnv };
