# Coco Pinterest Publisher

Reusable publisher for the Coco the Axolotl Pinterest launch.

## Generate visuals

```powershell
python scripts/pinterest/generate_pinterest_assets.py
```

This creates:

- `pinterest-pins/pin-001.png` through `pinterest-pins/pin-030.png`
- `scripts/pinterest/pins-queue.json`

## Publish

`PINTEREST_TOKEN` must be provided through the environment. Never commit it.

```powershell
$env:PINTEREST_TOKEN = "..."
python scripts/pinterest/publish.py --boards-only
python scripts/pinterest/publish.py --limit 2
```

The first command creates or syncs the seven thematic boards in `boards.json`.
The second command publishes two pending pins and marks them as `published` in `pins-queue.json`.

Useful checks:

```powershell
python scripts/pinterest/publish.py --dry-run
(Get-ChildItem pinterest-pins\pin-*.png).Count
```

The script uses Pinterest API v5 endpoints:

- `GET /v5/boards`
- `POST /v5/boards`
- `POST /v5/pins`
