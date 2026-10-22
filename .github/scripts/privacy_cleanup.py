"""Prepare audited history, then refresh hosting after its authorized publication."""

import base64
from datetime import datetime, timedelta, timezone
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time
from urllib.parse import urlsplit
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def git(*args):
    result = subprocess.run(["git", *args], capture_output=True)
    if result.returncode:
        raise RuntimeError("A Git cleanup operation failed. No command or credential details were logged.")
    return result.stdout


def github(method, path, data=None):
    request = Request("https://api.github.com/repos/" + os.environ["GITHUB_REPOSITORY"] + path,
                      data=json.dumps(data).encode() if data is not None else None,
                      method=method, headers={"Authorization": "Bearer " + os.environ["GH_TOKEN"],
                      "Content-Type": "application/json", "Accept": "application/vnd.github+json",
                      "X-GitHub-Api-Version": "2022-11-28"})
    try:
        with urlopen(request, timeout=45) as response:
            return json.loads(response.read()) if response.status != 204 else None
    except HTTPError as error:
        raise RuntimeError(f"GitHub API returned HTTP {error.code} for {method} {path}.") from error


def private_values():
    values = [os.environ[name].strip() for name in
              ("CPANEL_HOST", "CPANEL_USERNAME", "CPANEL_REPOSITORY_ROOT", "CPANEL_API_TOKEN")]
    raw = values[0]
    hostname = urlsplit(raw if "://" in raw else "https://" + raw).hostname
    if hostname:
        values.extend([hostname, hostname.split(".")[0]])
    return sorted({value.encode() for value in values if value}, key=len, reverse=True)


def rewrite(values):
    with tempfile.TemporaryDirectory() as temporary:
        replacements = Path(temporary) / "replacements.txt"
        replacements.write_bytes(b"\n".join(b"literal:" + value + b"==>[redacted]" for value in values))
        result = subprocess.run([
            "git", "filter-repo", "--force", "--path", "DEPLOYMENT.md", "--invert-paths",
            "--replace-text", str(replacements), "--replace-message", str(replacements), "--email-callback",
            'return email if email.endswith(b"@users.noreply.github.com") else b"59712311+zincodrone@users.noreply.github.com"',
        ], capture_output=True)
        if result.returncode:
            raise RuntimeError("History filtering failed; the remote branch has not been rewritten.")


def audit(values):
    metadata = git("log", "--all", "--format=%ae%n%ce")
    if any(b"@" in email and not email.endswith(b"@users.noreply.github.com")
           for email in metadata.splitlines()):
        raise RuntimeError("A personal email remains in rewritten commit metadata.")
    if any(value in git("log", "--all", "--format=%B") for value in values):
        raise RuntimeError("A sensitive value remains in a rewritten commit message.")
    signatures = re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----|"
                            rb"github_pat_[A-Za-z0-9_]{20,}|gh[pousr]_[A-Za-z0-9]{30,}|AKIA[0-9A-Z]{16}")
    for entry in git("rev-list", "--objects", "--all").splitlines():
        parts = entry.split(b" ", 1)
        if len(parts) != 2:
            continue
        oid, name = parts
        if git("cat-file", "-t", oid.decode()).strip() != b"blob":
            continue
        data = git("cat-file", "blob", oid.decode())
        if name == b"DEPLOYMENT.md" or any(value in data for value in values) or signatures.search(data):
            raise RuntimeError("A sensitive value remains in rewritten history; remote publication stopped.")


