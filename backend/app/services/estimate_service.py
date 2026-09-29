from fastapi import HTTPException
from app.engines.curtain_math import fabric_meters
from app.modules.exposure import display, rules, types
from app.repositories import fabrics, history, settings_repo, windows

def run_estimate(window_id: int, fabric_id: int, save: bool, note: str, exposure_type: str = "indoor"):
    w = windows.get_window(window_id)
    f = fabrics.get_fabric(fabric_id)
    if not w or not f:
        raise HTTPException(404, "not found")
    if w.get("data_quality") == "dirty":
        raise HTTPException(422, "dirty window")
    try:
        requested = types.parse(exposure_type)
    except types.ExposureError as e:
        raise HTTPException(422, str(e))
    settings = settings_repo.get_all()
    fullness = float(w.get("fullness") or settings.get("default_fullness", 2.0))
    calc = fabric_meters(w["width"], w["height"], fullness, f["hem_top"], f["hem_bottom"], f["fabric_width"])
    try:
        expo = rules.apply(calc, requested, settings)
    except types.ExposureError as e:
        raise HTTPException(422, str(e))
    result = {**calc, **expo}
    run_id = history.insert_run(window_id, fabric_id, result, note) if save else None
    return {"window": w, "fabric": f, "run_id": run_id,
            "exposure_label": display.label_of(expo["exposure_type"]), **result}
