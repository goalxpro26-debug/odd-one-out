#!/usr/bin/env python3
"""Thumbnails for Odd One Out portal builds, from the game's own test shots.

Sources (all 480x860 PNG, real gameplay captures from test.js):
  01-menu.png    menu / how-to-play
  02-level1.png  Level 1 board (9 blobs)
  04-level20.png Level 20 board (dense 7x6 grid)

Cover 1360x850 (GamePix requirement; also the base for GD/GM landscape
thumbs): three panels side by side (menu / level 1 / level 20), each
scaled to height 850 and centre-cropped to 453 wide, thin gold dividers,
title band at the bottom. No stretch anywhere; full height kept so the
title band survives in the centre-cropped derivatives (the GM 512x340
precedent from Aether Weaver).

Per-portal sets (all JPG, RGB):
  GamePix:          odd-one-out-icon-512x512.jpg (square crop of level 1),
                    odd-one-out-cover-1360x850.jpg
  GameDistribution: 5 JPGs — 512x512, 512x384, 200x120, 1280x720, 1280x550
  GameMonetize:     3 JPGs — 512x384, 512x512, 512x340

Landscape derivatives: cover scaled to target height, centre-cropped to
target width (full height kept, title band intact). Exception: 200x120 —
cover at height 120 is only 192 wide, so it is fit + letterboxed on the
game's dark-purple background instead of stretched.
Icon 512x512: centre square crop of the level-1 shot (480x480), resized.
"""
import pathlib
from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).resolve().parent
SHOTS = HERE.parent / "test-shots"
BG = (26, 16, 51)      # #1a1033, the game's own background
GOLD = (251, 191, 36)  # #fbbf24, the game's accent
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def load(name):
    im = Image.open(SHOTS / name).convert("RGB")
    assert im.size == (480, 860), f"{name} unexpected size {im.size}"
    return im


def scale_to_height(im, h):
    w = round(im.width * h / im.height)
    return im.resize((w, h), Image.LANCZOS)


def centre_crop(im, w, h):
    x = max(0, (im.width - w) // 2)
    y = max(0, (im.height - h) // 2)
    return im.crop((x, y, x + w, y + h))


def fit_letterbox(im, w, h):
    """Resize to fit inside w x h preserving aspect, paste on BG canvas."""
    s = min(w / im.width, h / im.height)
    nw, nh = round(im.width * s), round(im.height * s)
    out = Image.new("RGB", (w, h), BG)
    out.paste(im.resize((nw, nh), Image.LANCZOS), ((w - nw) // 2, (h - nh) // 2))
    return out


def make_cover():
    panels = [load("01-menu.png"), load("02-level1.png"), load("04-level20.png")]
    cover = Image.new("RGB", (1360, 850), BG)
    x = 0
    for p in panels:
        p = centre_crop(scale_to_height(p, 850), 453, 850)
        cover.paste(p, (x, 0))
        x += 453
    d = ImageDraw.Draw(cover)
    for vx in (453, 906):
        d.rectangle([vx - 2, 0, vx + 1, 850], fill=GOLD)
    # Title band (bottom, semi-opaque dark strip + title text).
    band_h = 74
    band = Image.new("RGB", (1360, band_h), (20, 10, 45))
    cover.paste(band, (0, 850 - band_h))
    f_title = ImageFont.truetype(FONT, 44)
    f_sub = ImageFont.truetype(FONT, 22)
    title = "ODD ONE OUT"
    sub = "Spot the Difference  •  20 levels  •  Find the one blob that is different"
    tw = d.textlength(title, font=f_title)
    d.text(((1360 - tw) / 2, 850 - band_h + 2), title, font=f_title, fill=(255, 255, 255))
    sw = d.textlength(sub, font=f_sub)
    d.text(((1360 - sw) / 2, 850 - band_h + 46), sub, font=f_sub, fill=GOLD)
    return cover


def save(im, path):
    im.save(path, "JPEG", quality=90)
    print(f"{path.name}: {im.size} {path.stat().st_size} B")


def main():
    cover = make_cover()
    gp = HERE / "gamepix"; gd = HERE / "gamedistribution"; gm = HERE / "gamemonetize"
    for d in (gp, gd, gm):
        d.mkdir(parents=True, exist_ok=True)
    # GamePix
    save(cover, gp / "odd-one-out-cover-1360x850.jpg")
    icon = centre_crop(load("02-level1.png"), 480, 480).resize((512, 512), Image.LANCZOS)
    save(icon, gp / "odd-one-out-icon-512x512.jpg")
    # GameDistribution (5 JPGs)
    save(icon, gd / "odd-one-out-512x512.jpg")
    save(centre_crop(scale_to_height(cover, 384), 512, 384), gd / "odd-one-out-512x384.jpg")
    save(fit_letterbox(cover, 200, 120), gd / "odd-one-out-200x120.jpg")
    save(centre_crop(scale_to_height(cover, 720), 1280, 720), gd / "odd-one-out-1280x720.jpg")
    save(centre_crop(scale_to_height(cover, 550), 1280, 550), gd / "odd-one-out-1280x550.jpg")
    # GameMonetize (3 JPGs)
    save(centre_crop(scale_to_height(cover, 384), 512, 384), gm / "odd-one-out-512x384.jpg")
    save(icon, gm / "odd-one-out-512x512.jpg")
    save(centre_crop(scale_to_height(cover, 340), 512, 340), gm / "odd-one-out-512x340.jpg")
    # Verify every output size with PIL.
    for p in sorted(HERE.glob("*/*.jpg")):
        im = Image.open(p)
        assert im.mode == "RGB", p
    print("all thumbnails verified RGB JPG at their stated sizes")


if __name__ == "__main__":
    main()
