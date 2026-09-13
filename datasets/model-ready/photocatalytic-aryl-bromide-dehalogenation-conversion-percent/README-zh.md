# 光催化芳基溴脱卤转化率（%）

[English](README.md)

这是一个可直接用于反应建模的 ORD 数据子集。主表为
[`photocatalytic-aryl-bromide-dehalogenation-conversion-percent-dataset.csv`](photocatalytic-aryl-bromide-dehalogenation-conversion-percent-dataset.csv)；它的内容与不可变
[`v0.1.0-model-ready-preview-1`](https://github.com/thinktraveller/ord-datasets/releases/tag/v0.1.0-model-ready-preview-1)
发布版本中的 `dataset.csv` 相同，只是本目录使用了更容易识别的语义化文件名。

## 快速信息

| 项目 | 内容 |
|---|---|
| 主数据文件 | [`photocatalytic-aryl-bromide-dehalogenation-conversion-percent-dataset.csv`](photocatalytic-aryl-bromide-dehalogenation-conversion-percent-dataset.csv) |
| 纳入 / 排除 / 输入记录 | 1,152 / 0 / 1,152 |
| 标签列 | `conversion_percent` |
| 标签含义与单位 | percent conversion |
| 标签选择规则 | `unique_structured_scalar_no_aggregation` |
| 模型/基准就绪状态 | `active_generated_pending_release_validation` |
| 数据许可证 | `CC-BY-SA-4.0` |
| 相关论文 | [10.1021/acscatal.0c02247](https://doi.org/10.1021/acscatal.0c02247) |

> “model-ready”表示文件可以直接读取和建模，并不表示它已被接受为通用基准。建模或比较前，请结合上表的就绪状态与标签含义判断是否适合您的问题。

## 化学范围与筛选

面向 Ir(III) 光催化芳基溴脱卤的 5 小时转化率建模。体系强调光催化剂、芳基底物和照射条件的匹配关系，标签为估计转化率而非分离产率，适合研究光催化剂筛选。

- 本目标只使用下方列出的 ORD 物理数据源。
- 只有满足 `unique_structured_scalar_no_aggregation` 的标签记录被纳入主表；不会对多个候选标签做未声明的平均或聚合。
- 实际排除情况：无额外排除。
- `audit.jsonl` 保留每条反应的标签候选、最终决定和理由；`exclusions.csv` 保留未纳入记录，因此筛选过程可以复查。

## 字段一览

| 字段角色 | 列名 |
|---|---|
| 反应物 | `reactant-1`、`reactant-2` |
| 试剂、催化剂、溶剂等 | `reagent-1`、`catalyst-1`、`catalyst-2`、`catalyst-3`、`solvent-1`、`solvent-2` |
| 产物 | 无 |
| 条件 | `reaction_time_s`、`illumination_wavelength_nm` |
| 标签 | `conversion_percent` |

完整列顺序、单位及字段角色以 [`schema.json`](schema.json) 为准。通常，分子结构列使用 SMILES；单位已经写在条件列名称中，例如 `_c`、`_s`、`_kpa` 或 `_nm`。

## 文件说明

| 文件 | 用途 |
|---|---|
| [`photocatalytic-aryl-bromide-dehalogenation-conversion-percent-dataset.csv`](photocatalytic-aryl-bromide-dehalogenation-conversion-percent-dataset.csv) | 可直接用于分析或建模的主表；每行是一条纳入的反应。 |
| [`schema.json`](schema.json) | 字段、字段角色、标签定义和提取规则。 |
| [`row-map.csv`](row-map.csv) | 把主表中的行号连接回 ORD 反应记录。 |
| [`audit.jsonl`](audit.jsonl) | 逐条记录标签候选、最终选择和原因。 |
| [`exclusions.csv`](exclusions.csv) | 未纳入主表的记录及排除原因。 |
| [`source-links.json`](source-links.json) | 固定到 ORD 提交版本的原始文件链接和 SHA-256。 |
| [`metadata.json`](metadata.json) | 数据集名称、规模、标签单位、许可证和就绪状态。 |
| [`yonod-config.json`](yonod-config.json) | 供 [YONOD](https://github.com/thinktraveller/YONOD) 使用的配置：将表格字段映射到建模角色，并提供示例设置；人工分析时可不使用。 |
| [`target-build-provenance.json`](target-build-provenance.json) | 构建本目标所用的输入文件、转换规则和哈希；用于复现或审计构建过程。 |
| [`checksums.csv`](checksums.csv) | 文件路径、SHA-256 指纹和大小；用于检查下载是否完整以及文件是否意外变动。 |

## 如何溯源一条反应

1. 在 [`photocatalytic-aryl-bromide-dehalogenation-conversion-percent-dataset.csv`](photocatalytic-aryl-bromide-dehalogenation-conversion-percent-dataset.csv) 中选定一行；其 CSV 行号（把表头算作第 1 行）就是 `row-map.csv` 的 `csv_row_number`。
2. 在 [`row-map.csv`](row-map.csv) 中按该行号找到 `physical_dataset_id`、`source_row_index` 和 `label_decision_id`。
3. 在 [`audit.jsonl`](audit.jsonl) 中搜索 `label_decision_id`，查看这个标签为何被选择或排除。
4. 在 [`source-links.json`](source-links.json) 中按 `physical_dataset_id` 找到固定的 ORD 原始 Parquet 链接、提交版本和 SHA-256。
5. 用 `physical_dataset_id` 加 `source_row_index` 在完整 ORD 语料中定位同一条反应；请勿仅靠行号或 SMILES 匹配。

## 固定数据来源

- `ord_dataset-b440f8c90b6343189093770060fc4098`：[data/b4/ord_dataset-b440f8c90b6343189093770060fc4098.parquet](https://github.com/open-reaction-database/ord-data/blob/83f971f586f6ad18f358ae4ae99d045e94ed2066/data/b4/ord_dataset-b440f8c90b6343189093770060fc4098.parquet)  (ORD revision `83f971f586f6ad18f358ae4ae99d045e94ed2066`；SHA-256 `d289e2e9fbb77df61faadeb65cfadfbee0216b05a7d209b3ae3b3aca04a9993a`)

如需在论文、报告或可复现工作流中引用此数据，请同时保留本目录的 `metadata.json`、`source-links.json`、`row-map.csv` 和 `checksums.csv`，并引用上方不可变发布版本。数据及其派生元数据采用 CC BY-SA 4.0；请保留署名、来源和许可证信息。
