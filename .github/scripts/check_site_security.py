"""Keep a restrictive CSP synchronized with the existing inline page code."""

import argparse
import base64
import hashlib
from pathlib import Path
import re


def inline_hashes(root, tag):
    hashes = set()
    pages = [*root.glob("*.html"), *root.glob("blog/**/*.html")]
    for page in pages:
        html = page.read_text(encoding="utf-8")
        for attributes, content in re.findall(
                rf"<{tag}\b([^>]*)>(.*?)</{tag}\s*>", html, re.IGNORECASE | re.DOTALL):
            if tag == "script" and re.search(r"(?:^|\s)src\s*=", attributes, re.IGNORECASE):
                continue
            if content.strip():
                digest = base64.b64encode(hashlib.sha256(content.encode()).digest()).decode()
                hashes.add("'sha256-" + digest + "'")
    return sorted(hashes)


def content_security_policy(root):
    return "; ".join([
        "default-src 'none'",
        "script-src 'self' https://static.cloudflareinsights.com/beacon.min.js " + " ".join(inline_hashes(root, "script")),
        "script-src-attr 'none'",
        "style-src 'self' " + " ".join(inline_hashes(root, "style")),
        "style-src-attr 'none'",
        "img-src 'self' data:", "font-src 'self'", "connect-src https://cloudflareinsights.com/cdn-cgi/rum",
        "object-src 'none'", "base-uri 'none'", "form-action 'none'",
        "frame-ancestors 'none'",
    ])


def check(root, update=False):
    target = root / ".htaccess"
    original = target.read_text(encoding="utf-8")
    expected = '    Header always set Content-Security-Policy "' + content_security_policy(root) + '"'
    pattern = r'^\s*Header always set Content-Security-Policy "[^"\n]*"$'
    matches = list(re.finditer(pattern, original, re.MULTILINE))
    if len(matches) != 1:
        raise RuntimeError("Expected exactly one Content-Security-Policy header.")
    current = matches[0].group().lstrip("\n\r")
    if update:
        result = re.sub(pattern, lambda _: expected, original, flags=re.MULTILINE)
        target.write_text(result, encoding="utf-8", newline="\n")
    elif current != expected:
        raise RuntimeError("Inline page code changed. Run python .github/scripts/check_site_security.py --update and review the policy.")
    if "-Indexes" not in original.splitlines()[0]:
        raise RuntimeError("Directory listings must remain disabled.")
    for name in ("X-Content-Type-Options", "X-Frame-Options", "Referrer-Policy", "Permissions-Policy", "Strict-Transport-Security"):
        if f"Header always set {name} " not in original:
            raise RuntimeError("Missing security header: " + name)
    print("Security headers, directory protection, and inline CSP hashes verified.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--update", action="store_true", help="Regenerate the reviewed inline-code hashes")
    args = parser.parse_args()
    check(Path(__file__).resolve().parents[2], args.update)
