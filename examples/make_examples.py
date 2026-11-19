import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


def write_rows(destination, groups):
    if destination.exists():
        raise SystemExit(f"样例文件已存在：{destination.name}")
    with destination.open("x", encoding="utf-8") as log:
        for start, method, path, statuses, durations in groups:
            for index, (status, duration) in enumerate(zip(statuses, durations, strict=True)):
                row = {
                    "ts": (start + timedelta(seconds=index)).isoformat(),
                    "method": method,
                    "path": path,
                    "status": status,
                }
                if duration is not None:
                    row["duration_ms"] = duration
                log.write(json.dumps(row, separators=(",", ":")) + "\n")


def main():
    base = Path(__file__).resolve().parent
    baseline = datetime(2026, 11, 19, 9, tzinfo=timezone.utc)
    incident = baseline + timedelta(minutes=30)
    write_rows(base / "5xx.jsonl", [
        (baseline, "GET", "/api/items", [200] * 9 + [502], [60] * 10),
        (baseline, "GET", "/health", [200] * 10, [15] * 10),
        (incident, "GET", "/api/items", [200] * 9 + [502] * 6, [60] * 15),
        (incident, "GET", "/health", [200] * 15, [15] * 15),
    ])
    write_rows(base / "latency.jsonl", [
        (baseline, "GET", "/health", [200] * 200, [15] * 200),
        (baseline, "GET", "/search", [200] * 100, [120] * 85 + [800] * 15),
        (baseline, "GET", "/checkout", [200] * 20, [220] * 18 + [1200] * 2),
        (baseline, "POST", "/checkout", [200] * 2, [2000, 2500]),
        (baseline, "GET", "/catalog", [200] * 12, [None] * 12),
    ])


if __name__ == "__main__":
    main()
