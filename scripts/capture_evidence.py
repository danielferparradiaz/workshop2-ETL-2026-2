"""Capture actual local UI evidence using installed Edge (optional Playwright)."""
import json
from pathlib import Path
from urllib.parse import quote

from playwright.sync_api import sync_playwright

root = Path(__file__).resolve().parents[1]
summary = json.loads((root / 'docs/evidence/latest_reliability.json').read_text())
output = root / 'docs/evidence/screenshots'
output.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch(channel='msedge', headless=True)
    page = browser.new_page(viewport={'width': 1600, 'height': 1000}, device_scale_factor=1)
    for kind in ['baseline', 'failure', 'rerun']:
        url = f'http://localhost:8082/dags/reliable_music_pipeline/runs/{quote(summary[kind], safe="")}'
        page.goto(url, wait_until='networkidle', timeout=60000)
        page.wait_for_timeout(2500)
        if summary[kind] not in page.url:
            # SimpleAuthManager's first local login redirects to Home.
            page.goto(url, wait_until='networkidle', timeout=60000)
            page.wait_for_timeout(2500)
        assert summary[kind] in page.url, 'Requested run not displayed'
        print(kind, page.url, page.locator('body').inner_text()[:1400])
        page.screenshot(path=str(output / f'{kind}.png'), full_page=True)
    page.goto(f'http://localhost:8082/dags/reliable_music_pipeline/runs/{summary["failure"]}/tasks/validate_spotify_raw', wait_until='networkidle', timeout=60000)
    page.wait_for_timeout(3000)
    # Reveal the exception near the end of the scrollable task log.
    page.evaluate("""() => {
        for (const el of document.querySelectorAll('div')) {
            const overflow = getComputedStyle(el).overflowY;
            if (['auto', 'scroll'].includes(overflow) && el.scrollHeight > el.clientHeight) {
                el.scrollTop = el.scrollHeight;
            }
        }
    }""")
    page.wait_for_timeout(500)
    page.screenshot(path=str(output / 'failure_task.png'), full_page=True)
    page.goto('http://localhost:8502', wait_until='networkidle', timeout=60000)
    page.get_by_text('AR1 · Cobertura', exact=True).wait_for(timeout=60000)
    page.wait_for_timeout(2000)
    page.screenshot(path=str(output / 'dashboard.png'), full_page=True)
    print('dashboard', page.locator('body').inner_text()[:1200])
    browser.close()
