"""Install a verified local scanner and enable this checkout's pre-push hook."""

import hashlib
import io
import os
from pathlib import Path
import platform
import subprocess
import sys
import tarfile
from urllib.request import urlopen
import zipfile


VERSION = "1.9.0"
ARCHIVES = {
    ("Windows", "x64"): ("windows_x64.zip", "b765daec9fda475b031b5a5159798cbe4294a3f2a50683cbc0471226e376d3da"),
    ("Windows", "arm64"): ("windows_arm64.zip", "3e5b9b6cdbfe8d486ae2dd2fa137473dc9ab42bf50317f051b73561121861816"),
    ("Linux", "x64"): ("linux_x64.tar.gz", "f8b185a39ffcece2a1ca82bf3a4e7435cd81963ffd16b7a9128daf75f35f6de7"),
    ("Linux", "arm64"): ("linux_arm64.tar.gz", "1d39116e0a58dc94574715e2aa12a2dbd5062f193eee3fec011fef6ba06bd13b"),
    ("Darwin", "x64"): ("darwin_x64.tar.gz", "68dfd83458d9e7f90663daa7a81c7f944083b170dae82e4f5f8d0581ed519ef1"),
    ("Darwin", "arm64"): ("darwin_arm64.tar.gz", "83dd7eaab13d44a1e8e347a17064cdef153a1478db473276d41b38d55613d3f2"),
}


def git(root, *args, optional=False):
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    if result.returncode and not (optional and result.returncode == 1):
        raise RuntimeError("Could not inspect or configure this Git checkout.")
    return result.stdout.strip()


def install(root):
    configured = git(root, "config", "--get", "core.hooksPath", optional=True)
    default_hook = Path(git(root, "rev-parse", "--path-format=absolute", "--git-path", "hooks/pre-push"))
    if configured and configured != ".githooks":
        raise RuntimeError("An existing hooks directory is configured. Integrate the pre-push check there instead; it was not overwritten.")
    if not configured and default_hook.exists():
        raise RuntimeError("An existing pre-push hook was found. Integrate this check with it instead; it was not overwritten.")
    hook = root / ".githooks/pre-push"
    if not hook.is_file():
        raise RuntimeError("The tracked pre-push hook is missing.")

    architecture = platform.machine().lower()
    architecture = {"amd64": "x64", "x86_64": "x64", "aarch64": "arm64"}.get(architecture, architecture)
    try:
        suffix, expected_hash = ARCHIVES[(platform.system(), architecture)]
    except KeyError as error:
        raise RuntimeError("This platform has no configured BetterLeaks release archive.") from error
    name = f"betterleaks_{VERSION}_{suffix}"
    url = f"https://github.com/betterleaks/betterleaks/releases/download/v{VERSION}/{name}"
    print("Downloading the pinned BetterLeaks release...", flush=True)
    with urlopen(url, timeout=90) as response:
        archive = response.read()
    if hashlib.sha256(archive).hexdigest() != expected_hash:
        raise RuntimeError("BetterLeaks archive checksum mismatch. Push protection was not changed.")

    binary_name = "betterleaks.exe" if platform.system() == "Windows" else "betterleaks"
    if suffix.endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
            binary = bundle.read(binary_name)
    else:
        with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as bundle:
            member = bundle.getmember(binary_name)
            if not member.isfile():
                raise RuntimeError("The scanner archive does not contain the expected executable.")
            binary = bundle.extractfile(member).read()

    git_dir = Path(git(root, "rev-parse", "--path-format=absolute", "--git-common-dir"))
    destination = git_dir / "security-tools" / f"betterleaks-{VERSION}" / binary_name
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".download")
    temporary.write_bytes(binary)
    temporary.chmod(0o755)
    os.replace(temporary, destination)
    hook.chmod(0o755)
    git(root, "config", "--local", "core.hooksPath", ".githooks")
    print("Verified BetterLeaks and enabled pre-push protection for this checkout.", flush=True)


if __name__ == "__main__":
    try:
        install(Path(__file__).resolve().parents[2])
    except RuntimeError as error:
        print("Setup failed: " + str(error), file=sys.stderr)
        sys.exit(1)
    except Exception:
        print("Setup failed. Check the download connection and checkout permissions; no hook configuration was changed.", file=sys.stderr)
        sys.exit(1)
