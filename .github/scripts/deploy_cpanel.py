"""Update and verify a cPanel Git deployment using its HTTPS API."""

import json
import os
from pathlib import Path
import re
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Do not forward the account token to another host or a login page.
        raise RuntimeError("cPanel redirected the API request; check its hostname.")


class CPanel:
    def __init__(self, host, username, token, root):
        address = urlsplit(host if "://" in host else f"https://{host}")
        hostname = address.hostname or ""
        if (address.scheme != "https" or address.username or address.password
                or address.port not in (None, 2083)
                or not re.fullmatch(r"[A-Za-z0-9.-]+", hostname)):
            raise RuntimeError("Invalid cPanel hostname.")
        self.base = f"https://{hostname}:2083/execute"
        self.authorization = f"cpanel {username}:{token}"
        self.root = root
        self.opener = build_opener(NoRedirect())

    def call(self, module, function, **params):
        url = f"{self.base}/{module}/{function}?{urlencode(params)}"
        request = Request(url, headers={
            "Authorization": self.authorization,
            "Accept": "application/json",
        })
        try:
            with self.opener.open(request, timeout=45) as response:
                payload = response.read()
                content_type = response.headers.get("Content-Type", "unknown")
        except HTTPError as error:
            raise RuntimeError(f"cPanel API returned HTTP {error.code}.") from error
        except URLError as error:
            raise RuntimeError(f"Could not connect to the cPanel API: {error.reason}") from error
        try:
            envelope = json.loads(payload)
            result = envelope.get("result", envelope.get("cpanelresult", {}).get("result", envelope))
            if not isinstance(result, dict) or "status" not in result:
                raise ValueError("Missing API status")
        except (ValueError, KeyError) as error:
            if b"<html" in payload.lower() or "text/html" in content_type:
                raise RuntimeError("cPanel returned a login/HTML page instead of API data. Verify that the token belongs to this username on this server and that the host permits API-token authentication.") from error
            raise RuntimeError(f"cPanel returned an unexpected API response ({content_type}).") from error
        if result.get("status") != 1:
            raise RuntimeError(f"cPanel rejected {module}/{function}: {result.get('errors')}")
        return result.get("data")

    def repository(self):
        repositories = self.call("VersionControl", "retrieve") or []
        for repository in repositories:
            if repository.get("repository_root") == self.root:
                return repository
        raise RuntimeError("The configured repository was not found in cPanel.")


def deploy(client, expected_commit, sleep=time.sleep):
    repository = client.repository()
    source = repository.get("source_repository", {})
    if source.get("url", "").removesuffix(".git").rstrip("/") not in {
        "https://github.com/zincodrone/zinco.gay-website",
        "git@github.com:zincodrone/zinco.gay-website",
    }:
        raise RuntimeError("cPanel's source repository does not match this website.")

    print("Updating the cPanel repository from origin/main…", flush=True)
    for attempt in range(3):
        try:
            client.call("VersionControl", "update", repository_root=client.root,
                        branch="main", source_repository=json.dumps({"remote_name": "origin"}))
            break
        except RuntimeError as error:
            if attempt == 2 or not any(word in str(error).lower() for word in ("timeout", "timed out")):
                raise
            print("cPanel's Git update timed out; retrying the same fast-forward update…", flush=True)
            sleep(10 * (attempt + 1))
    for _ in range(60):
        repository = client.repository()
        if not repository.get("tasks"):
            if repository.get("last_update", {}).get("identifier") != expected_commit:
                raise RuntimeError("cPanel did not reach this commit. Check its update log; main may have advanced.")
            if repository.get("branch") != "main" or not repository.get("deployable"):
                raise RuntimeError("cPanel reports that main cannot deploy. Check the working tree and .cpanel.yml.")
            break
        sleep(3)
    else:
        raise RuntimeError("Timed out waiting for cPanel to update the repository.")

    task = client.call("VersionControlDeployment", "create", repository_root=client.root)
    deployment_id = str(task["deploy_id"])
    print(f"Waiting for cPanel deployment {deployment_id}…", flush=True)
    for _ in range(100):
        tasks = client.call("VersionControlDeployment", "retrieve") or []
        deployment = next((item for item in tasks
                           if str(item.get("deploy_id")) == deployment_id
                           and item.get("repository_root") == client.root), None)
        if deployment:
            timestamps = deployment.get("timestamps", {})
            if timestamps.get("failed") or timestamps.get("canceled"):
                raise RuntimeError(f"cPanel deployment failed. Review {deployment.get('log_path', 'its deployment log')}.")
            if timestamps.get("succeeded"):
                if deployment.get("repository_state", {}).get("identifier") != expected_commit:
                    raise RuntimeError("cPanel deployed a different commit; check for concurrent manual deployments.")
                print(f"cPanel successfully deployed {expected_commit}.", flush=True)
                return
        sleep(3)
    raise RuntimeError("Timed out waiting for deployment. Check cPanel's deployment log.")


def verify_live(expected_commit, sleep=time.sleep):
    version = re.search(r">(v[\d.]+)</a>", Path("index.html").read_text(encoding="utf-8")).group(1)
    opener = build_opener(NoRedirect())
    for _ in range(12):
        try:
            request = Request(f"https://zinco.gay/?deploy={expected_commit}", headers={"Cache-Control": "no-cache"})
            with opener.open(request, timeout=20) as response:
                html = response.read().decode("utf-8")
            if f">{version}</a>" in html:
                print(f"Live homepage is reachable and displays {version}.", flush=True)
                return
        except (HTTPError, URLError):
            pass
        sleep(3)
    raise RuntimeError("cPanel reported success, but the expected live version could not be verified.")


def main():
    required = ("CPANEL_HOST", "CPANEL_USERNAME", "CPANEL_REPOSITORY_ROOT", "CPANEL_API_TOKEN")
    missing = [name for name in required if not os.environ.get(name, "").strip()]
    if missing:
        raise RuntimeError("Add these GitHub Actions repository secrets: " + ", ".join(missing))
    token = os.environ.get("CPANEL_API_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Add CPANEL_API_TOKEN under GitHub Settings → Secrets and variables → Actions.")
    if any(character.isspace() for character in token):
        raise RuntimeError("CPANEL_API_TOKEN contains whitespace. Save only the generated token value in GitHub, not its label or accompanying text.")
    client = CPanel(os.environ["CPANEL_HOST"].strip(), os.environ["CPANEL_USERNAME"].strip(),
                    token, os.environ["CPANEL_REPOSITORY_ROOT"].strip())
    expected = os.environ["EXPECTED_COMMIT"]
    deploy(client, expected)
    verify_live(expected)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        message = str(error)
        for name in ("CPANEL_API_TOKEN", "CPANEL_REPOSITORY_ROOT", "CPANEL_USERNAME", "CPANEL_HOST"):
            value = os.environ.get(name, "").strip()
            if value:
                message = message.replace(value, "[redacted]")
                if name == "CPANEL_HOST":
                    hostname = urlsplit(value if "://" in value else f"https://{value}").hostname
                    if hostname:
                        message = message.replace(hostname, "[redacted]")
        print(f"Deployment failed: {message}", file=sys.stderr)
        sys.exit(1)
