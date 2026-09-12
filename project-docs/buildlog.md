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

## [2026-09-11 22:54 CST] 步骤 04 完成：建立零遗漏 disposition 契约

### 本步目标

以步骤 03 的 6,050 个对象为封闭输入集，为每个对象唯一赋予 disposition、目标路径或 manifest-only 位置、分类理由、许可候选和后续 step owner；任何规则未命中的文件必须保守隔离。

### 已完成内容

- 生成 `provenance/artifact-inventory.csv` 与 `provenance/artifact-path-map.csv`，二者均以 snapshot 的稳定 `artifact_id` 为主键，逐项保留 old path、SHA-256、大小、处置、目标位置、理由和许可候选。
- 建立确定性规则矩阵：41 个逻辑全量表映射为 corpus；19 个 target 的数据、schema、config、exclusions、row map、audit、metadata 映射为 model-ready 七件套；语义名称正式确定前使用 `_pending-semantic-name` 并明确标记，不创建该临时目录。
- 53 个物理 CSV 加 `datasets.csv` 映射至 `intermediate/01-physical-csv/`；来源 manifest、字段分析、YONOD package 过程证据、验证配置和旧 migration 证据分别映射至 02、04、05、06、07、00 阶段。
- 42 个有效处理脚本/测试映射到 `pipeline/scripts/` 或 `pipeline/tests/`；11 个 `__pycache__` 文件排除，1 个 `.orig` 标记 `superseded`。
- 210 个 `_needs_review` 文件全部标记 `quarantined`；3,645 个 run/report 文件在相关性、第三方内容、secret 和许可审计前同样保守隔离。
- 1,701 个目录条目作为 `manifest_only` 元数据排除独立复制，其子对象仍逐项分类，因此不会借目录级规则隐藏文件。
- 对全部文件按 SHA-256 建立重复组和 canonical candidate：241 个重复 hash 组、1,012 个文件实例；本步只记录，不提前删除或物理去重。

### 验证证据

- snapshot、artifact inventory 与 path map 均为 6,050 条，三者 artifact ID 集合和 old path 集合完全相等且各自唯一。
- 记录级 disposition：216 `authoritative`、266 `intermediate`、3,855 `quarantined`、1 `superseded`、1,712 `excluded`；后者由 1,701 个目录和 11 个缓存文件组成。
- 文件级数量：216 + 266 + 3,855 + 1 + 11 = 4,349。
- 文件级字节：13,613,033,941 + 15,684,565,199 + 15,077,692,931 + 8,622 + 271,614 = 44,375,572,307，与步骤 03 snapshot 完全守恒。
- corpus 权威表：41；model-ready target：19，每个目标恰有 `dataset.csv`、`metadata.json`、`schema.json`、`yonod-config.json`、`exclusions.csv`、`row-map.csv`、`audit.jsonl` 七个映射；pipeline 文件：42。
- `_needs_review` 文件：210/210 均为 `quarantined`；未命中 `R99_UNCLASSIFIED_QUARANTINE` 的文件为 0。
- 482 个非隔离、非 manifest-only 活动目标路径全部唯一；路径冲突为 0；无绝对路径、`..` 跳转或 `file://` URI。
- 所有记录的 disposition、reason、new path、license candidate、redistribution status、origin 和 step owner 均非空；许可字段仍是候选，步骤 06 前不构成上传授权。
- `artifact-inventory.csv` SHA-256：`5f12f84351a860121a4ad191cece809de01f992dac00cee453d155655cdb9dcc`。
- `artifact-path-map.csv` SHA-256：`42c8662069740887fe9c0477e9b4e2201ac7c10e61118261232ac25be2902a43`。

### 产物状态

- 状态：`complete`
- 新增正式产物：2 个 provenance 清单；未搬运、删除或上传任何被分类对象。
- 所有 `pending_step_06_license_audit` 与 `blocked_pending_audit` 状态继续阻止远端发布。
- 下一步：步骤 05——基于最大文件、重复 hash、分类字节与候选平台限制完成存储预评估；只形成提案，不执行上传。

## [2026-09-11 23:23 CST] 步骤 05 完成：完成存储容量与后端预评估

### 本步目标

以步骤 04 的 disposition 清单为唯一输入，量化拟发布核心集与潜在扩展集的体量、重复、最大对象、分片需求和平台约束；只提出发布架构，不上传或创建远端资源。

### 已完成内容

- 生成 `reports/release-acceptance/storage-preflight.md` 与同内容的机器可读 `storage-preflight.json`，把输入清单、计算口径、平台来源 URL、决策和未决事项固化为可复核报告。
- 将 `authoritative + intermediate` 定义为拟发布核心集；将再加 `quarantined` 的集合仅作为隔离审计上限，未据此提升任何隔离对象的发布资格。
- 对每个文件的 SHA-256 做内容去重计算，列出最大对象、GitHub 普通 Git 与 LFS 阈值命中情况，并为 1 GiB 上限给出确定性分片数量。
- 比较 GitHub、Git LFS、Hugging Face Dataset 与版本化 S3 兼容对象存储；官方平台限制、价格均记录为采集时参考，需在实际发布前复核。
- 形成提案：GitHub 仅承载控制平面；Hugging Face Dataset 为主候选（需账户/小规模发布演练）；版本化 S3 兼容对象存储为回退；Git LFS 因对象和额度限制不作为主发布面。

### 验证证据

- 核心集为 482 个逻辑文件路径、442 个唯一内容，逻辑字节 `29,297,599,140`（27.285515 GiB），唯一内容字节 `29,297,543,018`（27.285463 GiB）；内容去重仅节省 56,122 字节。
- 核心集中 14 个对象超过 GitHub 100 MiB 限制、5 个超过 1 GiB；其中 2 个超过所有 GitHub LFS 方案的 5 GiB 单文件上限。
- 若按 1 GiB 物理对象上限发布，442 个唯一内容需形成 463 个物理分片；5 个输入对象需拆分，较未拆分对象数增加 21 个分片。表格采用按行分片并重复表头；任意字节分片仅用于无损打包并以逻辑 SHA-256 验证重组。
- 潜在扩展集为 4,337 个路径、3,566 个唯一内容，唯一内容 30,961,331,025 字节（28.834987 GiB）；它只用于容量上限审计，不能替代步骤 06/07 的许可与敏感内容裁决。
- GitHub LFS 免费档在首次完整下载后的参考储存成本约为每月 1.21 美元；Hugging Face 免费公共存储为尽力而为、无容量保证；S3 Standard 的代表性核心集存储参考约为每月 0.6738 美元。价格、区域、流量和历史版本均须在实际发布前重新确认。
- 两个正式报告无本机绝对路径；Markdown SHA-256 为 `306aae16aa8a0043d88ace77de94eebf2ea36c055ef2b8e157016de8f4943926`，JSON SHA-256 为 `b4deda16aa8ec542af73a144f5b62a27290cf3e729a606adaf26d30d494f1f1d`。

### 产物状态

- 状态：`complete`
- 本步仅新增两份预评估报告；未复制数据 payload、未创建仓库、未配置 LFS、未上传任何文件。
- 下一步：步骤 06——落实数据、代码、第三方材料的许可证边界、NOTICE 和再分发阻断条件。


## [2026-09-11 23:35 CST] 步骤 06 完成：建立许可证边界与逐对象裁决

### 本步目标

