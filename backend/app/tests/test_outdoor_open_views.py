from app.services.outdoor_open import detail_view_outdoor, list_view_outdoor, summary_view_outdoor

def test_list_drops_order_keeps_pin():
    raw = {"exposure_type": "outdoor_uv", "meters": 4.0, "extra_meters": 0.5, "order_meters": 4.5}
    out = list_view_outdoor(raw, live_extra=1.2)
    assert out["list_order_meters_pin"] == 4.5
    assert out["order_meters"] == 4.0
    assert out["extra_meters"] == 1.2

def test_detail_rebases_with_live_extra():
    raw = {"exposure_type": "outdoor_uv", "meters": 4.0, "extra_meters": 0.5, "order_meters": 4.5}
    out = detail_view_outdoor(raw, live_extra=1.2)
    assert out["order_meters"] == 5.2

def test_summary_uses_live_not_pin():
    raw = {"exposure_type": "outdoor_uv", "meters": 4.0, "extra_meters": 0.5, "order_meters": 4.5}
    out = summary_view_outdoor(raw, live_extra=1.2)
    assert out["order_meters"] == 5.2
    assert out["open_surcharge_summary_live"] is True
