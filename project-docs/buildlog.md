# ord-datasets 构建日志

## [2026-09-11 22:05 CST] 步骤 01 完成：创建最小项目骨架与安全边界

### 本步目标

按 `project-plan.md` 步骤 01 建立可由 Git 追踪的发布项目骨架，明确只读来源、可写范围、staging 规则和禁止隐式操作；本步不复制数据、不建立远端、不配置大文件后端。

### 已完成内容

- 创建根目录说明 `README.md`、安全边界 `SOURCE_BOUNDARIES.md` 和本地排除规则 `.gitignore`。
- 创建并追踪 `LICENSES/` 占位与许可边界说明；正式许可文本留待步骤 06。
- 创建 `datasets/corpus/` 与 `datasets/model-ready/`，明确完整语料与任务投影的不同契约。
- 创建 `intermediate/00-snapshot-inventory/` 至 `08-runs-and-reports/`，以及隔离的 `90-legacy-needs-review/`。
- 创建 `pipeline/{scripts,tests,policies,schemas,configs,workflows}/`，并声明所有 source/output root 必须参数化。
- 创建 `provenance/` 和 `reports/{data-quality,license-audit,release-acceptance}/`。
- 为暂时为空的叶目录加入小型 `.gitkeep`，未添加任何真实数据对象。

### 安全边界

- 同级 `../ord-data/` 与 `../dataset/` 被声明为只读输入。
- 所有临时构建必须进入被忽略的 `.staging/<release-id>/<step-id>/`。
- 明确禁止复制原始 ORD Parquet、未经授权上传、提交凭证/环境/cache、把 `_needs_review` 当作权威数据。
- 本步骤未修改 `project-docs/goal.md` 或 `project-docs/project-plan.md`。

### 验证证据

- `find . -maxdepth 3 -type d -not -path './.git*' -print`：目标顶层目录和全部计划叶目录均存在。
- `rg --files -g '*.parquet' -g '*.csv' -g '*.jsonl' -g '*.pb' -g '*.pb.gz' .`：退出码 1、无匹配，确认未复制数据文件。
- `rg -n '/home/|wangzh685' .gitignore SOURCE_BOUNDARIES.md README.md LICENSES datasets intermediate pipeline provenance reports`：退出码 1、无匹配，确认 operational scaffold 不含工作站绝对路径。
- `du -sh ...`：各目录为 8–88KB 的说明和占位文件，未出现大对象。
- `git check-ignore -v --no-index ...`：`.staging/`、`.tmp/`、`.env`、`.venv/` 正确忽略；`pipeline/configs/config.json` 未被误忽略。

### 产物状态

- 状态：`complete`
- 数据基线：未改变；仍以 53 physical、41 logical、2,428,291 reactions、15 packages、19 targets 为后续验收基线。
- 下一步：步骤 02——冻结 ORD 上游公开 revision，并生成 53 个源文件的初始 source manifest；不得直接沿用规划时 commit 而不复核 hash。

## [2026-09-11 22:13 CST] 步骤 02 完成：冻结 ORD 上游 revision

### 本步目标

在不复制原始 Parquet 的前提下，确认一个公开可访问、与本地 53 个物理 ORD 文件内容一致的上游 revision，并固化逐文件路径、URL、hash、LFS oid、大小、名称和 Reaction 数。

### 已完成内容

- 确认上游 remote 为 `https://github.com/open-reaction-database/ord-data.git`。
- 重新解析 `origin/main`，冻结 revision `83f971f586f6ad18f358ae4ae99d045e94ed2066`；没有直接信任计划书中的候选值。
- 通过 `git diff --quiet <revision> -- data` 和 `git status --short -- data` 确认本地 data tree 与该 revision 一致且无工作区修改。
- 将 `dataset/standardized/csv-data/datasets.csv` 的 53 条 catalog 记录与实际 `data/*/*.parquet`、`git lfs ls-files --long` 做集合对账。
- 流式计算 53 个 Parquet 的 SHA-256，并逐项验证其等于 Git LFS oid。
- 生成 `provenance/source-files.initial.csv`：包含 physical/source ID、remote、固定 revision、upstream path、commit-pinned GitHub URL、SHA-256、LFS oid、字节数、Reaction 数、名称/描述、许可和验证状态。
- 生成 `intermediate/00-snapshot-inventory/ord-source-snapshot.json`：保存聚合计数、总字节、manifest hash、许可和验证结论。
- `direct_download_url` 明确留空并标记延后到正式 provenance/release 步骤验证，避免把未经回读确认的镜像链接声明为生效来源。

### 验证证据

