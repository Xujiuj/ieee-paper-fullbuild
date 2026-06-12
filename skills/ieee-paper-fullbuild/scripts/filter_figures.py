#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Figure quality classifier.

Scans a directory of candidate figures and rejects those that are
letters, scanned documents, or text-heavy pages — portrait images with
high white-pixel ratio.

Usage:
    python filter_figures.py <image_dir>

Output (one line per file):
    image1.jpeg ACCEPT  aspect=1.77 white=0.01
    image16.jpeg REJECT aspect=0.71 white=0.68 reason=letter

Exit code 0 always.
"""
import os, sys
try:
    from PIL import Image
    import numpy as np
except ImportError:
    print("ERROR: install Pillow and numpy", file=sys.stderr)
    sys.exit(2)

ASPECT_THRESHOLD = 1.0
WHITE_THRESHOLD = 0.5

def classify(path):
    img = Image.open(path).convert('L')
    arr = np.array(img)
    w, h = img.size
    aspect = w / h
    white_ratio = (arr > 240).sum() / arr.size
    is_letter = aspect < ASPECT_THRESHOLD and white_ratio > WHITE_THRESHOLD
    return aspect, white_ratio, is_letter

def main(image_dir):
    if not os.path.isdir(image_dir):
        print(f"ERROR: not a directory: {image_dir}", file=sys.stderr)
        sys.exit(2)
    accepted, rejected = [], []
    for name in sorted(os.listdir(image_dir)):
        if not name.lower().endswith(('.png', '.jpg', '.jpeg')):
            continue
        path = os.path.join(image_dir, name)
        try:
            aspect, white, is_letter = classify(path)
        except Exception as e:
            print(f"{name} ERROR {e}")
            continue
        if is_letter:
            print(f"{name} REJECT aspect={aspect:.2f} white={white:.2f} reason=letter")
            rejected.append(name)
        else:
            print(f"{name} ACCEPT aspect={aspect:.2f} white={white:.2f}")
            accepted.append(name)
    print(f"\nSummary: {len(accepted)} accepted, {len(rejected)} rejected")
    return 0

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python filter_figures.py <image_dir>", file=sys.stderr)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