以步骤 04 的 6,050 个 artifact 为闭集，落实数据与代码的双许可证边界；对权利不明、第三方或隔离材料保守拒绝进入发布 allowlist，而不是用项目根许可证将其一并授权。

### 已完成内容

- 读取冻结上游 revision 26e17b78d9ab44a46a4b4327aa55c53549ec0596 的 README、LICENSE 与 LICENSE-CODE，确认上游将 data/ 和描述性元数据置于 CC-BY-SA-4.0，将 scripts/ 与 .github/ 置于 Apache-2.0。
- 新增 6,050 行 provenance/license-inventory.csv，逐项记录审计许可、证据、署名与 share-alike 义务、再分发状态、allowlist 状态、裁决理由和下一闸门。
- 逐字复制冻结上游许可证为 LICENSE-DATA 与 LICENSE-CODE，并写入 NOTICE 和 LICENSES/README.md，明确双许可证不是对未审计材料的 blanket grant。
- 对活动候选中的 440 个数据或派生元数据确认 CC-BY-SA-4.0；对 15 个含明确 Open Reaction Database Project Apache-2.0 文件头的脚本确认 Apache-2.0，二者均仅推进至步骤 07 敏感信息审计。
- 对 27 个缺乏明确文件头、且无法与冻结上游内容逐字匹配的活动工作区脚本执行 withholding：在权利人确认或补充不可变上游 provenance 前拒绝再分发。
- 3,855 个 quarantined 对象、缓存、目录元数据、superseded 和其他未选对象保持 deny 或不适用；没有隔离对象因本步被提升。

### 验证证据

- license inventory 与 artifact inventory 的 artifact_id 均为 6,050 个且唯一；所有记录都有 origin、audited_license_id、再分发状态和 allowlist 状态。
- 活动候选为 482 个：455 个 pending_step_07（440 CC-BY-SA-4.0 + 15 Apache-2.0），27 个 deny 且均为 withhold_unverified_workspace_code。
- 15 个 Apache 通过项均回读验证为同时含 Open Reaction Database Project Authors 版权行和 Apache-2.0 许可行的源文件。
- LICENSE-DATA、LICENSE-CODE 分别与冻结上游许可证逐字相同；SHA-256 分别为 5e436ff8ffbb77d8607220e9bce20c8915d860010feeb6c1ebef5a85688e9b39 与 c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4。
- 正式审计产物无本机绝对路径；license-inventory.csv、summary JSON、报告 Markdown、NOTICE 的 SHA-256 分别为 d45457e89d7e6c44db3e9367b0f4a48430e8b60106ef2678358070eab7114de3、611b400f25597be15f74cf8fd1f1da37e181b6d40b820b7a16de776b1d9d50c9、23f62c81cc7550eeefe954e533998ca58ea37e2d02f46b8249cb00fb4b5046b8、cfed44c8cdf9efb720ea0942cbde960c4ab686b4b32f3ac466ac2d3c0c7490e7。

### 产物状态

- 状态：complete
- 本步未复制数据 payload、未移动源文件、未创建远端资源或上传内容。
- 下一步：步骤 07——在仅含 pending_step_07 候选的范围内执行凭证、PII 与危险内容扫描；报告不得记录 secret 明文。

## [2026-09-11 23:54 CST] 步骤 07 完成：建立敏感信息扫描与结构化脱敏闸门

### 本步目标

在许可证初审通过的候选中扫描 credential、token、私钥、带凭证 URL、个人邮箱和危险发布内容；不得把命中值、片段或凭证明文写入审计报告，并将发现转化为明确的发布 disposition。

### 已完成内容

- 对 455 个 `pending_step_07` 候选作流式/路径级扫描，并将全部源内容 SHA-256 与冻结 inventory 逐一复核。
- 扫描未发现 credential/token/private-key/credential URL 模式、credential/key 文件名或 source hash 漂移；JSON 审计只保存相对路径、类别、严重度与裁决，不保存匹配值、邮箱、上下文、行文本或每文件命中次数。
- 发现 94 个原始 CSV 的邮箱信号，恰为 53 个物理反应导出及其 41 个 logical corpus 表；所有原始对象均保持 `deny_until_sanitized_derivative_verified`，不能因存在上游 CC 许可而被直接上传。
- 字段级只读判定确认邮箱位于嵌入 `reaction_json` 的 provenance 人员字段（包括值被错误填入 `name` 的情况）；创建结构化 redaction policy 与 Apache-2.0 sanitizer，只删除值本身为邮箱的 JSON dictionary field 或 list item，保留 reaction ID、行顺序、CSV 列、时间戳与非邮箱署名。
- 新增 sanitizer 回归测试，验证只删除 literal email、保持其他 JSON 内容与行级字段，并确保 audit 不含邮箱值。

### 验证证据

- 候选文件 455/455 的冻结 source hash 均通过；无邮箱信号的文件为 361，原始 CSV 脱敏待处理为 94，测试 fixture 信息性信号为 1。
- `credential_or_hash_drift_findings=0`；原始邮件 CSV 的发布状态均为 deny，且下一闸门明确为 `step-11-redacted-copy-and-rescan`。
- `sensitive-disposition.csv` 共 455 行：94 行 `redaction_required_before_promotion`，361 行 `passed_sensitive_gate`；审计 JSON 状态为 `redaction_required_before_promotion`。
- 正式审计文件不含邮箱字面量或本机绝对路径；sanitizer 单元测试与 Python 编译均通过。
- `sensitive-disposition.csv`、审计 JSON、审计 Markdown、sanitizer、测试、policy 的 SHA-256 分别为 `3e1272413c426612f9facbb3ba462d28d9300d037593992da23c99b414aa7c1b`、`79c2eadb722cc9a4a73ae474d7118f087fb04d0c1b65ae2efc10a0ed95b89cd9`、`fdee7775f2b7dca56f4d0ee3a4caa495c8b4fe3e778713ea91d7ff652d0d16ce`、`bcffbdf7353b9bbb3eb426fe88327e5fb3417ff0a2d4f426d7f2b1bd819d00fa`、`e70840629ae3c0b2baabaad0d298a21a450254e39a27c85ec5301deeaae11861`、`a60a23f5febf7100ba8593e7cf24d9bedac4b9bf2fa932c8f32aeb9d5e86bddb`。

### 产物状态

- 状态：`complete`
- 本步只新增脱敏审计、政策、脚本与测试；未复制原始 data payload、未改写源文件、未创建远端资源或上传内容。
- 下一步：步骤 08——为 41 个 logical corpus 生成唯一、可审阅的语义名称；随后步骤 11 必须通过 sanitizer 构建并复扫 94 个原始邮箱 CSV 的衍生版本。

## [2026-09-11 23:59 CST] 步骤 08 完成：定义 corpus 语义名称

### 本步目标

在不替换 logical/physical 稳定身份的前提下，为 41 个 corpus logical dataset 创建基于冻结名称、描述、成员、DOI 与上游来源证据的可读目录 slug、英文名与中文名。

### 已完成内容

- 新增 `provenance/semantic-name-map.csv`：每行保留 logical ID、所有 physical ID 与固定 source path、DOI/upstream aliases、英文名、中文名、命名证据、状态和规划目录。
- 为 6 个同文献 logical 组和 2 个同上游组采用共同 publication/campaign 主题；33 个独立 logical dataset 使用冻结物理数据集的反应或来源语义。
- 新增 `pipeline/policies/semantic-naming-policy.md`，规定 slug 仅为人类目录标签，logical/physical ID 仍是 metadata、hash 与 lineage 的不可变机器身份；不允许根据未记录信息臆测反应类别、测量或 benchmark 状态。
- 新增 machine-readable 与 Markdown 命名审阅报告，固定四个输入 manifest 的 SHA-256 和所有覆盖/冲突统计。

