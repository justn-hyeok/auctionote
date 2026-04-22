"""One-off screenshot helper for the deployed Streamlit app.

Not part of the pipeline; run manually after a successful deploy to populate
docs/screenshots/*.png referenced from README.md.

Streamlit Cloud wraps the app in an iframe; navigate to the inner `~/+/`
frame URL directly so the Cloud chrome is dropped and the real app fills the
viewport. Streamlit manages its own scroll container (document body is not
scrollable), so per-section shots are taken via element.screenshot() on the
Plotly chart div and the st_folium iframe.
"""
from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

APP_ROOT = "https://auctionote-g5gndhc2ri3ca5h6qbyappb.streamlit.app"
INNER_URL = f"{APP_ROOT}/~/+/"
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "screenshots"

BOOT_WAIT_MS = 22_000
OVERVIEW_VIEWPORT = {"width": 1440, "height": 1800}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport=OVERVIEW_VIEWPORT,
            device_scale_factor=2,
        )
        page = context.new_page()
        page.set_default_timeout(120_000)

        print(f"navigating → {INNER_URL}", flush=True)
        page.goto(INNER_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(BOOT_WAIT_MS)

        # 01 overview — tall viewport + full_page to capture the whole column
        page.screenshot(path=str(OUT / "01_overview.png"), full_page=True)
        print("saved 01_overview.png", flush=True)

        # 02 discount chart — element shot
        chart = page.locator('[data-testid="stPlotlyChart"]').first
        chart.scroll_into_view_if_needed()
        page.wait_for_timeout(1_500)
        chart.screenshot(path=str(OUT / "02_discount_chart.png"))
        print("saved 02_discount_chart.png", flush=True)

        # 03 map — the folium component is rendered in an iframe; shoot the
        # iframe element's bounding box
        fmap = page.locator("iframe.stCustomComponentV1").first
        fmap.scroll_into_view_if_needed()
        page.wait_for_timeout(2_500)
        fmap.screenshot(path=str(OUT / "03_map.png"))
        print("saved 03_map.png", flush=True)

        browser.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        raise
