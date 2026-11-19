# hwlog 0.1.0

[HelloWorld Python 专栏](https://www.helloworld.net/special/85645260264) · [v0.1.0 Release](https://github.com/jiulu313/hwlog/releases/tag/v0.1.0) · [下载完整发布包](https://github.com/jiulu313/hwlog/releases/download/v0.1.0/hwlog-0.1.0.zip)

用 Python 分析 UTF-8 JSON Lines 访问日志。按文件、时间和 HTTP 方法筛选，查看错误率、P95 与热门请求，并导出终端摘要、CSV 或 JSON。

## 安装

需要 Python 3.11 或更高版本。解压发布包，在已激活的虚拟环境中进入解压后的 `hwlog-0.1.0` 目录：

```text
python -m pip install --no-deps dist/helloworld_log_cli-0.1.0-py3-none-any.whl
hwlog --help
```

## 快速验证

```text
hwlog examples/access.jsonl --since 2026-11-19T16:00:00Z --until 2026-11-19T17:00:00Z --top 1 --format csv
```

```csv
method,path,requests
GET,/search,3
```

## 两个排查案例

```text
python examples/compare_5xx.py examples/5xx.jsonl --since 2026-11-19T09:00:00Z --split 2026-11-19T09:30:00Z --until 2026-11-19T10:00:00Z
python examples/slow_paths.py examples/latency.jsonl --slow-ms 500
```

示例输出位于 `examples/expected/`。要重新生成两份案例日志，请把 `examples/make_examples.py` 复制到空目录并运行。示例使用合成数据。

## 指标口径

- 每行一个 JSON 对象，必须有 `ts`、`method`、`path`、`status`。时间戳带 UTC 偏移或以 `Z` 结尾；`duration_ms` 可选。
- 时间窗口包含起点，排除终点。可识别的查询参数会从路径中去除。坏记录按整份文件计数。
- 错误率以窗口内的有效请求为分母，4xx 与 5xx 计入错误。报表也单列 5xx 比例。
- P95 使用最邻近秩法，仅统计有效耗时。精确 P95 会保留耗时列表；没有有效样本时，JSON 写入 `null`。
- `--format csv` 输出请求排行，`--format json` 输出完整指标。`--output` 只创建新文件。

## 从源码验证或重建

```text
python -m pip install -e ".[test]"
python -m pytest -q
python -m pip wheel --no-deps --wheel-dir dist .
```

源码位于 `src/hwlog/`，测试位于 `tests/`，命令入口和测试依赖声明在 `pyproject.toml` 中。
