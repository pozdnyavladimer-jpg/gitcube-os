def hamming_distance(a, b):
    return sum(x != y for x, y in zip(a, b))


def is_local_transition(a, b):
    return hamming_distance(a, b) == 1


def get_neighbors(state):
    neighbors = []
    for i in range(len(state)):
        s = list(state)
        s[i] = 1 - s[i]
        neighbors.append(tuple(s))
    return neighbors
