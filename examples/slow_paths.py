import argparse
import math
from collections import Counter, defaultdict

from hwlog.log_cli import build_parser, parse_args, selected_rows
from hwlog.metrics import percentile_95


def nonnegative_ms(text):
    try:
        value = float(text)
    except ValueError as error:
        raise argparse.ArgumentTypeError("请传入有限且非负的毫秒数") from error
    if not math.isfinite(value) or value < 0:
        raise argparse.ArgumentTypeError("请传入有限且非负的毫秒数")
    return value


def summarize(lines, args):
    counts = Counter()
    durations = defaultdict(list)
    skipped = Counter()
    for request in selected_rows(lines, args, skipped):
        endpoint = (request.method, request.path)
        counts[endpoint] += 1
        if request.duration_ms is not None:
            durations[endpoint].append(request.duration_ms)

    groups = []
    for endpoint, total in counts.items():
        samples = durations[endpoint]
        slow = sum(duration > args.slow_ms for duration in samples)
        groups.append((endpoint, total, len(samples), percentile_95(samples), slow))
    groups.sort(key=lambda group: (-group[4], -group[2], group[0]))
    return groups, skipped


def main(argv=None):
    parser = build_parser("按请求分组统计 P95 和超阈值次数")
    parser.add_argument("--slow-ms", type=nonnegative_ms, default=500.0, help="慢请求的毫秒阈值")
    args = parse_args(parser, argv)
    try:
        with args.input.open(encoding="utf-8") as log:
            groups, skipped = summarize(log, args)
    except (OSError, UnicodeError) as error:
        parser.error(f"无法读取输入：{error}")

    print(f"慢请求阈值：>{args.slow_ms:g} ms；整份输入跳过：{sum(skipped.values())}")
    for (method, path), total, samples, p95, slow in groups:
        p95_text = f"{p95:g} ms" if p95 is not None else "无样本"
        slow_text = str(slow) if samples else "无样本"
        print(f"{method} {path}｜请求 {total}｜耗时样本 {samples}｜P95 {p95_text}｜慢请求 {slow_text}")


if __name__ == "__main__":
    main()
