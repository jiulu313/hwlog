import json
from dataclasses import FrozenInstanceError
from datetime import timezone

import pytest

from hwlog.log_cli import parse_record
from hwlog.records import Request


@pytest.mark.parametrize(("raw", "expected"), [(None, None), (True, None), (0, 0.0)])
def test_record_normalizes_path_timezone_and_duration(raw, expected):
    line = json.dumps({
        "ts": "2026-11-20T00:00:00+08:00",
        "method": "GET",
        "path": "/search?q=python",
        "status": 200,
        "duration_ms": raw,
    })
    request, reason = parse_record(line)
    assert reason is None
    assert isinstance(request, Request)
    assert request.ts.tzinfo == timezone.utc
    assert request.ts.hour == 16
    assert request.path == "/search"
    assert request.duration_ms == expected

    with pytest.raises(FrozenInstanceError):
        setattr(request, "path", "/other")