### 验证证据

- 语义映射为 41 行 logical dataset，一对一且无大小写 slug 冲突；53 个 physical ID 均覆盖一次，Reaction 总数精确为 2,428,291。
- relationship 分布为 33 `independent`、6 `same_publication`、2 `same_upstream_source`；manual review 行为 0。
- 所有 slug 满足 `^[a-z][a-z0-9-]{2,79}$`，均非 UUID-only，所有原 logical ID 均保留在 aliases 中，aliases 无重复。
- 输入固定 hash：logical datasets `6e21baaae2c37d5d092cf5eb2cf4ee25c34ac67942c749bab7a933a6a716661d`、members `ca3f2d586bcaaa1d8c821d2db125624cecec52032c51c839a91cb51bc13df366`、physical datasets `b7289e8ae564b6750cff880e60910d43d43dca07878c7fc2140b05db64045fd5`、source evidence `c659cbab662fe972208f6d988831fd8e6c81b200e7f4e2aaf14d9bd122099656`。
- semantic map、JSON review、Markdown review、naming policy 的 SHA-256 分别为 `72cc994b7f7c3f79c9647894250527258d0c424f2e769af80b083815ecd233f6`、`ffd0d04fd8f99eca4b9d1a5ac2d1230a6d2ae8bbc5737f18b056d5f82a5899ad`、`52715572c137414eba363097609d0c35c3e35cde9b9788427b591caa5faa2dc3`、`bcc6d0440edca8ccf778cf52b1ec2765cccaaf099065e8d4e86b4d9beb83aaec`。

### 产物状态

- 状态：`complete`
- 本步只新增命名 metadata、政策和审阅报告；未复制 payload、未改写源文件、未创建远端资源或上传内容。
- 下一步：步骤 09——为 19 个 model-ready target 固化语义名称、标签单位、source set 与真实完成状态。

## [2026-09-12 00:03 CST] 步骤 09 完成：定义 model-ready target 语义与状态契约

### 本步目标

为 15 个 package 的 19 个 target 建立唯一语义名称、标签字段/类型/单位、logical/physical 来源集合、included/excluded 计数和不会误报完成状态的双层 status contract。

### 已完成内容

- 新增 `provenance/semantic-target-map.csv`，逐 target 固定 semantic slug、中英文显示名、alias、corpus slug、source physical/source file 集、label contract、行数、manifest/schema hash 与规划目录。
- 分离 `artifact_status`（文件是否已生成）和 `readiness_status`（能否支撑宣称的 campaign/benchmark 用途）；所有 target 的 artifact 均为 `generated`，但 readiness 保留 active、pending、partial、source caveat、domain blocker 和 adapter blocker 的真实区别。
- 明确 6 类标签：reaction yield、conversion、relative LC area ratio、HPLC response、LC/UV area percent、signed S-minus-R ee；禁止在目录、catalog、评估或文档中把它们互称产率。
- 新增 `pipeline/policies/target-status-contract.md` 与两份命名/状态审阅报告；不复制任何 normalized dataset、config、row map 或 audit payload。

### 验证证据

- 15 个 package、19 个 target 全覆盖；slug 大小写唯一且全部符合 kebab-case；每个 logical ID 与步骤 08 corpus slug 一致。
- 每个 target 均满足 `included_count + excluded_count = source_count = audit_count`，并存在标准化 schema、normalized dataset、YONOD config、row map、exclusions 与 audit 的只读输入证据。
- readiness 分布：7 `active_generated_pending_release_validation`、6 `generated_pending_campaign_evaluation`、1 `partial_scope_generated`、3 `research_only_benchmark_blocked`、1 `generated_adapter_blocked`、1 `generated_with_source_caveat`。
- partial 的 Science target、3 个 catechol research target、asymmetric-alkylation adapter blocker 和 NiCOlit source caveat 均保留显著状态，未被写成 accepted/complete。
- semantic target map、JSON review、Markdown review、status policy 的 SHA-256 分别为 `df3028a5e68fdf1a244868a812291d64651286f9d22ce268262d72bb98f6fb8a`、`3d0223bcb0eda6576b429f9647c2e2cb5bbbab7271dc04026e5a73cea4a71d04`、`05d0037f911b147ad8504e2b4eac8c9fe2e24a58a3f851dbde1d153a3d28e876`、`1d566d8af47c327459ef8a30224d47f697ad33ec3e0d2c1fb12d4a0edcdb567f`。

### 产物状态

- 状态：`complete`
- 本步只新增 mapping、policy 与报告；未复制 payload、未改写源文件、未创建远端资源或上传内容。
- 下一步：步骤 10——冻结 catalog、dataset metadata、source links、artifact、row map、transformation 与 release manifest 的 schema 契约和 fixture。

## [2026-09-12 00:13 CST] 步骤 10 完成：冻结发布元数据契约

### 本步目标

为 catalog、per-dataset metadata、不可变 source links、artifact inventory、target row map、transformation graph 和 release manifest 固定可机器验证的字段、类型、nullable、枚举、路径与版本规则；在数据搬运前阻止无版本的契约漂移。

### 已完成内容

- 新增 `pipeline/schemas/schema-index.json`，冻结 `ord-datasets-release-contracts` family `1.0.0`：7 个 JSON Schema 加 1 个 CSV sidecar contract；`field-dictionary.md` 解释所有发布/溯源字段与三层关系。
- Catalog 与 metadata schema 分别区分 `corpus` 和 `model-ready`：前者强制 target/label 为 null，后者强制 target ID、label type/unit 与 model-ready 路径；两者都保留 logical ID、一个或多个 physical ID、source links、许可、hash 和发布状态。
- Source-link schema 只接受 Open Reaction Database GitHub 的 `data/<prefix>/ord_dataset-*.parquet` URL，且 URL 必须含 40 位 commit；拒绝 branch/tag/`main` 链接。fixture 使用 Shields logical dataset 的两个真实冻结 source 条目，并回读比对 source manifest 中的路径、revision、URL、SHA-256/LFS OID、字节数、Reaction 数和 CC-BY-SA-4.0。
- Row-map contract 让 included 与 excluded 均保留 physical/source/reaction/label-decision 关系，但只允许 included 行拥有 target CSV 行号；CSV sidecar 同时固定 corpus 的四个 lineage 列及 model-ready row-map/exclusions/lineage-edges 的顺序、类型和键。
- Transformation contract 固定 step、tool、40 位 pipeline commit、参数化 command、config/input/output hash、时间、状态和错误码；release manifest 固定 53 physical、41 corpus、19 target 的预期计数、双许可证、各契约版本、source manifest 和 hash-tree root。
- 新增 semver 与不可变升级 policy：破坏性变更升 MAJOR；兼容扩展升 MINOR；纯说明升 PATCH；进入数据搬运后不允许原地覆盖已用 schema。
- 新增 `validate_release_contracts.py` 和 pytest-independent unittest fixture。正例同时表达 multi-physical → logical → target；反例证明 target 缺标签、`/blob/main/`、excluded 行伪造 target 行号、以及本机绝对路径 command 均会被拒绝。

