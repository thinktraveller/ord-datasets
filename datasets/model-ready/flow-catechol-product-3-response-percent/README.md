# Flow Catechol Product 3 HPLC Response (%) / 连续流儿茶酚产物 3 HPLC 响应（%）

这是一个可直接用于反应建模的 ORD 数据子集。主表为
[`flow-catechol-product-3-response-percent-dataset.csv`](flow-catechol-product-3-response-percent-dataset.csv)；它的内容与不可变
[`v0.1.0-model-ready-preview-1`](https://github.com/thinktraveller/ord-datasets/releases/tag/v0.1.0-model-ready-preview-1)
发布版本中的 `dataset.csv` 相同，只是本目录使用了更容易识别的语义化文件名。

## 快速信息

| 项目 | 内容 |
|---|---|
| 主数据文件 | [`flow-catechol-product-3-response-percent-dataset.csv`](flow-catechol-product-3-response-percent-dataset.csv) |
| 纳入 / 排除 / 输入记录 | 1,227 / 0 / 1,227 |
| 标签列 | `product_3_yield_percent` |
| 标签含义与单位 | HPLC percentage response; not isolated yield |
| 标签选择规则 | `catechol_multitarget_v1:smiles_custom_name_hplc_yield` |
| 模型/基准就绪状态 | `research_only_benchmark_blocked` |
| 数据许可证 | `CC-BY-SA-4.0` |
| 相关论文 | [10.48550/arXiv.2506.07619](https://doi.org/10.48550/arXiv.2506.07619) |

> “model-ready”表示文件可以直接读取和建模，并不表示它已被接受为通用基准。建模或比较前，请结合上表的就绪状态与标签含义判断是否适合您的问题。

## 化学范围与筛选

研究型 target：面向瞬态流动反应中 Product 3 的 HPLC 百分比响应建模。特征包括底物、二元溶剂配比、温度和停留时间；当前缺少可靠的运行分组界定，因此不纳入批量建模。

- 本目标只使用下方列出的 ORD 物理数据源。
- 只有满足 `catechol_multitarget_v1:smiles_custom_name_hplc_yield` 的标签记录被纳入主表；不会对多个候选标签做未声明的平均或聚合。
- 实际排除情况：无额外排除。
- `audit.jsonl` 保留每条反应的标签候选、最终决定和理由；`exclusions.csv` 保留未纳入记录，因此筛选过程可以复查。

## 字段一览

| 字段角色 | 列名 |
|---|---|
| 反应物 | `reactant_smiles` |
| 试剂、催化剂、溶剂等 | `solvent_a_smiles`、`solvent_b_smiles` |
| 产物 | 无 |
| 条件 | `solvent_b_fraction`、`temperature_c`、`residence_time_s`、`residence_time_min` |
| 标签 | `product_3_yield_percent` |

完整列顺序、单位及字段角色以 [`schema.json`](schema.json) 为准。通常，分子结构列使用 SMILES；单位已经写在条件列名称中，例如 `_c`、`_s`、`_kpa` 或 `_nm`。

## 文件说明

| 文件 | 用途 |
|---|---|
| [`flow-catechol-product-3-response-percent-dataset.csv`](flow-catechol-product-3-response-percent-dataset.csv) | 可直接用于分析或建模的主表；每行是一条纳入的反应。 |
| [`schema.json`](schema.json) | 字段、字段角色、标签定义和提取规则。 |
| [`row-map.csv`](row-map.csv) | 把主表中的行号连接回 ORD 反应记录。 |
| [`audit.jsonl`](audit.jsonl) | 逐条记录标签候选、最终选择和原因。 |
| [`exclusions.csv`](exclusions.csv) | 未纳入主表的记录及排除原因。 |
| [`source-links.json`](source-links.json) | 固定到 ORD 提交版本的原始文件链接和 SHA-256。 |
| [`metadata.json`](metadata.json) | 数据集名称、规模、标签单位、许可证和就绪状态。 |
| [`yonod-config.json`](yonod-config.json) | 建模字段角色和示例配置。 |
| [`target-build-provenance.json`](target-build-provenance.json) | 构建本数据集的输入和转换哈希。 |
| [`checksums.csv`](checksums.csv) | 用于检查数据与溯源文件是否损坏或被修改。 |

## 如何溯源一条反应

1. 在 [`flow-catechol-product-3-response-percent-dataset.csv`](flow-catechol-product-3-response-percent-dataset.csv) 中选定一行；其 CSV 行号（把表头算作第 1 行）就是 `row-map.csv` 的 `csv_row_number`。
2. 在 [`row-map.csv`](row-map.csv) 中按该行号找到 `physical_dataset_id`、`source_row_index` 和 `label_decision_id`。
3. 在 [`audit.jsonl`](audit.jsonl) 中搜索 `label_decision_id`，查看这个标签为何被选择或排除。
4. 在 [`source-links.json`](source-links.json) 中按 `physical_dataset_id` 找到固定的 ORD 原始 Parquet 链接、提交版本和 SHA-256。
5. 用 `physical_dataset_id` 加 `source_row_index` 在完整 ORD 语料中定位同一条反应；请勿仅靠行号或 SMILES 匹配。

## 固定数据来源

- `ord_dataset-1ec2807f02fa4beda27d2a81b86eb843`：[data/1e/ord_dataset-1ec2807f02fa4beda27d2a81b86eb843.parquet](https://github.com/open-reaction-database/ord-data/blob/83f971f586f6ad18f358ae4ae99d045e94ed2066/data/1e/ord_dataset-1ec2807f02fa4beda27d2a81b86eb843.parquet)  （ORD revision `83f971f586f6ad18f358ae4ae99d045e94ed2066`；SHA-256 `b1fd81bb3034644117b7d07e0471ede7370597bb4bd2433dd4b5c20bf02fad99`）

如需在论文、报告或可复现工作流中引用此数据，请同时保留本目录的 `metadata.json`、`source-links.json`、`row-map.csv` 和 `checksums.csv`，并引用上方不可变发布版本。数据及其派生元数据采用 CC BY-SA 4.0；请保留署名、来源和许可证信息。
