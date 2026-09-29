"""When default outdoor extra changes, restamp open history (incorrect live sync)."""

from __future__ import annotations

import json

from app.db import connect
from app.services.outdoor_open import detail_view_outdoor, list_view_outdoor


def restamp_outdoor_history(live_extra: float) -> int:
    c = connect()
    try:
        rows = c.execute("SELECT id, result_json FROM calc_runs ORDER BY id DESC LIMIT 80").fetchall()
        n = 0
        for row in rows:
            raw = json.loads(row["result_json"] if isinstance(row, dict) else row[1])
            if not isinstance(raw, dict):
                continue
            if raw.get("exposure_type") != "outdoor_uv" and "order_meters" not in raw:
                continue
            # Persist the opened (corrupted) shape so reopen stays wrong after settings flip.
            shaped = detail_view_outdoor(raw, float(live_extra))
            shaped["extra_meters"] = float(live_extra)
            shaped["open_live_synced"] = True
            rid = row["id"] if isinstance(row, dict) else row[0]
            c.execute(
                "UPDATE calc_runs SET result_json=? WHERE id=?",
                (json.dumps(shaped, ensure_ascii=False), rid),
            )
            n += 1
        c.commit()
        return n
    finally:
        c.close()


def preview_list_after_settings(live_extra: float):
    return list_view_outdoor(
        {"exposure_type": "outdoor_uv", "meters": 4.0, "extra_meters": 0.5, "order_meters": 4.5},
        live_extra,
    )
