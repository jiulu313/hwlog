import json
from collections import Counter

import pytest

from hwlog.log_cli import build_parser, main, parse_args, parse_record, selected_rows
from hwlog.metrics import build_report, metrics_parser


def record(ts="2026-11-19T16:00:00Z", status=200, **fields):
    return json.dumps({
        "ts": ts,
        "method": "GET",
        "path": "/search?q=python",
        "status": status,
        **fields,
    })


@pytest.mark.parametrize(
    ("line", "expected_reason"),
    [
        ("\n", "空行"),
        ('{"ts":', "JSON 格式错误"),
        ("[]", "JSON 不是对象"),
        (record(status=True), "状态码无效"),
        (record(ts="2026-11-19T16:00:00"), "时间戳无效"),
    ],
)
def test_bad_records(line, expected_reason):
    assert parse_record(line) == (None, expected_reason)


def test_time_window_includes_only_start_boundary():
    parser = build_parser("日志测试")
    args = parse_args(parser, [
        "unused.jsonl",
        "--since", "2026-11-19T16:00:00Z",
        "--until", "2026-11-19T17:00:00Z",
        "--method", "GET",
    ])
    rows = [
        record(ts="2026-11-19T15:59:59Z"),
        record(ts="2026-11-20T00:00:00+08:00"),
        record(ts="2026-11-19T17:00:00Z"),
        record(method="POST"),
        "残缺记录",
    ]
    skipped = Counter()

    assert len(list(selected_rows(rows, args, skipped))) == 1
    assert skipped == {"JSON 格式错误": 1}


def test_error_rate_and_p95_use_different_samples():
    args = parse_args(metrics_parser("日志测试"), ["unused.jsonl"])
    rows = [
        record(status=200, duration_ms=40),
        record(status=404, duration_ms=80),
        record(status=502, duration_ms=300),
        record(status=200),
    ]
    report = build_report(rows, args)

    assert report["requests"] == 4
    assert report["error_rate"] == pytest.approx(0.5)
    assert report["latency_samples"] == 3
    assert report["p95_ms"] == 300
    assert report["top"] == [{"method": "GET", "path": "/search", "requests": 4}]


def test_empty_input_has_no_rate_or_latency():
    args = parse_args(metrics_parser("日志测试"), ["unused.jsonl"])
    report = build_report([], args)

    assert report["requests"] == 0
    assert report["error_rate"] is None
    assert report["p95_ms"] is None


def test_cli_reads_a_real_file(tmp_path, capsys):
    source = tmp_path / "access.jsonl"
    source.write_text(record() + "\n残缺记录\n", encoding="utf-8")

    main([str(source), "--method", "GET"])

    assert capsys.readouterr().out.splitlines() == [
        "符合筛选的请求：1",
        "整份输入跳过的记录：1",
    ]
