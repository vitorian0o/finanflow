"""Build a YouTube/README thumbnail from the dashboard screenshot."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
DASH = ROOT / "docs" / "screenshots" / "02-dashboard.png"
OUT_PNG = ROOT / "docs" / "videos" / "thumbnail.png"
OUT_JPG = ROOT / "docs" / "videos" / "youtube-thumbnail.jpg"

W, H = 1280, 720
NAVY = (11, 18, 32)
TEAL = (13, 148, 136)
TEAL_DEEP = (15, 118, 110)
WHITE = (248, 250, 252)
MUTED = (148, 163, 184)
CARD = (17, 28, 46)
ORANGE = (234, 88, 12)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "segoeuib.ttf" if bold else "segoeui.ttf"
    return ImageFont.truetype(str(Path("C:/Windows/Fonts") / name), size)


def rounded(image: Image.Image, radius: int) -> Image.Image:
    mask = Image.new("L", image.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, image.size[0] - 1, image.size[1] - 1), radius=radius, fill=255
    )
    out = image.convert("RGBA")
    out.putalpha(mask)
    return out


def teal_glow(size: tuple[int, int]) -> Image.Image:
    glow = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(glow)
    cx, cy = int(size[0] * 0.72), int(size[1] * 0.48)
    for radius, alpha in ((420, 55), (280, 80), (160, 70)):
        draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=(13, 148, 136, alpha))
    return glow.filter(ImageFilter.GaussianBlur(48))


def drop_shadow(base: Image.Image, xy: tuple[int, int], card: Image.Image) -> None:
    pad = 48
    shadow = Image.new("RGBA", (card.width + pad * 2, card.height + pad * 2), (0, 0, 0, 0))
    blob = Image.new("RGBA", card.size, (0, 0, 0, 160))
    shadow.paste(blob, (pad + 8, pad + 14))
    shadow = shadow.filter(ImageFilter.GaussianBlur(22))
    base.alpha_composite(shadow, (xy[0] - pad, xy[1] - pad))
    base.alpha_composite(card, xy)


def main() -> None:
    canvas = Image.new("RGBA", (W, H), NAVY + (255,))
    canvas.alpha_composite(teal_glow((W, H)))

    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 0, W, 8), fill=TEAL_DEEP)
    draw.rectangle((0, H - 8, W, H), fill=TEAL_DEEP)

    dash = Image.open(DASH).convert("RGB")
    # KPIs + charts only — skip header and yellow alert strip.
    crop = dash.crop((248, 318, 1428, 868))
    crop = crop.resize((860, 520), Image.Resampling.LANCZOS)
    preview = rounded(crop, 20)
    preview = preview.rotate(-6, resample=Image.Resampling.BICUBIC, expand=True)

    drop_shadow(canvas, (390, 78), preview)

    brand = font(20, bold=True)
    title = font(68, bold=True)
    subtitle = font(24)
    kpi_label = font(15, bold=True)
    kpi_value = font(26, bold=True)
    chip = font(15, bold=True)

    draw = ImageDraw.Draw(canvas)
    draw.text((56, 78), "FINANFLOW", font=brand, fill=TEAL)
    draw.rectangle((56, 112, 128, 116), fill=TEAL)
    draw.multiline_text((56, 132), "Dashboard\nfinanceiro", font=title, fill=WHITE, spacing=0)
    draw.text((56, 300), "para pequenas empresas", font=subtitle, fill=MUTED)

    pills = [
        ((56, 368), "RECEITA", "R$ 25 mil", TEAL),
        ((230, 368), "LUCRO", "R$ 14 mil", TEAL),
    ]
    for (x, y), label, value, color in pills:
        draw.rounded_rectangle((x, y, x + 158, y + 82), radius=14, fill=CARD)
        draw.text((x + 16, y + 12), label, font=kpi_label, fill=MUTED)
        draw.text((x + 16, y + 38), value, font=kpi_value, fill=color)

    draw.rounded_rectangle((56, 472, 214, 510), radius=999, fill=CARD)
    draw.text((74, 480), "DEMO  ·  1 MIN", font=chip, fill=ORANGE)

    # Play badge on the UI preview
    cx, cy, r = 980, 360, 46
    draw.ellipse((cx - r - 6, cy - r - 6, cx + r + 6, cy + r + 6), fill=(11, 18, 32, 90))
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=TEAL)
    draw.polygon([(cx - 12, cy - 18), (cx - 12, cy + 18), (cx + 22, cy)], fill=WHITE)

    final = canvas.convert("RGB")
    final.save(OUT_PNG, optimize=True)
    final.save(OUT_JPG, quality=92, optimize=True)
    print(f"Wrote {OUT_PNG} and {OUT_JPG}")


if __name__ == "__main__":
    main()
