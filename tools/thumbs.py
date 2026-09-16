#!/usr/bin/env python3
"""Regenerate image variants from img/*.webp: -t at 400w, -m at 800w.

Run after adding or replacing any full-size NNx.webp:  python3 tools/thumbs.py
Source of truth is the 1125w file; -t and -m are derived and safe to delete.
"""
from PIL import Image
from pathlib import Path

WIDES = {"-t": 400, "-m": 800}  # ponytail: fixed ratios match the 3:4 source, no cropping logic needed
root = Path(__file__).resolve().parent.parent / "img"
n = 0
for src in sorted(root.glob("*.webp")):
    if src.stem.endswith(("-t", "-m")):
        continue
    im = Image.open(src).convert("RGB")
    for suffix, w in WIDES.items():
        h = round(im.height * w / im.width)
        out = src.with_name(f"{src.stem}{suffix}.webp")
        im.resize((w, h), Image.LANCZOS).save(out, "WEBP", quality=82, method=6)
        n += 1
print(f"{n} variants written")

# ponytail: no build step and no CI; this script is manual, run it when a photo is added.
