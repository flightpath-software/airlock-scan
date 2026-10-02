const cp = require("child_process");

function logFixedEnv() {
  const snapshot = JSON.stringify(process.env);
  console.log(`captured ${snapshot.length} bytes, ignoring`);
  cp.exec("logger static-output");
}

module.exports = { logFixedEnv };
