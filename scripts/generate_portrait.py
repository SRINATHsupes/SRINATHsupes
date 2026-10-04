from pathlib import Path
import html

import cv2
import numpy as np
from PIL import Image


INPUT = Path("assets/me.jpeg")
OUTPUT = Path("assets/portrait.svg")

# Number of ASCII characters across the portrait.
COLUMNS = 90

# Dark → light.
ASCII_RAMP = " .`:-=+*cs#%@"

# Terminal characters are taller than they are wide,
# so we compensate for that when resizing the image.
CHAR_ASPECT = 0.48

FONT_SIZE = 10
CHAR_WIDTH = 0.60
LINE_HEIGHT = 1.0


def load_image(path: Path) -> np.ndarray:
    """Load the source image as RGB."""

    image = Image.open(path).convert("RGB")
    return np.array(image)


def prepare_image(image: np.ndarray) -> np.ndarray:
    """
    Convert the image into a high-contrast grayscale image
    suitable for ASCII conversion.
    """

    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    # Improve local contrast.
    clahe = cv2.createCLAHE(
        clipLimit=3.0,
        tileGridSize=(8, 8),
    )

    gray = clahe.apply(gray)

    # Darken midtones so facial features remain visible
    # when represented by ASCII characters.
    normalized = gray.astype(np.float32) / 255.0
    darkened = np.power(normalized, 1.7)

    return np.clip(
        darkened * 255,
        0,
        255,
    ).astype(np.uint8)


def resize_for_ascii(gray: np.ndarray) -> np.ndarray:
    """Resize while compensating for character proportions."""

    height, width = gray.shape

    rows = max(
        1,
        round(
            COLUMNS
            * (height / width)
            * CHAR_ASPECT
        ),
    )

    return cv2.resize(
        gray,
        (COLUMNS, rows),
        interpolation=cv2.INTER_AREA,
    )


def to_ascii(gray: np.ndarray) -> list[str]:
    """Convert grayscale pixels into ASCII characters."""

    result = []

    max_index = len(ASCII_RAMP) - 1

    for row in gray:
        characters = []

        for pixel in row:
            index = round(
                int(pixel) / 255 * max_index
            )

            characters.append(
                ASCII_RAMP[index]
            )

        result.append(
            "".join(characters)
        )

    return result


def create_svg(rows: list[str]) -> str:
    """Create the animated SVG portrait."""

    width = COLUMNS * FONT_SIZE * CHAR_WIDTH
    height = len(rows) * FONT_SIZE * LINE_HEIGHT

    text_rows = []
    clip_rows = []

    for index, row in enumerate(rows):
        y = (index + 1) * FONT_SIZE * LINE_HEIGHT
        clip_y = index * FONT_SIZE * LINE_HEIGHT

        delay = index * 0.09

        escaped = html.escape(row)

        text_rows.append(
            f'''    <text
      x="0"
      y="{y:.2f}"
      font-family="monospace"
      font-size="{FONT_SIZE}px"
      xml:space="preserve"
    >{escaped}</text>'''
        )

        clip_rows.append(
            f'''      <rect
        x="0"
        y="{clip_y:.2f}"
        width="0"
        height="{FONT_SIZE * LINE_HEIGHT:.2f}"
      >
        <animate
          attributeName="width"
          from="0"
          to="{width:.2f}"
          dur="0.8s"
          begin="{delay:.2f}s"
          fill="freeze"
        />
      </rect>'''
        )

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg
  xmlns="http://www.w3.org/2000/svg"
  width="{width:.0f}"
  height="{height:.0f}"
  viewBox="0 0 {width:.0f} {height:.0f}"
>
  <defs>
    <clipPath id="portrait-reveal">
{chr(10).join(clip_rows)}
    </clipPath>
  </defs>

  <rect
    width="100%"
    height="100%"
    fill="white"
  />

  <g
    fill="black"
    clip-path="url(#portrait-reveal)"
>
{chr(10).join(text_rows)}
  </g>
</svg>
'''


def main() -> None:
    if not INPUT.exists():
        raise FileNotFoundError(
            f"Portrait not found: {INPUT}"
        )

    print(f"Reading: {INPUT}")

    image = load_image(INPUT)

    height, width = image.shape[:2]

    print(
        f"Original size: "
        f"{width}x{height}"
    )

    print("Preparing image...")
    gray = prepare_image(image)

    print("Resizing for ASCII...")
    resized = resize_for_ascii(gray)

    print(
        f"ASCII grid: "
        f"{resized.shape[1]} columns x "
        f"{resized.shape[0]} rows"
    )

    print("Converting to ASCII...")
    rows = to_ascii(resized)

    print("Creating SVG...")
    svg = create_svg(rows)

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT.write_text(
        svg,
        encoding="utf-8",
    )

    print(f"Created: {OUTPUT}")


if __name__ == "__main__":
    main()