### 验证证据

- `python3 pipeline/scripts/validate_release_contracts.py` 输出：8 个 indexed contracts、10 个正例和 4 个反例；全部符合预期。
- 验证器使用 Draft 2020-12 对所有 7 个 JSON Schema 自身做 schema check，并检查 CSV header/column 一致性；source-link 正例与 `provenance/source-files.initial.csv` 的两个真实物理源逐字段一致。
- `python3 -m unittest discover -s pipeline/tests -v`：2/2 通过（release contract 与既有结构化脱敏回归测试）。
- `git diff --check` 通过；新增正式契约/fixture/验证代码未包含工作站绝对路径或 `file://` URI。反例中的 `/home/example` 仅作为故意拒绝的字符串，未指向实际工作站。
- 关键 SHA-256：schema index `2b6d529bf1a346f3a9593f4f2e54d243975d2d601344752d28339e6a9c4e1acf`；catalog schema `e6588bdfde1cc7bae0286863a55b5c0b9e19b463e07f0f44a730d9614a8a6b63`；metadata schema `0128b6b7744ff222c295aa13e084f8aed1e5f89dbe93b0e230da517014f24328`；source-links schema `bbaea53bd505c68a2857f9a07fe0d742e98de737dd7167be7a221fbf8ef80712`；CSV contract `13f97763853a1cf93f273c74490e604491618ca5f8175c1564a8fb75f9847a0b`；fixture `b1cc1085cad7c1d0cf846afb07eea60ab935223aab0d2539210a5e5dc33c554b`；validator `6105339eccd6584cbc332e3952ec37c16112ff27e120800cab10416ffbe282d2`。

### 产物状态

- 状态：`complete`
- 本步只新增 schema、policy、字段字典、fixture、验证器与测试；未复制任何数据 payload、未修改 `../ord-data/` 或 `../dataset/`，未创建远端或上传内容。
- 阶段 B/M2 契约部分完成；下一步为步骤 11：在 staging 中以结构化脱敏脚本构建 41 个 corpus 包，并在复制后复扫 94 个待脱敏 CSV 衍生版本。

## [2026-09-12 00:31 CST] 步骤 11 完成：构建并脱敏 41 个 corpus staging 包

### 本步目标

从只读 logical CSV 表逐个创建语义化 corpus staging 包，同时删除嵌入 `reaction_json` 的 literal email 值、保留 corpus 行与 source lineage，并为每个包生成 schema、metadata、固定 source links 和 checksums。

### 已完成内容

- 新增参数化 `build_corpus_staging.py`：所有 source/output root 均从 CLI 显式传入；不会向来源目录写入。它以 `.<slug>.partial` 临时目录构建，只有 CSV、JSON 结构复扫、member 行数、元数据和固定 source links 均通过后才原子提升为 `<slug>/`。
- 将 sanitizer 的 CSV field limit 安全提升至 Python 可表示的上限，支持 ORD 的超大 `reaction_json` 字段；不改变既有 literal-email 删除规则。首轮在默认 128 KiB 限制处停止，4 个已完整提升的包经 checksum/audit 验证后以 `--resume` 保留，未重写；余下包继续构建。
- 在 `.staging/ord-datasets-v0/step-11/datasets/corpus/` 形成 41 个 semantic corpus 目录。每个目录恰有 `reactions.csv`、`schema.json`、`source-links.json`、`checksums.csv` 与 `metadata.json`；41 份 redaction audit 位于同一 staging step 的隔离 audit 根。
- 每个 `source-links.json` 从冻结 `source-files.initial.csv` 生成并经 schema 验证；URL 固定至 40 位 upstream commit，不使用 `/blob/main/`。每个 metadata 记录 logical/physical IDs、CC-BY-SA-4.0、staged 状态、行数、输出 hash 及 source manifest hash。
- 生成小型、可提交的控制面 manifest `intermediate/08-runs-and-reports/step-11-corpus-staging-manifest.json`（31,839 bytes）；它固定 41 个 staged package 的行数、reaction/metadata/source-links/checksums hash、redaction-audit hash 与输入 manifest hash，不含任何 payload 或个人信息值。

### 验证证据

- 完整 staging run：41 corpus、2,428,291 行、53 个 unique physical source，logical membership 重复为 0；没有 partial 目录。
- 所有 41 个输出 CSV 均保留 header `physical_dataset_id,source_file,reaction_id,row_index,reaction_json`；每个输出的 logical member 行数与 semantic/member manifest 一致。
- 结构化复扫得到剩余 literal email value 为 0；共删除 7,693,116 个 literal email 值。审计仅记录聚合 key-path/count、input/output hash 和行数，不记录邮箱或原始行内容。
- 41 份 audit 均存在，且 audit output hash 与 corresponding `reactions.csv` hash 相同；所有 source-link URL 的 `/blob/main/` 计数为 0。
- staged reactions 总字节为 13,127,326,230；全部 package metadata/control files 合计后为 13,127,476,889 bytes；audit 合计 27,599 bytes。payload 保持在忽略的 staging tree，未进入 Git。
- `python3 -m unittest discover -s pipeline/tests -v`：3/3 通过；包括 corpus 的 clean-room 合成测试、release-contract 测试和 sanitizer 回归。`git diff --check` 通过；`../ord-data` 的 `data/` 工作树仍无修改。
- SHA-256：staging run manifest `eeaed2fecb737b40c05d19e654e409c5bee85319745744129f064c6af529ad85`；可提交 staging manifest `fb0475232ca5666151da9955706057af70bc7f56733b7820f852ce69c80186e6`；corpus builder `a5b9e5df472c49b17bacde283bbb4be7f8dc03afc67f01b8d9b01cb5770a1de9`；sanitizer `bcef389b9337c3af28e272cbe29e74fb04b644b08c40f0f11e0d9b12d837db6f`；manifest snapshotter `ed126af62266ab25785a0bd63edb2adc61b70c1e1d9abab292e89bb6e456a5bb`。

### 产物状态

- 状态：`complete`
- 41 个 corpus 仍是本地 staging，`artifact_status=staged`，不构成远端发布或 release acceptance。大 CSV 没有提交到 Git；正式对象指针与远端操作仍受后续 object-backend/release gate 约束。
- 下一步：步骤 12——从 staging 全量校验 CSV、hash、reaction key、source-row 范围、member 唯一性、语义/固定链接与计数守恒，并产出 per-corpus 和总体验收报告。

## [2026-09-12 00:42 CST] 步骤 12 完成：全量验收 corpus staging 层

### 本步目标

独立于步骤 11 构建器重新读取全部 corpus staging payload，验证 CSV/JSON/schema/hash、row-level source range、reaction key、排序、logical membership、固定 source links 与敏感信息清零；产出可提交的 per-corpus 机器报告和简明汇总。

### 已完成内容

- 新增只读 `validate_corpus_staging.py`：不接受写入 staging 的参数；它从 semantic map、logical membership、frozen source manifest 和步骤 11 控制面 manifest 交叉验证每个 package。
- 为每个 corpus 检查目录文件集、CSV header、local CSV contract、metadata/source-links JSON Schema、checksums、metadata 中的 artifact hash 以及步骤 11 control manifest hash。
- 为 2,428,291 行创建按 physical source size 分配的紧凑 row-index 位图，验证每个 source row index 非负、范围正确、无重复、无缺失；同时检查 non-empty/unique reaction ID、`source_file,row_index` 确定性排序与 `reaction_json` 可解析性。
- 再次结构化遍历全部 reaction JSON，仅计数 literal-email value，不保留命中内容；验证每个 source link 与 frozen source manifest 的路径、revision、URL、hash/LFS oid 和 license 一致。
- 新增 `reports/data-quality/corpus-staging-validation.json`（每 corpus 的行数、source 数、reaction hash/字节数）和 Markdown 摘要。报告仅包含控制面信息，不含 reaction payload、邮箱或匹配上下文。

