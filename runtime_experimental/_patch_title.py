def apply_title(task_obj, step):
    payload_title = str(task_obj.get("payload", {}).get("title", "")).strip()

    if payload_title:
        task_obj["title"] = f"{payload_title} / step {step + 1}"
    else:
        task_obj["title"] = f"Task step {step + 1}"

    return task_obj
