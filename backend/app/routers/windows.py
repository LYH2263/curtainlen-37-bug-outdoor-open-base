from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.modules.exposure import types
from app.repositories import windows as repo

router = APIRouter()


class ExposureTypeBody(BaseModel):
    exposure_type: str


@router.get("/windows")
def list_windows(): return {"items": repo.list_windows()}
@router.get("/windows/{wid}")
def get_window(wid: int):
    r = repo.get_window(wid)
    if not r: raise HTTPException(404)
    return r
@router.put("/windows/{wid}/exposure")
def update_exposure(wid: int, body: ExposureTypeBody):
    try:
        parsed = types.parse(body.exposure_type)
    except types.ExposureError as e:
        raise HTTPException(422, str(e))
    if not repo.set_exposure_type(wid, parsed.value):
        raise HTTPException(404, "not found")
    return repo.get_window(wid)
