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
