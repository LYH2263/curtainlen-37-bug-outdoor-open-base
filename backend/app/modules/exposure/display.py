"""测算/历史的曝晒展示口径。

只读落库快照：类型、加米、订货米三列均取自写入时钉住的字段，展示层绝不按
现行设置重算。旧记录缺曝晒字段时按普通室内、订货米=基础米展示。
"""
from app.modules.exposure.types import ExposureType, label_of


def summarize_run(result: dict) -> dict:
    base = result.get("meters")
    t = result.get("exposure_type") or ExposureType.INDOOR.value
    return {
        "type": t,
        "label": label_of(t),
        "base_meters": base,
        "extra_meters": result.get("extra_meters", 0.0),
        "order_meters": result.get("order_meters", base),
    }
