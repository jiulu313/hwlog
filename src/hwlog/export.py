import csv
import json
import sys
from pathlib import Path

from .log_cli import parse_args
from .metrics import build_report, format_report, metrics_parser


def write_report(report, style, output):
    if style == "csv":
        writer = csv.DictWriter(output, fieldnames=["method", "path", "requests"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(report["top"])
    elif style == "json":
        json.dump(report, output, ensure_ascii=False, indent=2, allow_nan=False)
        output.write("\n")
    else:
        output.write(format_report(report) + "\n")


def main(argv=None):
    parser = metrics_parser("导出日志报表")
    parser.add_argument("--format", choices=["text", "csv", "json"], default="text", help="输出格式")
    parser.add_argument("--output", type=Path, help="保存到新文件，省略时写到标准输出")
    args = parse_args(parser, argv)

    try:
        with args.input.open(encoding="utf-8") as log:
            report = build_report(log, args)
    except (OSError, UnicodeError) as error:
        parser.error(f"无法读取输入：{error}")

    try:
        if args.output is None:
            write_report(report, args.format, sys.stdout)
        else:
            with args.output.open("x", encoding="utf-8", newline="") as output:
                write_report(report, args.format, output)
    except (OSError, UnicodeError) as error:
        parser.error(f"无法写入报表：{error}")


if __name__ == "__main__":
    main()
