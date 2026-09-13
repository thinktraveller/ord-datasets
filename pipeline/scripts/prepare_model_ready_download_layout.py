#!/usr/bin/env python3
"""Prepare semantic file names and human-readable READMEs for model-ready data.

The immutable ``v0.1.0-model-ready-preview-1`` release keeps its original
``dataset.csv`` layout.  This script prepares the separately maintained
``main/datasets/model-ready`` download layout: the main table in each target
directory is named ``<target-slug>-dataset.csv``.  Separate English
``README.md`` and Chinese ``README-zh.md`` files explain how to use and trace
that target.

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
    ("schema.json", "Exact columns, field roles, label definition, and extraction rule.", "字段、字段角色、标签定义和提取规则。"),
    ("row-map.csv", "Maps a main-table row to its ORD reaction record.", "把主表中的行号连接回 ORD 反应记录。"),
    ("audit.jsonl", "Records the label candidates, selected value, and reason for every decision.", "逐条记录标签候选、最终选择和原因。"),
    ("exclusions.csv", "Lists records excluded from the main table and the reason for each decision.", "未纳入主表的记录及排除原因。"),
    ("source-links.json", "Commit-pinned ORD source links and SHA-256 values.", "固定到 ORD 提交版本的原始文件链接和 SHA-256。"),
    ("metadata.json", "Dataset identity, size, label unit, licence, and readiness state.", "数据集名称、规模、标签单位、许可证和就绪状态。"),
    (
        "yonod-config.json",
        "Configuration for [YONOD](https://github.com/thinktraveller/YONOD): maps table columns to model roles and includes an example setup; optional for manual analysis.",
        "供 [YONOD](https://github.com/thinktraveller/YONOD) 使用的配置：将表格字段映射到建模角色，并提供示例设置；人工分析时可不使用。",
    ),
    (
        "target-build-provenance.json",
        "Input files, transformation rules, and hashes used to build this target; use it to reproduce or audit the build.",
        "构建本目标所用的输入文件、转换规则和哈希；用于复现或审计构建过程。",
    ),
    (
        "checksums.csv",
        "File paths, SHA-256 fingerprints, and sizes for checking download integrity or unexpected changes.",
        "文件路径、SHA-256 指纹和大小；用于检查下载是否完整以及文件是否意外变动。",
    ),
)

ENGLISH_SCOPE_NOTES = {
    "ahneman-c-n-cross-coupling-yield-percent": "Percent-yield modelling for Buchwald-Hartwig-type C-N cross-coupling. Aryl substrates, amine substrates, ligands, bases, palladium catalysts, and solvents vary together, making the target useful for studying substrate generalisation and catalytic-system selection.",
    "asymmetric-alkylation-ee-s-minus-r-percent": "Enantioselectivity modelling for photoredox/organocatalytic aldehyde alpha-asymmetric alkylation. The label is signed ee (S minus R, percentage points), not yield; product stereochemistry is used only to determine the label, not as a model feature.",
    "cernak-reductive-amination-conversion-percent": "Conversion modelling for miniaturised reductive amination of staurosporine with aldehyde or ketone substrates. It combines condition optimisation with library synthesis and can be used to assess group generalisation from seen substrates to new aldehydes or ketones.",
    "cernak-suzuki-coupling-conversion-percent": "Conversion modelling for miniaturised Suzuki coupling of aryl halides with boronic acids or boronate esters. The combinations span aryl-halide cores, boron partners, palladium precatalysts, bases, and solvents, enabling study of catalyst-substrate matching.",
    "cernak-ultra-hte-c-n-yield-percent": "Assay-yield modelling for Pd-, Ni-, and Cu-catalysed C-N coupling. This high-throughput system varies aryl halides, amines, metal/ligand combinations, bases, temperatures, and solvents across a broad chemical space.",
    "chan-lam-sulfonamide-coupling-yield-percent": "Yield modelling for Chan-Lam coupling of primary sulfonamides and boronic acids. The target covers diverse sulfonamides, boronic acids, copper catalysts, bases, and solvents, including replicate experiments for examining compatibility and robustness.",
    "chemrxiv-aniline-amidation-yield-percent": "Yield modelling for amidation of a fixed carboxylic-acid core with varied anilines. It chiefly compares amine substrates, activating agents, bases, and solvent combinations to identify conditions that transfer across aniline substrates.",
    "chemrxiv-imidazole-c-h-arylation-yield-percent": "Yield modelling for Pd-catalysed C5-H arylation of imidazoles with aryl bromides. Substrate pairs, monophosphine ligands, and reaction conditions are key variables for evaluating condition transferability.",
    "flow-catechol-product-2-response-percent": "Research-only modelling target for the HPLC percentage response of Product 2 in a transient flow reaction. Features include substrate, binary-solvent composition, temperature, and residence time; reliable run grouping is not yet available, so it is not a batch-model benchmark.",
    "flow-catechol-product-3-response-percent": "Research-only modelling target for the HPLC percentage response of Product 3 in a transient flow reaction. Features include substrate, binary-solvent composition, temperature, and residence time; reliable run grouping is not yet available, so it is not a batch-model benchmark.",
    "flow-catechol-total-product-response-percent": "Research-only flow solvent-selection target for the sum of Product 2 and Product 3 percentage responses. The label is their deterministic sum; reliable run grouping is not yet available.",
    "nano-c-n-photochemistry-yield-percent": "Product-yield modelling for photochemical C-N reactions with diverse substrates and photocatalytic conditions. Labels come from UPLC-MS quantification, supporting study of substrate electronics/sterics, photocatalyst systems, and solvents together.",
    "nicolit-nickel-coupling-yield-percent": "Percent-yield modelling for nickel-catalysed organolithium cross-coupling involving C-O/C-N bond activation of ethers or aryl ammonium salts. Zero values are retained; GC and isolated yields are not distinguished and should be treated as an interpretation limitation.",
    "pfizer-hte-lc-area-percent": "LC/UV area-percent modelling for a large high-throughput reaction collection. The target contains about 39,000 reactions and diverse reactant, reagent, and catalyst combinations; its label is an analytical signal, not isolated yield or conversion.",
    "photocatalytic-aryl-bromide-dehalogenation-conversion-percent": "Five-hour conversion modelling for Ir(III)-photocatalysed aryl-bromide dehalogenation. The target emphasises matching among photocatalyst, aryl substrate, and irradiation conditions; the label is estimated conversion rather than isolated yield.",
    "roche-borylation-yield-percent": "Percent-yield modelling for organoborylation reactions. Structured records contain reactants, reagents, catalysts, and solvents, supporting analysis of how functional groups and condition combinations affect borylation outcomes.",
    "science-hte-relative-lc-area-ratio": "Relative LC-MS response modelling for palladium-catalysed cross-coupling with multiple nucleophiles. The label is target-product AREA divided by biphenyl internal-standard AREA, not yield or conversion.",
    "shields-arylation-yield-percent": "Percent-yield modelling for arylation reactions. The data combine substrates, catalysts, bases, solvents, and continuous condition variables in an optimisation-trajectory-like design that can support Bayesian optimisation or condition recommendation studies.",
    "suzuki-miyaura-nanoscale-yield-percent": "Percent-yield modelling for Suzuki-Miyaura C-C coupling. Aryl electrophiles and organoboron nucleophiles are combined systematically with ligands, bases, solvents, and catalytic conditions at small scale, supporting study of structure-condition interactions.",
}


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


def write_text(path: Path, value: str) -> None:
    """Atomically write generated explanatory documentation."""
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(value, encoding="utf-8")
    os.replace(temporary, path)


def markdown_list_zh(values: list[str]) -> str:
    return "、".join(f"`{value}`" for value in values) if values else "无"


def markdown_list_en(values: list[str]) -> str:
    return ", ".join(f"`{value}`" for value in values) if values else "None"


def format_sources(links: list[dict[str, Any]], language: str) -> str:
    lines = []
    for link in links:
        if language == "en":
            qualifier = f"ORD revision `{link['upstream_revision']}`; SHA-256 `{link['source_sha256']}`"
            separator = ": "
        else:
            qualifier = f"ORD revision `{link['upstream_revision']}`；SHA-256 `{link['source_sha256']}`"
            separator = "："
        lines.append(
            f"- `{link['physical_dataset_id']}`{separator}"
            f"[{link['source_file']}]({link['source_file_url']})  "
            f"({qualifier})"
        )
    return "\n".join(lines)


def format_exclusions(path: Path, language: str) -> str:
    counts = Counter(row["exclusion_reason"] for row in read_csv(path))
    if not counts:
        return "No additional exclusions." if language == "en" else "无额外排除。"
    if language == "en":
        return "; ".join(f"`{reason}`: {count} record(s)" for reason, count in sorted(counts.items()))
    return "；".join(f"`{reason}`：{count} 条" for reason, count in sorted(counts.items()))


def render_readme_en(directory: Path, metadata: dict[str, Any], schema: dict[str, Any], links: dict[str, Any]) -> str:
    slug = metadata["dataset_slug"]
    data_name = f"{slug}-dataset.csv"
    label = metadata["label"]
    roles = schema["column_roles"]
    target_metadata = schema.get("target_metadata", {})
    doi = target_metadata.get("doi")
    publication_en = f"[{doi}](https://doi.org/{doi})" if doi else "No DOI supplied"
    total = metadata["included_count"] + metadata["excluded_count"]
    english_note = ENGLISH_SCOPE_NOTES[slug]
    files_en = "\n".join(
        [f"| [`{data_name}`]({data_name}) | Analysis-ready main table; each row is an included reaction. |"]
        + [f"| [`{filename}`]({filename}) | {description_en} |" for filename, description_en, _ in SUPPORTING_FILES]
    )
    source_section_en = format_sources(links["links"], "en")
    exclusions_en = format_exclusions(directory / "exclusions.csv", "en")

    return f"""# {metadata['display_name_en']}