def upload_history(existing):
    """Upload objects without moving main; the connected GitHub app publishes the audited tip."""
    uploaded = set(existing)

    def upload_object(oid):
        if oid in uploaded:
            return
        kind = git("cat-file", "-t", oid).decode().strip()
        if kind == "blob":
            result = github("POST", "/git/blobs", {
                "encoding": "base64", "content": base64.b64encode(git("cat-file", "blob", oid)).decode()})
        elif kind == "tree":
            entries = []
            for entry in git("ls-tree", "-z", oid).split(b"\0"):
                if not entry:
                    continue
                metadata, name = entry.split(b"\t", 1)
                mode, object_type, child = metadata.decode().split()
                upload_object(child)
                entries.append({"path": name.decode(), "mode": mode,
                                "type": object_type, "sha": child})
            result = github("POST", "/git/trees", {"tree": entries})
        else:
            raise RuntimeError("Unexpected object type in the website history.")
        if result["sha"] != oid:
            raise RuntimeError("An uploaded Git object did not match the audited object.")
        uploaded.add(oid)

    def identity(line):
        match = re.fullmatch(rb"(.+) <([^<>]+)> (\d+) ([+-])(\d{2})(\d{2})", line)
        if not match:
            raise RuntimeError("Unexpected commit identity format.")
        name, email, seconds, sign, hours, minutes = match.groups()
        offset = timedelta(hours=int(hours), minutes=int(minutes)) * (-1 if sign == b"-" else 1)
        return {"name": name.decode(), "email": email.decode(),
                "date": datetime.fromtimestamp(int(seconds), timezone(offset)).isoformat()}

    mapped = {}
    commits = git("rev-list", "--reverse", "--topo-order", "HEAD").decode().splitlines()
    for oid in commits:
        header, message = git("cat-file", "commit", oid).split(b"\n\n", 1)
        fields = {}
        parents = []
        for line in header.splitlines():
            if line.startswith(b"parent "):
                parents.append(mapped[line[7:].decode()])
            elif line.startswith((b"tree ", b"author ", b"committer ")):
                key, value = line.split(b" ", 1)
                fields[key] = value
        tree = fields[b"tree"].decode()
        upload_object(tree)
        result = github("POST", "/git/commits", {
            "tree": tree, "parents": parents, "message": message.decode(),
            "author": identity(fields[b"author"]), "committer": identity(fields[b"committer"])})
        mapped[oid] = result["sha"]
    return mapped[commits[-1]]


def prepare():
    original = git("rev-parse", "HEAD").decode().strip()
    existing = {line.split(b" ", 1)[0].decode()
                for line in git("rev-list", "--objects", "--all").splitlines()}
    values = private_values()
    rewrite(values)
    audit(values)
    final = upload_history(existing)
    print(f"SANITIZED_HEAD={final}", flush=True)
    print(f"EXPECTED_HEAD={original}", flush=True)
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
        output.write(f"sanitized_head={final}\noriginal_head={original}\n")
    print("Audited history preparation completed.", flush=True)


def activate():
    original = os.environ["ORIGINAL_HEAD"]
    final = os.environ["SANITIZED_HEAD"]
    if not all(re.fullmatch(r"[a-f0-9]{40}", value) for value in (original, final)):
        raise RuntimeError("Invalid history publication identifiers.")
    print("Audited history is prepared. Waiting for the connected GitHub app to publish it.", flush=True)
    for _ in range(160):
        current = github("GET", "/git/ref/heads/main")["object"]["sha"]
        if current == final:
            break
        if current != original:
            raise RuntimeError("Main changed unexpectedly; publication and deployment stopped.")
        time.sleep(3)
    else:
        raise RuntimeError("Timed out waiting for authorized history publication; hosting was not changed.")
    remote = "https://github.com/" + os.environ["GITHUB_REPOSITORY"] + ".git"

    spec = importlib.util.spec_from_file_location("cpanel", ".github/scripts/deploy_cpanel.py")
    cp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cp)
    root = os.environ["CPANEL_REPOSITORY_ROOT"].strip() + "-clean-history"
    client = cp.CPanel(os.environ["CPANEL_HOST"].strip(), os.environ["CPANEL_USERNAME"].strip(),
                       os.environ["CPANEL_API_TOKEN"].strip(), root)
    repositories = client.call("VersionControl", "retrieve") or []
    if not any(item.get("repository_root") == root for item in repositories):
        client.call("VersionControl", "create", name="Website clean history", repository_root=root,
                    type="git", source_repository=json.dumps({"remote_name": "origin", "url": remote}))
    for _ in range(100):
        repository = client.repository()
        if not repository.get("tasks") and repository.get("last_update"):
            break
        time.sleep(3)
    else:
        raise RuntimeError("Timed out waiting for the clean cPanel checkout.")
    cp.deploy(client, final)
    cp.verify_live(final)

    previous_runs = []
    page = 1
    while True:
        runs = github("GET", f"/actions/workflows/deploy-cpanel.yml/runs?per_page=100&page={page}")["workflow_runs"]
        previous_runs.extend(run["id"] for run in runs if run["status"] == "completed")
        if len(runs) < 100:
            break
        page += 1
    for run_id in previous_runs:
        github("DELETE", f"/actions/runs/{run_id}")
    print(f"Removed {len(previous_runs)} old deployment runs and their logs.", flush=True)
    print("Privacy cleanup and live deployment verification completed.", flush=True)


if __name__ == "__main__":
    try:
        {"prepare": prepare, "activate": activate}[os.environ["CLEANUP_PHASE"]]()
    except Exception as error:
        message = str(error)
        for value in private_values():
            message = message.replace(value.decode(), "[redacted]")
        print("Privacy cleanup stopped: " + message, flush=True)
        raise SystemExit(1)
