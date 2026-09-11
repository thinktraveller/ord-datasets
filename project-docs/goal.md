# ord-datasets 项目目标与发布任务书

## 文档状态

- 文档日期：2026-09-11（Asia/Shanghai）
- 目标项目：`/home/wangzh685/桌面/ord-data/ord-datasets`
- 当前阶段：仅完成目标定义、许可审阅和发布任务书；不搬运数据、不改写处理结果、不上传远端。
- 当前基线来源：同级 `ord-data/` 与 `dataset/` 的本地只读盘点。
- 本文是 `ord-datasets` 项目的现行目标基线；后续实现若改变范围、计数、许可或目录契约，必须先更新本文并留下新的 QA 记录。

## 澄清问答记录
<!-- GOAL-QA-LOG-START -->

### QA-R001：建立处理后 ORD 数据的独立发布项目
<!-- GOAL-QA-R001-START -->

- 提问时间：2026-09-11
- 用户输入：浏览 `ord-data/` 与 `dataset/`；确认 `ord-data` 的开源协议是否允许将二次处理后的数据和中间文件重新上传；为新项目 `ord-datasets/` 制定任务书。新项目至少应包含：语义化命名的全部最终数据集、每一步处理过程和中间文件、整体处理框架，以及无需复制原始 Parquet 但能定位其下载链接的完整溯源方法。
- 本轮澄清结论：
  1. “全部处理好的 ORD 数据集”按三层理解：53 个物理 ORD 数据集的转换层、覆盖它们的 41 个逻辑全量数据集，以及目前 15 个建模包中的 19 个目标数据集；三层不得混为同一完成状态。
  2. 原始 `ord-data/data/**/*.parquet` 不复制到新项目；每个物理源文件必须有固定版本链接、路径、ID、哈希和行数，能够从新项目反查并重新获取。
  3. `dataset/` 中与数据处理有关的中间文件、脚本、配置、schema、审计和验证报告均进入发布盘点；缓存、虚拟环境、锁文件、凭证、临时文件和第三方权利不明文件只登记处置原因，不上传。
  4. `_needs_review` 不得静默删除，也不得伪装成最终产物；默认进入隔离的历史/待审层，逐文件标记 `publishable`、`quarantined`、`superseded` 或 `excluded`。
  5. 最终目录名称必须可读且表达反应/来源/目标语义；ORD UUID、logical ID 和旧路径作为稳定机器标识保留在 metadata 与 catalog 中，不能继续充当唯一的人类可读目录名。
- 暂不阻塞规划、但实际上传前需确认：远端仓库地址与权限、大文件后端及额度、发布版本号，以及待审/阻塞数据是否进入首个公开 release。

<!-- GOAL-QA-R001-END -->

### QA-R002：当前最终目录状态确认
<!-- GOAL-QA-R002-START -->

- **提问时间**：2026-09-11 16:56
- **提问目的**：澄清用户询问的“最终文件夹目录结果”是当前仓库真实文件树，还是目标构建完成后的规划目录，并把两者明确区分，避免把规划目录误认为已经生成的发布目录。
- **问题列表**
  1. 目前 `ord-datasets/` 实际已经生成了哪些目录和文件？
  2. 按目标目录契约，后续构建完成后的规划最终目录应是什么样？
  3. 哪些规划目录目前尚未创建？
- **用户回答**
  1. 用户询问：“目前最终文件夹的目录结果是什么样的”。
  2. 用户未补充新的目录范围要求。
  3. 用户未要求本轮创建目录、搬运数据或上传远端。
- **提炼结论**
  - 当前实际目录仅包含 Git 仓库元数据与 `project-docs/goal.md`；`datasets/`、`intermediate/`、`pipeline/`、`provenance/`、`reports/` 等发布目录尚未创建。
  - `goal.md` 中的“目标目录契约”是后续构建完成后的规划结构，不是当前文件树。
  - 本轮只回答目录状态并记录澄清，不执行数据搬运、目录创建或上传。
- **影响的目标文档章节**
  - 目标目录契约
  - 完成边界
  - 澄清问答记录

<!-- GOAL-QA-R002-END -->

<!-- GOAL-QA-LOG-END -->

## 一、审计基线

### 1.1 已浏览的权威材料