### 验证证据

- 41/41 corpus 通过；53 个 physical source 全部且仅归属一个 logical corpus；总 Reaction 精确为 2,428,291。
- orphan physical source = 0；duplicate logical membership = 0；`/blob/main/` URL = 0；remaining literal email value = 0。
- 每个 corpus 的 `reactions.csv`、`schema.json`、`source-links.json`、`checksums.csv`、`metadata.json` 文件集精确存在，且三层 hash（checksums、metadata、step-11 control manifest）一致。
- 本步加入的合成 corpus test 通过 builder 后立即调用独立 validator；全套 `python3 -m unittest discover -s pipeline/tests -v` 为 3/3 通过，`git diff --check` 通过。
- SHA-256：validator `8d8e6e87f2861b49352f2f7be2ce85ab859435977cebc89e78fd52b3b6800d2c`；更新的 corpus staging test `0c48775efc8a83127bbcc1a5bc2f1d679f34b084c030fb90ef30c95bb7277a0f`；JSON report `3c53c7c52845778386b59078dd0b3580f1f1409463cd49959cad5bf9c4cd3941`；Markdown report `b4a8c6b22ac8df4c34951033773aaa38053db48906f939bbd6b07b2a3db7b30d`。

### 产物状态

- 状态：`complete`
- corpus staging 通过本地全量验收，但仍未提升为正式目录、未创建对象后端、未上传或公开发布。
- 下一步：步骤 13——按步骤 09 的 19 个 target semantic map 构建 model-ready staging 包，保留 dataset/schema/config/exclusions/row-map/audit/metadata 与真实 readiness status。

## [2026-09-12 00:42 CST] 步骤 13 完成：构建 19 个 model-ready staging 包

### 本步目标

由冻结的 19 个 target mapping、processing target artifacts 与 standardized target artifacts 生成语义化 model-ready staging 包；保留任务级 label、config、row map、included/excluded、audit、状态与回到 immutable ORD source 的路径。

### 已完成内容

- 新增参数化 `build_model_ready_staging.py`，明确读取 processing/standardized target roots，输出只写入指定 staging root。它验证每个 target manifest 与 standardized schema 的冻结 hash，并对 byte-preserving copies 逐文件回算 SHA-256。
- 为每个 target 输出 `dataset.csv`、`schema.json`、`yonod-config.json`、`row-map.csv`、`audit.jsonl`、`metadata.json`，以及 `source-links.json`、`target-build-provenance.json`、`checksums.csv` 三个发布/溯源支持文件。
- 将 legacy exclusions 规范化为含 `label_decision_id` 的新 `exclusions.csv`：逐行从 target audit 反查 decision ID，保留 reaction key、physical ID、source row index 与 reason；原 exclusions hash 和新输出 hash 都写入 per-target build provenance。
- 每个 metadata 保留 semantic target/corpus/logical/physical identity、label type/unit/policy、included/excluded count、真实 readiness status、CC-BY-SA-4.0 与 frozen source-manifest relationship；source links 使用固定 40 位 upstream revision。
- 生成并提交准备 `intermediate/08-runs-and-reports/step-13-model-ready-staging-manifest.json`，这是不含 payload 的控制面 manifest，记录 19 个 target 的状态、计数与 10 个 staging artifact 的 hash/字节数。

### 验证证据

- staging 目录为 19 个且 slug 唯一；每个目录文件集精确为 10 个指定控制/数据文件，无 partial 目录。
- 合计 included 为 128,712，excluded 为 499，且 `included + excluded = source_count`；staging package 总字节为 211,008,093，payload 保持在被忽略的 staging root、没有加入 Git。
- 19 个 `target_manifest.json` 与 semantic target map 的 manifest hash、19 个 standardized schema hash 均逐项匹配；所有 copy 输出 hash 与其受验证输入一致。唯一转换的 enriched exclusions 有显式 input/output hash 与 decision ID join 约束。
- staging target tree 的 email 与 credential/private-key token pattern 文件命中均为 0（只输出路径、从不记录匹配内容）；`../ord-data/data` 工作树仍无修改；`git diff --check` 通过。
- SHA-256：staging run manifest `fa27c9cc6bcbcabe5a18422c3efda174867ff575c9988e7674265c34e0a79f86`；可提交 staging manifest `79a2e522c29453a5b974f38a6a5b640d449f8bf97e09ada165c23e3fe13d2578`；builder `e5b7a455ee9f6bca9e184b84bbd4b19a2b2d7b47a57e93de0d5b68282407b8cf`；snapshotter `da8e7a04bfcacdd43381265eb5db712b43b7cca8c80ae82d6775a4bdd4ce4f3b`。

### 产物状态

- 状态：`complete`
- 所有 target 仅为本地 staging；原 mapping 中的 partial/blocked/pending readiness status 原样保留，未被提升为 benchmark accepted，未执行远端创建或上传。
- 下一步：步骤 14——独立检查 19 个 target 的 label/schema/config、included/excluded/source/audit 对账、row-map/source index、状态、feature denylist 和无标签泄漏约束。

## [2026-09-12 00:48 CST] 步骤 14 完成：全量验收 model-ready staging 层

### 本步目标

独立验证 19 个 staged target 的 schema/config/label 语义、row map、exclusions、audit、source index、status、hash 与 immutable source link；不能因 artifact 已生成而把 pending/partial/blocked target 误称为 benchmark accepted。

### 已完成内容

- 新增只读 `validate_model_ready_staging.py`，交叉读取 semantic target map、53 source manifest、步骤 13 control manifest 与每个 staged package；它不写入或重建 target payload。
- 校验每个 package 的 10 个文件、checksums、metadata artifact hash、metadata/source-links JSON Schema、target build provenance、control manifest 和原 mapping 的 target ID/label/status。
- 对 dataset/row-map/exclusions/audit 执行 count 和 decision 闭合：row map 的 physical ID/source index 均在 frozen source 范围内，included audit decision 与 row-map 的 `label_decision_id` 一致，excluded decision 与 enriched exclusions 一致。
- 检查 declared schema label column 与 target map 相同，且 label 不在 declared `feature_columns` / `column_roles.features` 中；同时检查 19 个 source-link set 和 fixed URLs。
- 发现 Science target 合法携带 `campaign_id` 附加 row-map 列。按 schema versioning policy 将 CSV contract 从 1.0.0 兼容升级为 1.1.0：该字段是可选 campaign provenance，不是特征或 label；1.0.0 core artifacts 继续有效。相应更新 schema index、release-manifest schema、字段字典和 contract validator。
- 生成 `reports/data-quality/model-ready-staging-validation.json` 与 Markdown 摘要；只记录 target hash/计数/状态，不记录训练行、标签值或敏感匹配文本。

### 验证证据

