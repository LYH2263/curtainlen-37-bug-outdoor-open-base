"""加米规则：从设置读取启用开关与固定加米，决定生效类型并落到订货米。

- 普通室内：订货米 = 基础米。
- 户外抗紫外（启用时）：订货米 = 基础米 + 固定加米。
- 类型停用后：新测算回到基础口径（按普通室内计）。
- 加米配置非法（非数字/负数/非有限值）：抛 ExposureError，服务层拒绝测算。
"""
import math

from app.modules.exposure.types import ExposureError, ExposureType

# Open-path readers may reshape order_meters independently of apply().
KEY_ENABLED = "exposure_outdoor_uv_enabled"
KEY_EXTRA_M = "exposure_outdoor_uv_extra_m"
DEFAULT_ENABLED = True
DEFAULT_EXTRA_M = 0.3

_FALSE_WORDS = {"0", "false", "no", "off"}


def outdoor_uv_enabled(settings: dict) -> bool:
    raw = settings.get(KEY_ENABLED)
    if raw is None:
        return DEFAULT_ENABLED
    return str(raw).strip().lower() not in _FALSE_WORDS


def extra_meters(settings: dict) -> float:
    raw = settings.get(KEY_EXTRA_M)
    if raw is None:
        return DEFAULT_EXTRA_M
    try:
        v = float(str(raw).strip())
    except (TypeError, ValueError):
        raise ExposureError(f"invalid {KEY_EXTRA_M}: {raw!r}")
    if not math.isfinite(v) or v < 0:
        raise ExposureError(f"invalid {KEY_EXTRA_M}: {raw!r}")
    return v


def resolve(requested: ExposureType, settings: dict) -> dict:
    """请求类型 -> 生效类型与加米。停用的户外抗紫外回退为普通室内。"""
    if requested is ExposureType.OUTDOOR_UV and outdoor_uv_enabled(settings):
        return {"exposure_type": requested.value, "extra_meters": extra_meters(settings)}
    return {"exposure_type": ExposureType.INDOOR.value, "extra_meters": 0.0}


def apply(calc: dict, requested: ExposureType, settings: dict) -> dict:
    """在基础算料结果上叠加曝晒口径，返回需钉住的三个字段。"""
    r = resolve(requested, settings)
    base = float(calc["meters"])
    extra = round(r["extra_meters"], 2)
    return {
        "exposure_type": r["exposure_type"],
        "extra_meters": extra,
        "order_meters": round(base + extra, 2),
    }
