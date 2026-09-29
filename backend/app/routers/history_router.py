from fastapi import APIRouter, HTTPException
from app.modules.exposure import display
from app.repositories import history as repo

router = APIRouter()


def _attach_views(item: dict):
    """列表、详情主字段、户外摘要三路均从同一份落库快照只读派生。"""
    snapshot = item.get("result") or {}
    item["exposure"] = display.summarize_run(snapshot)
    item["outdoor_summary"] = display.outdoor_card(snapshot)
    return item


@router.get("/runs")
def runs(limit: int = 50):
    items = repo.list_runs(limit)
    for it in items:
        _attach_views(it)
    return {"items": items}


@router.get("/runs/{run_id}")
def run(run_id: int):
    r = repo.get_run(run_id)
    if not r:
        raise HTTPException(404, "not found")
    return _attach_views(r)
