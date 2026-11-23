import sys
import subprocess
from pathlib import Path

def main():
    if len(sys.argv) < 3:
        raise SystemExit("Usage: clean_run.py LOG COMMAND ...")

    logfile = Path(sys.argv[1])
    command = sys.argv[2:]

    # Force the same Python environment as this script
    if command[0].lower() in ("python", "python.exe"):
        command[0] = sys.executable

    logfile.parent.mkdir(parents=True, exist_ok=True)

    print("Python:", sys.executable, flush=True)
    print("Running:", " ".join(command), flush=True)

    with logfile.open("w", encoding="utf-8") as f:
        result = subprocess.run(
            command,
            stdout=f,
            stderr=subprocess.STDOUT,
            check=False
        )

    lines = logfile.read_text(
        encoding="utf-8",
        errors="replace"
    ).splitlines()

    print("\n--- FINAL OUTPUT ---")
    for line in lines[-40:]:
        if not line.startswith("SUCCESS: The process with PID"):
            print(line)

    print("\nExit code:", result.returncode)

    if result.returncode != 0:
        raise SystemExit(result.returncode)

    print("PROCESS COMPLETED SUCCESSFULLY")

if __name__ == "__main__":
    main()