| 类别 | 本地证据 | 规划时结论 |
|---|---|---|
| ORD 数据许可 | `ord-data/LICENSE`、`ord-data/README.md` | `data/` 中的数据集及描述它们的仓库元数据为 CC BY-SA 4.0 |
| ORD 代码许可 | `ord-data/LICENSE-CODE`、`ord-data/README.md` | `scripts/`、`.github/` 等代码为 Apache-2.0 |
| 贡献授权 | `ord-data/CONTRIBUTING.md` 的 Terms of Use | 贡献者向 ORDP 及数据接收者授予复制、制作衍生作品和分发等权利 |
| 物理数据清单 | `dataset/standardized/csv-data/datasets.csv` | 53 个物理数据集，共 2,428,291 条 Reaction |
| 逻辑归并清单 | `dataset/processing/derived/csv/manifests/logical_datasets.csv`、`logical_dataset_members.csv` | 53 个物理数据集非破坏归并为 41 个逻辑数据集 |
| 全量逻辑产物 | `dataset/standardized/derived/csv/tables/` | 41 个 `reactions.csv`，总行数必须保持 2,428,291 |
| 建模包 | `dataset/processing/derived/yonod/datasets/*/package_manifest.json` | 15 个包，合计 19 个目标数据集；状态包含 generated、partial 和 blocked |
| 来源证据 | `source_evidence.csv`、`export_partitions.csv`、各包 `row_map.csv` 与 `row_audit.jsonl` | 已存在 dataset、file、reaction 和 target 多级映射，但链接需要从可变 `main` 改为固定 revision |
| 当前体量 | `dataset/processing`、`standardized`、`reports` | 约 42GB；其中 `_needs_review` 约 14GB，不能直接塞入普通 Git object |

规划时上游远端为 `https://github.com/open-reaction-database/ord-data.git`。本地 `ord-data/data/` 与 `origin/main` 无差异，审计到的 `origin/main` revision 为 `83f971f586f6ad18f358ae4ae99d045e94ed2066`；实际发布必须重新验证 53 个源文件哈希后再锁定 release 使用的 revision，不能盲目沿用本文中的快照值。

### 1.2 当前三层产物口径

| 层 | 当前数量 | 定位 | 发布角色 |
|---|---:|---|---|
| 物理转换层 | 53 个 CSV / 2,428,291 行 | `standardized/csv-data/` | 中间层；保持与 53 个源 Parquet 一一对应 |
| 逻辑全量层 | 41 个 CSV / 2,428,291 行 | `standardized/derived/csv/tables/` | 最终语料层；保留全部 Reaction，不因建模资格而删行 |
| 建模目标层 | 15 个 package / 19 个 target | `processing/derived/yonod/datasets/` | 最终建模层；每个 target 独立公布 included/excluded 和状态 |

“最终”只表示它在对应处理层中是权威输出，不等于所有 target 都已经通过建模验收。`wave_d_generated_partial` 与 `research_full_standardized_benchmark_blocked` 必须在目录卡片、catalog 和 release notes 中显著标识。

## 二、开源许可结论与发布条件

### 2.1 结论

结论为：**支持二次处理并重新上传**。

`ord-data/LICENSE` 是 CC BY-SA 4.0。该许可明确允许复制和公开分享原许可材料，也允许制作、复制和公开分享改编材料；对数据库权利还明确允许提取、再利用、复制和分享全部或实质部分。因此，将 ORD 数据转换为 CSV、做逻辑归并、字段投影、标签规范化并公开发布，属于许可允许的使用。

允许发布不等于无条件发布。新项目必须同时满足：

1. 保留合理署名、版权与免责声明信息，并提供原材料 URI、CC BY-SA 4.0 名称及许可链接。
2. 明确标记做过转换、归并、规范化、筛选、排除或字段派生，并保留此前修改说明。
3. 对构成 ORD 数据改编材料或改编数据库的发布物采用 CC BY-SA 4.0 或 BY-SA 兼容许可，不能附加更严格的下游限制或技术措施。
4. 每个数据集均能追溯到固定 revision 的 ORD 源文件，而不只链接论文 DOI 或仓库 `main` 分支。
5. 代码与数据分开授权：处理脚本沿用/采用 Apache-2.0；数据、数据派生元数据、数据卡和含实质数据内容的中间文件采用 CC BY-SA 4.0。
6. CC 许可只覆盖许可人有权授予的版权及相似权利，不授予专利、商标、隐私等权利。凡是从 ORD 之外引入的论文 PDF、补充材料、第三方数据、模型权重、图片或软件，必须单独审计，不能借用 ORD 的 CC BY-SA 声明直接发布。

