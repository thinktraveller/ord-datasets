# ORD 反应规范化数据集：可溯源完整与可直接建模的化学反应数据集

[English Version](README.md)

这个项目把 Open Reaction Database（ORD）中的反应数据整理成两类可下载的数据集：一类尽可能保留每条反应的原始实验信息，适合查找和溯源完整记录；另一类把特定反应类型整理成可直接分析或建模的普通表格。两类数据分开发布，避免把一个用于建模的小数据集误认为 ORD 的完整反应集合。

| 发布 | 适合做什么 | 规模 | 下载 |
|---|---|---|---|
| **完整语料** `v0.2.0-corpus-preview-1` | 查阅完整 ORD 反应 JSON、重新提取字段、逐条溯源 | 41 个语料包；53 个固定 ORD 源；2,428,291 条反应；12.23 GiB | [Hugging Face 固定标签](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1)，commit `260cde0feb414c75b2bf971d6f3a4dbbee7b2e95` |
| **模型就绪** `v0.1.0-model-ready-preview-1` | 直接分析产率、转化率、LC 响应或 ee | 15 个来源包中的 19 个目标；纳入 128,712 条、排除 499 条；所有 `*-dataset.csv` 共 26.6 MiB，整包 201.2 MiB | [在 `main` 中逐个浏览](https://github.com/thinktraveller/ord-datasets/tree/main/datasets/model-ready)；[不可变发布版本](https://github.com/thinktraveller/ord-datasets/releases/tag/v0.1.0-model-ready-preview-1)，commit `7d52dd27071c5625008a14737a1a8e1252ae6217` |

> **两种入口，主表内容相同：** `main` 分支的 `datasets/model-ready/` 保留了与发布版本逐字节相同的主数据表，但改用语义化的 `*-dataset.csv` 文件名，并为每个目标加入分开的英文和中文说明，方便逐个浏览和下载；若需要旧式目录布局的固定版本，请引用不可变发布版本。体积大得多的完整语料仍放在 Hugging Face，不复制到 `main`。

## 仓库目录结构

```text
ord-datasets/
├── README.md                     # 英文总说明
├── README-zh.md                  # 中文总说明
├── datasets/
│   ├── README.md                 # 数据区域总说明
│   ├── corpus/                   # 完整语料目录；实际载荷位于 Hugging Face
│   └── model-ready/              # 19 个可单独下载的建模目标
│       └── <target-slug>/
│           ├── README.md         # 该目标的英文说明
│           ├── README-zh.md      # 该目标的中文说明
│           ├── <target-slug>-dataset.csv
│           ├── schema.json       # 字段与标签定义
│           ├── row-map.csv       # 行级 ORD 溯源映射
│           ├── audit.jsonl       # 标签选择决策
│           ├── exclusions.csv    # 排除记录及原因
│           ├── source-links.json # 固定的 ORD 源文件
│           ├── metadata.json     # 范围、许可证和就绪状态
│           ├── yonod-config.json # 供 YONOD 使用的字段角色配置
│           ├── target-build-provenance.json # 可复现构建记录
│           └── checksums.csv     # 下载完整性指纹
├── pipeline/                     # 构建、验证、schema 和测试
├── provenance/                   # 来源、产物与行级溯源记录
├── reports/                      # 数据质量、许可证与发布证据
└── project-docs/                 # 项目计划和构建记录
```

## 使用指南

### 我应该下载哪一个？

- 如果您只想用 Excel、Origin、R 或 Python 分析“反应条件 → 产率/转化率”，先下载较小的**模型就绪版**。每个目标的 `<target-slug>-dataset.csv` 都是一张普通表格。
- 如果您需要实验步骤、加料、装置、后处理、分析方法或 ORD 的完整嵌套记录，下载**完整语料版**中对应的一个包即可；不必一开始下载 12.23 GiB 全集。
- 模型就绪版中同一条反应可以服务于多个目标，因此 19 个目标的行数不能相加后当成“独立反应总数”。完整语料的 2,428,291 才是本版本的全局反应数。

如果只想下载一个模型就绪数据表，不需要安装任何软件：

1. 在下方 [19 个模型就绪目标表](#19-个模型就绪目标)中点击所需的数据集名称。
2. 在打开的目录中点击以 `<target-slug>-dataset.csv` 结尾的主数据文件。
3. 点击文件页面右上角的 **Download raw file**（向下箭头）按钮，将文件保存到电脑。
4. 建议同时下载 `schema.json` 和 `metadata.json`，它们分别说明字段、标签、单位和就绪状态；如果研究需要完整溯源和审计，请保留全部 10 个数据/溯源文件及该目标的 `README.md`（英文）或 `README-zh.md`（中文）。

如果会使用命令行，可以只检出一个完整的数据集目录，不把另外 18 个数据集写入工作目录。复制下面三行，并把最后一个目录名替换成所需目标：

```bash
git clone --depth 1 --filter=blob:none --sparse https://github.com/thinktraveller/ord-datasets.git
cd ord-datasets
git sparse-checkout set datasets/model-ready/ahneman-c-n-cross-coupling-yield-percent
```

需要一次下载全部 19 个模型就绪目标或完整语料时，可使用：

```bash
# 19 个模型就绪目标
git clone --depth 1 https://github.com/thinktraveller/ord-datasets.git

# 完整语料（体积较大；需支持 Hugging Face/Xet 的 Git 环境）
git clone --depth 1 --branch v0.2.0-corpus-preview-1 https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus
```

### 文件怎么读？

每个完整语料包有 5 个文件：

| 文件 | 化学用户通常用它做什么 |
|---|---|
| `reactions.csv` | 主表。每行是一条反应；`reaction_json` 保存 ORD 完整反应记录。 |
| `schema.json` | 说明主表的 5 个固定字段。 |
| `source-links.json` | 给出固定到 ORD 某次提交的原始 Parquet 链接、源文件大小和 SHA-256。 |
| `metadata.json` | 数据集名称、行数、成员和许可证。 |
| `checksums.csv` | 检查下载文件有没有损坏或被改动。 |

完整语料 `reactions.csv` 的字段对所有 41 个包都相同：

| 字段 | 含义 |
|---|---|
| `physical_dataset_id` | ORD 原始物理数据集编号。 |
| `source_file` | ORD 仓库中的原始 Parquet 路径。 |
| `reaction_id` | ORD 为这条反应分配的唯一编号。 |
| `row_index` | 反应在原始物理数据集中的位置；**从 0 开始计数**。 |
| `reaction_json` | 完整反应内容，包括反应物、试剂、催化剂、溶剂、条件、产物、测量和来源等嵌套字段。 |

每个模型就绪目标有 10 个数据/溯源文件，另有分开的英文和中文说明：

| 文件 | 化学用户通常用它做什么 |
|---|---|
| `<target-slug>-dataset.csv` | 可以直接分析/建模的表；每行是一条纳入的反应。 |
| `schema.json` | **先看这里**：列出该目标的完整字段、字段角色、标签定义和提取规则。 |
| `row-map.csv` | 把主数据表的每一行连回 ORD 反应。 |
| `audit.jsonl` | 逐条记录标签候选、最终选择、数值和选择理由；一行一个 JSON 对象。 |
| `exclusions.csv` | 没有进入主数据表的记录及排除原因。即使为空也保留表头。 |
| `source-links.json` | 固定 ORD 原始文件链接、版本和哈希。 |
| `metadata.json` | 标签单位、纳入/排除数、就绪状态等。 |
| `yonod-config.json` | [YONOD](https://github.com/thinktraveller/YONOD) 使用的配置：将表格字段映射到建模角色，并提供示例设置；人工分析时可不使用。 |
| `target-build-provenance.json` | 构建本目标所用的输入文件、转换规则和哈希；用于复现或审计构建过程。 |
| `checksums.csv` | 文件路径、SHA-256 指纹和大小，用于检查下载是否完整以及文件是否意外变动；说明性 README 不在此校验集合中。 |
| `README.md` | 用英文通俗说明该目标的范围、标签、字段、筛选、来源、状态和溯源方法。 |
| `README-zh.md` | 上述目标说明的中文版本。 |

### 数据经过了哪些筛选？

完整语料层不按产率或标签筛行：53 个冻结物理源被无损组合为 41 个语义包，行数保持不变。发布时会从 `reaction_json` 删除字面电子邮箱值，但不因此删除反应行；原始 Parquet、`_needs_review`、凭证及清洁重建副本不在发布载荷中。

模型就绪层只处理每个目标声明的物理源子集，并按 `schema.json` 的 `label_policy` 选择标签。多数目标要求“恰好一个结构化标量，不做聚合”；连续流目标使用声明的多目标规则，不对数据取平均；有符号 ee 目标按 `S-R` 定义。不能满足目标规则的记录不会静默丢失，而是写入 `exclusions.csv` 和 `audit.jsonl`。每个目标的实际排除原因见[目标总表](#19-个模型就绪目标)。

### 一步步溯源一条反应（真实示例）

下面从 `main` 中 Ahneman C-N 交叉偶联目标的第一条数据开始。整个过程像“查快递单号”：语义化主数据表给结果，`row-map.csv` 给反应单号，`audit.jsonl` 解释标签怎么选，`source-links.json` 给原始文件地址和指纹，完整语料再给回整条反应记录。

1. 打开 [`ahneman-c-n-cross-coupling-yield-percent-dataset.csv`](https://github.com/thinktraveller/ord-datasets/blob/main/datasets/model-ready/ahneman-c-n-cross-coupling-yield-percent/ahneman-c-n-cross-coupling-yield-percent-dataset.csv)。第 1 行是表头，所以第一条数据的 CSV 行号是 **2**。它的 `yield_percent` 是 `54.390403747558594`。
2. 打开同一目录的 [`row-map.csv`](https://github.com/thinktraveller/ord-datasets/blob/main/datasets/model-ready/ahneman-c-n-cross-coupling-yield-percent/row-map.csv)，筛选 `csv_row_number = 2`，得到：

   ```text
   reaction_key        = ord_dataset-46ff9a32d9e04016b9380b1b1ef949c3:ord-001c0b7f789d41b48e325967a9941ad6
   physical_dataset_id = ord_dataset-46ff9a32d9e04016b9380b1b1ef949c3
   source_row_index    = 3239
   label_decision_id   = d966e2c9e5acdd4ad6becd3c73ba17cc92c9c205913e86cff10c430a5395868f
   ```

   注意：`csv_row_number` 把表头算作第 1 行；`source_row_index` 从 0 开始。这两个数字不是同一种编号。
3. 打开 [`audit.jsonl`](https://github.com/thinktraveller/ord-datasets/blob/main/datasets/model-ready/ahneman-c-n-cross-coupling-yield-percent/audit.jsonl)，用文本搜索上面的 `label_decision_id`。这条审计记录显示：`status=included`、`reason=unique`、候选数为 1，选择的是 `UPLC` 的 `YIELD` 百分数，数值正是 `54.390403747558594`。这一步回答“为什么用这个标签”。
4. 打开 [`source-links.json`](https://github.com/thinktraveller/ord-datasets/blob/main/datasets/model-ready/ahneman-c-n-cross-coupling-yield-percent/source-links.json)，按 `physical_dataset_id` 找到源文件：

   ```text
   upstream revision = 83f971f586f6ad18f358ae4ae99d045e94ed2066
   source file       = data/46/ord_dataset-46ff9a32d9e04016b9380b1b1ef949c3.parquet
   source SHA-256    = 39440ea3e5442dddbb4daccbc48fb53940724085327c0e3b82909e1fd8cc661a
   ```

   `source_file_url` 是固定到上述 ORD revision 的链接，不会随 ORD 的 `main` 分支变化；SHA-256 相当于文件指纹。
5. 在完整语料中下载 [`ahneman-c-n-cross-coupling/reactions.csv`](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/ahneman-c-n-cross-coupling/reactions.csv)。同时用 `physical_dataset_id` 和 `row_index = 3239` 筛选，找到 `reaction_id = ord-001c0b7f789d41b48e325967a9941ad6`；它应与第 2 步 `reaction_key` 冒号后的部分完全一致。该行的 `reaction_json` 就是可读的完整 ORD 记录。
6. 最后可点击 `source_file_url` 下载原始 Parquet，并计算 SHA-256 与第 4 步比较。哈希一致，说明您拿到的是本发布实际使用的原始字节，而不是后来更新过的同名文件。

不建议用 Excel 打开很大的 `reactions.csv`：`reaction_json` 可能包含换行，超长单元格也可能被截断。若您已下载上述两个目录，可把下面代码复制到 Python 3；只需把最上面的两个路径改成自己的路径，它会按 CSV 规则安全地完成这次核对，不需要安装额外软件包。

```python
import csv
import json
from pathlib import Path

target_dir = Path("这里改成/ahneman-c-n-cross-coupling-yield-percent")
corpus_csv = Path("这里改成/ahneman-c-n-cross-coupling/reactions.csv")
wanted_csv_row = "2"

with (target_dir / "ahneman-c-n-cross-coupling-yield-percent-dataset.csv").open(encoding="utf-8", newline="") as f:
    dataset_row = next(row for number, row in enumerate(csv.DictReader(f), start=2)
                       if str(number) == wanted_csv_row)

with (target_dir / "row-map.csv").open(encoding="utf-8", newline="") as f:
    row_map = next(row for row in csv.DictReader(f)
                   if row["csv_row_number"] == wanted_csv_row)

with (target_dir / "audit.jsonl").open(encoding="utf-8") as f:
    audit = next(item for item in map(json.loads, f)
                 if item["label_decision_id"] == row_map["label_decision_id"])

source_links = json.loads((target_dir / "source-links.json").read_text(encoding="utf-8"))
source = next(item for item in source_links["links"]
              if item["physical_dataset_id"] == row_map["physical_dataset_id"])

with corpus_csv.open(encoding="utf-8", newline="") as f:
    corpus_row = next(row for row in csv.DictReader(f)
                      if row["physical_dataset_id"] == row_map["physical_dataset_id"]
                      and row["row_index"] == row_map["source_row_index"])

print("模型行：", dataset_row)
print("行映射：", row_map)
print("标签审计：", audit)
print("固定源：", source)
print("ORD reaction_id:", corpus_row["reaction_id"])
print(json.dumps(json.loads(corpus_row["reaction_json"]), ensure_ascii=False, indent=2))
```

对于完整语料中的任意一行，流程更短：从 `reactions.csv` 读取 `physical_dataset_id`、`source_file`、`reaction_id` 和 `row_index`，再在同目录的 `source-links.json` 中按 `physical_dataset_id` 查固定源即可。

## 全部数据集

下列数字来自已验收且与远端逐字节一致的发布候选。`MiB`/`GiB` 是二进制单位。表中“数据文件 / 整包”分别表示主 CSV 与该数据集目录内全部发布文件的大小。

### 41 个完整语料包

所有包共享前述 5 个字段和相同筛选规则：不按标签删行，仅清除字面邮箱值。点击数据集名称可浏览文件；点击 “fixed ORD source” 可查看每个原始 Parquet 的固定 URL、源大小、反应数、许可证和 SHA-256。

| 数据集 | 反应数 | ORD 源数 | `reactions.csv` / 整包 | 论文与固定源 |
|---|---:|---:|---:|---|
| [Ahneman C-N 交叉偶联](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/ahneman-c-n-cross-coupling) | 4,312 | 1 | 30.6 MiB / 30.6 MiB | [10.1126/science.aar5169](https://doi.org/10.1126/science.aar5169)<br>[固定 ORD 源 ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/ahneman-c-n-cross-coupling/source-links.json) |
| [AIChemEco 酰胺偶联条件](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/aichemeeco-amide-coupling-conditions) | 47,015 | 1 | 474.3 MiB / 474.3 MiB | [10.1039/d5sc03364k](https://doi.org/10.1039/d5sc03364k)<br>[固定 ORD 源 ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/aichemeeco-amide-coupling-conditions/source-links.json) |
| [阿斯利康 ELN Buchwald-Hartwig 产率](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/astrazeneca-eln-buchwald-hartwig-yields) | 750 | 1 | 2.7 MiB / 2.7 MiB | [10.26434/chemrxiv.14589498.v2](https://doi.org/10.26434/chemrxiv.14589498.v2)<br>[固定 ORD 源 ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/astrazeneca-eln-buchwald-hartwig-yields/source-links.json) |
| [不对称烷基化化学空间](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/asymmetric-alkylation-chemical-space) | 1,430 | 1 | 15.6 MiB / 15.6 MiB | [10.1038/s41467-023-42446-5](https://doi.org/10.1038/s41467-023-42446-5)<br>[固定 ORD 源 ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/asymmetric-alkylation-chemical-space/source-links.json) |
| [自动动力学 HPLC 优化](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/automated-kinetic-profiling-hplc-optimization) | 7 | 1 | 923.1 KiB / 926.5 KiB | [10.1039/c9re00086k](https://doi.org/10.1039/c9re00086k)<br>[固定 ORD 源 ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/automated-kinetic-profiling-hplc-optimization/source-links.json) |
| [Impatien A 偶氮-Heck 配体筛选](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/aza-heck-impatien-a-ligand-screen) | 24 | 1 | 297.6 KiB / 300.9 KiB | [固定 ORD 源 ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/aza-heck-impatien-a-ligand-screen/source-links.json) |
| [Cernak 微型化多样性反应](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/cernak-miniaturized-diversity-reactions) | 2,696 | 3 | 26.2 MiB / 26.2 MiB | [10.1038/s44160-023-00351-1](https://doi.org/10.1038/s44160-023-00351-1)<br>[固定 ORD 源 ×3](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/cernak-miniaturized-diversity-reactions/source-links.json) |
| [Cernak 超高通量 C-N 偶联](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/cernak-ultra-hte-c-n-coupling) | 50,688 | 1 | 485.5 MiB / 485.5 MiB | [10.1021/jacs.6c05959](https://doi.org/10.1021/jacs.6c05959)<br>[固定 ORD 源 ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/cernak-ultra-hte-c-n-coupling/source-links.json) |
| [Chan-Lam 磺酰胺-硼酸偶联](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/chan-lam-sulfonamide-boronic-acid-coupling) | 9,632 | 1 | 87.6 MiB / 87.6 MiB | [10.26434/chemrxiv-2024-22jrq](https://doi.org/10.26434/chemrxiv-2024-22jrq)<br>[固定 ORD 源 ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/chan-lam-sulfonamide-boronic-acid-coupling/source-links.json) |
| [化学信息员库](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/chemistry-informer-libraries) | 354 | 2 | 1.5 MiB / 1.5 MiB | [10.1039/C5SC04751J](https://doi.org/10.1039/C5SC04751J)<br>[固定 ORD 源 ×2](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/chemistry-informer-libraries/source-links.json) |
| [ChemRxiv 脱羧烯烃化优化系列](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/chemrxiv-decarboxylative-olefination-campaigns) | 256 | 2 | 1.0 MiB / 1.0 MiB | [10.26434/chemrxiv.15001213/v1](https://doi.org/10.26434/chemrxiv.15001213/v1)<br>[固定 ORD 源 ×2](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/chemrxiv-decarboxylative-olefination-campaigns/source-links.json) |
| [ChemRxiv 咪唑芳基化与苯胺酰胺化](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/chemrxiv-imidazole-arylation-and-aniline-amidation) | 2,496 | 2 | 14.3 MiB / 14.3 MiB | [10.1038/s41586-024-07021-y](https://doi.org/10.1038/s41586-024-07021-y)<br>[固定 ORD 源 ×2](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/chemrxiv-imidazole-arylation-and-aniline-amidation/source-links.json) |
| [铜催化烯烃对映选择性氢胺化](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/copper-enantioselective-alkene-hydroamination) | 3 | 1 | 28.5 KiB / 32.0 KiB | [10.15227/orgsyn.095.0080](https://doi.org/10.15227/orgsyn.095.0080)<br>[固定 ORD 源 ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/copper-enantioselective-alkene-hydroamination/source-links.json) |
| [脱氧氟化筛选](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/deoxyfluorination-screen) | 80 | 1 | 320.6 KiB / 323.8 KiB | [10.1021/jacs.8b01523](https://doi.org/10.1021/jacs.8b01523)<br>[固定 ORD 源 ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/deoxyfluorination-screen/source-links.json) |
| [电还原烯基-苄基卤化物偶联](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/electroreductive-alkenyl-benzyl-halide-coupling) | 27 | 1 | 196.4 KiB / 199.8 KiB | [10.1021/acscatal.9b01785](https://doi.org/10.1021/acscatal.9b01785)<br>[固定 ORD 源 ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/electroreductive-alkenyl-benzyl-halide-coupling/source-links.json) |
| [连续流儿茶酚重排](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/flow-catechol-rearrangement) | 1,227 | 1 | 14.7 MiB / 14.7 MiB | [10.48550/arXiv.2506.07619](https://doi.org/10.48550/arXiv.2506.07619)<br>[固定 ORD 源 ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/flow-catechol-rearrangement/source-links.json) |
| [Golden 吡啶-亲核试剂交叉偶联](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/golden-pyridine-nucleophile-cross-coupling) | 288 | 1 | 1.6 MiB / 1.6 MiB | [10.1016/j.chempr.2024.04.001](https://doi.org/10.1016/j.chempr.2024.04.001)<br>[固定 ORD 源 ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/golden-pyridine-nucleophile-cross-coupling/source-links.json) |
| [高通量 Suzuki 偶联](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/hte-suzuki-coupling) | 376 | 1 | 1.3 MiB / 1.3 MiB | [10.1021/jacs.2c08592](https://doi.org/10.1021/jacs.2c08592)<br>[固定 ORD 源 ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/hte-suzuki-coupling/source-links.json) |
| [咪唑并吡啶三组分合成](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/imidazopyridine-three-component-synthesis) | 384 | 1 | 1.3 MiB / 1.3 MiB | [固定 ORD 源 ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/imidazopyridine-three-component-synthesis/source-links.json) |
| [Islatravir 生物催化级联](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/islatravir-biocatalytic-cascade) | 3 | 1 | 27.3 KiB / 30.7 KiB | [10.1126/science.aay8484](https://doi.org/10.1126/science.aay8484)<br>[固定 ORD 源 ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/islatravir-biocatalytic-cascade/source-links.json) |
| [微波辅助 Biginelli 缩合](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/microwave-biginelli-condensation) | 48 | 1 | 192.9 KiB / 196.3 KiB | [10.1021/cc010044j](https://doi.org/10.1021/cc010044j)<br>[固定 ORD 源 ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/microwave-biginelli-condensation/source-links.json) |
| [纳米 C-N 光化学信息员库](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/nano-c-n-photochemistry-informer) | 1,728 | 1 | 16.7 MiB / 16.7 MiB | [10.1021/acs.accounts.0c00760](https://doi.org/10.1021/acs.accounts.0c00760)<br>[固定 ORD 源 ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/nano-c-n-photochemistry-informer/source-links.json) |
| [Newman 1-辛烯 Mizoroki-Heck 偶联](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/newman-1-octene-mizoroki-heck) | 96 | 1 | 1.2 MiB / 1.2 MiB | [固定 ORD 源 ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/newman-1-octene-mizoroki-heck/source-links.json) |
| [Newman N-乙烯基吡咯烷酮 Mizoroki-Heck 偶联](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/newman-n-vinyl-pyrrolidone-mizoroki-heck) | 96 | 1 | 906.4 KiB / 909.8 KiB | [固定 ORD 源 ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/newman-n-vinyl-pyrrolidone-mizoroki-heck/source-links.json) |
| [Newman 苯乙烯 Mizoroki-Heck 偶联](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/newman-styrene-mizoroki-heck) | 96 | 1 | 812.6 KiB / 815.9 KiB | [固定 ORD 源 ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/newman-styrene-mizoroki-heck/source-links.json) |
| [Newman 乙烯醚 Mizoroki-Heck 偶联](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/newman-vinyl-ether-mizoroki-heck) | 96 | 1 | 1.0 MiB / 1.0 MiB | [固定 ORD 源 ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/newman-vinyl-ether-mizoroki-heck/source-links.json) |
| [镍催化 Suzuki-Miyaura 交叉偶联](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/nickel-suzuki-miyaura-cross-coupling) | 450 | 1 | 2.6 MiB / 2.6 MiB | [10.1126/science.abj4213](https://doi.org/10.1126/science.abj4213)<br>[固定 ORD 源 ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/nickel-suzuki-miyaura-cross-coupling/source-links.json) |
| [NiCOlit 镍催化交叉偶联](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/nicolit-nickel-cross-couplings) | 1,762 | 1 | 3.3 MiB / 3.3 MiB | [10.1002/chem.201603436](https://doi.org/10.1002/chem.201603436)<br>[固定 ORD 源 ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/nicolit-nickel-cross-couplings/source-links.json) |
| [辉瑞高通量反应条件](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/pfizer-hte-reaction-conditions) | 39,347 | 1 | 214.7 MiB / 214.7 MiB | [10.1038/s41557-023-01393-w](https://doi.org/10.1038/s41557-023-01393-w)<br>[固定 ORD 源 ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/pfizer-hte-reaction-conditions/source-links.json) |
| [光催化芳基溴脱卤](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/photocatalytic-aryl-bromide-dehalogenation) | 1,152 | 1 | 6.3 MiB / 6.3 MiB | [10.1021/acscatal.0c02247](https://doi.org/10.1021/acscatal.0c02247)<br>[固定 ORD 源 ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/photocatalytic-aryl-bromide-dehalogenation/source-links.json) |
| [PyParser 噁唑 C-H 活化](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/pyparser-oxazole-c-h-activation) | 48 | 1 | 411.1 KiB / 414.4 KiB | [固定 ORD 源 ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/pyparser-oxazole-c-h-activation/source-links.json) |
| [Reizman Suzuki-Miyaura 反馈优化](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/reizman-suzuki-miyaura-feedback-optimization) | 385 | 4 | 2.1 MiB / 2.1 MiB | [10.1039/C6RE00153J](https://doi.org/10.1039/C6RE00153J)<br>[固定 ORD 源 ×4](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/reizman-suzuki-miyaura-feedback-optimization/source-links.json) |
| [Rexgen Direct 反应 SMILES](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/rexgen-direct-reaction-smiles) | 479,035 | 3 | 1.37 GiB / 1.37 GiB | [固定 ORD 源 ×3](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/rexgen-direct-reaction-smiles/source-links.json) |
| [罗氏硼化 SURF 数据集](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/roche-borylation-surf) | 1,111 | 1 | 4.1 MiB / 4.1 MiB | [10.26434/chemrxiv-2023-nfq7h](https://doi.org/10.26434/chemrxiv-2023-nfq7h)<br>[固定 ORD 源 ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/roche-borylation-surf/source-links.json) |
| [罗氏 Minisci SURF 数据集](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/roche-minisci-surf) | 130 | 1 | 468.1 KiB / 471.3 KiB | [10.26434/chemrxiv-2023-nfq7h](https://doi.org/10.26434/chemrxiv-2023-nfq7h)<br>[固定 ORD 源 ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/roche-minisci-surf/source-links.json) |
| [Science 高通量钯催化交叉偶联](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/science-hte-palladium-cross-coupling) | 1,824 | 2 | 16.4 MiB / 16.4 MiB | [10.1126/science.1259203](https://doi.org/10.1126/science.1259203)<br>[固定 ORD 源 ×2](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/science-hte-palladium-cross-coupling/source-links.json) |
| [Shields 贝叶斯芳基化优化](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/shields-bayesian-arylation) | 1,984 | 2 | 12.4 MiB / 12.4 MiB | [10.1038/s41586-021-03213-y](https://doi.org/10.1038/s41586-021-03213-y)<br>[固定 ORD 源 ×2](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/shields-bayesian-arylation/source-links.json) |
| [sp3 羧基碳-芳基卤化物偶联](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/sp3-carboxyl-aryl-halide-coupling) | 24 | 1 | 181.0 KiB / 184.3 KiB | [固定 ORD 源 ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/sp3-carboxyl-aryl-halide-coupling/source-links.json) |
| [磺酰胺连续流合成库](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/sulfonamide-flow-synthesis-library) | 39 | 1 | 193.6 KiB / 196.9 KiB | [10.1021/co400012m](https://doi.org/10.1021/co400012m)<br>[固定 ORD 源 ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/sulfonamide-flow-synthesis-library/source-links.json) |
| [Suzuki-Miyaura 纳米尺度筛选](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/suzuki-miyaura-nanoscale-screen) | 5,760 | 1 | 29.8 MiB / 29.8 MiB | [10.1126/science.aap9112](https://doi.org/10.1126/science.aap9112)<br>[固定 ORD 源 ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/suzuki-miyaura-nanoscale-screen/source-links.json) |
| [USPTO 授权专利反应](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/uspto-grants-reactions) | 1,771,032 | 1 | 9.41 GiB / 9.41 GiB | [固定 ORD 源 ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/uspto-grants-reactions/source-links.json) |

### 19 个模型就绪目标

“纳入 / 排除”是标签决策数；“筛选”只列实际出现的排除原因。所有目标都先限制到自己声明的物理源，再执行 `schema.json` 中的标签规则。状态字母反映**作为建模/基准任务的就绪程度**，不是下载状态；19 个文件包都已发布并通过发布载荷验证。

| 状态 | 仓库状态 | 含义 |
|---|---|---|
| A | `active_generated_pending_release_validation` | 活跃目标；生成时仍等待下游就绪门。载荷后来已完成发布验证。 |
| B | `generated_pending_campaign_evaluation` | 文件已生成，仍需评估实验系列/分组后才能作为基准。 |
| C | `partial_scope_generated` | 只覆盖逻辑数据集声明的一部分物理源，不代表完整逻辑数据集。 |
| D | `research_only_benchmark_blocked` | 研究用目标；缺少可靠运行分组，不可直接宣称为批量基准。 |
| E | `generated_with_source_caveat` | 源测量口径有限制；NiCOlit 中 GC 与分离产率未区分。 |
| F | `generated_adapter_blocked` | 文件存在，但已声明的适配器/就绪门尚未通过。 |

| 目标 | 论文与固定源 | 纳入 / 排除 | `*-dataset.csv` / 整包 | 标签 | 实际排除 | 状态 |
|---|---|---:|---:|---|---|:---:|
| [Ahneman C-N 交叉偶联产率（%）](https://github.com/thinktraveller/ord-datasets/tree/main/datasets/model-ready/ahneman-c-n-cross-coupling-yield-percent) | [10.1126/science.aar5169](https://doi.org/10.1126/science.aar5169)<br>[固定 ORD 源 ×1](https://github.com/thinktraveller/ord-datasets/blob/v0.1.0-model-ready-preview-1/datasets/model-ready/ahneman-c-n-cross-coupling-yield-percent/source-links.json) | 4,312 / 0 | 1.2 MiB / 5.8 MiB | `yield_percent`<br>源测量定义的百分比产率 | 无额外排除 | A |
| [不对称烷基化 ee（S-R，%）](https://github.com/thinktraveller/ord-datasets/tree/main/datasets/model-ready/asymmetric-alkylation-ee-s-minus-r-percent) | [10.1038/s41467-023-42446-5](https://doi.org/10.1038/s41467-023-42446-5)<br>[固定 ORD 源 ×1](https://github.com/thinktraveller/ord-datasets/blob/v0.1.0-model-ready-preview-1/datasets/model-ready/asymmetric-alkylation-ee-s-minus-r-percent/source-links.json) | 1,430 / 0 | 296.3 KiB / 4.3 MiB | `ee_s_minus_r_percent`<br>百分点，S-R | 无额外排除 | F |
| [Cernak 还原胺化转化率（%）](https://github.com/thinktraveller/ord-datasets/tree/main/datasets/model-ready/cernak-reductive-amination-conversion-percent) | [10.1038/s44160-023-00351-1](https://doi.org/10.1038/s44160-023-00351-1)<br>[固定 ORD 源 ×1](https://github.com/thinktraveller/ord-datasets/blob/v0.1.0-model-ready-preview-1/datasets/model-ready/cernak-reductive-amination-conversion-percent/source-links.json) | 1,152 / 0 | 323.4 KiB / 1.5 MiB | `conversion_percent`<br>百分比转化率 | 无额外排除 | B |
| [Cernak Suzuki 偶联转化率（%）](https://github.com/thinktraveller/ord-datasets/tree/main/datasets/model-ready/cernak-suzuki-coupling-conversion-percent) | [10.1038/s44160-023-00351-1](https://doi.org/10.1038/s44160-023-00351-1)<br>[固定 ORD 源 ×1](https://github.com/thinktraveller/ord-datasets/blob/v0.1.0-model-ready-preview-1/datasets/model-ready/cernak-suzuki-coupling-conversion-percent/source-links.json) | 1,320 / 120 | 306.8 KiB / 1.8 MiB | `conversion_percent`<br>百分比转化率 | 非有限标签 | B |
| [Cernak 超高通量 C-N 产率（%）](https://github.com/thinktraveller/ord-datasets/tree/main/datasets/model-ready/cernak-ultra-hte-c-n-yield-percent) | [10.1021/jacs.6c05959](https://doi.org/10.1021/jacs.6c05959)<br>[固定 ORD 源 ×1](https://github.com/thinktraveller/ord-datasets/blob/v0.1.0-model-ready-preview-1/datasets/model-ready/cernak-ultra-hte-c-n-yield-percent/source-links.json) | 50,668 / 20 | 11.6 MiB / 68.2 MiB | `yield_percent`<br>源测量定义的百分比产率 | 标签越界 | B |
| [Chan-Lam 磺酰胺偶联产率（%）](https://github.com/thinktraveller/ord-datasets/tree/main/datasets/model-ready/chan-lam-sulfonamide-coupling-yield-percent) | [10.26434/chemrxiv-2024-22jrq](https://doi.org/10.26434/chemrxiv-2024-22jrq)<br>[固定 ORD 源 ×1](https://github.com/thinktraveller/ord-datasets/blob/v0.1.0-model-ready-preview-1/datasets/model-ready/chan-lam-sulfonamide-coupling-yield-percent/source-links.json) | 9,602 / 30 | 1.8 MiB / 12.8 MiB | `yield_percent`<br>源测量定义的百分比产率 | 标签越界 | B |
| [ChemRxiv 苯胺酰胺化产率（%）](https://github.com/thinktraveller/ord-datasets/tree/main/datasets/model-ready/chemrxiv-aniline-amidation-yield-percent) | [10.1038/s41586-024-07021-y](https://doi.org/10.1038/s41586-024-07021-y)<br>[固定 ORD 源 ×1](https://github.com/thinktraveller/ord-datasets/blob/v0.1.0-model-ready-preview-1/datasets/model-ready/chemrxiv-aniline-amidation-yield-percent/source-links.json) | 957 / 3 | 232.7 KiB / 1.3 MiB | `yield_percent`<br>源测量定义的百分比产率 | 标签越界 | A |
| [ChemRxiv 咪唑 C-H 芳基化产率（%）](https://github.com/thinktraveller/ord-datasets/tree/main/datasets/model-ready/chemrxiv-imidazole-c-h-arylation-yield-percent) | [10.1038/s41586-024-07021-y](https://doi.org/10.1038/s41586-024-07021-y)<br>[固定 ORD 源 ×1](https://github.com/thinktraveller/ord-datasets/blob/v0.1.0-model-ready-preview-1/datasets/model-ready/chemrxiv-imidazole-c-h-arylation-yield-percent/source-links.json) | 1,529 / 7 | 384.8 KiB / 2.1 MiB | `yield_percent`<br>源测量定义的百分比产率 | 标签越界 | A |
| [连续流儿茶酚产物 2 HPLC 响应（%）](https://github.com/thinktraveller/ord-datasets/tree/main/datasets/model-ready/flow-catechol-product-2-response-percent) | [10.48550/arXiv.2506.07619](https://doi.org/10.48550/arXiv.2506.07619)<br>[固定 ORD 源 ×1](https://github.com/thinktraveller/ord-datasets/blob/v0.1.0-model-ready-preview-1/datasets/model-ready/flow-catechol-product-2-response-percent/source-links.json) | 1,227 / 0 | 213.6 KiB / 2.9 MiB | `product_2_yield_percent`<br>HPLC 百分响应；不是分离产率 | 无额外排除 | D |
| [连续流儿茶酚产物 3 HPLC 响应（%）](https://github.com/thinktraveller/ord-datasets/tree/main/datasets/model-ready/flow-catechol-product-3-response-percent) | [10.48550/arXiv.2506.07619](https://doi.org/10.48550/arXiv.2506.07619)<br>[固定 ORD 源 ×1](https://github.com/thinktraveller/ord-datasets/blob/v0.1.0-model-ready-preview-1/datasets/model-ready/flow-catechol-product-3-response-percent/source-links.json) | 1,227 / 0 | 213.6 KiB / 2.9 MiB | `product_3_yield_percent`<br>HPLC 百分响应；不是分离产率 | 无额外排除 | D |
| [连续流儿茶酚总产物 HPLC 响应（%）](https://github.com/thinktraveller/ord-datasets/tree/main/datasets/model-ready/flow-catechol-total-product-response-percent) | [10.48550/arXiv.2506.07619](https://doi.org/10.48550/arXiv.2506.07619)<br>[固定 ORD 源 ×1](https://github.com/thinktraveller/ord-datasets/blob/v0.1.0-model-ready-preview-1/datasets/model-ready/flow-catechol-total-product-response-percent/source-links.json) | 1,227 / 0 | 214.3 KiB / 3.7 MiB | `total_product_yield_percent`<br>HPLC 百分响应；不是分离产率 | 无额外排除 | D |
| [纳米 C-N 光化学产率（%）](https://github.com/thinktraveller/ord-datasets/tree/main/datasets/model-ready/nano-c-n-photochemistry-yield-percent) | [10.1021/acs.accounts.0c00760](https://doi.org/10.1021/acs.accounts.0c00760)<br>[固定 ORD 源 ×1](https://github.com/thinktraveller/ord-datasets/blob/v0.1.0-model-ready-preview-1/datasets/model-ready/nano-c-n-photochemistry-yield-percent/source-links.json) | 1,728 / 0 | 361.4 KiB / 2.3 MiB | `yield_percent`<br>源测量定义的百分比产率 | 无额外排除 | A |
| [NiCOlit 镍催化偶联产率（%）](https://github.com/thinktraveller/ord-datasets/tree/main/datasets/model-ready/nicolit-nickel-coupling-yield-percent) | [10.1002/chem.201603436](https://doi.org/10.1002/chem.201603436)<br>[固定 ORD 源 ×1](https://github.com/thinktraveller/ord-datasets/blob/v0.1.0-model-ready-preview-1/datasets/model-ready/nicolit-nickel-coupling-yield-percent/source-links.json) | 1,669 / 93 | 157.0 KiB / 4.2 MiB | `yield_percent`<br>源测量定义的百分比产率 | 缺少目标产物<br>缺少必要反应物 SMILES | E |
| [辉瑞高通量 LC 面积（%）](https://github.com/thinktraveller/ord-datasets/tree/main/datasets/model-ready/pfizer-hte-lc-area-percent) | [10.1038/s41557-023-01393-w](https://doi.org/10.1038/s41557-023-01393-w)<br>[固定 ORD 源 ×1](https://github.com/thinktraveller/ord-datasets/blob/v0.1.0-model-ready-preview-1/datasets/model-ready/pfizer-hte-lc-area-percent/source-links.json) | 39,347 / 0 | 6.7 MiB / 65.9 MiB | `lc_area_percent`<br>LC/UV 面积百分比；不是分离产率或转化率 | 无额外排除 | B |
| [光催化芳基溴脱卤转化率（%）](https://github.com/thinktraveller/ord-datasets/tree/main/datasets/model-ready/photocatalytic-aryl-bromide-dehalogenation-conversion-percent) | [10.1021/acscatal.0c02247](https://doi.org/10.1021/acscatal.0c02247)<br>[固定 ORD 源 ×1](https://github.com/thinktraveller/ord-datasets/blob/v0.1.0-model-ready-preview-1/datasets/model-ready/photocatalytic-aryl-bromide-dehalogenation-conversion-percent/source-links.json) | 1,152 / 0 | 232.7 KiB / 1.4 MiB | `conversion_percent`<br>百分比转化率 | 无额外排除 | A |
| [罗氏硼化产率（%）](https://github.com/thinktraveller/ord-datasets/tree/main/datasets/model-ready/roche-borylation-yield-percent) | [10.26434/chemrxiv-2023-nfq7h](https://doi.org/10.26434/chemrxiv-2023-nfq7h)<br>[固定 ORD 源 ×1](https://github.com/thinktraveller/ord-datasets/blob/v0.1.0-model-ready-preview-1/datasets/model-ready/roche-borylation-yield-percent/source-links.json) | 890 / 221 | 193.5 KiB / 1.4 MiB | `yield_percent`<br>源测量定义的百分比产率 | 标签越界<br>缺少目标产物 | B |
| [Science 高通量相对 LC 面积比](https://github.com/thinktraveller/ord-datasets/tree/main/datasets/model-ready/science-hte-relative-lc-area-ratio) | [10.1126/science.1259203](https://doi.org/10.1126/science.1259203)<br>[固定 ORD 源 ×1](https://github.com/thinktraveller/ord-datasets/blob/v0.1.0-model-ready-preview-1/datasets/model-ready/science-hte-relative-lc-area-ratio/source-links.json) | 1,531 / 5 | 332.7 KiB / 8.0 MiB | `relative_product_lc_area_ratio`<br>无量纲比值（产物 LC 面积 / 内标 LC 面积） | 联苯内标面积无效 | C |
| [Shields 芳基化产率（%）](https://github.com/thinktraveller/ord-datasets/tree/main/datasets/model-ready/shields-arylation-yield-percent) | [10.1038/s41586-021-03213-y](https://doi.org/10.1038/s41586-021-03213-y)<br>[固定 ORD 源 ×2](https://github.com/thinktraveller/ord-datasets/blob/v0.1.0-model-ready-preview-1/datasets/model-ready/shields-arylation-yield-percent/source-links.json) | 1,984 / 0 | 370.5 KiB / 2.7 MiB | `yield_percent`<br>源测量定义的百分比产率 | 无额外排除 | A |
| [Suzuki-Miyaura 纳米尺度产率（%）](https://github.com/thinktraveller/ord-datasets/tree/main/datasets/model-ready/suzuki-miyaura-nanoscale-yield-percent) | [10.1126/science.aap9112](https://doi.org/10.1126/science.aap9112)<br>[固定 ORD 源 ×1](https://github.com/thinktraveller/ord-datasets/blob/v0.1.0-model-ready-preview-1/datasets/model-ready/suzuki-miyaura-nanoscale-yield-percent/source-links.json) | 5,760 / 0 | 1.6 MiB / 8.1 MiB | `yield_percent`<br>源测量定义的百分比产率 | 无额外排除 | A |

#### 每个目标如何选择标签

下表把 19 个目标逐一映射到实际使用的适配器和标签策略。适配器回答“到 ORD 记录的哪里、按什么化学语义找数值”；标签策略回答“有几个候选时怎么办”。R1–R8 只是本 README 的阅读编号，不是数据字段。

| 规则 | `target_adapter` | `label_policy` | 适用目标 | 通俗说明 |
|---|---|---|---|---|
| R1 | `generic` | `unique_structured_scalar_no_aggregation` | `ahneman-c-n-cross-coupling-yield-percent`<br>`chemrxiv-aniline-amidation-yield-percent`<br>`chemrxiv-imidazole-c-h-arylation-yield-percent`<br>`nano-c-n-photochemistry-yield-percent`<br>`photocatalytic-aryl-bromide-dehalogenation-conversion-percent`<br>`shields-arylation-yield-percent`<br>`suzuki-miyaura-nanoscale-yield-percent` | 按目标测量类型选择唯一的结构化标量；不对多个测量取平均。 |
| R2 | `cernak_conversion` | `unique_structured_scalar_no_aggregation` | `cernak-reductive-amination-conversion-percent`<br>`cernak-suzuki-coupling-conversion-percent` | 按 Cernak 记录结构提取唯一转化率；Suzuki 目标实际排除了 120 个非有限值。 |
| R3 | `unique_desired_product` | `unique_structured_scalar_no_aggregation` | `cernak-ultra-hte-c-n-yield-percent`<br>`chan-lam-sulfonamide-coupling-yield-percent`<br>`roche-borylation-yield-percent` | 先要求能唯一确定目标产物，再取该产物唯一的结构化产率；缺目标产物或越界值会排除。 |
| R4 | `science_hte_relative_lc_area_ratio` | `unique_structured_scalar_no_aggregation` | `science-hte-relative-lc-area-ratio` | 标签是“产物 LC 面积 ÷ 联苯内标 LC 面积”，不是产率；内标面积无效时排除。 |
| R5 | `catechol_multitarget_v1` | `catechol_multitarget_v1:smiles_custom_name_hplc_yield` | `flow-catechol-product-2-response-percent`<br>`flow-catechol-product-3-response-percent`<br>`flow-catechol-total-product-response-percent` | 按 SMILES/自定义产物名找 Product 2、Product 3 的 HPLC 百分响应；总产物响应为两者确定性相加，不做样本间聚合。 |
| R6 | `nicolit_reported_yield_float_percent` | `unique_structured_scalar_no_aggregation` | `nicolit-nickel-coupling-yield-percent` | 解析 NiCOlit 报告的浮点百分数并要求必要反应物 SMILES/目标产物；GC 与分离产率口径没有区分。 |
| R7 | `signed_selectivity` | `signed_selectivity_v1:s_config_imms_percentage` | `asymmetric-alkylation-ee-s-minus-r-percent` | 从 S 构型 IMMS 百分数得到有符号 `S-R` ee；产物立体信息只用于标签判定，不作为特征。 |
| R8 | `pfizer_lcms` | `unique_structured_scalar_no_aggregation` | `pfizer-hte-lc-area-percent` | 选择唯一 LC/UV 面积百分数；它不是分离产率或转化率。 |

#### 每个目标的完整 `*-dataset.csv` 字段

下表没有省略列。为便于阅读，仅按“结构/组成/辅助字段”“条件字段”“标签”分组；精确角色以每个包的 `schema.json` 为准。空值用 `—` 表示。字段名是数据表中的原始英文列名，在中英文说明中相同。

字段名速读：

- `reactant-*`、`reagent-*`、`catalyst-*`、`solvent-*` 和 `product` 通常保存标准化的 SMILES（分子结构的文本表示）。编号只是同类组分的列位，不代表化学重要性排名。
- `temperature_c`、`reaction_time_s`、`residence_time_min`、`pressure_kpa` 和 `illumination_wavelength_nm` 的单位已写在名称末尾；`solvent_b_fraction` 是溶剂 B 的比例。
- 以 `_raw` 结尾的列保留源数值；以 `_gt_100` 结尾的列是“是/否超过 100”的质量检查标志，不是新的产率。
- 不要把 `yield_percent`、`conversion_percent`、`lc_area_percent`、HPLC 响应、LC 面积比和有符号 ee 混为同一种标签。它们的化学/分析含义不同。

| 目标目录 | 结构、组成与辅助字段 | 条件 | 标签 |
|---|---|---|---|
| `ahneman-c-n-cross-coupling-yield-percent` | `reactant-1`, `reactant-2`, `reagent-1`, `reagent-2`, `catalyst-1`, `solvent-1`, `solvent-2`, `solvent-3`, `solvent-4`, `solvent-5`, `product` | `temperature_c`, `reaction_time_s` | `yield_percent` |
| `asymmetric-alkylation-ee-s-minus-r-percent` | `reactant-1`, `reactant-2`, `reactant-3`, `catalyst-1`, `catalyst-2`, `solvent-1`, `solvent-2`, `solvent-3`, `solvent-4`, `solvent-5` | — | `ee_s_minus_r_percent` |
| `cernak-reductive-amination-conversion-percent` | `reactant-1`, `reactant-2`, `reagent-1`, `reagent-2`, `reagent-3`, `catalyst-1`, `solvent-1`, `solvent-2`, `solvent-3`, `solvent-4`, `solvent-5`, `solvent-6`, `solvent-7` | `temperature_c`, `reaction_time_s` | `conversion_percent` |
| `cernak-suzuki-coupling-conversion-percent` | `reactant-1`, `reactant-2`, `reagent-1`, `reagent-2`, `reagent-3`, `catalyst-1`, `solvent-1`, `solvent-2`, `solvent-3`, `solvent-4`, `solvent-5`, `solvent-6`, `solvent-7` | `reaction_time_s`, `reflux_value`, `conditions_are_dynamic_value` | `conversion_percent` |
| `cernak-ultra-hte-c-n-yield-percent` | `reactant-1`, `reactant-2`, `reagent-1`, `catalyst-1`, `catalyst-2`, `solvent-1`, `solvent-2`, `solvent-3`, `solvent-4`, `solvent-5`, `solvent-6`, `solvent-7`, `solvent-8`, `solvent-9`, `solvent-10`, `product` | `temperature_c`, `reaction_time_s` | `yield_percent` |
| `chan-lam-sulfonamide-coupling-yield-percent` | `reactant-1`, `reactant-2`, `reagent-1`, `catalyst-1`, `solvent-1`, `solvent-2`, `product` | `temperature_c`, `reaction_time_s` | `yield_percent` |
| `chemrxiv-aniline-amidation-yield-percent` | `reactant-1`, `reactant-2`, `reagent-1`, `reagent-2`, `catalyst-1`, `catalyst-2`, `solvent-1`, `solvent-2`, `solvent-3`, `product` | `temperature_c`, `reaction_time_s`, `reflux_value`, `conditions_are_dynamic_value` | `yield_percent` |
| `chemrxiv-imidazole-c-h-arylation-yield-percent` | `reactant-1`, `reactant-2`, `reagent-1`, `reagent-2`, `catalyst-1`, `catalyst-2`, `solvent-1`, `solvent-2`, `solvent-3`, `product` | `temperature_c`, `reaction_time_s`, `reflux_value`, `conditions_are_dynamic_value` | `yield_percent` |
| `flow-catechol-product-2-response-percent` | `reactant_smiles`, `solvent_a_smiles`, `solvent_b_smiles`, `starting_material_recovery_percent_raw`, `product_sum_yield_percent_raw`, `mass_balance_sum_percent`, `starting_material_gt_100`, `mass_balance_gt_100`, `pressure_kpa_raw` | `solvent_b_fraction`, `temperature_c`, `residence_time_s`, `residence_time_min` | `product_2_yield_percent` |
| `flow-catechol-product-3-response-percent` | `reactant_smiles`, `solvent_a_smiles`, `solvent_b_smiles`, `starting_material_recovery_percent_raw`, `product_sum_yield_percent_raw`, `mass_balance_sum_percent`, `starting_material_gt_100`, `mass_balance_gt_100`, `pressure_kpa_raw` | `solvent_b_fraction`, `temperature_c`, `residence_time_s`, `residence_time_min` | `product_3_yield_percent` |
| `flow-catechol-total-product-response-percent` | `reactant_smiles`, `solvent_a_smiles`, `solvent_b_smiles`, `starting_material_recovery_percent_raw`, `product_sum_yield_percent_raw`, `mass_balance_sum_percent`, `starting_material_gt_100`, `mass_balance_gt_100`, `pressure_kpa_raw` | `solvent_b_fraction`, `temperature_c`, `residence_time_s`, `residence_time_min` | `total_product_yield_percent` |
| `nano-c-n-photochemistry-yield-percent` | `reactant-1`, `reactant-2`, `catalyst-1`, `catalyst-2`, `catalyst-3`, `catalyst-4`, `solvent-1`, `solvent-2`, `solvent-3`, `product` | `temperature_c`, `reaction_time_s`, `illumination_wavelength_nm`, `reflux_value` | `yield_percent` |
| `nicolit-nickel-coupling-yield-percent` | `reactant-1`, `reactant-2`, `product` | `temperature_c`, `reaction_time_s` | `yield_percent` |
| `pfizer-hte-lc-area-percent` | `reactant-1`, `reactant-2`, `reactant-3`, `reagent-1`, `reagent-2`, `reagent-3`, `reagent-4`, `reagent-5`, `catalyst-1`, `catalyst-2`, `solvent-1`, `solvent-2`, `product` | — | `lc_area_percent` |
| `photocatalytic-aryl-bromide-dehalogenation-conversion-percent` | `reactant-1`, `reactant-2`, `reagent-1`, `catalyst-1`, `catalyst-2`, `catalyst-3`, `solvent-1`, `solvent-2` | `reaction_time_s`, `illumination_wavelength_nm` | `conversion_percent` |
| `roche-borylation-yield-percent` | `reactant-1`, `reagent-1`, `reagent-2`, `reagent-3`, `reagent-4`, `reagent-5`, `catalyst-1`, `catalyst-2`, `solvent-1`, `solvent-2`, `product` | `temperature_c`, `reaction_time_s` | `yield_percent` |
| `science-hte-relative-lc-area-ratio` | `reactant-1`, `reactant-2`, `reactant-3`, `reagent-1`, `reagent-2`, `catalyst-1`, `solvent-1`, `solvent-2`, `solvent-3`, `solvent-4` | `reaction_time_s` | `relative_product_lc_area_ratio` |
| `shields-arylation-yield-percent` | `reactant-1`, `reactant-2`, `reagent-1`, `catalyst-1`, `catalyst-2`, `solvent-1`, `product` | `temperature_c`, `reaction_time_s` | `yield_percent` |
| `suzuki-miyaura-nanoscale-yield-percent` | `reactant-1`, `reactant-2`, `reagent-1`, `catalyst-1`, `catalyst-2`, `solvent-1`, `solvent-2`, `solvent-3`, `solvent-4`, `solvent-5`, `solvent-6`, `solvent-7`, `product` | `temperature_c`, `pressure_kpa`, `reaction_time_s`, `conditions_are_dynamic_value` | `yield_percent` |

## 完整性、许可与维护

- 数据衍生物采用 CC BY-SA 4.0；处理代码采用 Apache-2.0。详见 `LICENSE-DATA`、`LICENSE-CODE`、`NOTICE` 和 `CITATION.cff`。
- 完整语料可在发布根目录运行 `sha256sum -c SHA256SUMS`；每个包也有自己的 `checksums.csv`。
- 精确机器可读总表是 [`datasets/catalog.csv`](datasets/catalog.csv)；源文件清单是 [`provenance/source-files.csv`](provenance/source-files.csv)；两跳行级索引与示例位于 [`provenance/row-lineage/`](provenance/row-lineage/)。
- 本仓库的输入边界、构建过程和验收证据见 [`SOURCE_BOUNDARIES.md`](SOURCE_BOUNDARIES.md)、[`project-docs/buildlog.md`](project-docs/buildlog.md) 和 [`reports/release-acceptance/`](reports/release-acceptance/)。
- 本发布不声称所有模型就绪目标都是已接受的公共基准；使用前请阅读上表的状态和标签单位。

维护者可运行：

```bash
python3 -m unittest discover -s pipeline/tests
```
