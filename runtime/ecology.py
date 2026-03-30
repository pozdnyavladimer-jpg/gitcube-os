from collections import Counter


def class_ecology_penalty(class_name, history):
    if not history:
        return 0.0

    last = history[-20:]
    counts = Counter(last)
    ratio = counts[class_name] / len(last)

    if ratio > 0.5:
        return round((ratio - 0.5) * 1.5, 3)

    return 0.0
