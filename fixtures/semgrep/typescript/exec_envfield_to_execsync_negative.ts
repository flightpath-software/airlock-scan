import { execSync } from "child_process";

function runFixedCommand(): void {
  const cmd: string = process.env.USER_CMD as string;
  console.log(`ignoring requested command: ${cmd}`);
  execSync("echo static-output");
}

export { runFixedCommand };
