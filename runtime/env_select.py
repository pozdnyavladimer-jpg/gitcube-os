from environments.balanced import BALANCED
from environments.harsh import HARSH
from environments.exploratory import EXPLORATORY


def get_environment(name: str):
    name = name.lower().strip()

    if name == "balanced":
        return BALANCED
    if name == "harsh":
        return HARSH
    if name == "exploratory":
        return EXPLORATORY

    return BALANCED
