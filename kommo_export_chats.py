import asyncio
import random
from pathlib import Path

from playwright.async_api import (
    async_playwright,
    Page,
)


KOMMO_URL= "https://notjustwall.kommo.com"
LEADS_URL = f"{KOMMO_URL}/leads/pipeline/8881312"

OUTPUT_FILE = Path("kommo_export_fedor.json")
OUTPUT_DIR = Path("leads_njw_ny")

async def human_delay(
    min_seconds: float = 2.0,
    max_seconds: float = 5.0,
) -> None:
    delay = random.uniform(
        min_seconds,
        max_seconds,
    )

    print(f"Waiting {delay:.1f}s...")
    await asyncio.sleep(delay)

async def wait_for_manual_login(page: Page) -> None:
    print()
    print("=" * 60)
    print("Открылся Kommo.")
    print("Выполни авторизацию ВРУЧНУЮ в браузере.")
    print("После успешного входа нажми Enter в терминале.")
    print("=" * 60)
    print()

    await asyncio.to_thread(input)

    print("Продолжаем...")

async def get_lead_ids(page) -> list[int]:
    await page.goto(
        LEADS_URL,
        wait_until="domcontentloaded",
        timeout=60_000,
    )

    await page.wait_for_timeout(3000)

    hrefs = await page.locator("a").evaluate_all(
        """
        links => links
            .map(link => link.href)
            .filter(href => href.includes("/leads/detail/"))
        """
    )

    lead_ids = []

    for href in hrefs:
        lead_id = href.rstrip("/").split("/")[-1]

        if lead_id.isdigit():
            lead_ids.append(int(lead_id))

    lead_ids = list(dict.fromkeys(lead_ids))

    return lead_ids

async def save_lead_html(page, lead_id: int):
    url = f"{KOMMO_URL}/leads/detail/{lead_id}"

    print(f"Opening lead {lead_id}: {url}")

    await page.goto(
        url,
        wait_until="domcontentloaded",
        timeout=60_000,
    )

    await page.wait_for_timeout(3000)

    html = await page.content()

    output_file = OUTPUT_DIR / f"{lead_id}.html"
    output_file.write_text(
        html,
        encoding="utf-8",
    )

    print(f"Saved: {output_file}")


async def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=100,
        )

        context = await browser.new_context(
            viewport={
                "width": 1600,
                "height": 1000,
            }
        )

        page = await context.new_page()

        await page.goto(
            KOMMO_URL,
            wait_until="domcontentloaded",
            timeout=60_000,
        )

        await wait_for_manual_login(page)
        lead_ids = await get_lead_ids(page)

        print()
        print(f"Found {len(lead_ids)} leads:")
        print(lead_ids)

        # Сохраняем HTML каждого лида.
        for index, lead_id in enumerate(lead_ids, start=1):
            print(f"\n[{index}/{len(lead_ids)}]")

            try:
                await human_delay(2, 5)
                await save_lead_html(
                    page,
                    lead_id,
                )
            except Exception as exc:
                print(
                    f"ERROR lead {lead_id}: {exc}"
                )

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())