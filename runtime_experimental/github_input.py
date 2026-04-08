import os
import json
import urllib.request

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
GITHUB_REPO = os.environ.get("GITHUB_REPO", "").strip()


def is_enabled():
    return bool(GITHUB_TOKEN and GITHUB_REPO and "/" in GITHUB_REPO)


def fetch_latest_issue():
    if not is_enabled():
        return None

    url = f"https://api.github.com/repos/{GITHUB_REPO}/issues?state=open&per_page=1"

    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "gitcube-os"
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if not data:
                return None

            issue = data[0]

            return {
                "kind": "issue",
                "source": "github",
                "title": issue.get("title"),
                "body": issue.get("body"),
                "url": issue.get("html_url"),
                "number": issue.get("number"),
            }

    except Exception as e:
        return None


def write_external_signal(issue):
    if not issue:
        return

    signal = {
        "kind": "issue",
        "intensity": 0.95,
        "payload": {
            "title": issue["title"],
            "body": issue["body"],
            "url": issue["url"],
            "number": issue["number"],
        }
    }

    with open("external_signal.json", "w", encoding="utf-8") as f:
        json.dump(signal, f, indent=2)


def run():
    issue = fetch_latest_issue()
    if issue:
        write_external_signal(issue)
    else:


if __name__ == "__main__":
    run()
