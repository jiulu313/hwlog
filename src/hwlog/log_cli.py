import argparse
import json
from collections import Counter
from collections.abc import Iterable, Iterator
from datetime import datetime, timezone
from pathlib import Path

from .records import Request, normalize_duration


REQUIRED = {"ts", "method", "path", "status"}


def as_utc(text):
    moment = datetime.fromisoformat(text)
    if moment.utcoffset() is None:
        raise ValueError("时间必须带 UTC 偏移")
    return moment.astimezone(timezone.utc)


def timestamp_arg(text):
    try:
        return as_utc(text)
    except (ValueError, OverflowError) as error:
        raise argparse.ArgumentTypeError("请传入带时区的 ISO 8601 时间") from error


def build_parser(description):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("input", type=Path, help="UTF-8 JSON Lines 文件")
    parser.add_argument("--since", type=timestamp_arg, help="开始时间，包含此刻")
    parser.add_argument("--until", type=timestamp_arg, help="结束时间，不包含此刻")
    parser.add_argument("--method", help="仅统计指定方法，如 GET")
    return parser


def parse_args(parser, argv=None):
    args = parser.parse_args(argv)
    if args.since is not None and args.until is not None and args.since >= args.until:
        parser.error("--since 必须早于 --until")
    return args


def parse_record(line: str) -> tuple[Request, None] | tuple[None, str]:
    if not line.strip():
        return None, "空行"
    try:
        row = json.loads(line)
    except json.JSONDecodeError:
        return None, "JSON 格式错误"
    if not isinstance(row, dict):
        return None, "JSON 不是对象"
    if REQUIRED.difference(row):
        return None, "缺少必填字段"

    method, path, status = row["method"], row["path"], row["status"]
    if not isinstance(method, str) or not method or not method.isascii() or not method.isalpha():
        return None, "请求方法无效"
    if not isinstance(path, str) or not path.startswith("/") or "\r" in path or "\n" in path:
        return None, "路径无效"
    if type(status) is not int or not 100 <= status <= 599:
        return None, "状态码无效"

    timestamp = row["ts"]
    if not isinstance(timestamp, str):
        return None, "时间戳无效"
    try:
        moment = as_utc(timestamp)
    except (ValueError, OverflowError):
        return None, "时间戳无效"

    return Request(moment, method, path.split("?", 1)[0], status, normalize_duration(row.get("duration_ms"))), None


def selected_rows(
    lines: Iterable[str],
    args: argparse.Namespace,
    skipped: Counter[str],
) -> Iterator[Request]:
    for line in lines:
        request, reason = parse_record(line)
        if reason is not None:
            skipped[reason] += 1
            continue
        assert request is not None
        if args.since is not None and request.ts < args.since:
            continue
        if args.until is not None and request.ts >= args.until:
            continue
        if args.method is not None and request.method != args.method:
            continue
        yield request


def main(argv=None):
    parser = build_parser("按时间和 HTTP 方法统计日志")
    args = parse_args(parser, argv)
    skipped = Counter()
    try:
        with args.input.open(encoding="utf-8") as log:
            total = sum(1 for _ in selected_rows(log, args, skipped))
    except (OSError, UnicodeError) as error:
        parser.error(f"无法读取输入：{error}")
    print(f"符合筛选的请求：{total}")
    print(f"整份输入跳过的记录：{sum(skipped.values())}")


if __name__ == "__main__":
    main()
