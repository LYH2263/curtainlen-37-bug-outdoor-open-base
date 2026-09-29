from app.db import connect

DEFAULT_SETTINGS = {
    "default_fullness": "2.0",
    "exposure_outdoor_uv_enabled": "1",
    "exposure_outdoor_uv_extra_m": "0.3",
}

def init_db():
    c = connect()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS windows(id INTEGER PRIMARY KEY,name TEXT,width REAL,height REAL,fullness REAL,data_quality TEXT,note TEXT,exposure_type TEXT NOT NULL DEFAULT 'indoor');
    CREATE TABLE IF NOT EXISTS fabrics(id INTEGER PRIMARY KEY,name TEXT,fabric_width REAL,hem_top REAL,hem_bottom REAL,data_quality TEXT,note TEXT);
    CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT);
    CREATE TABLE IF NOT EXISTS calc_runs(id INTEGER PRIMARY KEY AUTOINCREMENT,window_id INT,fabric_id INT,result_json TEXT,note TEXT,created_at TEXT);
    """)
    # 旧库幂等迁移：窗户现行空间类型（只约束之后新开的单，不回刷历史）
    cols = {r["name"] for r in c.execute("PRAGMA table_info(windows)").fetchall()}
    if "exposure_type" not in cols:
        c.execute("ALTER TABLE windows ADD COLUMN exposure_type TEXT NOT NULL DEFAULT 'indoor'")
    if c.execute("SELECT COUNT(*) c FROM windows").fetchone()["c"] == 0:
        c.executemany("INSERT INTO windows(name,width,height,fullness,data_quality,note,exposure_type) VALUES (?,?,?,?,?,?,?)",[
            ("客厅落地窗",3.0,2.6,2.0,"clean","","indoor"),
            ("卧室窗",2.2,1.5,2.0,"clean","","indoor"),
            ("脏数据-零宽",0.0,2.0,2.0,"dirty","宽度为0","indoor"),
        ])
        c.executemany("INSERT INTO fabrics(name,fabric_width,hem_top,hem_bottom,data_quality,note) VALUES (?,?,?,?,?,?)",[
            ("遮光1.4m",1.4,0.10,0.15,"clean",""),
            ("纱帘2.8m",2.8,0.08,0.12,"clean",""),
            ("脏数据-零门幅",0.0,0.1,0.1,"dirty",""),
        ])
    for k, v in DEFAULT_SETTINGS.items():
        c.execute("INSERT OR IGNORE INTO settings(key,value) VALUES (?,?)", (k, v))
    c.commit()
    c.close()
