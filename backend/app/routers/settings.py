from fastapi import APIRouter
from app.repositories import settings_repo

router = APIRouter()


@router.get("/settings")
def settings():
    return settings_repo.get_all()


@router.put("/settings")
def update_settings(body: dict[str, str]):
    # 设置只约束之后新开的户外单，绝不回刷已落库的历史编号。
    settings_repo.set_many(body)
    return settings_repo.get_all()
