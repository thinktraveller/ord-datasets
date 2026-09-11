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
