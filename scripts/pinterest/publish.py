from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


API_BASE = "https://api.pinterest.com/v5"
ROOT = Path(__file__).resolve().parents[2]
BOARDS_PATH = Path(__file__).with_name("boards.json")
QUEUE_PATH = Path(__file__).with_name("pins-queue.json")


BOARD_DEFINITIONS = [
    {
        "name": "Free Coloring Pages for Kids",
        "description": "Free printable coloring pages with Coco the Axolotl and friends. Perfect for kids ages 3-10.",
    },
    {
        "name": "Kids Mazes Printable",
        "description": "Free printable mazes for kids. Fun puzzles to print at home, ages 4-10.",
    },
    {
        "name": "Word Search for Kids",
        "description": "Free word search puzzles for children. Themed by animals, school, holidays.",
    },
    {
        "name": "Dot to Dot Activities",
        "description": "Connect the dots printable for kids. Ages 3-10, easy to advanced.",
    },
    {
        "name": "Color by Number",
        "description": "Free color by number printables. Educational and fun activities for kids.",
    },
    {
        "name": "Axolotl Coloring & Crafts",
        "description": "Everything Axolotl: coloring pages, crafts and stories starring Coco the Axolotl.",
    },
    {
        "name": "Coco's Bedtime Stories",
        "description": "Free bedtime activities, stories and lullabies featuring Coco the Axolotl.",
    },
]


class PinterestError(RuntimeError):
    def __init__(self, message: str, status: int | None = None, body: str | None = None):
        super().__init__(message)
        self.status = status
        self.body = body


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def request_json(token: str, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = None
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = Request(f"{API_BASE}{path}", data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=30) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        if exc.code == 401:
            hint = "Pinterest returned 401. Check that PINTEREST_TOKEN is valid and has the required scopes."
        elif exc.code == 429:
            hint = "Pinterest returned 429. Rate limit reached; wait before retrying."
        else:
            hint = f"Pinterest returned HTTP {exc.code}."
        raise PinterestError(hint, status=exc.code, body=body) from exc
    except URLError as exc:
        raise PinterestError(f"Pinterest request failed: {exc.reason}") from exc


def list_boards(token: str) -> list[dict[str, Any]]:
    boards: list[dict[str, Any]] = []
    bookmark = None
    while True:
        path = "/boards?page_size=100"
        if bookmark:
            path += f"&bookmark={bookmark}"
        response = request_json(token, "GET", path)
        boards.extend(response.get("items", []))
        bookmark = response.get("bookmark")
        if not bookmark:
            return boards


def normalize_boards(existing_boards: list[dict[str, Any]], stored: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_name = {board.get("name"): board for board in existing_boards}
    stored_by_name = {board.get("name"): board for board in stored}
    normalized = []
    for definition in BOARD_DEFINITIONS:
        name = definition["name"]
        api_board = by_name.get(name)
        saved = stored_by_name.get(name, {})
        normalized.append(
            {
                "name": name,
                "description": definition["description"],
                "id": (api_board or saved).get("id"),
                "url": (api_board or saved).get("url"),
                "created_by_script": bool(saved.get("created_by_script")),
            }
        )
    return normalized


def ensure_boards(token: str) -> list[dict[str, Any]]:
    stored = load_json(BOARDS_PATH, [])
    boards = normalize_boards(list_boards(token), stored)
    for board in boards:
        if board.get("id"):
            continue
        print(f"Creating board: {board['name']}")
        created = request_json(
            token,
            "POST",
            "/boards",
            {
                "name": board["name"],
                "description": board["description"],
                "privacy": "PUBLIC",
            },
        )
        board["id"] = created.get("id")
        board["url"] = created.get("url")
        board["created_by_script"] = True
        save_json(BOARDS_PATH, boards)
        time.sleep(1)
    save_json(BOARDS_PATH, boards)
    return boards


def publish_pin(token: str, item: dict[str, Any], board_id: str) -> dict[str, Any]:
    payload = {
        "title": item["title"],
        "description": item["description"],
        "link": item["link"],
        "board_id": board_id,
        "media_source": {
            "source_type": "image_url",
            "url": item["media_url"],
            "is_standard": True,
        },
        "alt_text": item["alt_text"],
    }
    return request_json(token, "POST", "/pins", payload)


def validate_public_urls(queue: list[dict[str, Any]]) -> None:
    missing = []
    for item in queue:
        local_path = ROOT / str(item.get("local_pin", ""))
        if not local_path.exists():
            missing.append(str(local_path))
    if missing:
        raise SystemExit("Missing local pin images:\n" + "\n".join(missing))


def run(limit: int, boards_only: bool, dry_run: bool) -> int:
    token = os.environ.get("PINTEREST_TOKEN")
    if not token and not dry_run:
        raise SystemExit("PINTEREST_TOKEN is required. Example: $env:PINTEREST_TOKEN='...' ; python scripts/pinterest/publish.py")

    queue = load_json(QUEUE_PATH, [])
    validate_public_urls(queue)

    if dry_run:
        pending = [item for item in queue if item.get("status") == "pending"]
        print(f"Dry run OK: {len(pending)} pending pins, {len(queue)} queued pins total.")
        return 0

    boards = ensure_boards(token or "")
    board_ids = {board["name"]: board.get("id") for board in boards}
    missing = sorted({item["board_name"] for item in queue if not board_ids.get(item["board_name"])})
    if missing:
        raise SystemExit("Missing board IDs for: " + ", ".join(missing))
    if boards_only:
        print(f"Boards ready: {len(boards)} configured boards.")
        return 0

    published = 0
    for item in queue:
        if item.get("status") == "published":
            continue
        if published >= limit:
            break
        board_id = board_ids[item["board_name"]]
        print(f"Publishing {item['id']}: {item['title']}")
        try:
            response = publish_pin(token or "", item, str(board_id))
        except PinterestError as exc:
            item["status"] = "error"
            item["error"] = {"message": str(exc), "status": exc.status, "body": exc.body, "at": utc_now()}
            save_json(QUEUE_PATH, queue)
            raise
        item["status"] = "published"
        item["pin_id"] = response.get("id")
        item["published_at"] = utc_now()
        item.pop("error", None)
        save_json(QUEUE_PATH, queue)
        published += 1
        time.sleep(2)

    print(f"Published {published} pin(s).")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish Coco Pinterest pins from pins-queue.json.")
    parser.add_argument("--limit", type=int, default=2, help="Number of pending pins to publish per run.")
    parser.add_argument("--boards-only", action="store_true", help="Create or sync boards, then stop.")
    parser.add_argument("--dry-run", action="store_true", help="Validate local queue and images without calling Pinterest.")
    args = parser.parse_args()
    try:
        return run(limit=args.limit, boards_only=args.boards_only, dry_run=args.dry_run)
    except PinterestError as exc:
        print(str(exc), file=sys.stderr)
        if exc.body:
            print(exc.body, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
