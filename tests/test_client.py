import responses
import pytest
from meister_export.client import MindMeisterClient, MapInfo

LIST_MAPS_URL = "https://www.mindmeister.com/services/rest/oauth2"
EXPORT_BASE = "https://www.mindmeister.com/api/v2/maps"

SAMPLE_LIST_RESPONSE = {
    "rsp": {
        "stat": "ok",
        "maps": {
            "page": "1", "pages": "1", "perpage": "100", "total": "2",
            "map": [
                {"id": "111", "title": "My Map", "modified": "2026-01-01 10:00:00", "owner": "42"},
                {"id": "222", "title": "Another Map", "modified": "2026-01-02 10:00:00", "owner": "42"},
            ]
        }
    }
}


@responses.activate
def test_list_maps_returns_all_maps():
    responses.add(responses.GET, LIST_MAPS_URL, json=SAMPLE_LIST_RESPONSE)
    client = MindMeisterClient("test_token")
    maps = client.list_maps()
    assert len(maps) == 2
    assert maps[0].id == "111"
    assert maps[0].title == "My Map"


@responses.activate
def test_list_maps_sends_bearer_auth():
    responses.add(responses.GET, LIST_MAPS_URL, json=SAMPLE_LIST_RESPONSE)
    client = MindMeisterClient("my_token")
    client.list_maps()
    assert responses.calls[0].request.headers["Authorization"] == "Bearer my_token"


@responses.activate
def test_export_map_returns_bytes():
    responses.add(responses.GET, f"{EXPORT_BASE}/111.pdf", body=b"%PDF-1.4 test")
    client = MindMeisterClient("test_token")
    data = client.export_map("111", "pdf")
    assert data == b"%PDF-1.4 test"


@responses.activate
def test_export_map_uses_map_images_for_png():
    responses.add(
        responses.GET,
        "https://www.mindmeister.com/api/v2/map_images/111.png",
        body=b"\x89PNG"
    )
    client = MindMeisterClient("test_token")
    data = client.export_map("111", "png")
    assert data == b"\x89PNG"


def test_client_requires_token():
    with pytest.raises(ValueError, match="API token"):
        MindMeisterClient("")


@responses.activate
def test_list_maps_handles_single_map():
    """Edge case: API returns a dict instead of list when there's only one map."""
    single_map_response = {
        "rsp": {
            "stat": "ok",
            "maps": {
                "page": "1", "pages": "1", "perpage": "100", "total": "1",
                "map": {"id": "111", "title": "Only Map", "modified": "2026-01-01", "owner": "42"}
            }
        }
    }
    responses.add(responses.GET, LIST_MAPS_URL, json=single_map_response)
    client = MindMeisterClient("test_token")
    maps = client.list_maps()
    assert len(maps) == 1
    assert maps[0].title == "Only Map"
