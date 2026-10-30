#!/usr/bin/env python3
"""
Generate placeholder image assets for the Stonegrove Hub.

    python hub/build/placeholders.py            # create any that are missing
    python hub/build/placeholders.py --force    # regenerate all placeholders

Reads bible/hand_supplied.yaml. For each image entry whose file is absent
from hub/source/, draws a serviceable placeholder with Pillow and writes a
sidecar <name>.meta.yaml marking it `placeholder: true` so the manifest says
so. A file that is present is never touched: that is the hand-supplied rule.
Document-type entries (the brand guide, templates) are authored .md sources
and are not generated here.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
HUB = HERE.parent
PROJECT = HUB.parent
SOURCE = HUB / "source"
LORE = PROJECT / "curriculum-and-lore" / "World-building" / "assets" / "Stonegrove"
FONTS = Path("C:/Windows/Fonts")

PALETTE = {
    "Parchment": "#f5f0e0", "Deep Parchment": "#ede8dc", "Stonegrove Navy": "#1a1a2e",
    "Stonegrove Gold": "#c9a84c", "Grove Green": "#7a9e82", "Ember Coral": "#d98878",
}


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    for cand in [name, "georgia.ttf", "times.ttf", "arial.ttf"]:
        p = FONTS / cand
        if p.exists():
            return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def coat(size: int, transparent: bool = True) -> Image.Image:
    src = LORE / ("stongegrove-coat-of-arms-transparent-bg.png" if transparent else "stongegrove-coat-of-arms.png")
    return Image.open(src).convert("RGBA").resize((size, size), Image.LANCZOS)


# ----------------------------------------------------------------- generators

def logo(path: Path, reversed_: bool = False) -> None:
    W, H = 1600, 560
    bg = (26, 26, 46, 255) if reversed_ else (0, 0, 0, 0)
    fg = (245, 240, 224, 255) if reversed_ else (26, 26, 46, 255)
    im = Image.new("RGBA", (W, H), bg)
    c = coat(440)
    im.alpha_composite(c, (60, 60))
    d = ImageDraw.Draw(im)
    f1 = font("georgia.ttf", 150)
    f2 = font("georgia.ttf", 72)
    d.text((560, 150), "Stonegrove", font=f1, fill=fg)
    d.text((566, 320), "UNIVERSITY", font=f2, fill=(201, 168, 76, 255))
    im.save(path)


def coat_copy(path: Path, transparent: bool) -> None:
    coat(1024, transparent).save(path)


def clear_space(path: Path) -> None:
    W, H = 1400, 900
    im = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    d = ImageDraw.Draw(im)
    s = 300
    x0, y0 = 450, 250
    d.rectangle([x0 - s, y0 - s, x0 + s + 560, y0 + s + s], outline=(217, 136, 120, 255), width=4)
    im.alpha_composite(coat(s), (x0, y0))
    d.text((x0 + s + 50, y0 + 80), "Stonegrove", font=font("georgia.ttf", 96), fill=(26, 26, 46, 255))
    d.text((x0 + s + 54, y0 + 190), "UNIVERSITY", font=font("georgia.ttf", 46), fill=(201, 168, 76, 255))
    f = font("arial.ttf", 30)
    for (x, y, t) in [(x0 - s + 20, y0 - s + 10, "clear space = shield height on every side"),
                      (x0 + 40, y0 + s + 20, "shield height")]:
        d.text((x, y), t, font=f, fill=(217, 136, 120, 255))
    d.line([x0 - 40, y0, x0 - 40, y0 + s], fill=(217, 136, 120, 255), width=4)
    im.save(path)


def palette_png(path: Path) -> None:
    W = 1600
    sw = 240
    im = Image.new("RGB", (W, 520), (255, 255, 255))
    d = ImageDraw.Draw(im)
    d.text((40, 30), "Stonegrove University colour palette", font=font("georgia.ttf", 48), fill=(26, 26, 46))
    f = font("arial.ttf", 26)
    x = 40
    for name, hexv in PALETTE.items():
        d.rectangle([x, 120, x + sw, 360], fill=hexv, outline=(200, 200, 200))
        d.text((x, 380), name, font=f, fill=(46, 46, 66))
        d.text((x, 416), hexv, font=f, fill=(136, 136, 128))
        x += sw + 16
    d.text((40, 470), "Ember Coral is an accent only: never for text or backgrounds. No gradients. No drop shadows.", font=f, fill=(46, 46, 66))
    im.save(path)


def pdf_from_png(png: Path, pdf: Path) -> None:
    Image.open(png).convert("RGB").save(pdf, "PDF", resolution=150)


def type_specimen(path: Path) -> None:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    c = canvas.Canvas(str(path), pagesize=A4)
    w, h = A4
    c.setFont("Times-Bold", 30); c.drawString(60, h - 90, "Type specimen")
    c.setFont("Helvetica", 11); c.drawString(60, h - 112, "Stonegrove University brand, version 2.1. Placeholder rendering: the brand faces are Playfair Display and Source Sans 3; fallbacks shown are Georgia and Arial equivalents.")
    y = h - 170
    c.setFont("Times-Bold", 14); c.drawString(60, y, "Headings: Playfair Display (fallback Georgia)"); y -= 40
    for size in (36, 24, 18):
        c.setFont("Times-Bold", size); c.drawString(60, y, "Stonegrove University"); y -= size + 14
    y -= 20
    c.setFont("Helvetica-Bold", 14); c.drawString(60, y, "Body: Source Sans 3 (fallback Arial)"); y -= 30
    c.setFont("Helvetica", 11)
    for line in ["Warm, plain, confident. Short sentences. British spelling.",
                 "Headings in the serif; everything else in the sans. Never more than two typefaces on a page.",
                 "No display, script, rounded or novelty faces. No exclamation marks in official communications."]:
        c.drawString(60, y, line); y -= 18
    c.showPage(); c.save()


def photo(path: Path, src_name: str, max_px: int = 900, quality: int = 72) -> None:
    im = Image.open(LORE / src_name).convert("RGB")
    im.thumbnail((max_px, max_px), Image.LANCZOS)
    im.save(path, "JPEG", quality=quality, optimize=True)


def pencil_tree(path: Path, size: int = 800, shadow: bool = False) -> None:
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    # gradient background (deliberately off brand)
    grad = Image.new("RGBA", (size, size))
    gd = ImageDraw.Draw(grad)
    for y in range(size):
        t = y / size
        gd.line([0, y, size, y], fill=(int(255 * (1 - t) + 160 * t), int(230 * (1 - t) + 255 * t), int(120 * (1 - t) + 200 * t), 255))
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([20, 20, size - 20, size - 20], fill=255)
    im.paste(grad, (0, 0), mask)
    d = ImageDraw.Draw(im)
    # trunk and pencil-canopy
    d.rectangle([size * 0.46, size * 0.6, size * 0.54, size * 0.88], fill=(120, 72, 30, 255))
    import math
    cx, cy = size / 2, size * 0.45
    for i in range(14):
        a = i * (2 * math.pi / 14)
        x1, y1 = cx + math.cos(a) * size * 0.08, cy + math.sin(a) * size * 0.08
        x2, y2 = cx + math.cos(a) * size * 0.3, cy + math.sin(a) * size * 0.3
        d.line([x1, y1, x2, y2], fill=(255, 200, 40, 255), width=int(size * 0.035))
        d.polygon([(x2, y2), (x2 + math.cos(a + 0.5) * size * 0.03, y2 + math.sin(a + 0.5) * size * 0.03),
                   (x2 + math.cos(a) * size * 0.06, y2 + math.sin(a) * size * 0.06),
                   (x2 + math.cos(a - 0.5) * size * 0.03, y2 + math.sin(a - 0.5) * size * 0.03)], fill=(60, 180, 60, 255))
    d.text((size * 0.18, size * 0.9), "Dept of Education", font=font("comic.ttf", int(size * 0.06)), fill=(255, 60, 166, 255))
    if shadow:
        sh = Image.new("RGBA", (size + 40, size + 40), (0, 0, 0, 0))
        alpha = im.split()[3].point(lambda a: int(a * 0.5))
        sh.paste((0, 0, 0, 255), (24, 24), alpha)
        sh = sh.filter(ImageFilter.GaussianBlur(12))
        sh.alpha_composite(im, (0, 0))
        im = sh
    im.save(path)


def old_logo(path: Path) -> None:
    W, H = 1600, 520
    im = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    im.alpha_composite(coat(380, transparent=True), (60, 70))
    d = ImageDraw.Draw(im)
    d.text((480, 110), "Stonegrove College", font=font("times.ttf", 120), fill=(122, 31, 46, 255))
    d.text((486, 260), "of the Vale", font=font("times.ttf", 110), fill=(122, 31, 46, 255))
    d.text((490, 400), "Founded in the meeting of forest and mountain", font=font("times.ttf", 40), fill=(90, 90, 90, 255))
    im.save(path)


# ----------------------------------------------------------------- dispatch

def make(entry: dict, path: Path) -> bool:
    name = path.name.lower()
    rel = path.relative_to(SOURCE).as_posix()
    if "logo reversed" in name:
        logo(path, reversed_=True)
    elif rel.endswith("Logo/Stonegrove University logo.png"):
        logo(path)
    elif "coat of arms transparent" in name:
        coat_copy(path, True)
    elif "coat of arms" in name and path.suffix == ".png":
        coat_copy(path, False)
    elif "clear space" in name:
        clear_space(path)
    elif "colour palette" in name and path.suffix == ".png":
        palette_png(path)
    elif "colour palette" in name and path.suffix == ".pdf":
        png = path.with_suffix(".png")
        if not png.exists():
            palette_png(png)
        pdf_from_png(png, path)
    elif "type specimen" in name:
        type_specimen(path)
    elif "pencil tree logo small" in name:
        pencil_tree(path, 120)
    elif "pencil tree logo final" in name:
        pencil_tree(path, 800, shadow=True)
    elif "pencil tree" in name:
        pencil_tree(path, 800)
    elif "college of the vale logo" in name:
        old_logo(path)
    elif path.suffix == ".jpg":
        pool = ["university-wide-shot.jpg", "library-1.jpg", "dining-hall.jpg", "forge-1.jpg", "outdoor-classroom-1.jpg", "vaulted-arches.jpg", "sunset-wide-shot.jpg", "elven-library.jpg"]
        photo(path, pool[sum(map(ord, path.name)) % len(pool)])
    else:
        return False
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    spec = yaml.safe_load((HUB / "bible" / "hand_supplied.yaml").read_text(encoding="utf-8"))
    made = kept = skipped = 0
    for entry in spec["files"]:
        path = SOURCE / entry["path"]
        if path.suffix.lower() not in (".png", ".jpg", ".pdf") or entry.get("kind") == "document" and "specimen" not in path.name.lower() and "palette" not in path.name.lower():
            skipped += 1
            continue
        if path.exists() and not args.force:
            kept += 1
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        if make(entry, path):
            side = path.with_name(path.name + ".meta.yaml")
            side.write_text(yaml.safe_dump({"placeholder": True, "hand_supplied": True, "title": path.stem,
                                             "note": entry.get("placeholder", "").strip()}, allow_unicode=True), encoding="utf-8")
            made += 1
            print("  made", path.relative_to(SOURCE).as_posix())
        else:
            skipped += 1
    print(f"placeholders: {made} made, {kept} kept (hand-supplied, untouched), {skipped} not image assets")
    return 0


if __name__ == "__main__":
    sys.exit(main())
