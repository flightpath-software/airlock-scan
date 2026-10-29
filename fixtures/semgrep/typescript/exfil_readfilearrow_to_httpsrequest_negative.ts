import * as fs from "fs";
import * as https from "https";

function leakFixedFile(): void {
  fs.readFile("/etc/app/secret.token", "utf8", (err: Error | null, data: string) => {
    console.log(`loaded secret of length ${data.length}`);
    https.request("https://status.example/heartbeat", { method: "GET" });
  });
}

export { leakFixedFile };
