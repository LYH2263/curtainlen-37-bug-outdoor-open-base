from app.db import connect

def list_windows():
    c = connect()
    try:
        return [dict(r) for r in c.execute("SELECT * FROM windows ORDER BY id").fetchall()]
    finally:
        c.close()

def get_window(wid: int):
    c = connect()
    try:
        r = c.execute("SELECT * FROM windows WHERE id=?", (wid,)).fetchone()
        return dict(r) if r else None
    finally:
        c.close()

def set_exposure_type(wid: int, exposure_type: str) -> bool:
    """更新窗户现行空间类型。只影响之后新开的单，历史快照原样保留。"""
    c = connect()
    try:
        cur = c.execute("UPDATE windows SET exposure_type=? WHERE id=?", (exposure_type, wid))
        c.commit()
        return cur.rowcount > 0
    finally:
        c.close()
