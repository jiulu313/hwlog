import argparse
from collections import Counter

from .log_cli import build_parser, parse_args, selected_rows


def positive_int(text):
    try:
        value = int(text)
    except ValueError as error:
        raise argparse.ArgumentTypeError("请传入正整数") from error
    if value < 1:
        raise argparse.ArgumentTypeError("请传入正整数")
    return value


def metrics_parser(description):
    parser = build_parser(description)
    parser.add_argument("--top", type=positive_int, default=5, help="列出前 N 个请求分组")
    return parser


def percentile_95(samples):
    if not samples:
        return None
    ordered = sorted(samples)
    rank = (95 * len(ordered) + 99) // 100
    return ordered[rank - 1]


def build_report(lines, args):
    skipped = Counter()
    endpoints = Counter()
    latencies = []
    client_errors = server_errors = 0
    for request in selected_rows(lines, args, skipped):
        endpoints[request.method, request.path] += 1
        client_errors += 400 <= request.status < 500
        server_errors += 500 <= request.status < 600
        if request.duration_ms is not None:
            latencies.append(request.duration_ms)

    total = sum(endpoints.values())
    return {
        "requests": total,
        "client_errors": client_errors,
        "server_errors": server_errors,
        "error_rate": (client_errors + server_errors) / total if total else None,
        "server_error_rate": server_errors / total if total else None,
        "latency_samples": len(latencies),
        "p95_ms": percentile_95(latencies),
        "skipped": dict(skipped),
        "top": [
            {"method": method, "path": path, "requests": count}
            for (method, path), count in endpoints.most_common(args.top)
        ],
    }


def percent(rate):
    return f"{rate:.2%}" if rate is not None else "无数据"


def format_report(report):
    p95 = report["p95_ms"]
    latency_text = f"{p95:g} ms" if p95 is not None else "无有效样本"
    lines = [
        f"有效请求：{report['requests']}",
        f"整份输入跳过：{sum(report['skipped'].values())}",
        f"错误率（4xx + 5xx）：{percent(report['error_rate'])}",
        f"5xx 比例：{percent(report['server_error_rate'])}",
        f"P95：{latency_text}（{report['latency_samples']} 条耗时样本）",
        "访问量排行（方法 + 路径）：",
    ]
    for item in report["top"]:
        lines.append(f"  {item['method']} {item['path']}  {item['requests']}")
    return "\n".join(lines)


def main(argv=None):
    parser = metrics_parser("统计错误率、P95 和热门请求分组")
    args = parse_args(parser, argv)
    try:
        with args.input.open(encoding="utf-8") as log:
            report = build_report(log, args)
    except (OSError, UnicodeError) as error:
        parser.error(f"无法读取输入：{error}")
    print(format_report(report))


if __name__ == "__main__":
    main()
