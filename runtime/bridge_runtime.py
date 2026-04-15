import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

# BRIDGE RUNTIME LAYER

from bridges.registry import load_bridges


class BridgeRuntime:
    def __init__(self):
        self.bridges = load_bridges()
        self.graph = self._build_graph()

    def _build_graph(self):
        graph = {}

        for b in self.bridges:
            if "error" in b:
                continue

            src = b.get("source")
            dst = b.get("target")

            if not src or not dst:
                continue

            graph.setdefault(src, []).append(dst)

        return graph

    def get_neighbors(self, node):
        return self.graph.get(node, [])

    def find_path(self, start, end, path=None):
        if path is None:
            path = []

        path = path + [start]

        if start == end:
            return path

        if start not in self.graph:
            return None

        for node in self.graph[start]:
            if node not in path:
                new_path = self.find_path(node, end, path)
                if new_path:
                    return new_path

        return None


    def find_all_paths(self, start, end, path=None):
        if path is None:
            path = []

        path = path + [start]

        if start == end:
            return [path]

        if start not in self.graph:
            return []

        paths = []
        for node in self.graph[start]:
            if node not in path:
                new_paths = self.find_all_paths(node, end, path)
                for pth in new_paths:
                    paths.append(pth)

        return paths

    def score_path(self, path):
        if not path:
            return -1

        score = 0.0

        # коротші шляхи кращі
        score += max(0, 10 - len(path))

        # бонус за проходження через core
        if "core" in path:
            score += 3.0

        # бонус за проходження через runtime_experimental
        if "runtime_experimental" in path:
            score += 2.0

        # штраф за examples як проміжний вузол
        if len(path) > 2 and "examples" in path[1:-1]:
            score -= 2.0

        return round(score, 3)

    def find_best_path(self, start, end):
        paths = self.find_all_paths(start, end)

        if not paths:
            return None

        ranked = []
        for pth in paths:
            ranked.append({
                "path": pth,
                "score": self.score_path(pth),
            })

        ranked.sort(key=lambda x: x["score"], reverse=True)
        return ranked[0]


    def execute_route(self, start, end):
        route = self.find_best_path(start, end)

        if not route:
            return {
                "ok": False,
                "reason": "no_route"
            }

        path = route["path"]

        execution_log = []

        for i in range(len(path) - 1):
            src = path[i]
            dst = path[i + 1]

            bridge_name = f"{src}_to_{dst}_adapter"

            try:
                mod = __import__(f"bridges.{bridge_name}", fromlist=["connect"])
                result = mod.connect()

                execution_log.append({
                    "bridge": bridge_name,
                    "status": "ok",
                    "result": result
                })

            except Exception as e:
                execution_log.append({
                    "bridge": bridge_name,
                    "status": "error",
                    "error": str(e)
                })

        return {
            "ok": True,
            "path": path,
            "steps": execution_log
        }


    def explain_route(self, start, end):
        best = self.find_best_path(start, end)
        if not best:
            return {
                "ok": False,
                "reason": "no_route",
                "start": start,
                "end": end,
            }

        return {
            "ok": True,
            "start": start,
            "end": end,
            "path": best["path"],
            "score": best["score"],
            "reason": "best_scored_route",
        }


    def debug_print(self):
        print("=== BRIDGE GRAPH ===")
        for k, v in self.graph.items():
            print(f"{k} -> {v}")


if __name__ == "__main__":
    rt = BridgeRuntime()
    rt.debug_print()

    print("\n=== TEST PATH ===")
    print("app -> core:", rt.find_path("app", "core"))
    print("examples -> core:", rt.find_path("examples", "core"))

    print("\n=== ROUTING AI ===")
    print("best app -> core:", rt.find_best_path("app", "core"))
    print("best examples -> core:", rt.find_best_path("examples", "core"))
    print("explain examples -> core:", rt.explain_route("examples", "core"))


print("\n=== EXECUTION ===")
print(rt.execute_route("examples", "core"))

