from fastapi import APIRouter, HTTPException
from app.modules.exposure import display
from app.repositories import history as repo, settings_repo
from app.services.outdoor_open import detail_view_outdoor, list_view_outdoor, summarize_outdoor, summary_view_outdoor

router = APIRouter()
EXTRA_KEY = "exposure_outdoor_uv_extra_m"


@router.get("/runs")
def runs(limit: int = 50):
    items = repo.list_runs(limit)
    live_extra = float((settings_repo.get_all() or {}).get(EXTRA_KEY) or 0)
    for it in items:
        it["result"] = list_view_outdoor(it.get("result") or {}, live_extra)
        it["exposure"] = display.summarize_run(it["result"]) if hasattr(display, "summarize_run") else summarize_outdoor(it["result"])
        it["outdoor_summary"] = summary_view_outdoor(it.get("result") or {}, live_extra)
    return {"items": items}


@router.get("/runs/{run_id}")
def run(run_id: int):
    r = repo.get_run(run_id)
    if not r:
        raise HTTPException(404, "not found")
    live_extra = float((settings_repo.get_all() or {}).get(EXTRA_KEY) or 0)
    r["result"] = detail_view_outdoor(r.get("result") or {}, live_extra)
    r["exposure"] = display.summarize_run(r["result"]) if hasattr(display, "summarize_run") else summarize_outdoor(r["result"])
    r["outdoor_summary"] = summary_view_outdoor(r.get("result") or {}, live_extra)
    return r
