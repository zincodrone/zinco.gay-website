"""Request a private cPanel account backup and wait for its completion."""

import json
import os
import time
from urllib.parse import urlencode, urlsplit
from urllib.request import Request

from deploy_cpanel import CPanel


def backup_status(client, username):
    # UAPI's date-only list cannot distinguish pending and completed manual backups.
    # This read-only API 2 endpoint supplies that completion status.
    params = {"cpanel_jsonapi_user": username, "cpanel_jsonapi_apiversion": 2,
              "cpanel_jsonapi_module": "Backups", "cpanel_jsonapi_func": "listfullbackups"}
    url = client.base.removesuffix("/execute") + "/json-api/cpanel?" + urlencode(params)
    request = Request(url, headers={"Authorization": client.authorization, "Accept": "application/json"})
    with client.opener.open(request, timeout=45) as response:
        payload = json.load(response).get("cpanelresult", {})
    if payload.get("error") or payload.get("event", {}).get("result") != 1 or not isinstance(payload.get("data"), list):
        raise RuntimeError("cPanel could not list manual backup completion status. Use its Backup Wizard instead.")
    return payload["data"]


def request_backup(client, username, sleep=time.sleep):
    previous = backup_status(client, username)
    if any(str(entry.get("status", "")).lower() == "pending" for entry in previous):
        raise RuntimeError("An account backup is already pending. Check cPanel before starting another.")
    existing = {entry.get("file") for entry in previous}
    task = client.call("Backup", "fullbackup_to_homedir", homedir="include")
    if not isinstance(task, dict) or not str(task.get("pid", "")).isdigit():
        raise RuntimeError("cPanel did not confirm that a backup process started.")
    print("cPanel accepted the private account-backup request. Waiting for completion...", flush=True)
    for _ in range(180):
        for entry in backup_status(client, username):
            filename = entry.get("file", "")
            if filename and filename.endswith(".tar.gz") and filename not in existing and str(entry.get("status", "")).lower() == "complete":
                print("cPanel confirmed a completed new account backup in the private home directory.", flush=True)
                print("Download that backup through cPanel and keep it outside public_html and GitHub.", flush=True)
                return
        sleep(5)
    raise RuntimeError("Backup completion was not confirmed within 15 minutes. Check cPanel before requesting another backup.")


def main():
    required = ("CPANEL_HOST", "CPANEL_USERNAME", "CPANEL_API_TOKEN")
    if any(not os.environ.get(name, "").strip() for name in required):
        raise RuntimeError("The cPanel connection secrets are missing.")
    client = CPanel(os.environ["CPANEL_HOST"].strip(), os.environ["CPANEL_USERNAME"].strip(),
                    os.environ["CPANEL_API_TOKEN"].strip(), "")
    request_backup(client, os.environ["CPANEL_USERNAME"].strip())


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        message = str(error)
        values = [os.environ.get(name, "").strip() for name in ("CPANEL_HOST", "CPANEL_USERNAME", "CPANEL_API_TOKEN")]
        raw_host = os.environ.get("CPANEL_HOST", "").strip()
        hostname = urlsplit(raw_host if "://" in raw_host else "https://" + raw_host).hostname
        values += [hostname or "", (hostname or "").split(".")[0]]
        for value in sorted(set(values), key=len, reverse=True):
            if value:
                message = message.replace(value, "[redacted]")
        print("Hosting backup stopped: " + message, flush=True)
        raise SystemExit(1)
