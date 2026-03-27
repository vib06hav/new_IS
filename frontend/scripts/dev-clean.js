const fs = require("fs");
const path = require("path");
const { spawn } = require("child_process");

const nextDir = path.join(process.cwd(), ".next");

try {
  fs.rmSync(nextDir, { recursive: true, force: true });
  console.log("Removed stale .next cache.");
} catch (error) {
  console.error("Failed to remove .next cache.", error);
  process.exit(1);
}

const args = process.argv.slice(2);
const child = spawn("npx", ["next", "dev", ...args], {
  stdio: "inherit",
  shell: true,
});

child.on("exit", (code) => {
  process.exit(code ?? 0);
});
