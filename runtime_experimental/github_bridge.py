import json
import os
import urllib.request
import urllib.parse

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
GITHUB_REPO = os.environ.get("GITHUB_REPO", "").strip()


def is_github_enabled():
    return bool(GITHUB_TOKEN and GITHUB_REPO and "/" in GITHUB_REPO)


def _github_headers():
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json; charset=utf-8",
        "User-Agent": "gitcube-os",
    }


def normalize_meta_key(text):
    s = str(text or "").strip().lower()
    out = []
    for ch in s:
        if ch.isalnum():
            out.append(ch)
        elif ch in ("_", "-", ":", "/", "|"):
            out.append(ch)
        else:
            out.append("_")
    return "".join(out)


def build_meta_problem_key(task):
    payload = task.get("payload", {}) or {}

    problem = str(payload.get("problem", "generic_problem")).strip().lower()
    path = str(payload.get("path", "")).strip()
    has_path = "path" if path else "no_path"

    priority = str(payload.get("priority", "")).strip().lower()
    origin = str(task.get("origin", "")).strip().lower()

    raw = f"{problem}|{has_path}|{priority}|{origin}"
    return normalize_meta_key(raw)


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
        headers=_github_headers(),
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


def list_open_issues(limit=100):
    if not is_github_enabled():
        return []

    per_page = max(1, min(int(limit), 100))
    query = urllib.parse.urlencode({
        "state": "open",
        "per_page": per_page,
    })
    url = f"https://api.github.com/repos/{GITHUB_REPO}/issues?{query}"

    req = urllib.request.Request(
        url,
        method="GET",
        headers=_github_headers(),
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if isinstance(data, list):
                # exclude pull requests
                return [x for x in data if "pull_request" not in x]
            return []
    except Exception:
        return []


def find_open_issue_by_meta_key(meta_key, limit=100):
    target = f"meta_key: {normalize_meta_key(meta_key)}"

    for issue in list_open_issues(limit=limit):
        body = str(issue.get("body", "") or "")
        if target in body.lower():
            return {
                "number": issue.get("number"),
                "url": issue.get("html_url", ""),
                "title": issue.get("title", ""),
            }

    return None


def build_issue_from_task(task, action, result_path=""):
    payload_text = json.dumps(task.get("payload", {}), ensure_ascii=False, indent=2)
    meta_key = build_meta_problem_key(task)

    body = (
        "GitCube Task\n\n"
        f"id: {task.get('id')}\n"
        f"title: {task.get('title')}\n"
        f"origin: {task.get('origin')}\n"
        f"kind: {task.get('kind')}\n"
        f"action: {action}\n"
        f"result_path: {result_path}\n"
        f"meta_key: {meta_key}\n\n"
        "Payload:\n"
        f"{payload_text}"
    )

    return {
        "title": f"[GitCube] {task.get('id')}: {task.get('title')}",
        "body": body,
        "meta_key": meta_key,
    }
