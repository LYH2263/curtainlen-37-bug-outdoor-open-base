from fastapi import APIRouter, HTTPException
from app.modules.exposure import display
from app.repositories import history as repo

router = APIRouter()


def _pin_views(r: dict) -> dict:
    """列表/详情/户外摘要三路同源：全部钉住落库快照，绝不各算各的。"""
    result = r.get("result") or {}
    summary = display.summarize_run(result)
    r["exposure"] = summary
    r["outdoor_summary"] = summary
    return r


@router.get("/runs")
def runs(limit: int = 50):
    items = [_pin_views(r) for r in repo.list_runs(limit)]
    return {"items": items}


@router.get("/runs/{run_id}")
def run(run_id: int):
    r = repo.get_run(run_id)
    if not r:
        raise HTTPException(404, "not found")
    return _pin_views(r)