这是一项基于仓库现有许可文本的工程合规判断，不替代特定司法辖区的法律意见。

### 2.2 目标仓库的许可布局

实现阶段应建立清晰的多许可边界：

- `LICENSE-DATA`：CC BY-SA 4.0 完整文本，覆盖 `datasets/`、数据派生的 `intermediate/`、`provenance/` 中的数据与数据元数据。
- `LICENSE-CODE`：Apache-2.0 完整文本，覆盖 `pipeline/` 中自有或从 ORD Apache 代码演化的脚本、测试和工作流。
- `NOTICE`：列出 Open Reaction Database、固定源 revision、原仓库链接、修改概述、无背书声明和本项目维护者。
- `LICENSES/` 或等价机器可读目录：保存全部第三方许可文本；`artifact_inventory.csv` 为每个文件记录 `license_id` 与 `copyright_notice`。
- `CITATION.cff`：同时给出本项目 citation、ORD citation、固定源版本和各数据集 DOI/上游来源。

### 2.3 许可发布闸门

任何文件只有在 `artifact_inventory.csv` 同时具备 `origin`、`license_id`、`redistribution_status`、`sha256` 和 `disposition` 后才可进入上传清单。以下情况必须阻止公开发布：许可未知、包含未授权第三方整文件、包含密钥/token、包含不必要的个人邮箱或其他敏感信息、声明许可证与目录实际内容冲突。

## 三、项目范围

### 3.1 必须包含

1. 覆盖全部 53 个物理 ORD 数据集的 41 个语义化逻辑全量数据集。
2. 当前 15 个建模 package 中的 19 个 target 数据集，以及每个 target 的 schema、配置、排除记录、row map、审计和状态。
3. 从物理 CSV、来源扫描、逻辑归并、字段分析、模型投影、目标适配、验证到报告的每一步可发布中间产物。
4. 可独立运行的处理框架：脚本、测试、schema、policy、配置模板、依赖锁定、命令入口和流程文档。
5. 文件级、数据集级、转换步骤级和行级 lineage；所有 53 个源 Parquet 的固定版本链接。
6. 完整清单、哈希、体量、行数、状态、许可、旧路径到新路径映射，以及 release 验收报告。

### 3.2 不直接上传但必须可追溯

- `ord-data/data/**/*.parquet` 原始源文件。
- 论文正文、付费补充材料或外部网站整文件。
- 可从明确来源重新安装的依赖包与容器层。

### 3.3 默认排除

- `.git/`、`.venv/`、`venv/`、`__pycache__/`、`.pytest_cache/`、`.ruff_cache/`。
- `.env`、token、cookie、credential、SSH key、带凭证 URL。
- 运行锁、PID、临时下载、损坏文件、纯缓存和可无损重建的重复对象；排除必须在清单中记录理由和替代来源。
- YONOD 模型权重与纯建模实验结果默认不属于数据发布核心；仅保留证明数据生成与验证所必需的配置、指标和审计。若用户随后要求完整模型归档，另立范围与许可审计。

## 四、目标目录契约

