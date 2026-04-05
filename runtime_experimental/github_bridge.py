import json
import os
import urllib.request
import urllib.error

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
GITHUB_REPO = os.environ.get("GITHUB_REPO", "").strip()


def is_github_enabled():
    return bool(GITHUB_TOKEN and GITHUB_REPO and "/" in GITHUB_REPO)


def create_issue(title, body):
    if not is_github_enabled():
        return {
            "ok": False,
            "error": "GitHub is not configured"
        }

    url = f"https://api.github.com/repos/{GITHUB_REPO}/issues"

    payload = json.dumps({
        "title": title,
        "body": body
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "gitcube-os"
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return {
                "ok": True,
                "url": data.get("html_url", ""),
                "number": data.get("number"),
            }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e)
        }


def build_issue_from_task(task, action, result_path=""):
    payload_text = json.dumps(task.get("payload", {}), ensure_ascii=False, indent=2)

    body = (
        "GitCube Task\n\n"
        f"id: {task.get('id')}\n"
        f"title: {task.get('title')}\n"
        f"origin: {task.get('origin')}\n"
        f"kind: {task.get('kind')}\n"
        f"action: {action}\n"
        f"result_path: {result_path}\n\n"
        "Payload:\n"
        f"{payload_text}"
    )

    return {
        "title": f"[GitCube] {task.get('id')}: {task.get('title')}",
        "body": body,
    }
