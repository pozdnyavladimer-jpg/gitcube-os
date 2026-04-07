def apply_pressure(task_obj):
    audit_status = str(task_obj.get("audit_status", "none")).upper()

    result = {
        "applied": False,
        "reason": "none",
        "intensity_before": float(task_obj.get("intensity", 0.0)),
        "intensity_after": float(task_obj.get("intensity", 0.0)),
        "novelty_before": float(task_obj.get("novelty", 0.0)),
        "novelty_after": float(task_obj.get("novelty", 0.0)),
    }

    if audit_status != "LOW":
        return task_obj, result

    intensity_before = float(task_obj.get("intensity", 0.0))
    novelty_before = float(task_obj.get("novelty", 0.0))

    intensity_after = round(intensity_before * 0.7, 3)
    novelty_after = round(novelty_before * 0.8, 3)

    task_obj["intensity"] = intensity_after
    task_obj["novelty"] = novelty_after
    task_obj["pressure_applied"] = True

    result = {
        "applied": True,
        "reason": "audit_low",
        "intensity_before": intensity_before,
        "intensity_after": intensity_after,
        "novelty_before": novelty_before,
        "novelty_after": novelty_after,
    }

    return task_obj, result
