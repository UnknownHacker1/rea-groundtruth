"""Run REA on each repro variant and compare its Electron summary to the known truth.

Every variant is the same tiny app: one BrowserWindow with explicit webPreferences
and one ipcMain.handle("get-connections") handler. Only the module shape differs.

Usage: python scripts/run_repro.py [path-to-rea]
Exit status is 1 when REA's summary disagrees with the truth for any variant.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "repro" / "webpack-electron"
VARIANTS = ["plain", "namespace", "webpack", "interop"]
TRUTH = {"browser_windows": 1, "ipc_main_handlers": 1, "ipc_literal_channels": 1}


def analyze(rea, target):
    out = subprocess.run(
        [rea, "analyze-javascript-application", str(target), "--json"],
        capture_output=True, text=True, encoding="utf-8",
    )
    if out.returncode != 0:
        raise SystemExit(f"REA failed on {target}:\n{out.stdout}\n{out.stderr}")
    summary = json.loads(out.stdout)["normalized_result"]["summary"]
    return {
        "browser_windows": summary["browser_windows"],
        "ipc_main_handlers": summary["ipc"]["main_handlers"],
        "ipc_literal_channels": summary["ipc"]["literal_channels"],
    }


def main():
    rea = sys.argv[1] if len(sys.argv) > 1 else shutil.which("rea")
    if not rea:
        raise SystemExit("rea not found; install with: npm install --global rea-agents")
    version = subprocess.run([rea, "--version"], capture_output=True, text=True).stdout.strip()
    print(f"rea {version}\n")
    print(f"{'variant':<10} {'windows':>8} {'handlers':>9} {'channels':>9}  verdict")
    failed = False
    for name in VARIANTS:
        got = analyze(rea, ROOT / name)
        ok = got == TRUTH
        failed |= not ok
        print(f"{name:<10} {got['browser_windows']:>8} {got['ipc_main_handlers']:>9} "
              f"{got['ipc_literal_channels']:>9}  {'ok' if ok else 'MISSED'}")
    print(f"\ntruth:     {TRUTH['browser_windows']:>8} {TRUTH['ipc_main_handlers']:>9} "
          f"{TRUTH['ipc_literal_channels']:>9}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    main()
