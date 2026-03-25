from typing import List, Tuple, Dict

Pixel = Tuple[int, int, int]
BinaryPixel = Tuple[int, int, int]
ImageGrid = List[List[Pixel]]
BinaryGrid = List[List[BinaryPixel]]


def pixel_to_binary(pixel: Pixel, threshold: int = 128) -> BinaryPixel:
    r, g, b = pixel
    return (
        int(r >= threshold),
        int(g >= threshold),
        int(b >= threshold),
    )


def image_to_binary_grid(image: ImageGrid, threshold: int = 128) -> BinaryGrid:
    return [
        [pixel_to_binary(pixel, threshold=threshold) for pixel in row]
        for row in image
    ]


def hamming_distance(a: BinaryPixel, b: BinaryPixel) -> int:
    return sum(x != y for x, y in zip(a, b))


def transition_allowed(a: BinaryPixel, b: BinaryPixel, max_distance: int = 1) -> bool:
    return hamming_distance(a, b) <= max_distance


def analyze_binary_image(
    grid: BinaryGrid,
    max_distance: int = 1,
) -> Dict[str, object]:
    """
    Analyze local transitions between neighboring pixels.
    Checks right and down neighbors only to avoid double counting.
    """
    allowed = 0
    blocked = 0
    samples = []

    rows = len(grid)
    cols = len(grid[0]) if rows else 0

    for i in range(rows):
        for j in range(cols):
            current = grid[i][j]

            # Right neighbor
            if j + 1 < cols:
                neighbor = grid[i][j + 1]
                ok = transition_allowed(current, neighbor, max_distance=max_distance)
                if ok:
                    allowed += 1
                else:
                    blocked += 1
                if len(samples) < 10:
                    samples.append(
                        {
                            "from": current,
                            "to": neighbor,
                            "direction": "right",
                            "distance": hamming_distance(current, neighbor),
                            "allowed": ok,
                        }
                    )

            # Down neighbor
            if i + 1 < rows:
                neighbor = grid[i + 1][j]
                ok = transition_allowed(current, neighbor, max_distance=max_distance)
                if ok:
                    allowed += 1
                else:
                    blocked += 1
                if len(samples) < 10:
                    samples.append(
                        {
                            "from": current,
                            "to": neighbor,
                            "direction": "down",
                            "distance": hamming_distance(current, neighbor),
                            "allowed": ok,
                        }
                    )

    total = allowed + blocked
    smooth_ratio = (allowed / total) if total else 0.0

    return {
        "allowed": allowed,
        "blocked": blocked,
        "total": total,
        "smooth_ratio": round(smooth_ratio, 3),
        "samples": samples,
    }


def make_demo_image() -> ImageGrid:
    """
    Small synthetic image with a mix of smooth and abrupt transitions.
    """
    return [
        [(20, 20, 20),   (40, 40, 40),   (220, 220, 220), (240, 240, 240)],
        [(25, 25, 25),   (60, 60, 60),   (210, 210, 210), (250, 250, 250)],
        [(10, 100, 200), (20, 120, 220), (200, 30, 30),   (230, 40, 40)],
        [(15, 110, 210), (25, 125, 225), (210, 35, 35),   (240, 50, 50)],
    ]
