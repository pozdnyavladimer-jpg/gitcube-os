from typing import Dict, List, Tuple


# --- базові вершини куба ---
def generate_nodes() -> List[Tuple[int, int, int]]:
    nodes = []
    for x in (0, 1):
        for y in (0, 1):
            for z in (0, 1):
                nodes.append((x, y, z))
    return nodes


# --- Hamming distance ---
def hamming(a: Tuple[int, int, int], b: Tuple[int, int, int]) -> int:
    return sum(x != y for x, y in zip(a, b))


# --- генерація звʼязків ---
def generate_edges(nodes: List[Tuple[int, int, int]]) -> List[Dict]:
    edges = []

    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            a = nodes[i]
            b = nodes[j]

            dist = hamming(a, b)

            edges.append({
                "from": a,
                "to": b,
                "distance": dist,
                "allowed": dist <= 1
            })

    return edges


# --- кольори вершин (RGB логіка) ---
def node_color(node: Tuple[int, int, int]) -> str:
    r, g, b = node

    if (r, g, b) == (0, 0, 0):
        return "#000000"
    if (r, g, b) == (1, 0, 0):
        return "#ff0000"
    if (r, g, b) == (0, 1, 0):
        return "#00ff00"
    if (r, g, b) == (0, 0, 1):
        return "#0000ff"
    if (r, g, b) == (1, 1, 0):
        return "#ffff00"
    if (r, g, b) == (1, 0, 1):
        return "#ff00ff"
    if (r, g, b) == (0, 1, 1):
        return "#00ffff"
    if (r, g, b) == (1, 1, 1):
        return "#ffffff"

    return "#888888"


# --- головна функція ---
def build_view_model(result: Dict) -> Dict:
    nodes = generate_nodes()
    edges = generate_edges(nodes)

    current = tuple(result["cube_position"])

    # маркуємо вузли
    node_data = []
    for n in nodes:
        node_data.append({
            "id": n,
            "color": node_color(n),
            "is_current": n == current
        })

    # маркуємо edges
    edge_data = []
    for e in edges:
        edge_data.append({
            "from": e["from"],
            "to": e["to"],
            "allowed": e["allowed"],
            "is_active": (
                e["from"] == current or e["to"] == current
            )
        })

    return {
        "nodes": node_data,
        "edges": edge_data,
        "current": current,
        "decision": result["decision"],
        "metrics": result["metrics"],
        "summary": result["summary"],
        "memory": result["transition_memory"],
    }
