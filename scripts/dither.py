#!/usr/bin/env python3
"""Turn a photo into a faint, monochrome dithered watermark PNG for the resume background.

Deterministic (no RNG) so builds are reproducible. Reads a local image, converts to
grayscale, optionally adjusts levels, applies an error-diffusion or ordered dither, and
writes an RGBA PNG where the "paper" (light) areas are transparent and the "ink" (dark)
areas use a chosen colour at a chosen opacity. LaTeX then places this faint image behind
the resume text.

Usage (from scripts/, via uv):
    uv run dither.py                              # defaults: ../src/assets/kestrel-source.jpg -> kestrel-dither.png
    uv run dither.py --mode atkinson --opacity 0.10 --ink 1F2A37 --width 1500
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

HERE = Path(__file__).resolve().parent
DEFAULT_IN = HERE.parent / "src" / "assets" / "kestrel-source.jpg"
DEFAULT_OUT = HERE.parent / "src" / "assets" / "kestrel-dither.png"


def hex_to_rgb(s: str) -> tuple[int, int, int]:
    s = s.lstrip("#")
    return tuple(int(s[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def parse_crop(s: str | None, w: int, h: int) -> tuple[int, int, int, int] | None:
    """Parse 'l,t,r,b' fractions (0..1) into a pixel box, or None."""
    if not s:
        return None
    l, t, r, b = (float(x) for x in s.split(","))
    return (round(l * w), round(t * h), round(r * w), round(b * h))


def prepare_gray(img: Image.Image, width: int, contrast: float, gamma: float,
                 autocontrast: bool, invert: bool, crop: str | None,
                 black_point: float, white_point: float) -> np.ndarray:
    """Return a float grayscale array in [0,1] (0=black/ink, 1=white/paper)."""
    img = img.convert("L")
    box = parse_crop(crop, img.width, img.height)
    if box:
        img = img.crop(box)
    if autocontrast:
        img = ImageOps.autocontrast(img, cutoff=1)
    if width and img.width != width:
        h = round(img.height * width / img.width)
        img = img.resize((width, h), Image.LANCZOS)
    g = np.asarray(img, dtype=np.float64) / 255.0
    if gamma != 1.0:
        g = np.power(g, gamma)
    if contrast != 1.0:                       # pivot around mid-grey
        g = np.clip((g - 0.5) * contrast + 0.5, 0.0, 1.0)
    if white_point < 1.0 or black_point > 0.0:   # levels: stretch [black,white] -> [0,1]
        g = np.clip((g - black_point) / max(1e-6, white_point - black_point), 0.0, 1.0)
    if invert:
        g = 1.0 - g
    return g


def dither_error_diffusion(g: np.ndarray, kernel: list[tuple[int, int, float]]) -> np.ndarray:
    """Generic error-diffusion dither. Returns a 0/1 array (1 = ink)."""
    g = g.copy()
    h, w = g.shape
    out = np.zeros((h, w), dtype=np.uint8)
    for y in range(h):
        for x in range(w):
            old = g[y, x]
            new = 0.0 if old < 0.5 else 1.0
            out[y, x] = 1 if new == 0.0 else 0          # ink where pixel is dark
            err = old - new
            for dx, dy, f in kernel:
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h:
                    g[ny, nx] += err * f
    return out


FLOYD_STEINBERG = [(1, 0, 7 / 16), (-1, 1, 3 / 16), (0, 1, 5 / 16), (1, 1, 1 / 16)]
ATKINSON = [(1, 0, 1 / 8), (2, 0, 1 / 8), (-1, 1, 1 / 8), (0, 1, 1 / 8),
            (1, 1, 1 / 8), (0, 2, 1 / 8)]


def dither_bayer(g: np.ndarray, n: int = 8) -> np.ndarray:
    """Ordered (Bayer) dithering — crisp, regular halftone. Returns 0/1 array (1 = ink)."""
    def bayer(order: int) -> np.ndarray:
        if order == 1:
            return np.array([[0.0]])
        m = bayer(order // 2)
        return np.block([[4 * m, 4 * m + 2], [4 * m + 3, 4 * m + 1]]) / (order * order)

    thresh = bayer(n)
    h, w = g.shape
    tiled = np.tile(thresh, (h // n + 1, w // n + 1))[:h, :w]
    return (g < tiled).astype(np.uint8)          # ink where pixel darker than threshold


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, default=DEFAULT_IN)
    ap.add_argument("--output", type=Path, default=DEFAULT_OUT)
    # Defaults reproduce the resume's background watermark from kestrel-source.jpg.
    ap.add_argument("--mode", choices=["fs", "atkinson", "bayer"], default="atkinson")
    ap.add_argument("--width", type=int, default=1500, help="resize width in px (0 = keep)")
    ap.add_argument("--opacity", type=float, default=0.17, help="ink alpha 0..1 (faintness)")
    ap.add_argument("--ink", default="1F2A37", help="ink colour hex (default slate)")
    ap.add_argument("--contrast", type=float, default=1.2)
    ap.add_argument("--gamma", type=float, default=1.05)
    ap.add_argument("--no-autocontrast", dest="autocontrast", action="store_false")
    ap.add_argument("--invert", action="store_true")
    ap.add_argument("--crop", default="0.42,0.0,0.77,1.0",
                    help="'l,t,r,b' fractions 0..1 to crop source")
    ap.add_argument("--black-point", type=float, default=0.0, help="levels black point 0..1")
    ap.add_argument("--white-point", type=float, default=0.82,
                    help="levels white point 0..1 (lower = drop background to white)")
    args = ap.parse_args()

    img = Image.open(args.input)
    g = prepare_gray(img, args.width, args.contrast, args.gamma, args.autocontrast,
                     args.invert, args.crop, args.black_point, args.white_point)

    if args.mode == "bayer":
        ink = dither_bayer(g)
    else:
        kernel = FLOYD_STEINBERG if args.mode == "fs" else ATKINSON
        ink = dither_error_diffusion(g, kernel)

    h, w = ink.shape
    r, gc, b = hex_to_rgb(args.ink)
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    rgba[..., 0] = r
    rgba[..., 1] = gc
    rgba[..., 2] = b
    rgba[..., 3] = (ink * round(args.opacity * 255)).astype(np.uint8)  # paper -> transparent

    args.output.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgba, "RGBA").save(args.output)
    coverage = 100.0 * ink.mean()
    print(f"wrote {args.output}  ({w}x{h}, mode={args.mode}, "
          f"opacity={args.opacity}, ink#{args.ink}, {coverage:.1f}% ink coverage)")


if __name__ == "__main__":
    main()
