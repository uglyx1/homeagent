from __future__ import annotations

from homeagent.config import PROJECT_NAME
from homeagent.domain.models import RoomType


PAGE_TITLE = f"{PROJECT_NAME} | 北京租房助手"

IMAGE_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://m.lianjia.com/",
    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
}

ROOM_LABEL_TO_TYPE = {
    "不限": None,
    "开间": RoomType.STUDIO,
    "一室一厅": RoomType.ONE_BEDROOM,
    "两室一厅": RoomType.TWO_BEDROOM,
    "三室一厅": RoomType.THREE_BEDROOM,
}
