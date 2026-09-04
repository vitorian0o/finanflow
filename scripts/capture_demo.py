"""Capture portfolio screenshots and human-paced demo videos of FinanFlow."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import Locator, Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "docs" / "screenshots"
VIDEOS = ROOT / "docs" / "videos"
BASE = "http://localhost:5175"
SAMPLE = ROOT / "sample_data" / "transacoes_exemplo.csv"
STATE = VIDEOS / "_auth.json"

TYPE_DELAY_MS = 130
VIEWPORT = {"width": 1440, "height": 900}


def pause(page: Page, ms: int = 2000) -> None:
    page.wait_for_timeout(ms)


def hover_click(page: Page, locator: Locator, after: int = 900) -> None:
    locator.scroll_into_view_if_needed()
    locator.hover()
    pause(page, 400)
    locator.click()
    pause(page, after)


def type_like_user(page: Page, locator: Locator, text: str) -> None:
    locator.click()
    pause(page, 350)
    locator.press("Control+A")
    pause(page, 220)
    locator.press_sequentially(text, delay=TYPE_DELAY_MS)
    pause(page, 450)


def login_typed(page: Page) -> None:
    page.goto(f"{BASE}/login", wait_until="networkidle")
    pause(page, 1800)
    type_like_user(page, page.get_by_label("E-mail"), "demo@finanflow.app")
    type_like_user(page, page.get_by_label("Senha"), "demo12345")
    pause(page, 700)
    hover_click(page, page.get_by_role("button", name="Entrar"), after=400)
    page.get_by_role("heading", name="Dashboard").wait_for(timeout=20000)
    pause(page, 2800)


def login_silent(page: Page) -> None:
    page.goto(f"{BASE}/login", wait_until="domcontentloaded")
    page.get_by_label("E-mail").fill("demo@finanflow.app")
    page.get_by_label("Senha").fill("demo12345")
    page.get_by_role("button", name="Entrar").click()
    page.get_by_role("heading", name="Dashboard").wait_for(timeout=20000)


def run_insights(page: Page) -> None:
    page.evaluate(
        """async () => {
          const token = localStorage.getItem('ff_token');
          await fetch('/api/v1/insights/run', {
            method: 'POST',
            headers: { Authorization: `Bearer ${token}` },
          });
        }"""
    )
    page.reload(wait_until="networkidle")
    page.get_by_role("heading", name="Dashboard").wait_for()
    pause(page, 800)


def shot(page: Page, name: str, full_page: bool = False) -> None:
    pause(page, 400)
    page.screenshot(path=str(SHOTS / name), full_page=full_page, animations="disabled")


def convert_to_mp4(webm: Path, mp4: Path) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        return
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-i",
            str(webm),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(mp4),
        ],
        check=False,
        capture_output=True,
    )


def save_video(page: Page, dest: Path) -> None:
    video = page.video
    if video is None:
        return
    source = Path(video.path())
    page.context.close()
    dest.parent.mkdir(parents=True, exist_ok=True)
    if source.exists():
        shutil.move(str(source), str(dest))
        convert_to_mp4(dest, dest.with_suffix(".mp4"))


def new_recorded_page(browser, folder: str, storage_state: str | None = None):
    context = browser.new_context(
        viewport=VIEWPORT,
        record_video_dir=str(VIDEOS / folder),
        record_video_size=VIEWPORT,
        storage_state=storage_state,
    )
    return context, context.new_page()


def capture_screenshots(browser) -> None:
    context = browser.new_context(viewport=VIEWPORT, device_scale_factor=1)
    page = context.new_page()
    login_silent(page)
    run_insights(page)
    shot(page, "02-dashboard.png")

    page.get_by_role("link", name="Lançamentos").click()
    page.get_by_role("heading", name="Lançamentos").wait_for()
    pause(page, 500)
    shot(page, "03-lancamentos.png")

    page.get_by_role("link", name="Contas a pagar").click()
    page.get_by_role("heading", name="Contas a pagar").wait_for()
    pause(page, 500)
    shot(page, "04-contas-pagar.png")

    page.get_by_role("link", name="Contas a receber").click()
    page.get_by_role("heading", name="Contas a receber").wait_for()
    pause(page, 500)
    shot(page, "05-contas-receber.png")

    page.get_by_role("link", name="Categorias").click()
    page.get_by_role("heading", name="Categorias").wait_for()
    pause(page, 400)
    shot(page, "06-categorias.png")

    page.get_by_role("link", name="Importar CSV").click()
    page.get_by_role("heading", name="Importar CSV").wait_for()
    page.locator("input[type=file]").set_input_files(str(SAMPLE))
    page.get_by_role("button", name="Validar arquivo").click()
    page.get_by_text("Pré-visualização").wait_for(timeout=10000)
    shot(page, "07-importacao.png")

    page.get_by_role("link", name="Relatórios").click()
    page.get_by_role("heading", name="Relatórios").wait_for()
    pause(page, 600)
    shot(page, "08-relatorios.png")
    context.close()

    mobile = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True)
    page = mobile.new_page()
    login_silent(page)
    run_insights(page)
    shot(page, "09-dashboard-mobile.png")
    page.get_by_label("Abrir menu").click()
    page.get_by_role("link", name="Lançamentos").click()
    page.get_by_role("heading", name="Lançamentos").wait_for()
    pause(page, 400)
    shot(page, "10-lancamentos-mobile.png")
    mobile.close()

    login_ctx = browser.new_context(viewport=VIEWPORT)
    page = login_ctx.new_page()
    page.goto(f"{BASE}/login", wait_until="networkidle")
    pause(page, 400)
    shot(page, "01-login.png")
    login_ctx.close()


def persist_session(browser) -> None:
    context = browser.new_context(viewport=VIEWPORT)
    page = context.new_page()
    login_silent(page)
    run_insights(page)
    context.storage_state(path=str(STATE))
    context.close()


def record_login_dashboard(browser) -> None:
    dest = VIDEOS / "01-login-dashboard.webm"
    _context, page = new_recorded_page(browser, "_tmp1")
    login_typed(page)
    hover_click(page, page.locator("select").first, after=500)
    page.locator("select").first.select_option("last_3_months")
    pause(page, 3200)
    hover_click(page, page.locator("select").first, after=400)
    page.locator("select").first.select_option("this_month")
    pause(page, 3200)
    hover_click(page, page.get_by_label("Notificações"), after=2800)
    hover_click(page, page.get_by_label("Notificações"), after=900)
    save_video(page, dest)


def record_accounts(browser) -> None:
    dest = VIDEOS / "02-contas-a-pagar.webm"
    _context, page = new_recorded_page(browser, "_tmp2", storage_state=str(STATE) if STATE.exists() else None)
    if STATE.exists():
        page.goto(f"{BASE}/", wait_until="networkidle")
        page.get_by_role("heading", name="Dashboard").wait_for(timeout=20000)
        pause(page, 1800)
    else:
        login_typed(page)
    hover_click(page, page.get_by_role("link", name="Contas a pagar"), after=600)
    page.get_by_role("heading", name="Contas a pagar").wait_for()
    pause(page, 2800)
    hover_click(page, page.get_by_role("button", name="Marcar como pago").first, after=2800)
    hover_click(page, page.get_by_role("link", name="Lançamentos"), after=600)
    page.get_by_role("heading", name="Lançamentos").wait_for()
    pause(page, 2800)
    save_video(page, dest)


def record_import(browser) -> None:
    dest = VIDEOS / "03-importacao-csv.webm"
    _context, page = new_recorded_page(browser, "_tmp3", storage_state=str(STATE) if STATE.exists() else None)
    if STATE.exists():
        page.goto(f"{BASE}/", wait_until="networkidle")
        page.get_by_role("heading", name="Dashboard").wait_for(timeout=20000)
        pause(page, 1600)
    else:
        login_typed(page)
    hover_click(page, page.get_by_role("link", name="Importar CSV"), after=600)
    page.get_by_role("heading", name="Importar CSV").wait_for()
    pause(page, 2200)
    page.locator("input[type=file]").set_input_files(str(SAMPLE))
    pause(page, 1800)
    hover_click(page, page.get_by_role("button", name="Validar arquivo"), after=500)
    page.get_by_text("Pré-visualização").wait_for(timeout=10000)
    pause(page, 3500)
    hover_click(page, page.get_by_role("button", name="Importar válidos"), after=500)
    page.get_by_text("Importação concluída").wait_for(timeout=10000)
    pause(page, 3500)
    save_video(page, dest)


def cleanup_tmp() -> None:
    for folder in VIDEOS.glob("_tmp*"):
        shutil.rmtree(folder, ignore_errors=True)
    if STATE.exists():
        STATE.unlink()


def main() -> None:
    videos_only = "--videos-only" in sys.argv
    SHOTS.mkdir(parents=True, exist_ok=True)
    VIDEOS.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, slow_mo=180)
        if not videos_only:
            capture_screenshots(browser)
        persist_session(browser)
        record_login_dashboard(browser)
        record_accounts(browser)
        record_import(browser)
        browser.close()
    cleanup_tmp()
    print("Screenshots:", sorted(p.name for p in SHOTS.glob("*.png")))
    print("Videos:", sorted(p.name for p in VIDEOS.glob("*.webm")))


if __name__ == "__main__":
    main()
