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

def count_runs():
    c = connect()
    try:
        return int(c.execute("SELECT COUNT(*) c FROM calc_runs").fetchone()["c"])
    finally:
        c.close()

def get_run(run_id):
    """原样返回落库快照；展示口径由 router 只读派生，不在此处重算。"""
    c = connect()
    try:
        row = c.execute(
            """SELECT r.*, w.name window_name, w.exposure_type window_exposure_type,
                      f.name fabric_name
               FROM calc_runs r
               LEFT JOIN windows w ON w.id=r.window_id
               LEFT JOIN fabrics f ON f.id=r.fabric_id
               WHERE r.id=?""", (run_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        d["result"] = json.loads(d.pop("result_json"))
        return d
    finally:
        c.close()

def list_runs(limit=50):
    """列表与详情共用同一份只读快照，不存在各算各的。"""
    c = connect()
    try:
        rows = c.execute(
            """SELECT r.*, w.name window_name, w.exposure_type window_exposure_type,
                      f.name fabric_name
               FROM calc_runs r
               LEFT JOIN windows w ON w.id=r.window_id
               LEFT JOIN fabrics f ON f.id=r.fabric_id
               ORDER BY r.id DESC LIMIT ?""", (limit,)).fetchall()
        out = []
        for row in rows:
            d = dict(row)
            d["result"] = json.loads(d.pop("result_json"))
            out.append(d)
        return out
    finally:
        c.close()