- 19/19 target 通过，included 128,712、excluded 499；每个 target 均满足 `included + excluded = source_count = audit_count`。
- status mismatch = 0；row-map error = 0；source-index error = 0；declared label leak = 0；unpinned `/blob/main/` URL = 0。
- `python3 pipeline/scripts/validate_release_contracts.py` 通过 8 个索引契约、10 个正例、4 个反例；全套 `python3 -m unittest discover -s pipeline/tests -v` 为 3/3 通过；`git diff --check` 通过。
- SHA-256：target validator `37248c7baae5a5b54e2a860a3f5d9d5563808b226b731cfe7ce12c3a06f00d04`；JSON report `38f9243d2fa817a793b5c3fb07f9213b485ebebaf97c0f4c6b4dcdbd30366ea2`；Markdown report `f30ca2633bb5095ed4c5d39431c0da3b53dfa7a1f42af887cef981c6b7ea325c`；CSV contract 1.1.0 `589eef821f868931c5250f7c47f3c3ea32167e1218ba5dda87431d48856f21f5`；schema index `f4317172def51bf5655bd140bc826df3b0d8b8b747a329d74bf15b20d18da464`。

### 产物状态

- 状态：`complete`
- corpus 与 model-ready 现均通过本地 staging 验收，但尚未生成用户可见的统一 catalog、未提升正式目录、未配置对象后端或远端发布。
- 下一步：步骤 15——从已验收 metadata 和 semantic maps 确定性生成 `datasets/catalog.csv` 与 `datasets/catalog.json`，使任一 corpus/target 可关联 logical/physical/source/status/path。

## [2026-09-12 00:52 CST] 步骤 15 完成：生成统一数据集 catalog

- 新增 `build_catalog.py`，从已提交的 corpus/model-ready staging control manifest 和两个 semantic map 确定性生成 `datasets/catalog.csv` 与 `datasets/catalog.json`；不读取或复制 payload。
- JSON 的 60 条 record 全部通过 catalog-record JSON Schema；CSV/JSON 均包含 semantic slug、logical/physical/source file 集、target/label（corpus 为 null）、真实 readiness、staged status、license、行数、content hash 和计划发布路径。
- 验收：41 corpus + 19 model-ready = 60，两个格式记录数和语义分层一致。SHA-256：CSV `c13e690152896e811ccbd28e3e2f4c2de4989bf88ce9e46861e0b3af84ef4509`，JSON `bb9de21780145197f17b39d1f92a4b3e978748f84554a7346549b61b04ef35ef`，builder `43b142343b5e39e00639a60dd059ae5a493ac20901c713760df3fa2de6ef2bdc`。
- 状态：`complete`。Catalog 是 staging index，不代表已上传或已发布；下一步为阶段 D 的中间资产归档与 pipeline 抽取。

## [2026-09-12 01:18 CST] 步骤 16 完成：归档 00～04 阶段中间资产索引

- 新增内容寻址归档器 `pipeline/scripts/archive_intermediate_indices.py`，为 `00`～`04` 写入 payload-free `archive-index.csv`。归档记录旧相对路径、SHA-256、字节数、disposition、许可/再分发状态、canonical artifact 和计划 archive path；不复制原始文件。
- 原始 53 physical CSV 在敏感审计中仍含 blocking PII finding，故保留为只读内容寻址引用，而非把未脱敏 payload 再写入发布工作区。此选择也避免将 physical、logical 与发布语料做物理重复保存。
- 验收：`01-physical-csv` index 有 53 个 physical CSV（另含 `datasets.csv` catalog），五个分组共 94 条记录；source evidence、logical manifests 与 4 个 field-profiling 文件均可由 hash 对账。
- 机器可读证据：`reports/release-acceptance/step-16-intermediate-archive.json`；状态：`complete`。

## [2026-09-12 01:24 CST] 步骤 17 完成：归档 05～08 阶段 model-ready 证据索引

- 新增 `pipeline/scripts/archive_model_ready_intermediates.py`，从已通过步骤 14 验收的 step-13 staging 生成 05～08 分组索引，而不是复制旧的、未审查的 `reactions_model.csv` 快照。
- 19 个 target 的 dataset 投影、row map/audit/exclusions/source links、schema/YONOD config 与 checksums 共 190 个 artifacts 已逐个记录路径、大小和 SHA-256。payload 保持为 staging 的内容寻址引用，避免重复大对象进入普通 Git。
- 验收：19 target / 15 package；05、06、07、08 分别有 19、114、38、19 条 index 记录。机器可读证据：`reports/release-acceptance/step-17-intermediate-archive.json`；状态：`complete`。

## [2026-09-12 01:26 CST] 步骤 18 完成：处置 legacy `_needs_review`

- 新增 `pipeline/scripts/audit_needs_review.py`，对全部 210 个待审文件从冻结 inventory 重新建立逐文件 review table，不复制任一待审 payload。
- 43 个与非待审 canonical artifact 逐字节相同的文件标记为 `superseded` / `excluded_duplicate`；其余 167 个保留 `quarantined`。首发 inclusion 为 0，未把待审对象默认为公开。
- 审计范围为 14,828,180,158 bytes；机器可读 review table：`intermediate/90-legacy-needs-review/review-disposition.csv`，摘要：`reports/release-acceptance/step-18-needs-review-audit.json`；状态：`complete`。

## [2026-09-12 01:35 CST] 步骤 19 部分完成：抽取生产 pipeline

- `pipeline/` 现有 12 个参数化脚本、schema、policy、fixtures 和测试被封装为 Python 项目；新增 `pyproject.toml`、archive indexer regression tests 和可执行说明。所有输出 root 由 CLI 调用方提供，脚本源码不含本机绝对路径。
- 静态检查（未定义名称）和 5 个单元/fixture 测试均通过；原先一处未使用 import 已清理。
- **阻塞**：`uv lock` 下载 `ruff` 时 TLS 连接失败，离线 resolver 亦无可用 ruff cache，故没有生成 `uv.lock`；未用未锁定依赖替代它。详见 `pipeline/DEPENDENCY_LOCK_BLOCKED.md` 与 `reports/release-acceptance/step-19-pipeline-extraction.json`。在网络可用环境生成 lock 前，本步骤不能标记 complete，也阻塞 RC 验收。

## [2026-09-12 01:43 CST] 步骤 21 完成：生成数据集级 provenance maps

- 新增 `build_dataset_provenance.py`，从冻结 source、semantic 和 target map 生成 physical、logical、membership、package、target 与 source-evidence 的规范 provenance 表，并将 source manifest 原样复制为 `provenance/source-files.csv`。
- 验收：53 physical source、41 logical corpus、53 memberships、15 packages、19 targets；所有 source URL 都带 40 位固定 upstream revision，`/blob/main/` 为 0。
- 输出 hash 写入 `reports/release-acceptance/step-21-dataset-provenance.json`；状态：`complete`。

## [2026-09-12 01:49 CST] 步骤 22 完成：验证行级 lineage

- 新增 `build_row_lineage_index.py`，为 41 corpus 和 19 target 构建紧凑的 hash index；行本身保留在已验收 staging payload 中，不以重复行级文件占用 regular Git。
- 全量重跑验收：2,428,291 corpus 行的 physical/source/reaction/row_index 均通过，53 physical source 无孤儿、重复 logical membership、可变 `main` URL 或残余 literal email；19 target 的 128,712 included 与 499 excluded 也重新验证，row map/source index/label leak/status mismatch 均为 0。
- `provenance/row-lineage/two-hop-query-examples.md` 说明 corpus 和 target 从行定位到固定 source manifest 的两跳路径。状态：`complete`。