```text
ord-datasets/
├── README.md
├── CITATION.cff
├── NOTICE
├── LICENSE-DATA
├── LICENSE-CODE
├── LICENSES/
├── datasets/
│   ├── catalog.csv
│   ├── catalog.json
│   ├── corpus/
│   │   └── <semantic-dataset-slug>/
│   │       ├── reactions.csv
│   │       ├── metadata.json
│   │       ├── source-links.json
│   │       ├── schema.json
│   │       └── checksums.sha256
│   └── model-ready/
│       └── <semantic-target-slug>/
│           ├── dataset.csv
│           ├── metadata.json
│           ├── schema.json
│           ├── yonod-config.json
│           ├── exclusions.csv
│           ├── row-map.csv
│           ├── audit.jsonl
│           └── checksums.sha256
├── intermediate/
│   ├── 00-snapshot-inventory/
│   ├── 01-physical-csv/
│   ├── 02-source-evidence/
│   ├── 03-logical-assembly/
│   ├── 04-field-profiling/
│   ├── 05-model-projection/
│   ├── 06-target-adaptation/
│   ├── 07-validation-configs/
│   ├── 08-runs-and-reports/
│   └── 90-legacy-needs-review/
├── pipeline/
│   ├── scripts/
│   ├── tests/
│   ├── policies/
│   ├── schemas/
│   ├── configs/
│   ├── workflows/
│   ├── pyproject.toml
│   ├── uv.lock
│   └── README.md
├── provenance/
│   ├── source-files.csv
│   ├── physical-datasets.csv
│   ├── logical-datasets.csv
│   ├── logical-dataset-members.csv
│   ├── target-datasets.csv
│   ├── source-evidence.csv
│   ├── artifact-inventory.csv
│   ├── artifact-path-map.csv
│   ├── transformations.jsonl
│   ├── lineage-edges.csv
│   └── release-manifest.json
├── reports/
│   ├── data-quality/
│   ├── license-audit/
│   └── release-acceptance/
└── project-docs/
    └── goal.md
```

同一大文件不得为了满足多个视图而物理复制多份。最终目录、intermediate 与 provenance 之间优先通过 catalog/manifest 引用同一对象；如果发布后端不支持链接，则生成分片 release bundle，并以对象哈希和路径映射恢复逻辑目录。

## 五、语义化命名契约

### 5.1 命名规则

- 目录 slug 使用小写 ASCII kebab-case，表达 `reaction/source/topic + target/measurement + optional publication key`；不得只使用 UUID 或 `physical_<id>`。
- 机器身份不依赖名称：每个目录的 `metadata.json` 必须保存 `dataset_slug`、`display_name`、`logical_dataset_id`、全部 `physical_dataset_id`、`target_id`（如有）和 `name_policy_version`。
- 多物理成员属于同一文献/上游源时，以逻辑数据集作为一个 corpus 目录，成员不重复发布；各物理成员仍完整列入 source links。
- 名称冲突时追加稳定而有含义的 DOI key、上游来源 key 或 8 位物理 ID 后缀；不得用运行时哈希决定名称。
- 改名通过 `aliases` 保持向后兼容；release 后改变既有 slug 视为破坏性版本变更。
- 中文可作为 `display_name_zh`，目录名和机器主键保持跨平台安全的英文/数字格式。

### 5.2 corpus 命名

41 个逻辑全量数据集必须全部出现在 `datasets/catalog.csv` 的 `artifact_class=corpus` 行中。语义名称从 `datasets.csv` 的 name/description、逻辑关系和可靠 DOI/上游来源共同生成；例如：

- `shields-arylation-nature-2021`
- `cernak-miniaturized-reactions-nature-synthesis-2023`
- `reizman-suzuki-cross-coupling-rce-2016`
- `uspto-grants-1976-present`
- `roche-surf-borylation`

这些只是命名规则示例。正式映射必须由人工审阅后写入 `semantic-name-map.csv`，并验证 41 个 logical ID 一对一映射、53 个 physical ID 全覆盖。

### 5.3 当前 15 个包 / 19 个 target 的语义发布基线

