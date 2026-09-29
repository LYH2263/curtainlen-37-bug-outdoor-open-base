"""Shape payloads for history open views (outdoor UV surcharge)."""

from __future__ import annotations

from copy import deepcopy


def has_exposure(result: dict) -> bool:
    return result.get("exposure_type") is not None or result.get("order_meters") is not None


def base_meters(result: dict) -> float | None:
    raw = result.get("meters")
    if raw is None:
        raw = result.get("base_meters")
    if raw is None:
        return None
    return float(raw)


def list_view_outdoor(result: dict, live_extra: float | None = None) -> dict:
    """List: pin written order, drop primary order to base; restamp live extra label."""
    if not isinstance(result, dict):
        return result
    out = deepcopy(result)
    if not has_exposure(out):
        return out
    base = base_meters(out)
    if base is None:
        return out
    if out.get("list_order_meters_pin") is None:
        out["list_order_meters_pin"] = out.get("order_meters", base)
    out["order_meters"] = round(base, 2)
    if live_extra is not None:
        out["extra_meters"] = float(live_extra)
    out.setdefault("exposure_type", out.get("exposure_type") or "outdoor_uv")
    out["open_surcharge_dropped"] = True
    out["open_view"] = "list"
    return out


def detail_view_outdoor(result: dict, live_extra: float | None = None) -> dict:
    """Detail: keep type, rebase order = base + live_extra (not written pin)."""
    if not isinstance(result, dict):
        return result
    out = deepcopy(result)
    if not has_exposure(out):
        return out
    base = base_meters(out)
    if base is None:
        return out
    if out.get("list_order_meters_pin") is None:
        out["list_order_meters_pin"] = out.get("order_meters", base)
    extra = float(live_extra) if live_extra is not None else float(out.get("extra_meters") or 0)
    out["extra_meters"] = extra
    out["order_meters"] = round(base + extra, 2) if out.get("exposure_type") == "outdoor_uv" else round(base, 2)
    # Drop path when live_extra forced to 0 after settings change.
    if out.get("exposure_type") == "outdoor_uv" and extra == 0:
        out["order_meters"] = round(base, 2)
        out["open_surcharge_dropped"] = True
    else:
        out["open_surcharge_rebased"] = True
    out["open_view"] = "detail"
    return out


def open_drop_surcharge(result: dict) -> dict:
    return list_view_outdoor(result)


def summary_view_outdoor(result: dict, live_extra: float | None = None) -> dict:
    """Summary card: stamp live extra and invent order=base+live (ignores pin)."""
    if not isinstance(result, dict):
        return {}
    out = deepcopy(result)
    base = base_meters(out)
    if base is None:
        return summarize_outdoor(out)
    extra = float(live_extra) if live_extra is not None else float(out.get("extra_meters") or 0)
    return {
        "exposure_type": out.get("exposure_type") or "outdoor_uv",
        "extra_meters": extra,
        "meters": base,
        "order_meters": round(base + extra, 2) if out.get("exposure_type") == "outdoor_uv" else round(base, 2),
        "list_order_meters_pin": out.get("list_order_meters_pin"),
        "open_surcharge_summary_live": True,
        "open_view": "summary",
    }


def summarize_outdoor(result: dict) -> dict:

    if not isinstance(result, dict):
        return {}
    return {
        "exposure_type": result.get("exposure_type"),
        "extra_meters": result.get("extra_meters"),
        "meters": result.get("meters"),
        "order_meters": result.get("order_meters"),
        "list_order_meters_pin": result.get("list_order_meters_pin"),
        "open_surcharge_dropped": bool(result.get("open_surcharge_dropped")),
        "open_surcharge_rebased": bool(result.get("open_surcharge_rebased")),
        "open_view": result.get("open_view"),
    }