## [2026-09-12 01:53 CST] 步骤 23 完成：组装 transformation graph 与 draft release hash tree

- 新增 `build_release_lineage_graph.py`，生成 113 个内容寻址 release artifact 节点（53 source、41 corpus、19 target）、72 条 source→corpus→target 边和两条受 schema 约束的 transformation record。
- `provenance/release-artifacts.jsonl` 是 release 图专用 inventory；`lineage-edges.csv`、`transformations.jsonl` 与 `release-manifest.json` 形成 draft RC 的 provenance 控制面。root SHA-256 为 `a757863ea622f1a69205024a9ee04482952b95bdee85bbb98c74a2990df970db`。
- manifest 的 release status 保持 `draft`，不表示 local RC 已接受或有远端对象；状态：`draft_complete`。

## [2026-09-12 01:58 CST] 步骤 24 完成：发布文档、署名与使用说明

- 新增 `DATA_CARD.md` 和 `CITATION.cff`，更新 README 的实际 staging/发布状态，并把 NOTICE 的 ORD revision 改为已验证的 `83f971f...`。
- 文档明确 corpus 与 model-ready 的口径、19 target 的 non-accepted 状态、CC BY-SA/Apache 边界、literal-email 脱敏、两跳 lineage、外部对象下载模式以及当前 release blockers；不把 draft 误称为 published benchmark。
- 机器可读检查：`reports/release-acceptance/step-24-documentation.json`；状态：`complete`。

## [2026-09-12 02:02 CST] 步骤 20 阻塞：clean-room 小样本重建

- 以最小的固定 source record 构造 GitHub raw URL 并从空路径执行下载探测；连接在 TLS 阶段以 `SSL_ERROR_SYSCALL` 失败。source manifest 的 direct download 字段也尚未经回读验证。
- 未以本地 `ord-data/`、staging 或缓存替代公网输入，因此没有把缓存命中误报告为 clean-room 成功。`uv.lock` 缺失和 source→target adapter 未完整抽取亦阻止端到端重建。
- 失败命令、固定 URL、source hash 与后续修复条件保存在 `reports/release-acceptance/step-20-clean-room-rebuild.json`；状态：`blocked`。

## [2026-09-12 02:05 CST] 步骤 25 阻塞：大文件后端 pilot

- 添加不含 credential、remote URL 或本机路径的 `pipeline/configs/release-object-storage.example.json`，固定控制面/数据面分离、SHA-256 content addressing、1 GiB shard 上限与 readback-hash 规则。
- 尚未收到 owner、visibility、后端账户和额度的授权选择，故没有创建测试对象、执行 upload/pull 或任何远端写入。local policy check 通过不替代真实 pilot。
- `reports/release-acceptance/step-25-storage-pilot.json` 列出阻塞条件；状态：`blocked`。

## [2026-09-12 02:07 CST] 步骤 26 阻塞：提升 staging 并生成 local RC

- draft lineage root 与 release manifest 已生成，但没有移动 41 corpus 或 19 target staging payload 到正式目录：dependency lock、clean-room rebuild 和 storage readback pilot 都尚未通过，release authorization 也尚未存在。
- 因没有提升任何大对象，正式 target tree 未被改变，也不需要 rollback。`reports/release-acceptance/step-26-release-candidate.json` 是逐闸门状态证据；状态：`blocked`。

## [2026-09-12 02:09 CST] 步骤 27 完成（rejected）：发布前本地验收

- 新增 `validate_release_candidate.py`，复核 catalog、staging 和 lineage 的控制面：41 corpus、19 target、113 nodes、72 edges，failed edge 为 0；没有远端写入。
- RC 未被接受。4 个 blocking check 仍为 dependency lock、clean-room rebuild、storage pilot 和 release authorization。机器可读结果：`reports/release-acceptance/step-27-release-candidate-validation.json`，状态：`rejected`。

## [2026-09-12 02:11 CST] 步骤 28 等待授权：冻结 release 决策

- `provenance/release-decision.json` 明确列出 remote URL/owner/visibility、版本/tag、object backend/quota、`_needs_review` 范围和 partial/blocked 展示方式这七项尚未由 owner 选择；`remote_write_authorized` 为 false。
- 本记录不包含 credential，也不构成上传授权；状态：`pending_owner_decision`。

## [2026-09-12 02:12 CST] 步骤 29 阻塞：上传与不可变 release

- release decision 仍为 pending，local RC 也处于 rejected；因此没有连接远端、上传 object、创建 commit/tag/release 或产生费用。upload checkpoint 记录 0 objects / 0 bytes：`reports/release-acceptance/step-29-upload-checkpoint.json`。
- 未来只能在通过闸门后从新的 immutable upload manifest 断点续传，禁止覆盖已存在 tag/object；状态：`blocked`。

## [2026-09-12 02:13 CST] 步骤 30 阻塞：无缓存远端回读

- 因未存在远端 release、tag 或 uploaded object，未执行 clone/download/readback，也没有将本地 staging 当作远端回读证据。expected draft root 已记录，verified remote root 保持 null。
- `reports/release-acceptance/step-30-remote-readback.json` 固化将来必须覆盖的 control-plane、小/最大数据对象、完整 target、lineage 与 sample rebuild；状态：`blocked`。

## [2026-09-12 02:15 CST] 步骤 31 完成（维护基线）：项目收尾

- 新增 `MAINTENANCE.md`，规定 ORD revision 更新、语义版本、schema/naming compatibility、immutable release 与复验流程；`project-docs/release-backlog.md` 为每个 blocking issue 指定 `project-owner` 和可复核 exit evidence。
- closeout 固定 53/41/2,428,291/15/19/210 的已知基线，16、17、18、21、22、24 为 complete，23 为 draft complete；初始 release 仍未关闭。
- `reports/release-acceptance/step-31-closeout.json` 确认无未归属 blocking issue；状态：`maintenance_baseline_established_release_not_closed`。

## [2026-09-12] 步骤 19 解除依赖锁阻塞

- 已在可联网环境生成并跟踪 `pipeline/uv.lock`，并将 clean-room 所需的 `ord-schema`、`pyarrow` 固化为运行依赖。
- `uv sync --group dev --locked`、`uv run pytest -q`（6 项）和 `uv run ruff check scripts tests` 均通过；原 TLS 阻塞记录已改为历史解决说明。
- 状态：`complete`。不含凭证、本机路径或远端写入。

## [2026-09-12] 步骤 20 部分完成：公开 LFS clean-room 重建

- 新增参数化 `rebuild_clean_room_sample.py`：只接受 source/semantic/member/target map、schema、physical/target ID 及显式 download/output/report root；不接受本地 staging 或 cache 作为输入。原始 Parquet 只下载到仓库外的临时 root。
- 对 Ahneman 单源 yield sample，通过固定 raw LFS pointer 与公开 Git LFS batch endpoint 下载 `ord_dataset-46ff9a32d9e04016b9380b1b1ef949c3.parquet`，SHA-256 为 `39440ea3e5442dddbb4daccbc48fb53940724085327c0e3b82909e1fd8cc661a`。
- 物理 CSV（4,312 行）及经 literal-email 结构化清理后的 corpus 均逐字节匹配冻结 staging 基线；独立重复运行的 23 文件 output root hash 均为 `d663773a78fc6dc2c6fdc9fcfdb4faa8b0c86841273102f9ef8070da035f8215`。
- 通用 yield adapter 已生成 target、row map、exclusions、audit 和 transformations provenance；included/excluded/source 计数为 4,312/0/4,312，符合冻结 target map。但它的 `dataset.csv` SHA-256 为 `433b1ca544cddd823baa482b9f5218c7b1dcb9af064b32ce9d9960eb5929e2a4`，尚未匹配冻结 baseline `6a912585bb987ab698e2502585e1927403c372e10d8e3bcf8ce26f93c4021acf`。
- 状态：`partial_target_byte_equivalence_unresolved`。未伪造通过、未读取 local staging payload、未写入只读输入或远端；精确剩余工作已转入 B2。

