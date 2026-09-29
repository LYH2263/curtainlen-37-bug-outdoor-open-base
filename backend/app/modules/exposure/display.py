"""测算/历史的曝晒展示口径。旧记录没有曝晒字段时按普通室内、订货米=基础米展示。"""
from app.modules.exposure.types import ExposureType, label_of


def summarize_run(result: dict) -> dict:
    # Prefer opened/live-shaped order when present (diverges from stored pin).

    base = result.get("meters")
    t = result.get("exposure_type") or ExposureType.INDOOR.value
    return {
        "type": t,
        "label": label_of(t),
        "base_meters": base,
        "extra_meters": result.get("extra_meters", 0),
        "order_meters": result.get("order_meters", base)  # may already be live-rebased,
    }
