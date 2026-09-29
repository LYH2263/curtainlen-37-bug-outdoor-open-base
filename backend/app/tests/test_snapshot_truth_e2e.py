"""端到端：落库快照是唯一订货真相。

覆盖剧本（均走真实 HTTP）：
- 户外抗紫外当场订货米 > 同参室内基础米，类型/加米/订货米三列分列且 order=base+extra；
- 写入后改设置默认加米（0.3 -> 1.0）、同窗类型室内再切回户外；
- 历史列表摘要、详情主字段、户外摘要三路打开同一编号，全部钉住写入快照：
  类型仍户外、订货米不掉回基础、不按新默认 1.0 重算、加米不丢失/不清零；
- 同参室内干算回基础口径，不增行、不改写已写入户外单；
- 加米配置非法，整单 422 且不增行；
- 现行设置只约束之后新开的户外单，不回刷旧编号。
"""
import pytest
from fastapi.testclient import TestClient

from app import db, seed


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "t.db")
    seed.init_db()
    from app.main import app
    return TestClient(app)


def _run_ids(items):
    return [it["id"] for it in items]


def _find(items, rid):
    return next(it for it in items if it["id"] == rid)


def test_outdoor_snapshot_is_single_order_truth(client):
    # 同参室内基础口径（1 号窗 + 1 号布：14.25）
    indoor = client.get("/api/estimate", params={
        "window_id": 1, "fabric_id": 1, "exposure_type": "indoor"}).json()
    base = indoor["meters"]
    assert indoor["exposure_type"] == "indoor"
    assert indoor["extra_meters"] == 0
    assert indoor["order_meters"] == base

    # 户外当场订货：三列分列，order = base + 加米，且严格大于室内基础米
    r = client.post("/api/estimate", json={
        "window_id": 1, "fabric_id": 1, "save": True, "exposure_type": "outdoor_uv"}).json()
    assert r["exposure_type"] == "outdoor_uv"
    assert r["extra_meters"] == 0.3
    assert r["order_meters"] == round(base + 0.3, 2)
    assert r["order_meters"] > base
    rid = r["run_id"]

    # 先把设置页默认加米改成另一合法值
    client.put("/api/settings", json={"exposure_outdoor_uv_extra_m": "1.0"})
    # 再把该窗空间类型改成室内（干算）再切回户外（干算，受新默认约束）
    back_indoor = client.get("/api/estimate", params={
        "window_id": 1, "fabric_id": 1, "exposure_type": "indoor"}).json()
    assert back_indoor["order_meters"] == base
    new_outdoor = client.get("/api/estimate", params={
        "window_id": 1, "fabric_id": 1, "exposure_type": "outdoor_uv"}).json()
    assert new_outdoor["extra_meters"] == 1.0
    assert new_outdoor["order_meters"] == round(base + 1.0, 2)

    # 干算不增行：库里仍只有先前那一条
    items = client.get("/api/runs").json()["items"]
    assert _run_ids(items) == [rid]

    pinned_order = round(base + 0.3, 2)

    # 一路：历史列表摘要
    row = _find(items, rid)
    assert row["result"]["exposure_type"] == "outdoor_uv"
    assert row["result"]["extra_meters"] == 0.3
    assert row["result"]["order_meters"] == pinned_order
    for view in (row["exposure"], row["outdoor_summary"]):
        assert view["type"] == "outdoor_uv"
        assert view["extra_meters"] == 0.3
        assert view["order_meters"] == pinned_order
        assert view["base_meters"] == base

    # 二路/三路：详情主字段与户外摘要
    detail = client.get(f"/api/runs/{rid}").json()
    assert detail["result"]["exposure_type"] == "outdoor_uv"
    assert detail["result"]["extra_meters"] == 0.3
    assert detail["result"]["order_meters"] == pinned_order
    assert detail["exposure"]["order_meters"] == pinned_order
    assert detail["exposure"]["extra_meters"] == 0.3
    assert detail["outdoor_summary"]["order_meters"] == pinned_order
    assert detail["outdoor_summary"]["extra_meters"] == 0.3

    # 不得掉回基础、不得按新默认 1.0 重算、加米不得清零
    assert pinned_order != base
    assert pinned_order != round(base + 1.0, 2)

    # 三路钉住同一组写入快照
    assert (row["exposure"]["order_meters"]
            == detail["result"]["order_meters"]
            == detail["outdoor_summary"]["order_meters"]
            == detail["exposure"]["order_meters"])


def test_indoor_dry_calc_does_not_rewrite_written_outdoor(client):
    r = client.post("/api/estimate", json={
        "window_id": 1, "fabric_id": 1, "save": True, "exposure_type": "outdoor_uv"}).json()
    rid, pinned = r["run_id"], r["order_meters"]

    # 同参改回室内干算：无户外加米的基础口径
    dry = client.get("/api/estimate", params={
        "window_id": 1, "fabric_id": 1, "exposure_type": "indoor"}).json()
    assert dry["run_id"] is None
    assert dry["extra_meters"] == 0
    assert dry["order_meters"] == dry["meters"]

    # 不增行、不改写已写入户外编号
    items = client.get("/api/runs").json()["items"]
    assert _run_ids(items) == [rid]
    detail = client.get(f"/api/runs/{rid}").json()
    assert detail["result"]["exposure_type"] == "outdoor_uv"
    assert detail["result"]["order_meters"] == pinned


def test_invalid_extra_config_fails_order_and_adds_no_row(client):
    before = client.get("/api/runs").json()["items"]
    client.put("/api/settings", json={"exposure_outdoor_uv_extra_m": "oops"})
    resp = client.post("/api/estimate", json={
        "window_id": 1, "fabric_id": 1, "save": True, "exposure_type": "outdoor_uv"})
    assert resp.status_code == 422
    after = client.get("/api/runs").json()["items"]
    assert _run_ids(after) == _run_ids(before)


def test_new_outdoor_order_uses_current_default_without_touching_old(client):
    old = client.post("/api/estimate", json={
        "window_id": 1, "fabric_id": 1, "save": True, "exposure_type": "outdoor_uv"}).json()
    old_id, old_order, old_extra = old["run_id"], old["order_meters"], old["extra_meters"]

    client.put("/api/settings", json={"exposure_outdoor_uv_extra_m": "0.8"})
    new = client.post("/api/estimate", json={
        "window_id": 1, "fabric_id": 1, "save": True, "exposure_type": "outdoor_uv"}).json()
    assert new["extra_meters"] == 0.8
    assert new["order_meters"] == round(new["meters"] + 0.8, 2)

    detail = client.get(f"/api/runs/{old_id}").json()
    assert detail["result"]["extra_meters"] == old_extra
    assert detail["result"]["order_meters"] == old_order
