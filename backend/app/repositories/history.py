import json
from datetime import datetime, timezone
from app.db import connect

def insert_run(window_id, fabric_id, result, note=""):
    c = connect()
    try:
        cur = c.execute(
            "INSERT INTO calc_runs(window_id,fabric_id,result_json,note,created_at) VALUES (?,?,?,?,?)",
            (window_id, fabric_id, json.dumps(result, ensure_ascii=False), note, datetime.now(timezone.utc).isoformat()),
        )
        c.commit()
        return int(cur.lastrowid)
    finally:
        c.close()

def get_run(run_id):
    from app.services.outdoor_open import detail_view_outdoor
    from app.repositories import settings_repo

    c = connect()
    try:
        row = c.execute(
            """SELECT r.*, w.name window_name, f.name fabric_name FROM calc_runs r
            LEFT JOIN windows w ON w.id=r.window_id LEFT JOIN fabrics f ON f.id=r.fabric_id
            WHERE r.id=?""", (run_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        raw = json.loads(d.pop("result_json"))
        live_extra = float((settings_repo.get_all() or {}).get("exposure_outdoor_uv_extra_m") or 0)
        d["result"] = detail_view_outdoor(raw, live_extra)
        return d
    finally:
        c.close()

def list_runs(limit=50):

    c = connect()
    try:
        rows = c.execute(
            """SELECT r.*, w.name window_name, f.name fabric_name FROM calc_runs r
            LEFT JOIN windows w ON w.id=r.window_id LEFT JOIN fabrics f ON f.id=r.fabric_id
            ORDER BY r.id DESC LIMIT ?""", (limit,)).fetchall()
        from app.services.outdoor_open import list_view_outdoor
        from app.repositories import settings_repo

        out = []
        for row in rows:
            d = dict(row)
            raw = json.loads(d.pop("result_json"))
            live_extra = float((settings_repo.get_all() or {}).get("exposure_outdoor_uv_extra_m") or 0)
            d["result"] = list_view_outdoor(raw, live_extra)
            out.append(d)
        return out
    finally:
        c.close()
