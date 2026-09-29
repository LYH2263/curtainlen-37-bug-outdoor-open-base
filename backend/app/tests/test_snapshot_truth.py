"""验收单：落库快照是唯一订货真相。

户外单写入后——
1. 改设置页默认加米为另一合法值；
2. 窗空间类型改室内再改回户外；
再从历史列表摘要、详情主字段、户外摘要打开该编号，三路必须钉住同一组快照；
干算室内回到基础口径且不脏写；非法配置整单失败不增行；现行设置/类型只管新单。
"""
import pytest
from fastapi import HTTPException

from app import db, seed
from app.repositories import history, settings_repo, windows
from app.routers import history_router
from app.services import estimate_service


@pytest.fixture()
def tmp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "t.db")
    seed.init_db()
    return tmp_path / "t.db"


def _views(run_id):
    """同一编号的三路：列表摘要、详情主字段、户外摘要。"""
    listed = next(x for x in history_router.runs()["items"] if x["id"] == run_id)
    detail = history_router.run(run_id)
    return listed, detail


def test_written_snapshot_is_sole_truth(tmp_db):
    # 1) 户外抗紫外单落库：订货 = 基础 + 加米，且当场订货米 > 同参室内基础米
    r = estimate_service.run_estimate(1, 1, True, "", "outdoor_uv")
    rid = r["run_id"]
    base = r["meters"]
    assert r["exposure_type"] == "outdoor_uv"
    assert r["extra_meters"] == 0.3
    assert r["order_meters"] == round(base + 0.3, 2)
    assert r["order_meters"] > base
    pinned = {"exposure_type": "outdoor_uv", "meters": base,
              "extra_meters": 0.3, "order_meters": r["order_meters"]}

    # 2) 设置页默认加米改成另一合法值；3) 窗类型改室内再改回户外
    settings_repo.set_many({"exposure_outdoor_uv_extra_m": "0.9"})
    assert windows.set_exposure_type(1, "indoor")
    assert windows.set_exposure_type(1, "outdoor_uv")

    # 三路打开：空间类型仍显示户外，订货米不掉基础、不按新默认重算、加米不丢不清零
    listed, detail = _views(rid)
    for view_name, item, summary in (
        ("列表", listed, listed["exposure"]),
        ("详情", detail, detail["exposure"]),
    ):
        assert item["result"]["exposure_type"] == pinned["exposure_type"], view_name
        assert item["result"]["meters"] == pinned["meters"], view_name
        assert item["result"]["extra_meters"] == pinned["extra_meters"], view_name
        assert item["result"]["order_meters"] == pinned["order_meters"], view_name
        assert summary["type"] == "outdoor_uv", view_name
        assert summary["order_meters"] == pinned["order_meters"], view_name
        assert summary["extra_meters"] == pinned["extra_meters"], view_name
    # 户外摘要（列表路与详情路各一份）同样钉住
    assert listed["outdoor_summary"]["order_meters"] == pinned["order_meters"]
    assert listed["outdoor_summary"]["extra_meters"] == pinned["extra_meters"]
    assert detail["outdoor_summary"]["order_meters"] == pinned["order_meters"]
    assert detail["outdoor_summary"]["extra_meters"] == pinned["extra_meters"]

    # 落库 JSON 原样，无任何 live 标记混入
    raw = history.get_run(rid)["result"]
    assert {k: raw[k] for k in ("exposure_type", "meters", "extra_meters", "order_meters")} == pinned
    assert "list_order_meters_pin" not in raw
    assert not any(k.startswith("open_") for k in raw)


def test_indoor_dry_run_uses_base_and_does_not_touch_written(tmp_db):
    r = estimate_service.run_estimate(1, 1, True, "", "outdoor_uv")
    rid, before = r["run_id"], history.count_runs()

    # 同参改回室内干算：无户外加米的基础口径
    dry = estimate_service.run_estimate(1, 1, False, "", "indoor")
    assert dry["exposure_type"] == "indoor"
    assert dry["extra_meters"] == 0
    assert dry["order_meters"] == dry["meters"]
    assert dry["run_id"] is None

    # 干算不增行、不改写已写入的户外编号，窗现行类型也不被干算改动
    assert history.count_runs() == before
    saved = history.get_run(rid)["result"]
    assert saved["exposure_type"] == "outdoor_uv"
    assert saved["order_meters"] == r["order_meters"]
    assert windows.get_window(1)["exposure_type"] == "outdoor_uv"


def test_invalid_extra_config_fails_whole_order_without_new_row(tmp_db):
    estimate_service.run_estimate(1, 1, True, "", "outdoor_uv")
    before = history.count_runs()
    settings_repo.set_many({"exposure_outdoor_uv_extra_m": "oops"})
    with pytest.raises(HTTPException) as e:
        estimate_service.run_estimate(1, 1, True, "", "outdoor_uv")
    assert e.value.status_code == 422
    assert history.count_runs() == before


@pytest.mark.parametrize("bad", ["-1", "nan", "inf", ""])
def test_invalid_extra_variants_rejected_without_row(tmp_db, bad):
    before = history.count_runs()
    settings_repo.set_many({"exposure_outdoor_uv_extra_m": bad})
    with pytest.raises(HTTPException) as e:
        estimate_service.run_estimate(1, 1, True, "", "outdoor_uv")
    assert e.value.status_code == 422
    assert history.count_runs() == before


def test_current_settings_and_window_type_only_affect_new_orders(tmp_db):
    old = estimate_service.run_estimate(1, 1, True, "", "outdoor_uv")
    old_order = old["order_meters"]

    settings_repo.set_many({"exposure_outdoor_uv_extra_m": "0.9"})
    # 新户外单按新默认加米，旧编号原样不动
    new = estimate_service.run_estimate(1, 1, True, "", "outdoor_uv")
    assert new["extra_meters"] == 0.9
    assert new["order_meters"] == round(new["meters"] + 0.9, 2)
    assert new["run_id"] != old["run_id"]
    assert history.get_run(old["run_id"])["result"]["order_meters"] == old_order
    assert history.get_run(old["run_id"])["result"]["extra_meters"] == 0.3

    # 窗现行类型已随新单落为户外；再改成室内只影响下一张单
    windows.set_exposure_type(1, "indoor")
    follow = estimate_service.run_estimate(1, 1, False, "", "indoor")
    assert follow["order_meters"] == follow["meters"]
    assert history.get_run(old["run_id"])["result"]["exposure_type"] == "outdoor_uv"


def test_window_exposure_update_endpoint_validates(tmp_db):
    from app.routers.windows import ExposureTypeBody, update_exposure

    updated = update_exposure(1, ExposureTypeBody(exposure_type="outdoor_uv"))
    assert updated["exposure_type"] == "outdoor_uv"
    with pytest.raises(HTTPException) as e:
        update_exposure(1, ExposureTypeBody(exposure_type="balcony"))
    assert e.value.status_code == 422
    with pytest.raises(HTTPException) as e:
        update_exposure(999, ExposureTypeBody(exposure_type="indoor"))
    assert e.value.status_code == 404
    # 非法更新未污染窗上现行类型
    assert windows.get_window(1)["exposure_type"] == "outdoor_uv"
