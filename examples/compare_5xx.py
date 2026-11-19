import argparse
from collections import Counter

from hwlog.log_cli import build_parser, parse_args, selected_rows, timestamp_arg
from hwlog.metrics import percent


def summarize(lines, args):
    counts = [Counter(), Counter()]
    failures = [Counter(), Counter()]
    skipped = Counter()
    for request in selected_rows(lines, args, skipped):
        window = 0 if request.ts < args.split else 1
        key = (request.method, request.path)
        counts[window][key] += 1
        if 500 <= request.status < 600:
            failures[window][key] += 1
    return counts, failures, skipped


def main(argv=None):
    parser = build_parser("比较分界点前后两个窗口的 5xx")
    parser.add_argument("--split", type=timestamp_arg, required=True, help="两个窗口的分界时刻")
    args = parse_args(parser, argv)
    if args.since is None or args.until is None or not args.since < args.split < args.until:
        parser.error("请指定 --since 和 --until，并使 --since < --split < --until")
    try:
        with args.input.open(encoding="utf-8") as log:
            counts, failures, skipped = summarize(log, args)
    except (OSError, UnicodeError) as error:
        parser.error(f"无法读取输入：{error}")

    for label, requests, failed in zip(("基线窗口", "异常窗口"), counts, failures, strict=True):
        total = sum(requests.values())
        errors = sum(failed.values())
        print(f"{label}：{total} 条请求，{errors} 条 5xx，5xx 比例 {percent(errors / total if total else None)}")

    delta = failures[1] - failures[0]
    print(f"整份输入跳过：{sum(skipped.values())}")
    print("5xx 增量排行：")
    for (method, path), increase in delta.most_common(5):
        key = (method, path)
        print(f"  {method} {path}  {failures[0][key]} → {failures[1][key]}（+{increase}）")


if __name__ == "__main__":
    main()
