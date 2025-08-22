from __future__ import annotations

"""
Minimal E2E test for the Web UI using Playwright (Python).

Usage (PowerShell on Windows):
  # 1) In one terminal: start the server
  #   cd C:\Users\mayum\fx-local-first; . .\.venv\Scripts\Activate.ps1
  #   python scripts\webapp.py
  # 2) In another terminal: run this E2E test
  #   . .\.venv\Scripts\Activate.ps1
  #   pip install playwright
  #   python -m playwright install chromium
  #   python scripts\e2e_playwright.py

Environment:
  BASE_URL: override base URL (default http://localhost:7860)
"""

import os
import sys
from pathlib import Path
from time import sleep
from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout


def main() -> int:
    base_url = os.environ.get("BASE_URL", "http://localhost:7860")
    out_dir = Path("out")
    out_dir.mkdir(parents=True, exist_ok=True)
    screenshot = out_dir / "e2e_screenshot.png"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()
        page.goto(base_url, wait_until="domcontentloaded")

        # Wait for CSV select
        page.wait_for_selector("select#csv", timeout=10_000)
        # Ensure options exist; if not, just proceed (page may still render)
        options = page.query_selector_all("select#csv > option")
        if options:
            # Select first CSV option
            first_val = options[0].get_attribute("value") or ""
            if first_val:
                page.select_option("select#csv", first_val)

        # Click Run
        page.click("button#run")

        # Wait for either equity canvas present or metrics updated
        try:
            page.wait_for_selector("canvas#equity", timeout=20_000)
        except PwTimeout:
            # Fallback: wait metrics text
            page.wait_for_selector("#m_tr", timeout=10_000)

        page.screenshot(path=str(screenshot))
        print(f"Saved screenshot: {screenshot}")
        browser.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())

