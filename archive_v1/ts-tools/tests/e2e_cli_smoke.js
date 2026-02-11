/* Simple CLI E2E smoke test for SquatchCut TS tools. */

const path = require("path");
const { execFile } = require("child_process");

const FIXTURE_DIR = path.join(__dirname, "..", "test-data");
const SMALL_CSV = path.join(FIXTURE_DIR, "valid_panels_small.csv");
const MULTI_CSV = path.join(FIXTURE_DIR, "valid_panels_multi_sheet.csv");
const INVALID_CSV = path.join(FIXTURE_DIR, "invalid_rows_mixed.csv");

function runCli(csvPath) {
  return new Promise((resolve) => {
    execFile("node", [path.join(__dirname, "..", "dist", "cli.js"), csvPath], (error, stdout, stderr) => {
      const code = error && typeof error.code === "number" ? error.code : 0;
      resolve({ code, stdout: stdout || "", stderr: stderr || "" });
    });
  });
}

async function main() {
  try {
    let res = await runCli(SMALL_CSV);
    if (res.code !== 0) {
      console.error("CLI failed for small CSV", res.stderr);
      process.exit(1);
    }
    console.log("CLI E2E passed for small CSV");

    res = await runCli(MULTI_CSV);
    if (res.code !== 0) {
      console.error("CLI failed for multi-sheet CSV", res.stderr);
      process.exit(1);
    }
    console.log("CLI E2E passed for multi-sheet CSV");

    res = await runCli(INVALID_CSV);
    if (res.code !== 0) {
      // tolerate non-zero but ensure errors surfaced
      if (!res.stderr.includes("ERROR:")) {
        console.error("CLI invalid CSV did not report errors as expected");
        process.exit(1);
      }
    } else if (!res.stderr.includes("ERROR:")) {
      console.error("CLI invalid CSV did not report errors as expected");
      process.exit(1);
    }
    console.log("CLI E2E handled invalid CSV with errors reported");

    process.exit(0);
  } catch (err) {
    console.error("CLI E2E failed:", err);
    process.exit(1);
  }
}

main();
