"""Refuse pushes when the outgoing commit history cannot pass BetterLeaks."""

from pathlib import Path
import platform
import re
import subprocess
import sys

from install_push_protection import VERSION


def pre_push(root, updates):
    outgoing = []
    for line in updates.splitlines():
        fields = line.split()
        if len(fields) != 4 or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", fields[1]):
            raise RuntimeError("Unexpected push information; refusing an unchecked push.")
        oid = fields[1]
        if set(oid) == {"0"}:
            continue  # Deleting a remote ref uploads no commits.
        check = subprocess.run(["git", "-C", str(root), "rev-parse", "--verify", oid + "^{commit}"],
                               capture_output=True, text=True)
        if check.returncode:
            raise RuntimeError("A pushed object cannot be inspected as commit history.")
        outgoing.append(check.stdout.strip())
    if not outgoing:
        return 0

    result = subprocess.run(["git", "-C", str(root), "rev-parse", "--path-format=absolute", "--git-common-dir"],
                            capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError("Could not locate the scanner for this checkout.")
    binary_name = "betterleaks.exe" if platform.system() == "Windows" else "betterleaks"
    scanner = Path(result.stdout.strip()) / "security-tools" / f"betterleaks-{VERSION}" / binary_name
    if not scanner.is_file():
        raise RuntimeError("Scanner missing. Run Python 3 on .github/scripts/install_push_protection.py before pushing.")

    print("Checking committed history with BetterLeaks before uploading...", flush=True)
    # Explicit IDs cover pushes of commits not otherwise reachable through local refs.
    log_options = "--all " + " ".join(sorted(set(outgoing)))
    scan = subprocess.run([str(scanner), "git", str(root), "--log-opts=" + log_options,
                           "--redact=100", "--no-banner", "--validation=false"],
                          stdin=subprocess.DEVNULL)
    if scan.returncode:
        print("Push blocked: BetterLeaks found a secret or could not complete its scan.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(pre_push(Path(__file__).resolve().parents[2], sys.stdin.read()))
    except Exception as error:
        print("Push blocked: " + str(error), file=sys.stderr)
        sys.exit(1)