| logical package | target（发布时转为 kebab-case slug） | 当前状态 |
|---|---|---|
| `lit_10_1038_s41586_021_03213_y` | `shields_yield_percent` | `wave_a_generated` |
| `lit_10_1038_s44160_023_00351_1` | `cernak_member_2be11_conversion_percent`；`cernak_member_3b8a2e_conversion_percent` | `wave_c_generated` |
| `lit_10_1126_science_1259203` | `science_hte_diverse_nucleophile_relative_lc_area_ratio` | `wave_d_generated_partial` |
| `physical_1ec2807f02fa4beda27d2a81b86eb843` | `catechol_product_2_yield_percent`；`catechol_product_3_yield_percent`；`catechol_total_product_yield_percent` | `research_full_standardized_benchmark_blocked` |
| `physical_46ff9a32d9e04016b9380b1b1ef949c3` | `ahneman_yield_percent` | `wave_a_generated` |
| `physical_5c9a10329a8a48968d18879a48bb8ab2` | `chan_lam_yield_percent` | `wave_b_generated` |
| `physical_68cb8b4b2b384e3d85b5b1efae58b203` | `suzuki_yield_percent` | `wave_a_generated` |
| `physical_805ad863feef48579d95d86a728035f4` | `c_n_yield_percent` | `wave_b_generated` |
| `physical_99c23cf435dc42f1af884053bc8b11c7` | `roche_borylation_yield_percent` | `wave_b_generated` |
| `physical_9b8aa9a7835143ef8ce3f70abfab7545` | `nicolit_yield_percent` | `wave_c_generated` |
| `physical_ac78456835404910b3a4c840248b6ac9` | `nano_yield_percent` | `wave_a_generated` |
| `physical_b440f8c90b6343189093770060fc4098` | `photodehalogenation_conversion_percent` | `wave_a_generated` |
| `physical_c5b00523487a4211a194160edf45e9ab` | `asymmetric_alkylation_ee_s_minus_r_percent` | `wave_d_generated` |
| `physical_d92976309c3a48a3a64a4cf5e7048086` | `pfizer_lcms_area_percent` | `wave_c_generated` |
| `upstream_chemrxiv_64c7e2e1658ec5f7e5808425` | `chemrxiv_amide_yield_percent`；`chemrxiv_ch_arylation_yield_percent` | `wave_a_generated` |

发布脚本不能把 `yield`、`conversion`、`LCMS area`、`relative LC area ratio`、`ee` 合并成无语义的 `y`；目录、schema 和 catalog 均需保留测量语义及量纲。

## 六、中间处理资产的归档规则

| 当前来源 | 目标角色 | 处理要求 |
|---|---|---|
| `dataset/standardized/csv-data/` | `intermediate/01-physical-csv/` | 保留 53 个物理 CSV、`datasets.csv`、原路径、行数和哈希 |
| `dataset/processing/derived/csv/manifests/` | `intermediate/02-source-evidence/` 与 `provenance/` | 保留来源证据、逻辑成员、归并决策、分区和验证清单 |
| `dataset/standardized/derived/csv/tables/` | `datasets/corpus/` | 重命名到 41 个语义目录；保留原 logical ID 和 output hash |
| `dataset/standardized/derived/csv/schema/` | `pipeline/schemas/` 与 `reports/data-quality/` | 区分可执行 schema、字段覆盖统计和比较报告 |
| `dataset/processing/derived/yonod/inventory/` | `intermediate/04-field-profiling/` | 保留 scope、cardinality、field profile 和选集依据 |
| `dataset/processing/derived/yonod/datasets/` | `datasets/model-ready/` + `intermediate/05-06/` | 数据与 schema 进入 target 目录；projection、audit、exclusion、row map 和 package manifest 保真归档 |
| `dataset/processing/derived/yonod/{formal_configs,extended_formal_configs,testsets}/` | `intermediate/07-validation-configs/` | 保留配置生成、sample100 和正式配置，标明是否最终采用 |
| `dataset/processing/derived/yonod/runs/`、`dataset/reports/` | `intermediate/08-runs-and-reports/` 与 `reports/` | 只保留数据生成/验收必需内容；大模型产物另行审计 |
| `dataset/processing/scripts/` | `pipeline/scripts/`、`pipeline/tests/` | 去除 cache；修复硬编码路径；保留来源 commit 与 Apache notice |
| `dataset/processing/migration/` | `intermediate/00-snapshot-inventory/` | 作为旧工作区到新项目的证据基线 |
| `dataset/processing/_needs_review/` | `intermediate/90-legacy-needs-review/` | 约 14GB；逐文件判定，默认隔离，不计入 authoritative dataset |

必须生成 `artifact-path-map.csv`，至少包含 `old_path,new_path,artifact_class,step_id,status,sha256,size_bytes,license_id,reason`。`dataset/` 范围内每个文件都必须有且只有一个处置记录；缓存也要以规则汇总登记，不能靠人工口头说明。

## 七、整体处理框架

```mermaid
flowchart LR
    A[固定 ORD revision 与 53 个源文件链接] --> B[53 个物理 CSV]
    B --> C[来源证据扫描与许可/PII 审计]
    C --> D[53 physical → 41 logical 非破坏归并]
    D --> E[41 个全量 single-row corpus]
    E --> F[字段覆盖与 model projection]
    F --> G[15 package / 19 target 适配与规范化]
    G --> H[排除、row map、schema、配置和样本验证]
    H --> I[release catalog、哈希、报告与上传]
```

