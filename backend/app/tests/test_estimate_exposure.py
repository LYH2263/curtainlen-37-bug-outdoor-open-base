import pytest
from fastapi import HTTPException

from app import db, seed
from app.repositories import history, settings_repo
from app.services import estimate_service


@pytest.fixture()
def tmp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "t.db")
    seed.init_db()
    return tmp_path / "t.db"


def test_estimate_pins_type_and_order(tmp_db):
    r = estimate_service.run_estimate(1, 1, True, "", "outdoor_uv")
    assert r["exposure_type"] == "outdoor_uv"
    assert r["extra_meters"] == 0.3
    assert r["order_meters"] == round(r["meters"] + 0.3, 2)
    saved = history.list_runs()[0]["result"]
    assert saved["exposure_type"] == "outdoor_uv"
    assert saved["order_meters"] == r["order_meters"]
    # 事后改默认加米，旧编号不得重算
    settings_repo.set_many({"exposure_outdoor_uv_extra_m": "1.0"})
    again = history.list_runs()[0]["result"]
    assert again["order_meters"] == saved["order_meters"]
    assert again["extra_meters"] == 0.3


def test_invalid_extra_config_rejected(tmp_db):
    settings_repo.set_many({"exposure_outdoor_uv_extra_m": "oops"})
    with pytest.raises(HTTPException) as e:
        estimate_service.run_estimate(1, 1, False, "", "outdoor_uv")
    assert e.value.status_code == 422


def test_disabled_type_falls_back_to_base(tmp_db):
    settings_repo.set_many({"exposure_outdoor_uv_enabled": "0"})
    r = estimate_service.run_estimate(1, 1, False, "", "outdoor_uv")
    assert r["exposure_type"] == "indoor"
    assert r["extra_meters"] == 0
    assert r["order_meters"] == r["meters"]


def test_unknown_type_rejected(tmp_db):
    with pytest.raises(HTTPException) as e:
        estimate_service.run_estimate(1, 1, False, "", "balcony")
    assert e.value.status_code == 422


def test_default_indoor_unchanged(tmp_db):
    r = estimate_service.run_estimate(1, 1, False, "")
    assert r["exposure_type"] == "indoor"
    assert r["order_meters"] == r["meters"] == 14.25
