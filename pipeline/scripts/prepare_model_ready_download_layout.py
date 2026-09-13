#!/usr/bin/env python3
"""Prepare semantic file names and human-readable READMEs for model-ready data.

The immutable ``v0.1.0-model-ready-preview-1`` release keeps its original
``dataset.csv`` layout.  This script prepares the separately maintained
``main/datasets/model-ready`` download layout: the main table in each target
directory is named ``<target-slug>-dataset.csv`` and a concise, bilingual
README explains how to use and trace that target.

The CSV bytes themselves are not changed.  The script updates the target-local
checksum and metadata records whose paths refer to the renamed file.  The
generated README is explanatory documentation and is intentionally outside the
data checksum set.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any


CHECKSUM_NAMES = {
    "dataset",
    "schema",
    "yonod-config",
    "row-map",
    "audit",
    "exclusions",
    "source-links",
    "target-build-provenance",
}
SUPPORTING_FILES = (
    ("schema.json", "字段、字段角色、标签定义和提取规则。"),
    ("row-map.csv", "把主表中的行号连接回 ORD 反应记录。"),
    ("audit.jsonl", "逐条记录标签候选、最终选择和原因。"),
    ("exclusions.csv", "未纳入主表的记录及排除原因。"),
    ("source-links.json", "固定到 ORD 提交版本的原始文件链接和 SHA-256。"),
    ("metadata.json", "数据集名称、规模、标签单位、许可证和就绪状态。"),
    ("yonod-config.json", "建模字段角色和示例配置。"),
    ("target-build-provenance.json", "构建本数据集的输入和转换哈希。"),
    ("checksums.csv", "用于检查数据与溯源文件是否损坏或被修改。"),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, value: Any) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["role", "path", "sha256", "size_bytes"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def markdown_list(values: list[str]) -> str:
    return "、".join(f"`{value}`" for value in values) if values else "无"


def format_sources(links: list[dict[str, Any]]) -> str:
    lines = []
    for link in links:
        lines.append(
            f"- `{link['physical_dataset_id']}`："
            f"[{link['source_file']}]({link['source_file_url']})  "
            f"（ORD revision `{link['upstream_revision']}`；SHA-256 `{link['source_sha256']}`）"
        )
    return "\n".join(lines)


def format_exclusions(path: Path) -> str:
    counts = Counter(row["exclusion_reason"] for row in read_csv(path))
    if not counts:
        return "无额外排除。"
    return "；".join(f"`{reason}`：{count} 条" for reason, count in sorted(counts.items()))


def render_readme(directory: Path, metadata: dict[str, Any], schema: dict[str, Any], links: dict[str, Any]) -> str:
    slug = metadata["dataset_slug"]
    data_name = f"{slug}-dataset.csv"
    label = metadata["label"]
    roles = schema["column_roles"]
    target_metadata = schema.get("target_metadata", {})
    doi = target_metadata.get("doi")
    note = target_metadata.get("notes", "未提供额外的化学说明。")
    publication = f"[{doi}](https://doi.org/{doi})" if doi else "未提供 DOI"
    total = metadata["included_count"] + metadata["excluded_count"]

    files = "\n".join(
        [f"| [`{data_name}`]({data_name}) | 可直接用于分析或建模的主表；每行是一条纳入的反应。 |"]
        + [f"| [`{filename}`]({filename}) | {description} |" for filename, description in SUPPORTING_FILES]
    )
    source_section = format_sources(links["links"])
    exclusions = format_exclusions(directory / "exclusions.csv")

    return f"""# {metadata['display_name_en']} / {metadata['display_name_zh']}

