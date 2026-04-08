from core.topological_filter import TopologicalFilter


def demo():
    engine = TopologicalFilter()

    seq_good = ["LIFE", "WATER", "LIGHT", "CORE"]
    seq_bad = ["WAR", "VOID", "CHAOS", "ERROR"]

    result_good = engine.process(seq_good)

    engine = TopologicalFilter()  # reset
    result_bad = engine.process(seq_bad)


if __name__ == "__main__":
    demo()
