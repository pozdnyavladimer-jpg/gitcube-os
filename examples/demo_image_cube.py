from runtime.image_cube import (
    make_demo_image,
    image_to_binary_grid,
    analyze_binary_image,
)


def demo():

    image = make_demo_image()
    binary = image_to_binary_grid(image, threshold=128)

    for row in binary:

    result = analyze_binary_image(binary, max_distance=1)


    for item in result["samples"]:



if __name__ == "__main__":
    demo()
