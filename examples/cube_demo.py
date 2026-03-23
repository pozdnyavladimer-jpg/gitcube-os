from core.cube_validator import CubeState, validate_cube


def demo():
    cube = CubeState(
        pressure=0.2,
        flow=0.7,
        structure=0.9,
        balance=0.85,
        law=0.9,
        future=0.3
    )

    result = validate_cube(cube)

    print("=== CUBE VALIDATION ===")
    print(result)


if __name__ == "__main__":
    demo()
