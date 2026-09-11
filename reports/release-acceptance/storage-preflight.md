# ord-datasets 存储容量与后端预评估

- 步骤：05
- 评估日期：2026-09-11
- 状态：存储决策提案；未创建远端、未上传对象、未产生外部费用
- 输入：`provenance/artifact-inventory.csv`
- 输入 SHA-256：`5f12f84351a860121a4ad191cece809de01f992dac00cee453d155655cdb9dcc`
- 机器可读配套：`storage-preflight.json`

## 决策结论

采用“单一逻辑项目、控制面与数据面分离”的发布提案：

1. **GitHub regular Git 作为控制面**：只保存代码、测试、文档、许可证、schema、配置、小型 catalog、provenance、checksums 和固定 revision 的数据面引用。
2. **Hugging Face Dataset 仓库作为首选数据面候选**：保存经过许可与敏感信息审计的不可变数据对象；最终 release manifest 同时固定 GitHub commit 与 Hugging Face commit。
3. **版本化 S3-compatible object storage 作为后备数据面候选**：若 Hugging Face 账户容量、公共数据政策或 pilot 不通过，则使用版本化对象 key、内容 SHA-256 和 GitHub 控制面 manifest 保持同一可验证 release。
4. **不采用 GitHub LFS 作为主数据面**：当前两个核心对象分别约 9.59 GiB 和 9.40 GiB，未经分片即超过所有 GitHub LFS 方案的单文件上限；即使分片，LFS 历史版本和下载流量仍计入仓库所有者用量。

该结论只决定后续实现方向，不授权 pilot 或正式上传。步骤 25 的远端 pilot 和步骤 28～29 的发布仍需分别满足计划闸门与用户授权。

## 冻结体量

| 范围 | 文件路径数 | 去重对象数 | 逻辑字节 | 去重字节 | 精确重复可省 |
|---|---:|---:|---:|---:|---:|
| 核心发布候选：`authoritative + intermediate` | 482 | 442 | 29,297,599,140（27.285515 GiB） | 29,297,543,018（27.285463 GiB） | 56,122 B |
| 审计后最大潜在范围：再含 `quarantined` | 4,337 | 3,566 | 44,375,292,071（41.327711 GiB） | 30,961,331,025（28.834987 GiB） | 13,413,961,046 B |
| 全部冻结文件：再含 `excluded + superseded` | 4,349 | 3,578 | 44,375,572,307（41.327972 GiB） | 30,961,611,261（28.835248 GiB） | 13,413,961,046 B |

潜在范围的逻辑体量比核心大约 14.0 GiB，但按 SHA-256 去重后的增量仅约 1.55 GiB。这说明 `_needs_review` 中存在大量权威对象的逐字节副本；后续只能记录 alias/canonical 关系，不能为了保留两个视图而再次物理存储同一内容。

存储可行性不能改变 disposition。当前 3,855 个 quarantined 文件仍禁止上传，只有完成许可、secret/PII、相关性与重复审计后才能提升。

## 最大对象与平台阈值

核心 442 个去重对象中：

- 48 个大于内部 regular-Git 上限 10 MiB；
- 19 个大于 GitHub 50 MiB warning；
- 14 个大于 GitHub regular Git 的 100 MiB hard block，总计 28,052,141,562 字节；
- 5 个大于 1 GiB；
- 2 个同时大于 GitHub LFS Free/Pro 2 GB、Team 4 GB 与 Enterprise Cloud 5 GB 上限；
- 0 个大于 Hugging Face 建议的 200 GB 文件规模。

| 排名 | 当前角色 | 旧路径 | 字节 | GiB |
|---:|---|---|---:|---:|
| 1 | corpus authoritative | `standardized/derived/csv/tables/logical_dataset_id=physical_1158e351757f315b93cbcbe7bc55f38e/reactions.csv` | 10,297,606,246 | 9.590393 |
| 2 | physical CSV intermediate | `standardized/csv-data/11/ord_dataset-1158e351757f315b93cbcbe7bc55f38e.csv` | 10,096,819,666 | 9.403396 |
| 3 | corpus authoritative | `standardized/derived/csv/tables/logical_dataset_id=upstream_rexgen_direct_c8sc04228d/reactions.csv` | 1,541,933,724 | 1.436038 |
| 4 | source evidence intermediate | `processing/derived/csv/manifests/source_evidence.csv` | 1,425,933,595 | 1.328004 |
| 5 | physical CSV intermediate | `standardized/csv-data/e7/ord_dataset-e7830cd6b11158b43994ccfb5ee9acb3.csv` | 1,270,272,656 | 1.183034 |

## 后端比较

### 普通 Git / GitHub

GitHub 会警告超过 50 MiB 的文件并阻止超过 100 MiB 的文件；官方建议仓库最好小于 1 GB，并强烈建议小于 5 GB。当前文档还给出 10 GB on-disk `.git` 建议上限与 2 GB push hard limit。核心发布面有 14 个对象直接触发 100 MiB block，且数据总量远超健康仓库建议，因此普通 Git **不适合作为数据面**。

内部策略进一步收紧为：

- regular Git 单文件最多 10 MiB；
- `datasets/**/reactions.csv`、`datasets/**/dataset.csv`、物理 CSV、行级 audit/source-evidence 即使小于 10 MiB 也走数据面；
- 控制面只保存可审阅、可 diff、可快速 clone 的小对象和数据对象引用。

