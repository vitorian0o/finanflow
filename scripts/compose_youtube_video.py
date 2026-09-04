"""Compose a single YouTube demo from the three FinanFlow clips."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

ROOT = Path(__file__).resolve().parents[1]
VIDEOS = ROOT / "docs" / "videos"
WORK = VIDEOS / "_compose"
OUTPUT = VIDEOS / "finanflow-demo-youtube.mp4"

WIDTH, HEIGHT = 1920, 1080
FPS = 30
NAVY = (11, 18, 32)
TEAL = (15, 118, 110)
WHITE = (241, 245, 249)
MUTED = (148, 163, 184)

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "segoeuib.ttf" if bold else "segoeui.ttf"
    return ImageFont.truetype(str(Path("C:/Windows/Fonts") / name), size)


def make_card(path: Path, eyebrow: str, title: str, subtitle: str = "") -> None:
    image = Image.new("RGB", (WIDTH, HEIGHT), NAVY)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, WIDTH, 8), fill=TEAL)
    draw.rectangle((0, HEIGHT - 8, WIDTH, HEIGHT), fill=TEAL)

    eyebrow_font = font(28, bold=True)
    title_font = font(86, bold=True)
    subtitle_font = font(36)

    eyebrow_box = draw.textbbox((0, 0), eyebrow, font=eyebrow_font)
    title_box = draw.textbbox((0, 0), title, font=title_font)
    subtitle_box = draw.textbbox((0, 0), subtitle, font=subtitle_font) if subtitle else (0, 0, 0, 0)

    block_h = (eyebrow_box[3] - eyebrow_box[1]) + 28 + (title_box[3] - title_box[1])
    if subtitle:
        block_h += 36 + (subtitle_box[3] - subtitle_box[1])
    y = (HEIGHT - block_h) // 2

    def centered(text: str, used_font, fill, top: int) -> int:
        box = draw.textbbox((0, 0), text, font=used_font)
        x = (WIDTH - (box[2] - box[0])) // 2
        draw.text((x, top), text, font=used_font, fill=fill)
        return top + (box[3] - box[1])

    y = centered(eyebrow.upper(), eyebrow_font, TEAL, y) + 28
    y = centered(title, title_font, WHITE, y)
    if subtitle:
        y += 36
        centered(subtitle, subtitle_font, MUTED, y)

    line_y = HEIGHT // 2 + 120
    draw.rectangle((WIDTH // 2 - 48, line_y, WIDTH // 2 + 48, line_y + 4), fill=TEAL)
    image.save(path)


def run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout or "ffmpeg failed")


def card_clip(image: Path, dest: Path, seconds: float) -> None:
    run(
        [
            FFMPEG,
            "-y",
            "-loop",
            "1",
            "-i",
            str(image),
            "-t",
            str(seconds),
            "-r",
            str(FPS),
            "-vf",
            f"fps={FPS},format=yuv420p",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-an",
            str(dest),
        ]
    )


def normalize_clip(source: Path, dest: Path) -> None:
    run(
        [
            FFMPEG,
            "-y",
            "-i",
            str(source),
            "-vf",
            (
                f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease,"
                f"pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2:color=0x0b1220,"
                f"fps={FPS},format=yuv420p"
            ),
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-an",
            str(dest),
        ]
    )


def concat(files: list[Path], dest: Path) -> None:
    listing = WORK / "concat.txt"
    listing.write_text("".join(f"file '{path.as_posix()}'\n" for path in files), encoding="utf-8")
    run(
        [
            FFMPEG,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(listing),
            "-c",
            "copy",
            str(dest),
        ]
    )


def main() -> None:
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)

    cards = {
        "open": ("Demonstração", "FinanFlow", "Gestão financeira para pequenas empresas"),
        "login": ("1.", "Login", "Acesse a conta e o dashboard"),
        "payable": ("2.", "Seção: Contas a pagar", "Vencimentos e marcar como pago"),
        "import": ("3.", "Seção: Importação de CSV", "Validação, preview e gravação"),
        "end": ("FinanFlow", "Obrigado por assistir", "demo@finanflow.app"),
    }
    for key, (eyebrow, title, subtitle) in cards.items():
        make_card(WORK / f"{key}.png", eyebrow, title, subtitle)

    card_clip(WORK / "open.png", WORK / "00-open.mp4", 3.4)
    card_clip(WORK / "login.png", WORK / "01-title.mp4", 2.8)
    normalize_clip(VIDEOS / "01-login-dashboard.webm", WORK / "01-clip.mp4")
    card_clip(WORK / "payable.png", WORK / "02-title.mp4", 2.8)
    normalize_clip(VIDEOS / "02-contas-a-pagar.webm", WORK / "02-clip.mp4")
    card_clip(WORK / "import.png", WORK / "03-title.mp4", 2.8)
    normalize_clip(VIDEOS / "03-importacao-csv.webm", WORK / "03-clip.mp4")
    card_clip(WORK / "end.png", WORK / "04-end.mp4", 3.2)

    concat(
        [
            WORK / "00-open.mp4",
            WORK / "01-title.mp4",
            WORK / "01-clip.mp4",
            WORK / "02-title.mp4",
            WORK / "02-clip.mp4",
            WORK / "03-title.mp4",
            WORK / "03-clip.mp4",
            WORK / "04-end.mp4",
        ],
        OUTPUT,
    )
    shutil.rmtree(WORK, ignore_errors=True)
    print(f"Wrote {OUTPUT} ({OUTPUT.stat().st_size / 1024 / 1024:.1f} MB)")


if __name__ == "__main__":
    main()