- source file count：53；physical ID 唯一数：53。
- Reaction 总数：2,428,291。
- 原始 Parquet 内容总字节：1,256,526,213。
- content SHA-256 与 LFS oid 相等：53/53。
- `source-files.initial.csv` SHA-256：`2daa4f0737333cec1a699f3c2f4b977d19db67aa06a0ef95749ec846e0ac72f7`。
- 所有生效 `source_file_url` 均含固定 revision；`/blob/main/` 记录为 0。
- staging 和正式目标中新增 `.parquet`、`.pb`、`.pb.gz`：0。
- 两个正式 manifest 中本机 `/home/...` 路径：0。

### 产物状态

- 状态：`complete`
- 新增正式产物：2 个小型 manifest；未复制或改写任何源数据。
- 步骤 01 安全边界保持有效；`../ord-data/` 与 `../dataset/` 未修改。
- 下一步：步骤 03——冻结整个 `dataset/` 工作快照，建立文件/目录/字节/hash/旧路径的零遗漏 inventory。

## [2026-09-11 22:45 CST] 步骤 03 完成：冻结 dataset 工作快照

### 本步目标

以同级只读 `dataset/` 为严格扫描根，建立包含全部文件和目录的内容快照，并解释约 42GB 工作区与约 14GB `_needs_review` 隔离子树的体量关系；不得把旧的全工作区 inventory 直接冒充当前快照。

### 已完成内容

- 对 `dataset/` 执行两遍独立 `os.scandir` 发现，关闭 symlink 跟随，并对两遍 path set、类型、大小、mtime 和 mode 做一致性比较。
- 对每个普通文件流式计算完整 SHA-256；目录记录路径、mtime 和 mode；若出现 symlink 则按 link target 字符串计算 SHA-256。
- 生成 `intermediate/00-snapshot-inventory/artifact-snapshot.csv`，记录稳定 artifact ID、相对旧路径、对象类型、大小、mtime、类型候选、SHA-256、hash policy、角色候选及扫描状态。
- 生成 `intermediate/00-snapshot-inventory/snapshot-summary.json`，保存总量、顶层目录、角色候选、扩展名、最大文件、缓存规则、`_needs_review` 体量和一致性结论。
- 生成空表头 `intermediate/00-snapshot-inventory/scan-errors.csv`；当前没有扫描错误。
- 缓存对象没有静默遗漏：仍逐文件进入 snapshot，并以 `cache_exclusion_candidate` 标记。共 12 个对象、11 个文件、271,614 字节。
- 回读旧 `processing/migration/01_inventory.csv` 作为历史交叉证据。该表的扫描根是迁移前的整个外层工作区，在当前 `dataset/` 前缀下只有 3 条可直接匹配记录；因此 path-set 差异被解释为迁移历史，不作为当前扫描遗漏。

### 验证证据

- 当前 snapshot：6,050 个对象 = 4,349 个文件 + 1,701 个目录；symlink 和其他对象均为 0。
- 普通文件完整 SHA-256 覆盖：4,349/4,349；artifact ID 和 `relative_path` 唯一：6,050/6,050。
- 文件逻辑总字节：44,375,572,307（41.327972 GiB，`du` 人类可读约 42G）。
- 顶层文件字节：`processing/` 17,653,583,455；`reports/` 163,682,656；`standardized/` 26,558,306,196；合计等于总量。
- `_needs_review`：423 个对象、210 个文件、14,828,180,158 字节（13.809819 GiB，约 14G），占总文件字节 33.415186%；它是 42G 工作区中的隔离子集，并非另一套需相加的数据。
- 两遍发现结果均为 6,050 条；新增、消失、metadata changed 路径均为 0，`stable=true`。
- 扫描错误：0；正式产物中的 `/home/...` 或用户名路径：0。
- `artifact-snapshot.csv` SHA-256：`ae4b3417bc989c98e4b5288ebabf032febe83722c13e60cd96918d890796a4bf`。
- `snapshot-summary.json` SHA-256：`b662822e0e59a3b9bfc460e75ce26f92d7af6a6e949eb7b629472540932c66b2`。
- `scan-errors.csv` SHA-256：`0154d2467603c9f05d333fff2be87ad311910972c607bb87ea4269bb9f77901d`。

### 产物状态

- 状态：`complete`
- 新增正式产物：3 个 inventory 文件；未复制任何被清点的数据对象。
- `../dataset/` 全树只读，所有生成动作均发生在 `ord-datasets/.staging/` 与正式目标目录。
- 下一步：步骤 04——以这 6,050 个对象为闭集建立逐对象 disposition 与 old→new path map；未裁决项必须进入 `quarantined`，不得静默遗漏。
