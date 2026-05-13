"""Generate app icon (apple-touch-icon + favicon). Run once: uv run static/make_icon.py"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT_DIR = Path(__file__).parent
SIZE = 180
BG = (33, 33, 38)
ACCENT = (94, 140, 255)
WHITE = (245, 245, 250)
RADIUS = 36


def rounded_rect(size, radius, fill):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([(0, 0), (size - 1, size - 1)], radius=radius, fill=fill)
    return img


def load_font(size):
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
    ]
    for p in candidates:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()


def make_icon(size):
    scale = size / SIZE
    img = rounded_rect(size, int(RADIUS * scale), BG)
    d = ImageDraw.Draw(img)

    # Markdown-style "M↓" — bold M in white with a blue down-arrow accent
    font_m = load_font(int(110 * scale))
    text = "M"
    bbox = d.textbbox((0, 0), text, font=font_m)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (size - tw) / 2 - bbox[0] - int(14 * scale)
    y = (size - th) / 2 - bbox[1] - int(6 * scale)
    d.text((x, y), text, font=font_m, fill=WHITE)

    # Down arrow (markdown rendered-into symbol)
    cx = size / 2 + int(38 * scale)
    cy = size / 2 + int(14 * scale)
    arm = int(22 * scale)
    w = int(8 * scale)
    # vertical stem
    d.rounded_rectangle(
        [cx - w // 2, cy - arm, cx + w // 2, cy + arm],
        radius=w // 2,
        fill=ACCENT,
    )
    # arrowhead (triangle)
    head = int(22 * scale)
    d.polygon(
        [
            (cx - head, cy + arm - int(4 * scale)),
            (cx + head, cy + arm - int(4 * scale)),
            (cx, cy + arm + head - int(4 * scale)),
        ],
        fill=ACCENT,
    )
    return img


def main():
    # Apple touch icon (180×180)
    icon = make_icon(180)
    icon.save(OUT_DIR / "apple-touch-icon.png", "PNG")
    icon.save(OUT_DIR / "apple-touch-icon-precomposed.png", "PNG")
    # Favicon (32×32) + larger PNG variant
    make_icon(32).save(OUT_DIR / "favicon.png", "PNG")
    make_icon(192).save(OUT_DIR / "icon-192.png", "PNG")
    print("Icons written to", OUT_DIR)


if __name__ == "__main__":
    main()