## [2026-09-12] 步骤 20 / B2 完成：标准化 target clean-room 字节复现

- 只读审阅原 target projection、schema、config 与 package 后，将 Ahneman 的 frozen contract 参数化迁入 `rebuild_clean_room_sample.py`：固定 14 个 feature/label 列、`physical_dataset_id:reaction_id` key、按 physical/reaction/source-row 排序、RDKit canonical isomeric SMILES、unique desired/single-product structured percentage-YIELD、温度/反应时间单位换算，以及 Python CSV 的稳定序列化。
- 适配器仍只从 revision-pinned public Git LFS payload 读入 Parquet；它不接受 `../dataset`、`../ord-data`、staging 或缓存作为输入。baseline manifests/index 仅在输出完成后用于 hash 对照。
- 两次新建外部 download/output root 的独立重建均得到 output-root SHA-256 `b1e1504872a5e7247e81c5272cc30d46984e99116fc781fdb505d989eb9325af`。物理 CSV `7a3e939aefc95556611e253ad20a8e754d6353c627149908191b063b805cc4dd`、corpus `889ed18c722dde3ba1a2f0e745091f4a6e330c985e42a79369072dd288e9a27c`、target `dataset.csv` `6a912585bb987ab698e2502585e1927403c372e10d8e3bcf8ce26f93c4021acf` 均与冻结基线一致。
- fixture 覆盖无本地 payload 输入、RDKit canonical SMILES、feature-slot contract 和 reaction-ID 排序；locked 环境 `pytest`（6 项）与 Ruff 均通过。步骤 20 报告状态：`complete`。未进行远端写入。

## [2026-09-12] 发布计划修订：model-ready-only preview

- 按项目所有者的首发范围决策，`project-plan.md` 与 `goal.md` 新增 model-ready preview 轨道：只规划 19 个 target / 15 个 package 及其必要 catalog、provenance、许可证与文档。
- 规划依据为步骤 13 staging manifest：190 个 target-support 文件、`211,008,093` bytes，最大文件 `54,055,777` bytes。普通 Git 可作为候选传输，但最大文件超过 50 MiB 警告阈值，仍须在授权 pilot 中 clean-clone/readback 验证；LFS/object 后端仍可由 owner 选择。
- 41 个 corpus payload、所有 ORD Parquet 和 `_needs_review` payload 被明确排除。此变更不修改 payload、不重写既有 acceptance report、不表示 corpus 已发布，也不授权远端写入。
- 步骤 25～31 将以 preview 变体生成独立 catalog、inventory、lineage 子图、manifest、root hash 和不可变 tag；full corpus release 保留为有独立版本与验收的后续轨道。

## [2026-09-12] 步骤 26-preview 完成：原子生成独立 local RC

- 新增 `build_model_ready_preview_rc.py` 与 preview 专用 manifest schema。它从已验收 step-13 staging 读取并逐文件复核后，将 payload 复制到 Git 忽略的 `release-candidates/` 临时同级目录；所有 hash、preview catalog、artifact inventory、source closure、reference-only corpus lineage、documentation 和 manifest 完成后以单次 rename 提升。它拒绝覆盖既有 RC。
- 本次 local-only candidate 使用明确的非发布临时 ID `v0.0.0-model-ready-preview-local-rc`：19 target / 15 package / 190 target payload files，合计 `211,008,093` bytes；18 个固定 physical source、15 个 reference-only corpus node、52 个 lineage node 和 37 条完整边。release-tree root SHA-256 为 `ee9af36eb5efd7d42e63d68ffe028a9416bf4f0d3cdd7bacddfa65e8c38a159a`。
- `datasets/corpus/**` payload、所有 `.parquet` 和 `_needs_review` payload 均为 0；它们只可作为显式 excluded scope 或 provenance reference 存在。未改写既有 full-release draft manifest/graph，未移动仓库顶层 `datasets/model-ready/`，也未执行远端写入。

## [2026-09-12] 步骤 27-preview 完成：local RC 完整性验收

- 新增 `validate_model_ready_preview_rc.py`，独立复核 preview schema、19-record catalog、190-file inventory、per-target checksums/metadata/source links、53-source closure、两跳 reference-only lineage、root hash、scope/status wording 和 release-tree credential/email scan。
- 严格验收通过：blocking data-integrity failures 为 0，敏感扫描为 0，root hash 与生成时一致。唯一 warning 是 `pfizer-hte-lc-area-percent/audit.jsonl` 的 `54,055,777` bytes 超过普通 Git 50 MiB 警告阈值；它不是本地结构阻塞，但 pilot 必须完成 clean clone/readback。
- 状态是 `local_validation_passed_pending_owner_gates`，不是 upload acceptance。B3 仍需选定远端/transport 并授权可回读 pilot；B4 仍需冻结真实 version/tag 与 remote write `go`。步骤 26/27 报告记录在 `reports/release-acceptance/step-26-model-ready-preview-build.json` 与 `step-27-model-ready-preview-validation.json`。

## [2026-09-12] 步骤 25–31 preview 完成：发布、回读与收尾

- 所有者已选择公开 GitHub 仓库 `thinktraveller/ord-datasets` 和 ordinary Git。`pilot/v0.1.0-model-ready-preview-1` 在 `b224523…` 中覆盖 Ahneman（6,073,626 bytes）、Pfizer（69,097,967 bytes）以及发布 manifest；全新浅克隆回读逐文件一致，且无 LFS pointer/object。GitHub 对 Pfizer 的 54,055,777-byte 文件给出 >50 MiB 建议阈值警告，但接受传输。
- 以候选工作树的精确内容创建 `release/v0.1.0-model-ready-preview-1`，提交 `7d52dd2…`，并创建带注释 tag `v0.1.0-model-ready-preview-1`。GitHub prerelease 已发布；范围严格为 19 target / 15 package、190 个 target payload、211,008,093 bytes，release-tree root SHA-256 为 `24246a51ee47c36788892d813ec504eef53010aaf16af15c3e1774ef64b935e6`。
- 从远端 branch 重新 shallow-clone 后，release validator 通过：0 个 blocking check、0 个敏感扫描发现、0 个 owner gate。校验器同时修正为显式排除 clone-local `.git` 元数据，并添加回归测试；这不会排除或改变发布工作树中的任何文件。
- preview 发布闭环证据见 `step-25-model-ready-preview-pilot.json`、`step-29-model-ready-preview-v0.1.0-upload.json`、`step-30-model-ready-preview-v0.1.0-readback.json` 和 `step-31-model-ready-preview-closeout.json`。41 corpus、原始 Parquet 与 `_needs_review` 仍未发布，保留为独立的 full-release 轨道。