这是一个可直接用于反应建模的 ORD 数据子集。主表为
[`{data_name}`]({data_name})；它的内容与不可变
[`v0.1.0-model-ready-preview-1`](https://github.com/thinktraveller/ord-datasets/releases/tag/v0.1.0-model-ready-preview-1)
发布版本中的 `dataset.csv` 相同，只是本目录使用了更容易识别的语义化文件名。

## 快速信息

| 项目 | 内容 |
|---|---|
| 主数据文件 | [`{data_name}`]({data_name}) |
| 纳入 / 排除 / 输入记录 | {metadata['included_count']:,} / {metadata['excluded_count']:,} / {total:,} |
| 标签列 | `{label['column']}` |
| 标签含义与单位 | {label['unit']} |
| 标签选择规则 | `{label['policy']}` |
| 模型/基准就绪状态 | `{metadata['readiness_status']}` |
| 数据许可证 | `{metadata['license_id']}` |
| 相关论文 | {publication} |

> “model-ready”表示文件可以直接读取和建模，并不表示它已被接受为通用基准。建模或比较前，请结合上表的就绪状态与标签含义判断是否适合您的问题。

## 化学范围与筛选

{note}

- 本目标只使用下方列出的 ORD 物理数据源。
- 只有满足 `{label['policy']}` 的标签记录被纳入主表；不会对多个候选标签做未声明的平均或聚合。
- 实际排除情况：{exclusions}
- `audit.jsonl` 保留每条反应的标签候选、最终决定和理由；`exclusions.csv` 保留未纳入记录，因此筛选过程可以复查。

## 字段一览

| 字段角色 | 列名 |
|---|---|
| 反应物 | {markdown_list(roles.get('reactants', []))} |
| 试剂、催化剂、溶剂等 | {markdown_list(roles.get('others', []))} |
| 产物 | {markdown_list(roles.get('products', []))} |
| 条件 | {markdown_list(roles.get('conditions', []))} |
| 标签 | `{roles['label']}` |

完整列顺序、单位及字段角色以 [`schema.json`](schema.json) 为准。通常，分子结构列使用 SMILES；单位已经写在条件列名称中，例如 `_c`、`_s`、`_kpa` 或 `_nm`。

## 文件说明

| 文件 | 用途 |
|---|---|
{files}

## 如何溯源一条反应

1. 在 [`{data_name}`]({data_name}) 中选定一行；其 CSV 行号（把表头算作第 1 行）就是 `row-map.csv` 的 `csv_row_number`。
2. 在 [`row-map.csv`](row-map.csv) 中按该行号找到 `physical_dataset_id`、`source_row_index` 和 `label_decision_id`。
3. 在 [`audit.jsonl`](audit.jsonl) 中搜索 `label_decision_id`，查看这个标签为何被选择或排除。
4. 在 [`source-links.json`](source-links.json) 中按 `physical_dataset_id` 找到固定的 ORD 原始 Parquet 链接、提交版本和 SHA-256。
5. 用 `physical_dataset_id` 加 `source_row_index` 在完整 ORD 语料中定位同一条反应；请勿仅靠行号或 SMILES 匹配。

## 固定数据来源

{source_section}

如需在论文、报告或可复现工作流中引用此数据，请同时保留本目录的 `metadata.json`、`source-links.json`、`row-map.csv` 和 `checksums.csv`，并引用上方不可变发布版本。数据及其派生元数据采用 CC BY-SA 4.0；请保留署名、来源和许可证信息。
"""


def expected_data_name(slug: str) -> str:
    return f"{slug}-dataset.csv"


def migrate(directory: Path) -> None:
    metadata_path = directory / "metadata.json"
    checksums_path = directory / "checksums.csv"
    schema_path = directory / "schema.json"
    links_path = directory / "source-links.json"
    if not all(path.is_file() for path in (metadata_path, checksums_path, schema_path, links_path)):
        raise FileNotFoundError(f"required metadata is missing from {directory}")

    metadata = read_json(metadata_path)
    slug = metadata.get("dataset_slug")
    if not isinstance(slug, str) or directory.name != slug:
        raise ValueError(f"directory and dataset slug disagree: {directory}")
    old_path = directory / "dataset.csv"
    data_path = directory / expected_data_name(slug)
    if old_path.is_file() and data_path.exists():
        raise FileExistsError(f"both legacy and semantic data names exist in {directory}")
    if old_path.is_file():
        os.replace(old_path, data_path)
    if not data_path.is_file():
        raise FileNotFoundError(f"model table is missing from {directory}")

    checksum_rows = read_csv(checksums_path)
    by_role = {row["role"]: row for row in checksum_rows}
    if set(by_role) != CHECKSUM_NAMES:
        raise ValueError(f"unexpected checksum roles in {directory}")
    dataset_row = by_role["dataset"]
    if dataset_row["sha256"] != sha256(data_path) or int(dataset_row["size_bytes"]) != data_path.stat().st_size:
        raise ValueError(f"data bytes do not match the published checksum in {directory}")
    dataset_row["path"] = data_path.name
    write_csv(checksums_path, checksum_rows)

    artifacts = {item["role"]: item for item in metadata["content_artifacts"]}
    if "dataset" not in artifacts or "checksums" not in artifacts:
        raise ValueError(f"metadata artifact records are incomplete in {directory}")
    artifacts["dataset"].update(
        {
            "path": f"datasets/model-ready/{slug}/{data_path.name}",
            "sha256": sha256(data_path),
            "size_bytes": data_path.stat().st_size,
        }
    )
    artifacts["checksums"].update(
        {
            "path": f"datasets/model-ready/{slug}/checksums.csv",
            "sha256": sha256(checksums_path),
            "size_bytes": checksums_path.stat().st_size,
        }
    )
    write_json(metadata_path, metadata)
    (directory / "README.md").write_text(
        render_readme(directory, metadata, read_json(schema_path), read_json(links_path)),
        encoding="utf-8",
    )


def check(directory: Path) -> None:
    metadata = read_json(directory / "metadata.json")
    slug = metadata["dataset_slug"]
    data_path = directory / expected_data_name(slug)
    if (directory / "dataset.csv").exists() or not data_path.is_file() or not (directory / "README.md").is_file():
        raise ValueError(f"semantic download layout is incomplete in {directory}")
    checksum_rows = {row["role"]: row for row in read_csv(directory / "checksums.csv")}
    if set(checksum_rows) != CHECKSUM_NAMES:
        raise ValueError(f"unexpected checksum roles in {directory}")
    for role, row in checksum_rows.items():
        filename = data_path.name if role == "dataset" else row["path"]
        path = directory / filename
        if row["path"] != filename or not path.is_file() or row["sha256"] != sha256(path) or int(row["size_bytes"]) != path.stat().st_size:
            raise ValueError(f"checksum mismatch for {directory.name}/{filename}")
    artifacts = {item["role"]: item for item in metadata["content_artifacts"]}
    if artifacts["dataset"]["path"] != f"datasets/model-ready/{slug}/{data_path.name}" or artifacts["dataset"]["sha256"] != sha256(data_path):
        raise ValueError(f"dataset metadata path or hash mismatch in {directory}")
    if artifacts["checksums"]["sha256"] != sha256(directory / "checksums.csv"):
        raise ValueError(f"checksums metadata hash mismatch in {directory}")
    if data_path.name not in (directory / "README.md").read_text(encoding="utf-8"):
        raise ValueError(f"README does not link the semantic data file in {directory}")


def directories(root: Path) -> list[Path]:
    result = sorted(path for path in root.iterdir() if path.is_dir() and not path.name.startswith("."))
    if len(result) != 19:
        raise ValueError(f"expected 19 target directories under {root}, found {len(result)}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path, help="the datasets/model-ready directory")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--apply", action="store_true", help="rename files and generate package READMEs")
    mode.add_argument("--check", action="store_true", help="verify the semantic download layout without writing")
    args = parser.parse_args()
    if not args.root.is_dir():
        raise NotADirectoryError(args.root)
    targets = directories(args.root)
    if args.apply:
        for directory in targets:
            migrate(directory)
    for directory in targets:
        check(directory)
    print(json.dumps({"target_count": len(targets), "status": "complete"}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
