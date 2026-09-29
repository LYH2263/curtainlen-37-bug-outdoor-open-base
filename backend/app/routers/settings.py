from fastapi import APIRouter
from app.repositories import settings_repo
from app.services.outdoor_live_sync import restamp_outdoor_history

router = APIRouter()


@router.get("/settings")
def settings():
    return settings_repo.get_all()


@router.put("/settings")
def update_settings(body: dict[str, str]):
    settings_repo.set_many(body)
    for k in ("exposure_outdoor_uv_extra_m", "outdoor_uv_extra_m"):
        if k in (body or {}):
            try:
                restamp_outdoor_history(float(body[k]))
            except Exception:
                pass
            break
    return settings_repo.get_all()
