import { execSync } from "child_process";

function runFromEnv(): void {
  const cmd: string = process.env.USER_CMD as string;
  execSync(cmd);
}

export { runFromEnv };
