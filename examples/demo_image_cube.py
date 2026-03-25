from runtime.image_cube import (
    make_demo_image,
    image_to_binary_grid,
    analyze_binary_image,
)


def demo():
    print("=== GITCUBE OS IMAGE CUBE DEMO ===")
    print("Goal: test whether local binary color-state transitions remain stable")
    print("Interpretation: image formation can be seen as constrained state evolution")
    print("")

    image = make_demo_image()
    binary = image_to_binary_grid(image, threshold=128)

    print("--- BINARY GRID ---")
    for row in binary:
        print(row)

    result = analyze_binary_image(binary, max_distance=1)

    print("\n--- ANALYSIS ---")
    print("allowed:", result["allowed"])
    print("blocked:", result["blocked"])
    print("total:", result["total"])
    print("smooth_ratio:", result["smooth_ratio"])

    print("\n--- SAMPLE TRANSITIONS ---")
    for item in result["samples"]:
        print(item)

    print("\n=== INTERPRETATION ===")
    print("Each pixel is mapped into a binary RGB state cube.")
    print("Neighboring pixels are checked for local transitions.")
    print("Allowed transitions = smooth structural evolution.")
    print("Blocked transitions = abrupt jumps in color-state space.")
    print("This suggests a way to constrain image generation by geometry, not only by scoring.")


if __name__ == "__main__":
    demo()
