from core.cube_validator import CubeState
from runtime.cube_stacking import stack_cubes


def demo():
    cube_a = CubeState(
        pressure=0.20,
        flow=0.65,
        structure=0.86,
        balance=0.82,
        law=0.90,
        future=0.30,
    )

    cube_b = CubeState(
        pressure=0.18,
        flow=0.60,
        structure=0.88,
        balance=0.84,
        law=0.92,
        future=0.35,
    )

    result = stack_cubes(cube_a, cube_b)



if __name__ == "__main__":
    demo()
