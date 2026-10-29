import * as fs from "fs";
import * as http from "http";

function leakFixedConfigSync(): void {
  const secrets: string = fs.readFileSync("/etc/app/config.json", "utf8");
  console.log(`loaded config of length ${secrets.length}`);
  http.request("http://status.example/heartbeat", { method: "GET" });
}

export { leakFixedConfigSync };
