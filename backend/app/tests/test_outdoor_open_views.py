"""历史三路（列表摘要 / 详情主字段 / 户外摘要）必须钉住同一份写入快照。"""
from app.modules.exposure import display


def test_three_views_share_one_snapshot():
    raw = {"exposure_type": "outdoor_uv", "meters": 4.0, "extra_meters": 0.5, "order_meters": 4.5}
    expo = display.summarize_run(raw)
    card = display.outdoor_card(raw)
    assert expo["order_meters"] == 4.5 == card["order_meters"]
    assert expo["extra_meters"] == 0.5 == card["extra_meters"]
    assert expo["type"] == "outdoor_uv" == card["type"]
    assert expo["base_meters"] == 4.0
    # 现行默认加米即使变成别的值，也不进入任何视图
    raw_after_settings = {**raw}
    again = display.summarize_run(raw_after_settings)
    assert again["order_meters"] == 4.5
    assert again["extra_meters"] == 0.5


def test_legacy_run_without_exposure_fields():
    expo = display.summarize_run({"meters": 5.0})
    assert expo["type"] == "indoor"
    assert expo["label"] == "普通室内"
    assert expo["extra_meters"] == 0
    assert expo["order_meters"] == 5.0


def test_indoor_snapshot_order_equals_base():
    raw = {"exposure_type": "indoor", "meters": 4.0, "extra_meters": 0, "order_meters": 4.0}
    expo = display.summarize_run(raw)
    assert expo["order_meters"] == expo["base_meters"] == 4.0
