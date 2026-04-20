from __future__ import annotations

import difflib
from typing import Optional


def stdlib_similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio()


def safe_repo_similarity(a: str, b: str) -> float:
    """
    Безпечний міст:
    - якщо repo_difflib існує і має корисну функцію, беремо її
    - якщо ні, тихо падаємо назад на stdlib
    """
    try:
        import repo_difflib  # type: ignore

        # 1. найкращий варіант: явна функція
        if hasattr(repo_difflib, "repo_similarity_score"):
            fn = getattr(repo_difflib, "repo_similarity_score")
            value = float(fn(a, b))
            return max(0.0, min(1.0, value))

        # 2. альтернативна назва
        if hasattr(repo_difflib, "similarity"):
            fn = getattr(repo_difflib, "similarity")
            value = float(fn(a, b))
            return max(0.0, min(1.0, value))

    except Exception:
        pass

    return stdlib_similarity(a, b)


def blended_similarity(a: str, b: str, repo_weight: float = 0.15) -> float:
    base = stdlib_similarity(a, b)
    repo = safe_repo_similarity(a, b)

    weight = max(0.0, min(0.5, float(repo_weight)))
    value = (1.0 - weight) * base + weight * repo
    return max(0.0, min(1.0, value))
