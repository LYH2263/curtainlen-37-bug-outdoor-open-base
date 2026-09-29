from fastapi import APIRouter
from app.modules.exposure import rules, types
from app.repositories import settings_repo

router = APIRouter()

@router.get("/exposure/types")
def exposure_types():
    """曝晒类型清单（含启用状态与当前加米），前端算料台据此渲染，不写死。"""
    settings = settings_repo.get_all()
    items = []
    for t in types.ExposureType:
        item = {"value": t.value, "label": types.LABELS[t], "enabled": True,
                "extra_meters": 0.0, "config_valid": True}
        if t is types.ExposureType.OUTDOOR_UV:
            item["enabled"] = rules.outdoor_uv_enabled(settings)
            try:
                item["extra_meters"] = rules.extra_meters(settings)
            except types.ExposureError:
                item["extra_meters"] = None
                item["config_valid"] = False
        items.append(item)
    return {"items": items}