官方依据：[GitHub large files](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github)、[GitHub repository limits](https://docs.github.com/en/repositories/creating-and-managing-repositories/repository-limits)。

### GitHub LFS

GitHub LFS 的单文件上限按方案分别为 Free/Pro 2 GB、Team 4 GB、Enterprise Cloud 5 GB。Free/Pro 每月含 10 GiB storage 与 10 GiB download bandwidth，Team/Enterprise 各含 250 GiB；额外用量的官方 calculator 当前估值为 storage $0.07/GiB-month、download $0.0875/GiB。LFS 每次修改会计入一份完整新对象，下载与 GitHub Actions fetch 计入仓库所有者 bandwidth。

即使先按 1 GiB 分片，Free 方案下按 27.285463 GiB 核心去重体量估算：

- 月存储超额 17.285463 GiB，约 $1.21/月；
- 每个 billing cycle 第一次完整下载约产生 $1.5125 超额；
- 当 10 GiB 免费带宽已用完后，每次额外完整下载约 $2.3875；
- 以上不含历史版本、账户已有用量和方案订阅。

LFS 技术上可在分片后使用，但不作为主数据面。官方依据：[Git LFS file limits](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-git-large-file-storage)、[Git LFS billing](https://docs.github.com/en/billing/concepts/product-billing/git-lfs)、[GitHub pricing calculator](https://github.com/pricing/calculator?feature=lfs)。

### Hugging Face Dataset 仓库

官方当前将 Free 用户/组织的公共存储标为 best-effort，私人存储为 100 GB；公共数据的首个付费 add-on 为 1 TB、$12/月。Git-backed repository 建议少于 100,000 个文件、每目录少于 10,000 entries、文件小于 200 GB，单文件 hard limit 为 500 GB；HTTP 上传建议单 commit 少于 100 个文件。

当前核心或最大潜在范围均满足结构阈值：

- 核心去重对象 442；按 1 GiB 分片后 463；
- 最大潜在文件路径 4,337，远小于 100,000；
- 当前 planned path 中最宽目录为 32 个文件，远小于 10,000；
- 最大对象 9.590393 GiB，远小于 200 GB 建议值。

因此 Hugging Face 是首选公共数据面候选，但 Free public storage 没有容量保证。步骤 25 必须先确认账户/组织方案、dataset card 要求、公共复用目的和一次完整大对象回读。官方依据：[Hugging Face storage limits](https://huggingface.co/docs/hub/storage-limits)。

### 版本化对象存储

以 Amazon S3 Standard、US East (N. Virginia) 第一档 $0.023/decimal-GB-month 作为**代表性、非报价**估算：

- 核心 29.297543 decimal GB 去重对象约 $0.6738/月；
- 最大潜在 30.961331 decimal GB 去重对象约 $0.7121/月；
- request、对象历史版本、跨区域复制与 egress 未计入；
- AWS 当前说明除 China/GovCloud 外，跨 AWS 服务和区域聚合的前 100 GB/月公网流出免费；实际区域与账户现有用量必须在 pilot 时重新计算。

对象存储天然适合 immutable version ID、Range GET 和 content-addressed key，是 Hugging Face 不可用时的后备方案。官方依据：[Amazon S3 pricing](https://aws.amazon.com/s3/pricing/)、[AWS calculator assumptions](https://aws.amazon.com/calculator/calculator-assumptions/)。

## 去重与分片设计

1. 数据对象以 SHA-256 为物理身份，`datasets/`、`intermediate/` 和 provenance 中的多个逻辑视图只记录路径映射，不重复保存相同 hash。
2. 默认最大 shard 为 1 GiB，兼容 GitHub Free LFS 的 2 GB 单文件上限，并降低失败重传成本。
3. 核心 442 个去重对象中 5 个需要分片；分片后为 463 个物理对象，即增加 21 个 shard。
4. 表格优先在 CSV 行边界切分，每片重复 header，并记录 row range、row count、byte count 和 shard SHA-256。
5. 只有用于“逐字节恢复原逻辑文件”的 bundle 才使用 byte shard；shard manifest 必须记录顺序和完整文件 SHA-256。
6. clean-room 验收必须重组逻辑文件并得到与步骤 03/04 相同的 SHA-256。仅校验每个 shard 不足以证明原逻辑文件可恢复。

## Clone、下载与回读模式

- **默认 clone**：只 clone GitHub 控制面，不自动获取 27 GiB 数据。
- **按数据集下载**：从 release manifest 选择一个 semantic corpus 或 target，解析固定 Hugging Face commit / object version，下载后验证 size 与 SHA-256。
- **完整 release**：把全部唯一对象下载到干净的内容寻址 cache，再依据 path map 建立逻辑目录；相同 hash 复用一个对象。
- **CI**：普通 PR 只跑 manifest/schema/small-sample；发布候选在专用 full-data job 中重组并验证 hash tree。
- **pilot**：至少覆盖一个大于 5 GB 的逻辑文件或其全部 shards、一个小型 model-ready 七件套、一次 manifest-only clone 和一次无缓存回读。

## 后续阻塞条件

以下条件满足前，不得提升大对象或上传：

1. 步骤 06 完成文件级许可与第三方边界；`NOASSERTION` 对象不得进入数据面。
2. 步骤 07 完成 secret、PII、危险路径与外部整文件扫描。
3. 步骤 08～10 冻结语义名称、catalog、metadata 与 schema，消除 `_pending-semantic-name`。
4. 步骤 18 完成 quarantined 对象的逐项审计和 hash alias 去重。
5. 步骤 25 对选定账户与后端执行获准 pilot，并回读验证。
6. 步骤 28 获得正式发布授权；本报告不构成授权。

## 资料检查时间

所有平台限制与价格资料于 2026-09-11 回读。价格只是工程预估，实际账单取决于地区、方案、既有用量、历史版本、请求与流量；执行 pilot 前必须重新验证。
