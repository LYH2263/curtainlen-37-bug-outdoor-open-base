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
    # apply() 先按现行设置算出类型/加米/订货并校验配置；非法加米在此抛出，
    # insert_run 尚未执行，整单失败且不增行。
    try:
        expo = rules.apply(calc, requested, settings)
    except types.ExposureError as e:
        raise HTTPException(422, str(e))
    result = {**calc, **expo}
    run_id = None
    if save:
        run_id = history.insert_run(window_id, fabric_id, result, note)
        # 保存成功后把窗上现行类型同步为本次生效类型（只影响之后新开的单，
        # 不回刷任何旧编号）。
        windows.set_exposure_type(window_id, expo["exposure_type"])
    return {"window": w, "fabric": f, "run_id": run_id,
            "exposure_label": display.label_of(expo["exposure_type"]), **result}
