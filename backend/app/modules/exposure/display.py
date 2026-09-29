"""测算/历史的曝晒展示口径。所有视图（列表、详情、户外摘要）都从同一份落库
快照只读派生，绝不按现行设置或窗类型重算。旧记录没有曝晒字段时按普通室内、
订货米=基础米展示。"""
from app.modules.exposure.types import ExposureType, label_of


def summarize_run(result: dict) -> dict:
    base = result.get("meters")
    t = result.get("exposure_type") or ExposureType.INDOOR.value
    extra = result.get("extra_meters", 0)
    return {
        "type": t,
        "label": label_of(t),
        "base_meters": base,
        "extra_meters": extra,
        "order_meters": result.get("order_meters", base),
    }


# 户外摘要卡片：与 exposure 摘要同源，钉住写入快照的同一组字段。
outdoor_card = summarize_run
