from dataclasses import dataclass
from typing import Optional
import time
import requests

LIST_URL = "https://www.mindmeister.com/services/rest/oauth2"
API_V2 = "https://www.mindmeister.com/api/v2"


@dataclass
class MapInfo:
    id: str
    title: str
    modified: str
    owner: str


class MindMeisterClient:
    def __init__(self, token: str, rate_limit_delay: float = 0.5):
        if not token:
            raise ValueError("API token is required")
        self._token = token
        self._delay = rate_limit_delay
        self._session = requests.Session()
        self._session.headers["Authorization"] = f"Bearer {token}"

    def list_maps(self) -> list:
        resp = self._session.get(LIST_URL, params={
            "method": "mm.maps.getList",
            "output": "json",
        })
        resp.raise_for_status()
        data = resp.json()
        if data["rsp"]["stat"] != "ok":
            raise RuntimeError(f"API error: {data['rsp']}")
        maps_data = data["rsp"]["maps"]["map"]
        if isinstance(maps_data, dict):  # single map edge case
            maps_data = [maps_data]
        return [
            MapInfo(
                id=m["id"],
                title=m["title"],
                modified=m.get("modified", ""),
                owner=m.get("owner", ""),
            )
            for m in maps_data
        ]

    def export_map(self, map_id: str, fmt: str) -> bytes:
        if fmt == "png":
            url = f"{API_V2}/map_images/{map_id}.png"
        elif fmt == "jpeg":
            url = f"{API_V2}/map_images/{map_id}.jpeg"
        else:
            url = f"{API_V2}/maps/{map_id}.{fmt}"
        resp = self._session.get(url)
        resp.raise_for_status()
        time.sleep(self._delay)
        return resp.content
