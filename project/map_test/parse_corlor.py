from PIL import Image
import sys


def get_used_colors(image_path):
    img = Image.open(image_path)

    # Convert to RGB so colors have a consistent format
    img = img.convert("RGB")

    colors = set(img.getdata())

    return colors


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <image.bmp>")
        sys.exit(1)

    colors = get_used_colors(sys.argv[1])

    print(f"Found {len(colors)} unique colors:\n")

    for i, color in enumerate(colors):
        print(str(i) + ";" + ";".join([str(x) for x in list(color)]))