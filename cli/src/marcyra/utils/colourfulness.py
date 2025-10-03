import math
import numpy as np

from PIL import Image


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0


def stddev(values: list[float], mean_val: float) -> float:
    return math.sqrt(sum((x - mean_val) ** 2 for x in values) / len(values)) if values else 0


def calc_colourfulness(image: Image) -> float:
    width, height = image.size
    pixels = list(image.getdata())  # List of (R, G, B) tuples

    rg_diffs = []
    yb_diffs = []

    for r, g, b in pixels:
        rg = abs(r - g)
        yb = abs(0.5 * (r + g) - b)
        rg_diffs.append(rg)
        yb_diffs.append(yb)

    mean_rg = mean(rg_diffs)
    mean_yb = mean(yb_diffs)
    std_rg = stddev(rg_diffs, mean_rg)
    std_yb = stddev(yb_diffs, mean_yb)

    return math.sqrt(std_rg**2 + std_yb**2) + 0.3 * math.sqrt(mean_rg**2 + mean_yb**2)


def calc_colorfulness_np(image: Image) -> float:
    # Ensure RGB
    arr = np.asarray(image.convert("RGB"), dtype=np.float32)

    r = arr[..., 0]
    g = arr[..., 1]
    b = arr[..., 2]

    rg = np.abs(r - g)
    yb = np.abs(0.5 * (r + g) - b)

    std_rg = rg.std()
    std_yb = yb.std()
    mean_rg = rg.mean()
    mean_yb = yb.mean()

    return float(np.hypot(std_rg, std_yb) + 0.3 * np.hypot(mean_rg, mean_yb))


def get_variant(image: Image) -> str:
    colourfulness = calc_colorfulness_np(image)

    if colourfulness < 10:
        return "neutral"
    if colourfulness < 20:
        return "content"
    return "tonalspot"