框架必须满足：

- 单一命令或声明式任务图可从 source manifest 重建指定数据集，也能执行全量 release。
- 每一步有稳定 `step_id`、输入/输出契约、policy/schema 版本、幂等规则、失败状态和恢复方式。
- 大文件按 Parquet row group、CSV chunk 或数据集分片流式处理；禁止为方便打包而一次性载入 2,428,291 条完整 Reaction。
- 所有路径相对仓库根目录，不依赖 `/home/wangzh685/...` 绝对路径。
- 依赖版本至少锁定 Python、`ord-schema`（当前 manifest 为 0.8.3）、protobuf、pyarrow/pandas 或实际实现所用库，以及 YONOD 接口版本。
- 同一输入 revision、source hash、policy/schema version 和配置必须生成相同稳定键、行顺序与内容哈希。
- pipeline 的测试必须覆盖许可清单、计数守恒、逻辑成员唯一性、row map、源链接、schema、语义命名冲突、幂等和小样本端到端重建。

## 八、溯源契约

### 8.1 源文件级

`provenance/source-files.csv` 必须恰有 53 个生效物理源记录，至少包含：

`source_file_id, physical_dataset_id, upstream_repo_url, upstream_revision, upstream_path, source_file_url, direct_download_url, source_sha256, git_lfs_oid, size_bytes, reaction_count, dataset_name, dataset_description, data_license_id, retrieved_at, link_checked_at, verification_status`

其中：

- `source_file_url` 使用不可变 commit，例如 `https://github.com/open-reaction-database/ord-data/blob/<commit>/data/68/ord_dataset-...parquet`，禁止只写 `/blob/main/`。
- `direct_download_url` 可指向 GitHub LFS 或 Hugging Face mirror，但必须记录其自身 revision/etag/oid 并在 release CI 实际下载小样本或 HEAD/范围请求验证；镜像不能取代 GitHub authoritative path。
- DOI/论文 URL 另存为 publication evidence，不能代替 ORD 数据文件链接。
- 多物理成员的 logical/target 数据集必须列出全部源文件链接，不能只展示第一个成员。

### 8.2 数据集级

- `physical-datasets.csv`：53 个物理 ID、源路径、name/description、行数、hash。
- `logical-datasets.csv` 与 `logical-dataset-members.csv`：41 个 logical ID、53 个 membership、关系、证据、规则版本和计数。
- `target-datasets.csv`：15 个 package、19 个 target、测量语义、included/excluded、状态、输出路径和 source set。
- `catalog.csv/json`：面向用户的 semantic slug/display name，同时链接上述机器清单。

### 8.3 行级

- corpus 每行至少保留 `physical_dataset_id,source_file,reaction_id,row_index`；当前 41 个逻辑表已经具备这些字段。
- target 的 `row-map.csv` 至少保留 `csv_row_number,reaction_key,physical_dataset_id,source_row_index,label_decision_id`；通过 `physical_dataset_id + source_row_index/reaction_id` 回到原 Parquet。
- excluded 行同样必须可回溯，且提供机器可读 exclusion reason；不能只为 included 行建立 lineage。
- 不必额外复制一份 2.4M 行的全局 row map；允许 catalog 指向每个 corpus/target 自带映射，但所有映射必须纳入 release hash tree。

### 8.4 转换与文件级

- `transformations.jsonl`：每次步骤记录 step ID、工具 commit、命令、配置 hash、输入/输出 artifact ID、开始/结束时间、依赖版本、状态和错误。
- `lineage-edges.csv`：以 artifact hash 为节点，显式表达 `source → physical CSV → logical corpus → model projection → target dataset`。
- `artifact-inventory.csv`：覆盖最终文件、中间文件、脚本、报告、排除对象和外部链接；每个可上传对象有完整 SHA-256。
- `release-manifest.json`：固定 release ID、项目 commit、ORD revision、计数、总字节、文件数、root hash、许可 policy 和所有子 manifest hash。

用户从任一 `dataset.csv` 的任一行出发，最多经过 `row-map/metadata → physical_dataset_id → source-files.csv` 两跳即可得到原 ORD Parquet 的固定链接、源路径、哈希与原始 reaction 标识。

