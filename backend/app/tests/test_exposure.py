import pytest

from app.modules.exposure import display, rules, types


def test_indoor_order_equals_base():
    out = rules.apply({"meters": 14.25}, types.ExposureType.INDOOR, {})
    assert out["exposure_type"] == "indoor"
    assert out["extra_meters"] == 0
    assert out["order_meters"] == 14.25


def test_outdoor_uv_adds_fixed_extra():
    s = {"exposure_outdoor_uv_enabled": "1", "exposure_outdoor_uv_extra_m": "0.3"}
    out = rules.apply({"meters": 14.25}, types.ExposureType.OUTDOOR_UV, s)
    assert out["exposure_type"] == "outdoor_uv"
    assert out["extra_meters"] == 0.3
    assert out["order_meters"] == 14.55


def test_disabled_type_falls_back_to_base():
    s = {"exposure_outdoor_uv_enabled": "0", "exposure_outdoor_uv_extra_m": "0.3"}
    out = rules.apply({"meters": 14.25}, types.ExposureType.OUTDOOR_UV, s)
    assert out["exposure_type"] == "indoor"
    assert out["extra_meters"] == 0
    assert out["order_meters"] == 14.25


@pytest.mark.parametrize("bad", ["abc", "-0.5", "", "nan", "inf", "1,5"])
def test_invalid_extra_rejected(bad):
    s = {"exposure_outdoor_uv_enabled": "1", "exposure_outdoor_uv_extra_m": bad}
    with pytest.raises(types.ExposureError):
        rules.apply({"meters": 10}, types.ExposureType.OUTDOOR_UV, s)


def test_missing_keys_use_defaults():
    out = rules.apply({"meters": 10}, types.ExposureType.OUTDOOR_UV, {})
    assert out["extra_meters"] == rules.DEFAULT_EXTRA_M
    assert out["order_meters"] == 10 + rules.DEFAULT_EXTRA_M


def test_unknown_type_rejected():
    with pytest.raises(types.ExposureError):
        types.parse("balcony")


def test_display_legacy_run_without_exposure_fields():
    s = display.summarize_run({"meters": 5.0})
    assert s["type"] == "indoor"
    assert s["label"] == "普通室内"
    assert s["order_meters"] == 5.0


def test_display_pinned_run():
    s = display.summarize_run({"meters": 14.25, "exposure_type": "outdoor_uv",
                               "extra_meters": 0.3, "order_meters": 14.55})
    assert s["label"] == "户外抗紫外"
    assert s["order_meters"] == 14.55
