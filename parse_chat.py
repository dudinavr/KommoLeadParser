import json
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

from bs4 import BeautifulSoup


INPUT_DIR = Path('leads_njw_fedor')
OUTPUT_DIR = Path("chats_njw_fedor")

LOCAL_TZ = ZoneInfo("America/New_York")

def parse_message_datetime(
    value: str,
) -> datetime | None:
    reference_date = datetime.now(LOCAL_TZ)
    value = value.strip()

    if value.startswith("Today "):
        time_str = value.removeprefix("Today ").strip()

        parsed_time = datetime.strptime(
            time_str,
            "%I:%M%p",
        ).time()

        dt = datetime.combine(
            reference_date.date(),
            parsed_time,
        )

        return dt.replace(tzinfo=LOCAL_TZ)

    try:
        dt = datetime.strptime(
            value,
            "%m/%d/%Y %I:%M%p",
        )

        return dt.replace(tzinfo=LOCAL_TZ)

    except ValueError:
        return None

def get_source(note) -> str | None:
    origin = note.select_one(".feed-note__icon-origin img")

    if not origin:
        return None

    src = origin.get("src", "").lower()

    if "facebook" in src:
        return "facebook"

    if "instagram" in src:
        return "instagram"

    if "twilio" in src:
        return "twilio"

    return None

def normalize_name(name: str | None) -> str:
    if not name:
        return ""

    return " ".join(name.lower().split())


def get_client_name(soup) -> str | None:
    element = soup.select_one(
        "input.js-linked-name-view"
    )

    if not element:
        return None

    return element.get("value")


def get_direction(
    sender_name: str | None,
    client_name: str | None,
) -> str:
    if (
        sender_name
        and client_name
        and normalize_name(sender_name)
        == normalize_name(client_name)
    ):
        return "incoming"

    return "outgoing"


def parse_chat(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")

    messages = []

    for note in soup.select(
        ".feed-note-wrapper.feed-note-wrapper-amojo"
    ):
        message_body = note.select_one(
            ".feed-note__body"
        )

        if not message_body:
            continue

        message_parts = [
            element.get_text(" ", strip=True)
            for element in message_body.select(
                ".feed-note__message_paragraph"
            )
        ]

        if not message_parts:
            continue

        text = "\n".join(
            part
            for part in message_parts
            if part
        )

        date_element = note.select_one(
            ".feed-note__date"
        )

        date = (
            date_element.get_text(" ", strip=True)
            if date_element
            else None
        )

        author_element = note.select_one(
            ".js-amojo-author"
        )

        if not author_element:
            author_element = note.select_one(
                ".feed-note__amojo-user"
            )

        author = (
            author_element.get_text(" ", strip=True)
            if author_element
            else None
        )

        message_id = note.get("data-id")


        message_time = parse_message_datetime(
            date
        )
        client_name = get_client_name(soup)

        direction = get_direction(
            sender_name=author,
            client_name=client_name,
        )

        messages.append(
            {
                "id": message_id,
                "author": author,
                "text": text,
                "datetime": message_time.isoformat() if message_time else None,
                "direction": direction,
                "source": get_source(note),
                'client_name': client_name,
            }
        )

    return messages


def main():
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    html_files = INPUT_DIR.glob("*.html")

    for html_file in html_files:
        lead_id = html_file.stem

        html = html_file.read_text(
            encoding="utf-8"
        )

        messages = parse_chat(html)

        output_file = OUTPUT_DIR / f"{lead_id}.json"

        output_file.write_text(
            json.dumps(
                messages,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        print(
            f"{lead_id}: "
            f"{len(messages)} messages -> {output_file}"
        )


if __name__ == "__main__":
    main()