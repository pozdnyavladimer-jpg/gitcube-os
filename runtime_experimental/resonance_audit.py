def audit_task(task_obj):
    title = str(task_obj.get("title", "")).strip().lower()
    intensity = float(task_obj.get("intensity", 0.0))

    if not title:
        return {
            "status": "LOW",
            "reason": "empty_title"
        }

    bad_patterns = [
        "task step",
        "test",
        "demo"
    ]

    for pattern in bad_patterns:
        if pattern in title:
            return {
                "status": "LOW",
                "reason": f"bad_pattern:{pattern}"
            }

    if intensity < 0.55:
        return {
            "status": "LOW",
            "reason": "weak_intensity"
        }

    return {
        "status": "OK",
        "reason": "clean"
    }
