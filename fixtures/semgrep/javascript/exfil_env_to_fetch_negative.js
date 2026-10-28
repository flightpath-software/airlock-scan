function dumpFixedEnv() {
  const snapshot = JSON.stringify(process.env);
  console.log(`captured ${snapshot.length} bytes, not sending`);
  return fetch("https://status.example/heartbeat", { method: "POST", body: "ok" });
}

module.exports = { dumpFixedEnv };
