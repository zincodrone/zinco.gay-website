"""Save verified recovery archives and observed DNS records outside this checkout."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import zipfile


def git(root, *args):
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError("A Git backup or verification operation failed.")
    return result.stdout.strip()


def public_files(root):
    files = [root / name for name in (".htaccess", "index.html", "socials.html", "redirect.html", "social-links.js", "style.css")]
    files += [file for folder in ("blog", "images") for file in (root / folder).rglob("*") if file.is_file()]
    for file in files:
        if file.is_symlink() or not file.resolve().is_relative_to(root.resolve()):
            raise RuntimeError("A public file points outside the checkout; backup stopped.")
    return files


def archive(root, target, files):
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as output:
        for file in sorted(files):
            output.write(file, file.relative_to(root).as_posix())
    with zipfile.ZipFile(target) as output:
        if output.testzip() is not None:
            raise RuntimeError("The recovery ZIP failed verification.")


def dns_snapshot(domain, lookup=None):
    if not re.fullmatch(r"[A-Za-z0-9.-]+", domain) or ".." in domain:
        raise RuntimeError("Invalid DNS backup domain.")
    observations = []
    for name, kinds in ((domain, ("A", "AAAA", "MX", "NS", "TXT", "CAA", "SOA")),
                        ("www." + domain, ("A", "AAAA", "CNAME"))):
        for kind in kinds:
            if lookup:
                result = lookup(name, kind)
            else:
                url = "https://dns.google/resolve?" + urlencode({"name": name, "type": kind})
                with urlopen(Request(url, headers={"Accept": "application/dns-json"}), timeout=20) as response:
                    result = json.load(response)
            if result.get("Status") not in (0, 3):
                raise RuntimeError("A DNS lookup failed; the snapshot would be incomplete.")
            observations.append({"name": name, "type": kind, "response": result})
    return {"domain": domain, "scope": "Observed root and www records, not a complete DNS zone export.",
            "observations": observations}


def create(root, destination, domain="zinco.gay", lookup=None):
    root = root.resolve()
    destination = destination.resolve()
    if destination.is_relative_to(root) or any(part.lower() == "public_html" for part in destination.parts):
        raise RuntimeError("Choose a backup folder outside the repository and public_html.")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    version = re.search(r'class="site-version"[^>]*>v([^<]+)</a>', (root / "index.html").read_text(encoding="utf-8")).group(1)
    target = destination / f"website-{version}-{stamp}"
    target.mkdir(parents=True, mode=0o700)
    git(root, "bundle", "create", str(target / "repository.bundle"), "--all")
    git(root, "bundle", "verify", str(target / "repository.bundle"))
    archive(root, target / "website-files.zip", public_files(root))
    configuration = [root / name for name in (".cpanel.yml", ".gitattributes", ".gitignore", ".githooks/pre-push", "README.md", "AGENTS.md") if (root / name).is_file()]
    configuration += [p for p in (root / ".github").rglob("*") if p.is_file() and p.suffix in (".py", ".yml", ".yaml")]
    archive(root, target / "deployment-configuration.zip", configuration)
    snapshot = dns_snapshot(domain, lookup)
    (target / "observed-dns.json").write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    (target / "RESTORE.txt").write_text(
        "Recovery backup\n\n"
        "1. Verify archive SHA-256 hashes against manifest.json.\n"
        "2. Clone repository.bundle into a new directory, or extract website-files.zip for the public site.\n"
        "3. Restore deployment configuration, recreate GitHub Actions secrets from your password manager, and install the local push hook.\n"
        "4. Review observed-dns.json against your provider's full zone export before changing DNS.\n\n"
        "The bundle contains committed reachable history. ZIPs contain current working files, which may include uncommitted changes.\n"
        "This backup does not export account credentials, mail, databases, the full PremiumDNS zone, or cPanel account settings.\n"
        "Keep a separate private cPanel account backup and Namecheap DNS export. Full cPanel account restoration may require the hosting provider.\n"
        "These archives are not encrypted. Keep them on a private encrypted drive and never upload them to public_html or GitHub.\n",
        encoding="utf-8")
    manifest = {"created_utc": stamp, "website_version": version, "committed_head": git(root, "rev-parse", "HEAD"),
                "working_tree_changed": bool(git(root, "status", "--porcelain")), "sha256": {}}
    for file in sorted(target.iterdir()):
        manifest["sha256"][file.name] = hashlib.sha256(file.read_bytes()).hexdigest()
        file.chmod(0o600)
    (target / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (target / "manifest.json").chmod(0o600)
    print("Verified recovery backup saved outside the website and repository: " + str(target))
    return target


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=root.parent / "website-recovery-backups")
    parser.add_argument("--domain", default="zinco.gay")
    args = parser.parse_args()
    create(root, args.output_dir, args.domain)