[中文](README-zh.md)

This is an ORD subset prepared for direct reaction modelling. Its main table is
[`{data_name}`]({data_name}). The CSV bytes are identical to `dataset.csv` in the immutable
[`v0.1.0-model-ready-preview-1`](https://github.com/thinktraveller/ord-datasets/releases/tag/v0.1.0-model-ready-preview-1)
release; this directory uses a semantic filename to make individual downloads easier to identify.

## At a glance

| Item | Details |
|---|---|
| Main data file | [`{data_name}`]({data_name}) |
| Included / excluded / input records | {metadata['included_count']:,} / {metadata['excluded_count']:,} / {total:,} |
| Label column | `{label['column']}` |
| Label meaning and unit | {label['unit']} |
| Label-selection policy | `{label['policy']}` |
| Modelling/benchmark readiness | `{metadata['readiness_status']}` |
| Data licence | `{metadata['license_id']}` |
| Associated publication | {publication_en} |

> “Model-ready” means that the file can be read and modelled directly. It does not mean that the target is an accepted general-purpose benchmark. Consider the readiness state and label meaning before modelling or comparing results.

## Chemical scope and filtering

{english_note}

- This target uses only the ORD physical sources listed below.
- Only records satisfying `{label['policy']}` are included; multiple candidate labels are never averaged or aggregated without an explicit rule.
- Observed exclusions: {exclusions_en}
- `audit.jsonl` preserves the label candidates, final decision, and rationale for every reaction. `exclusions.csv` preserves the records that did not enter the main table.

## Columns

| Field role | Columns |
|---|---|
| Reactants | {markdown_list_en(roles.get('reactants', []))} |
| Reagents, catalysts, solvents, and other components | {markdown_list_en(roles.get('others', []))} |
| Products | {markdown_list_en(roles.get('products', []))} |
| Conditions | {markdown_list_en(roles.get('conditions', []))} |
| Label | `{roles['label']}` |

[`schema.json`](schema.json) is authoritative for the complete column order, units, and roles. Molecular-structure columns normally use SMILES; condition-column names carry their units, such as `_c`, `_s`, `_kpa`, or `_nm`.

## Files

| File | Purpose |
|---|---|
{files_en}

## Trace one reaction

1. Select a row in [`{data_name}`]({data_name}). Its CSV row number, counting the header as row 1, is the `csv_row_number` in `row-map.csv`.
2. Find that number in [`row-map.csv`](row-map.csv) to obtain `physical_dataset_id`, `source_row_index`, and `label_decision_id`.
3. Search [`audit.jsonl`](audit.jsonl) for `label_decision_id` to see why the label was included or excluded.
4. Use `physical_dataset_id` in [`source-links.json`](source-links.json) to find the pinned ORD Parquet URL, revision, and SHA-256.
5. Use `physical_dataset_id` plus `source_row_index` to locate the same reaction in the complete ORD corpus. Do not rely on row order or SMILES alone.

## Pinned data sources

{source_section_en}

For a paper, report, or reproducible workflow, keep `metadata.json`, `source-links.json`, `row-map.csv`, and `checksums.csv` with the main table and cite the immutable release above. The data and derived metadata are CC BY-SA 4.0; retain attribution, source, and licence information.
"""


def render_readme_zh(directory: Path, metadata: dict[str, Any], schema: dict[str, Any], links: dict[str, Any]) -> str:
    slug = metadata["dataset_slug"]
    data_name = f"{slug}-dataset.csv"
    label = metadata["label"]
    roles = schema["column_roles"]
    target_metadata = schema.get("target_metadata", {})
    doi = target_metadata.get("doi")
    publication_zh = f"[{doi}](https://doi.org/{doi})" if doi else "未提供 DOI"
    total = metadata["included_count"] + metadata["excluded_count"]
    chinese_note = target_metadata.get("notes", "未提供额外的化学说明。")
    files_zh = "\n".join(
        [f"| [`{data_name}`]({data_name}) | 可直接用于分析或建模的主表；每行是一条纳入的反应。 |"]
        + [f"| [`{filename}`]({filename}) | {description_zh} |" for filename, _, description_zh in SUPPORTING_FILES]
    )
    source_section_zh = format_sources(links["links"], "zh")
    exclusions_zh = format_exclusions(directory / "exclusions.csv", "zh")

    return f"""# {metadata['display_name_zh']}

[English](README.md)

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
| 相关论文 | {publication_zh} |

> “model-ready”表示文件可以直接读取和建模，并不表示它已被接受为通用基准。建模或比较前，请结合上表的就绪状态与标签含义判断是否适合您的问题。

## 化学范围与筛选

{chinese_note}

- 本目标只使用下方列出的 ORD 物理数据源。
- 只有满足 `{label['policy']}` 的标签记录被纳入主表；不会对多个候选标签做未声明的平均或聚合。
- 实际排除情况：{exclusions_zh}
- `audit.jsonl` 保留每条反应的标签候选、最终决定和理由；`exclusions.csv` 保留未纳入记录，因此筛选过程可以复查。

## 字段一览

| 字段角色 | 列名 |
|---|---|
| 反应物 | {markdown_list_zh(roles.get('reactants', []))} |
| 试剂、催化剂、溶剂等 | {markdown_list_zh(roles.get('others', []))} |
| 产物 | {markdown_list_zh(roles.get('products', []))} |
| 条件 | {markdown_list_zh(roles.get('conditions', []))} |
| 标签 | `{roles['label']}` |

完整列顺序、单位及字段角色以 [`schema.json`](schema.json) 为准。通常，分子结构列使用 SMILES；单位已经写在条件列名称中，例如 `_c`、`_s`、`_kpa` 或 `_nm`。

## 文件说明

| 文件 | 用途 |
|---|---|
{files_zh}

## 如何溯源一条反应

1. 在 [`{data_name}`]({data_name}) 中选定一行；其 CSV 行号（把表头算作第 1 行）就是 `row-map.csv` 的 `csv_row_number`。
2. 在 [`row-map.csv`](row-map.csv) 中按该行号找到 `physical_dataset_id`、`source_row_index` 和 `label_decision_id`。
3. 在 [`audit.jsonl`](audit.jsonl) 中搜索 `label_decision_id`，查看这个标签为何被选择或排除。
4. 在 [`source-links.json`](source-links.json) 中按 `physical_dataset_id` 找到固定的 ORD 原始 Parquet 链接、提交版本和 SHA-256。
5. 用 `physical_dataset_id` 加 `source_row_index` 在完整 ORD 语料中定位同一条反应；请勿仅靠行号或 SMILES 匹配。

## 固定数据来源

{source_section_zh}

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
    schema = read_json(schema_path)
    links = read_json(links_path)
    write_text(directory / "README.md", render_readme_en(directory, metadata, schema, links))
    write_text(directory / "README-zh.md", render_readme_zh(directory, metadata, schema, links))


def check(directory: Path) -> None:
    metadata = read_json(directory / "metadata.json")
    slug = metadata["dataset_slug"]
    data_path = directory / expected_data_name(slug)
    english_readme = directory / "README.md"
    chinese_readme = directory / "README-zh.md"
    if (directory / "dataset.csv").exists() or not data_path.is_file() or not english_readme.is_file() or not chinese_readme.is_file():
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
    english_text = english_readme.read_text(encoding="utf-8")
    chinese_text = chinese_readme.read_text(encoding="utf-8")
    if data_path.name not in english_text or data_path.name not in chinese_text:
        raise ValueError(f"README does not link the semantic data file in {directory}")
    if "README-zh.md" not in english_text or "README.md" not in chinese_text:
        raise ValueError(f"language README links are incomplete in {directory}")


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
