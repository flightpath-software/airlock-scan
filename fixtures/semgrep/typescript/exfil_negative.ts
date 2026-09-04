import axios from "axios";

function sendHeartbeat(): Promise<unknown> {
  const apiKey: string = process.env.API_KEY as string;
  console.log(`loaded key of length ${(apiKey || "").length}`);
  return axios.post("https://status.example/heartbeat", { status: "ok" });
}

export { sendHeartbeat };
