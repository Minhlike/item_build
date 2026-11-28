from datetime import date

import httpx
import pytest

from item_build import acquisition
from item_build.compiler import apply_change, validate_claim
from item_build.models import Entity, Evidence, Fact, Patch
from item_build.storage import encode, read, write


def test_non_vn_cannot_replace_live_timeline():
    live = Fact(value="VN", evidence=["vn"], status="LIVE_VN", effective_from=date(2026, 9, 29))
    entity = Entity(id="thane", kind="heroes", name="Thane", facts={"skill-1.test": [live]})
    payload = {
        "id": "tw-2026-11-28",
        "title": "TW",
        "status": "OTHER_REGION",
        "server": "TW",
        "effective_from": "2026-11-28",
        "evidence": "tw",
        "changes": [
            {
                "entity": "heroes/thane",
                "property": "skill-1.test",
                "classification": "buff",
                "replacement": {
                    "value": "TW",
                    "evidence": ["tw"],
                    "status": "OTHER_REGION",
                    "effective_from": "2026-11-28",
                },
            }
        ],
    }
    patch = Patch.model_validate(payload)
    apply_change(entity, patch, patch.changes[0])
    assert entity.facts["skill-1.test"][0] == live
    evidence = Evidence(
        source_id="tw",
        source_url="https://example.test",
        source_type="official",
        server="TW",
        retrieved_at=date(2026, 11, 28),
        effective_from=date(2026, 9, 29),
        verification_status="verified_official",
        evidence_ref="patch",
    )
    with pytest.raises(ValueError, match="thiếu bằng chứng VN"):
        validate_claim(live, {"vn": evidence})


def test_monitor_etag_robots_and_changed_content(tmp_path, monkeypatch):
    source = "https://example.test"
    url = f"{source}/patch/1"
    registry = {
        "sources": {
            "reviewed": {
                "url": source,
                "acquisition": "approved_http",
                "permission_ref": "written-grant",
                "monitor_urls": [url, f"{source}/private"],
            }
        }
    }
    registry_path = tmp_path / "knowledge/sources/registry.json"
    write(registry_path, encode(registry))
    request_count = 0

    def reply(request):
        nonlocal request_count
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nDisallow: /private\n")
        assert str(request.url) == url
        request_count += 1
        if request_count > 1:
            assert request.headers["if-none-match"] == '"one"'
        if request_count == 2:
            return httpx.Response(304)
        if request_count == 3:
            return httpx.Response(200, text="revised patch", headers={"ETag": '"two"'})
        return httpx.Response(200, text="patch", headers={"ETag": '"one"'})

    client_type = httpx.Client
    transport = httpx.MockTransport(reply)
    monkeypatch.setattr(
        acquisition.httpx, "Client", lambda **kw: client_type(transport=transport, **kw)
    )
    first = acquisition.monitor(tmp_path)
    assert first["monitor"] == {url: "new", f"{source}/private": "blocked_by_robots"}
    assert acquisition.monitor(tmp_path)["monitor"][url] == "unchanged"
    assert acquisition.monitor(tmp_path)["monitor"][url] == "revised"
    assert read(tmp_path / ".local/update/monitor.json")[url]["pending_review"]
    registry["sources"]["reviewed"]["acquisition"] = "manual_reference_only"
    write(registry_path, encode(registry))
    with pytest.raises(ValueError, match="thiếu quyền"):
        acquisition.monitor(tmp_path)