## 九、执行任务包

### WP0：冻结输入与建立零遗漏盘点

- 只读冻结 `ord-data` revision、53 个源文件 hash/LFS oid、`dataset/` 快照与当前处理 policy 版本。
- 扫描全部文件，生成大小、hash、类型、旧路径、来源、许可候选和处置候选。
- 输出：snapshot manifest、artifact inventory 初版、体量/存储预算报告。
- 闸门：53 个源文件和 `dataset/` 全部对象可对账，无未解释扫描错误。

### WP1：许可、敏感信息与第三方资产审计

- 建立 data/code/docs/third-party 多许可边界，生成 NOTICE 与 attribution 模板。
- 扫描 credentials、`.env`、个人邮箱、论文/补充材料、权重和未知二进制。
- 输出：license inventory、publish/quarantine/exclude 决策、风险清单。
- 闸门：任何 `unknown` 或 `restricted` 对象不得进入 upload manifest。

### WP2：语义命名与 catalog

- 为 41 个 corpus 和 19 个 target 生成并人工审阅 semantic slug、display name、aliases。
- 生成 old path、physical/logical/target ID 到新目录的稳定映射。
- 输出：`semantic-name-map.csv`、catalog 初版。
- 闸门：41 corpus 一对一、19 target 一对一、53 physical 全覆盖，slug 无冲突。

### WP3：构建最终 datasets 层

- 将 41 个逻辑 CSV重组到 `datasets/corpus/`；将 19 个目标文件及其必要配套材料重组到 `datasets/model-ready/`。
- 不改变 CSV 数据内容；若仅重命名/移动，hash 必须与基线一致。若规范格式发生变化，须作为新 transformation 并重新验收。
- 输出：per-dataset metadata、source-links、schema、checksums。
- 闸门：行数、键、输出 hash、included/excluded 与原 manifest 一致；partial/blocked 状态未被抹除。

### WP4：归档每一步 intermediate

- 按 00–08 阶段整理现有中间文件，保留命令、配置、日志、审计和验证上下文。
- 对 `_needs_review` 做 hash 去重和逐文件处置；如不进入首发，发布其 manifest 与排除理由，原件保留在隔离 release 或后续版本。
- 输出：分阶段中间资产、old→new path map。
- 闸门：`dataset/` 每个对象都有 disposition，且 authoritative、superseded、quarantined 不混淆。

### WP5：抽取可复现 pipeline

- 从 `dataset/processing/scripts/` 抽取生产脚本与测试，清理 cache 和绝对路径，补统一 CLI/任务图。
- 固化 schemas、policies、configs、依赖锁与最小/全量运行说明。
- 输出：`pipeline/`、单元测试、端到端 smoke fixture。
- 闸门：在干净环境可从一个固定源文件链接生成对应 physical CSV、logical 表和至少一个 target，hash 可复核。

### WP6：建立完整 provenance graph

- 生成 53 条源记录、41 条逻辑记录、53 条 membership、15 package/19 target 记录、转换边和 per-target row map 索引。
- 将所有 `/blob/main/` 来源改为固定 commit；验证链接与 source hash。
- 输出：`provenance/` 全部契约文件和 lineage 查询示例。
- 闸门：随机抽样与边界样本均能从最终行回到源 Parquet 固定 URL；孤儿/多重映射为 0。

### WP7：大文件与发布工程

- 依据约 42GB 基线选择后端。默认方案是同一 `ord-datasets` 项目中，小文件进入普通 Git，大 CSV/JSONL/归档进入 Git LFS；上传前验证配额、单文件限制和 clone 行为。
- 若 GitHub LFS 额度不足，项目 Git 仓库保持 authoritative catalog/pipeline，数据对象使用同名 Hugging Face dataset 或版本化对象存储；manifest 必须使其仍表现为一个可验证 release，不能用未固定的外链代替版本管理。
- 大对象按数据集或不超过后端限制的分片发布，支持断点续传和独立校验；不以一个 42GB 单体 zip 作为唯一交付。
- 输出：`.gitattributes`/上传配置、storage manifest、release bundle 方案。
- 闸门：从全新 checkout/下载路径可恢复目录，所有 LFS/object 指针均有可取回对象。

### WP8：发布前验收

- 执行计数守恒、schema、JSON、hash、link、license、secret、PII、路径大小写、跨平台文件名和重跑一致性检查。
- 生成机器可读与 Markdown acceptance report。
- 闸门：所有阻断项为 0；已知 partial/blocked 只作为数据状态存在，不被错误声明为 benchmark accepted。

### WP9：上传、发布与回读验证

- 经用户确认远端、版本和存储后再上传；创建不可变 tag/release，记录项目 commit 与 ORD revision。
- 从无本地缓存环境回读 catalog、随机小数据集、最大数据集分片和至少一个完整 lineage。
- 输出：公开仓库/release 地址、下载说明、校验报告、回滚/撤回说明。
- 闸门：远端内容与本地 release root hash 一致，链接公开可访问，许可与 citation 页面可见。

## 十、总体验收标准

1. `datasets/corpus/` 恰有 41 个语义数据集，覆盖 53 个 physical ID 和 2,428,291 条 Reaction；不增行、不漏行，每个 physical ID 恰属一个生效 logical dataset。
2. `datasets/model-ready/` 恰有当前清单中的 19 个 target；15 个 package 的 target status、included/excluded 数、label 语义和输出 hash 可与原 package manifest 对账。
3. 53 个物理源文件均有固定 revision 的 `source_file_url`、source path、hash/LFS oid 和 reaction count；不存在仅指向 `main` 或仅给 DOI 的源记录。
4. 任一最终行能在两跳内定位原 ORD 文件和原 reaction；included、excluded、多成员 logical dataset 均通过抽样与自动化验证。
5. `dataset/` 中所有现有文件有 disposition；authoritative、intermediate、superseded、quarantined、excluded 数量和字节合计与冻结快照守恒。
6. data/metadata 使用 CC BY-SA 4.0，代码使用 Apache-2.0；署名、修改说明、许可链接、NOTICE、citation 和第三方许可清单完整，无附加下游限制。
7. 无 secret、credential、环境文件、缓存、无必要个人信息或权利不明整文件进入 upload manifest。
8. 每个上传文件有 SHA-256，release manifest 有总文件数、总字节和 root hash；远端回读校验一致。
9. pipeline 在干净环境通过单元测试和小样本端到端测试；全量结果能由固定输入、版本化 policy/schema 和命令重建。
10. README 清楚解释三层数据口径、19 个 target 的测量语义、partial/blocked 状态、下载方式、磁盘需求、许可证、citation 和溯源示例。

## 十一、主要风险与默认处置

| 风险 | 默认处置 |
|---|---|
| 约 42GB 超出普通 Git/平台额度 | 大文件不得进入普通 Git；WP7 先做配额和回读试验，再全量上传 |
| `_needs_review` 约 14GB 且可能重复/过时 | 先隔离、去重和登记状态；未审完不进入 authoritative release |
| 现有 target manifest 使用 `/blob/main/` | 发布前统一替换为经 hash 验证的固定 commit URL |
| 本地 `ord-data` HEAD 含非上游提交 | source revision 以可公开访问且 hash 匹配的上游 commit 为准，不使用不可访问的本地 commit 作为唯一来源 |
| 数据与代码许可混淆 | 采用 `LICENSE-DATA`/`LICENSE-CODE`、目录级说明和逐文件 license inventory |
| 外部论文/补充材料被误当 ORD 数据 | 只保留 DOI/URL；整文件进入第三方许可闸门 |
| partial/blocked target 被误称完成 | status 进入目录名之外的显著 metadata、catalog 和 release notes；验收只检查忠实发布，不篡改状态 |
| 语义改名破坏旧引用 | 保留 logical/physical/target ID、旧路径、aliases；名称 policy 版本化 |
| 大表重复拷贝造成存储膨胀 | 内容寻址、manifest 引用和按对象一次存储；发布 bundle 提供逻辑路径恢复 |

## 十二、完成边界

本 creator 阶段完成条件仅为：许可结论有证据、项目范围与目录契约明确、任务包与验收标准可执行、目标文档提交到新的 `ord-datasets` Git 仓库。数据搬运、脚本改造、大文件配置、远端创建和上传均属于后续 builder 阶段，不在本轮执行。
