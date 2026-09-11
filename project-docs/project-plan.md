# ord-datasets 构建与发布计划书

## 0. 计划状态

- 计划版本：`ord-datasets-plan-v1`
- 编制日期：2026-09-11（Asia/Shanghai）
- 目标仓库：`/home/wangzh685/桌面/ord-data/ord-datasets`
- 权威目标：`project-docs/goal.md`，当前包含 QA-R001～QA-R003。
- 当前项目状态：仓库内只有目标文档，尚未创建数据、处理中间件、pipeline、provenance 或发布目录。
- 本计划阶段只编制和提交 `project-docs/project-plan.md`，不复制约 42GB 数据，不改写 `ord-data/` 或 `dataset/`，不创建远端、不上传。

## 1. 不可破坏的项目基线

后续任何步骤若无法保持以下基线，必须停止并先更新目标文档，不得自行降低验收口径：

| 对象 | 基线 |
|---|---:|
| ORD 物理源数据集 | 53 |
| ORD Reaction 总数 | 2,428,291 |
| 逻辑全量数据集 | 41 |
| 逻辑全量 `reactions.csv` | 41 |
| 建模 package | 15 |
| 建模 target | 19 |
| 现有资产体量 | 约 42GB |
| `_needs_review` | 约 14GB，默认隔离审查 |

核心语义不变量：

1. `physical_dataset_id` 对应 ORD 中实际存在的一个物理源文件和固定 source path，是文件、hash 与行级溯源单位。
2. `logical_dataset_id` 是一个或多个 physical dataset 的非破坏 membership 视图，是语义组织和 corpus 发布单位；不得覆盖 physical ID。
3. `datasets/corpus/` 是完整权威语料，41 个 logical dataset 合计仍为 2,428,291 条 Reaction，不因建模资格删行。
4. `datasets/model-ready/` 是 19 个 target 的任务特定投影，允许有明确的 included/excluded，也允许同一 Reaction 进入多个 target。
5. corpus 与 model-ready 是不同契约，但不要求物理重复保存同一对象；catalog、manifest、hash 和对象后端负责引用。
6. 原始 `ord-data/data/**/*.parquet` 不进入新项目，53 个源文件必须有不可变版本链接和可验证 hash。
7. `ord-data/` 与 `dataset/` 在整个构建期间只读；所有新产物只写入 `ord-datasets/` 的受控 staging 或目标目录。

## 2. 执行原则与提交规则

### 2.1 写入边界

- 允许写入：`ord-datasets/`。
- 只读输入：同级 `ord-data/`、`dataset/`，以及外层既有 `project-docs/`。
- 禁止纳入：源仓库 `.git/`、虚拟环境、cache、credential、临时锁、未审权利文件。
- 每一步先写入 `.staging/<release-id>/<step-id>/` 或等价受控临时目录，通过验证后再提升为正式路径。
- 失败产物移动到该 release 的隔离区或保留失败 manifest；不得用宽泛递归删除清理来源目录。

### 2.2 提交边界

- 一个已完成步骤对应一个独立 commit；数据量过大的步骤可按明确分片拆 commit，但一个 commit 只表达一种结果。
- 提交前必须运行该步骤列出的验证，并保存机器可读摘要。
- 不提交半成品指针、缺失 LFS object、未通过 schema 的 manifest 或含绝对本机路径的配置。
- commit message 采用 `build(step-NN): <结果>`、`test(step-NN): <验收>` 或 `docs(step-NN): <说明>`。
- 若步骤失败，回到最近一个已验收 commit；保留失败记录，不重写或 force-push 已发布历史。

### 2.3 版本契约

所有 release artifact 至少绑定：

- `release_id` 与语义版本；
- `ord_upstream_revision` 与 53 个 source hash/LFS oid；
- `name_policy_version`；
- `logical_rule_version`；
- `projection_schema_version`；
- `target_policy_version`；
- `provenance_schema_version`；
- `pipeline_commit`；
- `artifact_sha256`。

版本或语义变化必须显式升级，不能通过覆盖同名文件隐藏。

## 3. 阶段依赖

```mermaid
flowchart LR
    P0[阶段 A：冻结与治理] --> P1[阶段 B：许可与命名]
    P1 --> P2[阶段 C：corpus 与 target]
    P2 --> P3[阶段 D：中间件与 pipeline]
    P3 --> P4[阶段 E：provenance]
    P4 --> P5[阶段 F：发布工程与 RC]
    P5 --> P6[阶段 G：授权上传与回读]
```

未经前一阶段闸门通过，不得启动后一阶段的批量搬运或远端写入。

## 4. 阶段 A：冻结输入与建立治理基线

### 步骤 01：创建最小项目骨架与安全边界

- 依赖：目标书已确认。
- 只读输入：`project-docs/goal.md`、当前 Git 状态。
- 允许写入：根目录发布说明骨架、空目录占位或目录 README、`.gitignore`；不得写入真实数据。
- 动作：建立目标书规定的 `datasets/`、`intermediate/`、`pipeline/`、`provenance/`、`reports/` 骨架；声明 source roots 为只读；配置 staging、cache 和 credential 排除规则。
- 输出：目录骨架、写入边界说明、路径约定。
- 验收：实际树与目标目录契约一致；无绝对 `/home/...` 路径写入可执行配置；Git 状态只含预期文件。
- 提交：`build(step-01): initialize publication skeleton`。
- 失败恢复：撤销本步骤新建的空骨架或修正路径；不得触碰两个来源目录。

### 步骤 02：冻结 ORD 上游 revision

- 依赖：步骤 01。
- 只读输入：`ord-data` remote、HEAD、`origin/main`、`data/`、LFS metadata。
- 允许写入：`intermediate/00-snapshot-inventory/`、`provenance/` 初始 manifest。
- 动作：确认公开可访问且与当前 53 个源文件内容相符的 upstream commit；记录 remote、revision、path、size、SHA-256、LFS oid 和 reaction count。规划时的 `83f971f...` 只能作为候选，必须重验。
- 输出：`ord-source-snapshot.json`、`source-files.initial.csv`。
- 验收：恰有 53 个生效源记录；当前本地 data tree 与所选公开 revision 无内容差异；总 Reaction 为 2,428,291。
- 提交：`build(step-02): freeze ORD source snapshot`。
- 失败恢复：保持 manifest 状态为 `blocked_revision_mismatch`，不继续转换或改用本地不可访问 commit。

### 步骤 03：冻结 dataset 工作快照

- 依赖：步骤 01。
- 只读输入：同级 `dataset/` 全树与现有 migration inventory。
- 允许写入：`intermediate/00-snapshot-inventory/`。
- 动作：流式统计全部文件、目录、大小、hash 或大文件可验证 oid；记录旧路径、文件类型、mtime、当前角色候选。缓存类对象可按规则聚合，但规则和数量必须留痕。
- 输出：`artifact-snapshot.csv`、`snapshot-summary.json`、扫描错误清单。
- 验收：文件数和总字节可对账；扫描错误为 0 或全部有阻塞记录；约 42GB 与 14GB `_needs_review` 规模差异有解释。
- 提交：`build(step-03): inventory legacy dataset workspace`。
- 失败恢复：保留本次扫描摘要并重跑失败分片；不得用不完整 inventory 开始搬运。

### 步骤 04：建立零遗漏 disposition 契约

- 依赖：步骤 03。
- 只读输入：artifact snapshot、目标范围。
- 允许写入：`provenance/artifact-inventory.csv`、`artifact-path-map.csv` 初版。
- 动作：为每个对象赋予 `authoritative`、`intermediate`、`superseded`、`quarantined`、`excluded` 或 `external-link-only`，并填写目标路径、reason、license candidate 和 step owner。
- 输出：全量 disposition 与 old→new path map。
- 验收：每个输入文件恰有一个 disposition；数量/字节分类求和等于 snapshot；无空 reason 的排除项。
- 提交：`build(step-04): classify every source artifact`。
- 失败恢复：保持未裁决项为 `quarantined`，不能默认发布或静默遗漏。

### 步骤 05：完成存储容量与后端预评估

- 依赖：步骤 03～04。
- 只读输入：对象体量、最大文件、重复 hash 分布、候选远端限制。
- 允许写入：`reports/release-acceptance/storage-preflight.md`、机器可读摘要。
- 动作：估算普通 Git、Git LFS、Hugging Face dataset 或版本化对象存储的容量、带宽、单文件和成本；设计去重与分片边界。
- 输出：storage decision proposal，不执行上传。
- 验收：明确普通 Git 禁止对象类型；给出最大对象、预计 LFS/object 字节、clone/download 模式和回读方案。
- 提交：`docs(step-05): document storage preflight`。
- 失败恢复：未选定后端不阻塞本地小文件工作，但阻塞批量大文件提升和所有远端上传。

### 阶段 A 闸门 / 里程碑 M1

- 53 个源文件、2,428,291 条 Reaction 与整个 `dataset/` 均已冻结。
- 每个现有对象都有 disposition。
- 上游 revision mismatch、inventory 漏项和未识别大文件均为 0。

## 5. 阶段 B：许可、敏感信息与语义契约

### 步骤 06：建立多许可证边界

- 依赖：步骤 02～04。
- 只读输入：`ord-data/LICENSE`、`LICENSE-CODE`、`README.md`、`CONTRIBUTING.md`，以及全部第三方 notice。
- 允许写入：许可审计报告、`LICENSE-DATA`、`LICENSE-CODE`、`LICENSES/` 草案、artifact license 字段。
- 动作：将数据/数据派生元数据标为 CC BY-SA 4.0，将合格代码标为 Apache-2.0；对外部论文、补充材料、权重、图片和未知二进制单独裁决。
- 输出：`license-inventory.csv`、`reports/license-audit/`、许可文本草案。
- 验收：所有计划上传对象都有 `license_id`、origin 与 redistribution status；unknown/restricted 不在 upload allowlist。
- 提交：`build(step-06): establish license boundaries`。
- 失败恢复：权利不明对象转 `quarantined`；不通过扩大仓库总许可证来“覆盖”第三方文件。

### 步骤 07：执行 secret、PII 与危险内容扫描

- 依赖：步骤 04、06。
- 只读输入：所有候选 publishable 文件。
- 允许写入：扫描规则、脱敏/排除决策和报告；不得原样写出检测到的 secret。
- 动作：扫描 token、credential、`.env`、带密钥 URL、个人邮箱和不必要身份信息；区分合法署名信息与无需发布的 provenance PII。
- 输出：`sensitive-data-audit.json`、disposition 更新。
- 验收：upload allowlist 中严重 secret/credential 为 0；脱敏不破坏 CC attribution 或行级溯源。
- 提交：`test(step-07): gate sensitive release content`。
- 失败恢复：命中对象隔离，轮换真实凭证后才能继续；报告只保存指纹和路径，不保存值。

### 步骤 08：生成 41 个 corpus 语义名称

- 依赖：步骤 02、04。
- 只读输入：`datasets.csv`、logical datasets/members、source evidence、goal naming policy。
- 允许写入：`provenance/semantic-name-map.csv`、命名审阅报告。
- 动作：从可靠 name/description、反应类别、DOI/上游来源生成 kebab-case slug；多成员 logical 使用共同语义；冲突追加稳定来源 key。
- 输出：41 条 corpus 映射、display name、中文名、aliases、policy version。
- 验收：41 logical 一对一、53 physical 全覆盖、slug 唯一且跨平台安全；无 UUID-only 顶层目录名。
- 提交：`build(step-08): define semantic corpus names`。
- 失败恢复：歧义项标 `needs_manual_name_review`，不得自动使用猜测名称进入正式目录。

### 步骤 09：生成 19 个 target 语义名称与状态契约

- 依赖：步骤 04、08。
- 只读输入：15 个 package manifest、19 个 target manifest、goal target 清单。
- 允许写入：semantic map、target catalog 初版。
- 动作：为每个 target 固化 slug、display name、label type/unit、logical/physical source set、included/excluded 和当前状态；保持 yield、conversion、LCMS area、relative area ratio、ee 的语义区别。
- 输出：19 条 target mapping。
- 验收：15 package/19 target 无遗漏；partial/blocked 未提升为 accepted；同一 Reaction 的多 target 关系允许且有说明。
- 提交：`build(step-09): define semantic target names`。
- 失败恢复：manifest 冲突触发 `blocked_target_manifest_conflict`，不擅自取任一版本覆盖。

### 步骤 10：冻结 catalog、metadata 与 schema 契约

- 依赖：步骤 06～09。
- 只读输入：goal directory/provenance contracts、现有 schema。
- 允许写入：`pipeline/schemas/`、`pipeline/policies/` 和 sample fixtures。
- 动作：定义 catalog、per-dataset metadata、source links、artifact inventory、row map、transformation、release manifest 的列、类型、nullable、枚举和版本升级规则。
- 输出：JSON Schema/CSV schema、字段字典、示例记录。
- 验收：schema 能表达 physical→logical→target、多来源、included/excluded、license、hash 和固定 URL；示例全部通过校验。
- 提交：`build(step-10): freeze release metadata contracts`。
- 失败恢复：schema 变更在本阶段升版；进入数据搬运后禁止无版本覆盖。

### 阶段 B 闸门 / 里程碑 M2

- 所有候选文件具有许可与敏感信息处置。
- 41 corpus 与 19 target 具有唯一语义名称。
- catalog、metadata、provenance schema 已冻结并有测试 fixture。

## 6. 阶段 C：构建最终 datasets 层

### 步骤 11：构建 41 个 corpus staging 包

- 依赖：阶段 B 全部通过。
- 只读输入：`dataset/standardized/derived/csv/tables/`、logical/member manifests、semantic map。
- 允许写入：`.staging/<release>/datasets/corpus/`。
- 动作：将 41 个 `reactions.csv` 映射到语义目录；生成 metadata、schema、source links 与 checksums。无格式变更时保持内容 hash；任何转码均作为新 transformation。
- 输出：41 个 corpus staging 目录。
- 验收：每个表仍含 `physical_dataset_id,source_file,reaction_id,row_index`；41 表合计 2,428,291 行，53 physical 全覆盖，logical membership 唯一。
- 提交：先提交小型 manifest；大文件仅在步骤 22 后端就绪后提交对象指针。commit 说明 `build(step-11)`。
- 失败恢复：失败 logical 单独隔离并重建；已通过表不重写，source 文件不动。

### 步骤 12：执行 corpus 全量验收

- 依赖：步骤 11。
- 只读输入：corpus staging、source/export manifests。
- 允许写入：corpus validation reports。
- 动作：校验 schema、CSV 可解析性、行数、reaction key、source row 范围、hash、membership、重复 physical assignment 和确定性排序。
- 输出：per-corpus 与总体验收报告。
- 验收：41/41 通过；总行数精确为 2,428,291；孤儿 physical、未知 logical、计数漂移和无 source link 均为 0。
- 提交：`test(step-12): validate complete corpus layer`。
- 失败恢复：只回退失败 logical 的 staging 提升，修复后重跑其分片和总汇总。

### 步骤 13：构建 19 个 model-ready staging 包

- 依赖：步骤 09～12。
- 只读输入：`dataset/processing/derived/yonod/datasets/` 中 package/target files。
- 允许写入：`.staging/<release>/datasets/model-ready/`。
- 动作：按 target slug 组织 dataset、schema、YONOD config、exclusions、row map、audit 和 metadata；保留 package/logical/physical ID 与原 target status。
- 输出：19 个 target staging 目录。
- 验收：每个 target 的 included/excluded、label 字段、量纲、输出 hash 与原 manifest 对账；一个 logical 可有多个 target；不得把 task 行数用于 corpus 守恒。
- 提交：与步骤 11 相同，先小型 metadata、后大对象；commit 说明 `build(step-13)`。
- 失败恢复：单 target 隔离；不得因一个 target 失败阻断已验证 corpus，也不得删除 exclusion/audit 来“通过”。

### 步骤 14：执行 model-ready 全量验收

- 依赖：步骤 13。
- 只读输入：19 个 staging target、原 package manifests。
- 允许写入：target validation reports。
- 动作：检查 schema/config、标签语义、included+excluded 对账、row map 唯一性、源索引范围、状态、特征 denylist 和无标签泄漏规则。
- 输出：19 个 target 验收与 package 汇总。
- 验收：19/19 有明确发布状态；generated 数据通过结构验收；partial/blocked 保持原状态并有原因，不能被报告为 benchmark accepted。
- 提交：`test(step-14): validate model-ready targets`。
- 失败恢复：标记 target `release_blocked` 或修复可重建错误；禁止手改数据绕过 manifest。

### 步骤 15：生成统一 catalog 视图

- 依赖：步骤 12、14。
- 只读输入：41 corpus、19 target metadata 与 semantic maps。
- 允许写入：`datasets/catalog.csv`、`catalog.json`。
- 动作：生成面向用户的 corpus/task 双视图，关联 logical/physical/target、状态、行数、source links、license 和对象位置。
- 输出：双格式 catalog。
- 验收：41 条 corpus、19 条 model-ready 生效记录；JSON/CSV 语义一致；从任一 target 可回到 corpus 和 source set。
- 提交：`build(step-15): publish unified dataset catalog`。
- 失败恢复：重新由 metadata 生成，不手工修改其中一份格式。

### 阶段 C 闸门 / 里程碑 M3

- 41 个 corpus 与 19 个 target 均有可验证 staging 包。
- corpus 完整性与 model-ready 任务完整性分别验收，没有口径混淆。
- catalog 能同时服务语料用户和建模用户。

## 7. 阶段 D：归档中间资产并抽取 pipeline

### 步骤 16：归档 00～04 阶段中间资产

- 依赖：步骤 04、10、15。
- 只读输入：migration、physical CSV、CSV manifests、inventory、field profiles。
- 允许写入：`intermediate/00-04/` staging。
- 动作：按 snapshot、physical conversion、source evidence、logical assembly、field profiling 分类；保留旧路径、hash、生成步骤、状态和替代关系。
- 输出：00～04 中间资产与 index。
- 验收：53 physical CSV、一组逻辑/来源 manifests 和字段分析文件可对账；authoritative 与 superseded 不混淆。
- 提交：按阶段拆分 `build(step-16a..e)`，每个 commit 有独立 index/hash。
- 失败恢复：失败分组隔离重试；不覆盖最终 corpus。

### 步骤 17：归档 05～08 阶段中间资产

- 依赖：步骤 13～16。
- 只读输入：projection、target adaptation、formal configs、testsets、runs 和数据相关 reports。
- 允许写入：`intermediate/05-08/` staging、`reports/`。
- 动作：区分模型投影、target 适配、验证配置和验收报告；只纳入数据生成/验收必需内容，模型权重另审。
- 输出：05～08 中间资产与 run/report index。
- 验收：15 package/19 target 的必要生成证据可重建；无 credential、cache 或权利不明模型对象混入。
- 提交：按阶段拆分 `build(step-17a..d)`。
- 失败恢复：非必要模型结果可 `excluded`，但必须保留 disposition 与理由。

### 步骤 18：处理 `_needs_review`

- 依赖：步骤 03～07。
- 只读输入：`dataset/processing/_needs_review/`。
- 允许写入：`intermediate/90-legacy-needs-review/` 的 manifest/获准对象，隔离报告。
- 动作：按 hash 去重，判断 publishable、superseded、quarantined、excluded；不将其计入 authoritative corpus/target。
- 输出：逐文件审阅表、去重关系和首发 inclusion proposal。
- 验收：约 14GB 全部有 disposition；没有待审对象默认为公开；与权威产物同 hash 的对象只存一次并记录 alias。
- 提交：`build(step-18): classify legacy review artifacts`。
- 失败恢复：未完成审阅的对象保持隔离，可不进入首发大对象，但 manifest 必须进入 RC。

### 步骤 19：抽取生产 pipeline

- 依赖：步骤 10、16～18。
- 只读输入：`dataset/processing/scripts/`、相关配置与现有依赖文件。
- 允许写入：`pipeline/scripts/`、`tests/`、`configs/`、`schemas/`、`policies/`、`workflows/`、依赖锁。
- 动作：移植生产脚本和测试，删除 cache，替换绝对路径，统一 CLI/任务图；记录原代码 commit 与 Apache notice。
- 输出：可安装、可按单数据集/全量运行的 pipeline。
- 验收：静态检查、单元测试通过；所有输出位置参数化；没有写入只读 source root 的代码路径。
- 提交：可按模块拆分 `build(step-19)` 与 `test(step-19)`，每个 commit 保持测试通过。
- 失败恢复：保留原脚本只读，逐模块移植；不在来源脚本上直接打补丁。

### 步骤 20：执行 clean-room 小样本重建

- 依赖：步骤 19。
- 只读输入：固定 source manifest、代表性小数据集、pipeline。
- 允许写入：临时 clean-room 与 `reports/release-acceptance/`。
- 动作：从公开 source URL 获取一个源文件，重建 physical CSV、logical corpus、至少一个 target 和 provenance；不复用本地中间 cache。
- 输出：重建产物、命令、资源和 hash 报告。
- 验收：结果与 staging 基线 hash/语义一致；失败可由日志定位；依赖锁可在干净环境解析。
- 提交：`test(step-20): reproduce sample from pinned source`。
- 失败恢复：保留失败 run manifest，修复 pipeline 后从空临时目录重跑。

### 阶段 D 闸门 / 里程碑 M4

- 所有中间文件有阶段与 disposition。
- `_needs_review` 不污染权威数据。
- pipeline 可从固定源链接重建代表性端到端样本。

## 8. 阶段 E：建立四级 provenance

### 步骤 21：完成源文件与数据集级 provenance

- 依赖：步骤 02、08～15。
- 只读输入：source snapshot、logical manifests、package manifests、catalog。
- 允许写入：`provenance/source-files.csv`、physical/logical/member/target manifests。
- 动作：生成 53 physical、41 logical、53 membership、15 package/19 target 的规范关系；将 `/blob/main/` 改为 hash 匹配的固定 commit URL。
- 输出：数据集级 provenance 表。
- 验收：53/41/53/15/19 计数准确；多成员 logical 列出所有源文件；仅 DOI 或可变 main URL 的生效记录为 0。
- 提交：`build(step-21): publish dataset provenance maps`。
- 失败恢复：无法验证链接的记录设为 blocked，不生成虚假 direct URL。

### 步骤 22：完成行级 lineage

- 依赖：步骤 12～14、21。
- 只读输入：corpus 行、target row maps、exclusions、row audits。
- 允许写入：per-dataset row lineage index、验证摘要。
- 动作：验证 corpus 的 physical/source/reaction/row_index 与 target 的 reaction_key/source_row_index；included 与 excluded 均建立路径。
- 输出：行级索引和两跳查询示例。
- 验收：任一抽样最终行最多两跳得到 fixed source URL、source hash、physical ID 和 reaction ID；孤儿、越界、多义映射为 0。
- 提交：`build(step-22): validate row-level lineage`。
- 失败恢复：按 target/logical 隔离失败映射，不通过猜测 reaction 顺序修复。

### 步骤 23：完成 transformation graph 与 release hash tree

- 依赖：步骤 16～22。
- 只读输入：所有 artifact/index、pipeline commits、运行记录。
- 允许写入：`transformations.jsonl`、`lineage-edges.csv`、`release-manifest.json` 草案。
- 动作：以 artifact hash 为节点，连接 source→physical CSV→logical corpus→projection→target；记录命令、配置、版本、时间和状态；生成 root hash。
- 输出：完整 provenance graph 和 release manifest RC。
- 验收：所有 publishable artifact 在 graph 中可达；所有 graph 节点在 inventory 中存在；root hash 可重复计算。
- 提交：`build(step-23): assemble release lineage graph`。
- 失败恢复：禁止手改 root hash；修正源 manifest 后整体重算受影响子树。

### 阶段 E 闸门 / 里程碑 M5

- 文件、数据集、步骤、行四级 provenance 全部闭合。
- 53 个原 Parquet 均有固定来源链接。
- 任一 target 行能回到 corpus、physical dataset 和源文件。

## 9. 阶段 F：发布工程与 Release Candidate

### 步骤 24：完成顶层文档、署名与使用说明

- 依赖：步骤 06、15、21～23。
- 只读输入：许可审计、catalog、provenance、pipeline CLI。
- 允许写入：README、NOTICE、CITATION、许可文件、数据卡和下载/重建示例。
- 动作：解释三层口径、corpus/model-ready 差异、partial/blocked 状态、磁盘需求、下载、citation、许可和两跳溯源。
- 输出：面向发布的完整小文件文档。
- 验收：链接和示例由 CI 校验；许可范围不混淆；不宣称 blocked benchmark 已完成。
- 提交：`docs(step-24): document dataset release`。
- 失败恢复：文档错误独立修正，不重写数据对象。

### 步骤 25：执行大文件后端 pilot

- 依赖：步骤 05、11～18、23。
- 只读输入：最小文件、代表性 CSV/JSONL、最大 corpus 分片和 storage proposal。
- 允许写入：大文件配置、测试对象、pilot 报告；远端测试需用户授权。
- 动作：验证 Git LFS 配额、push/pull、pointer 完整性、clone 行为和回读 hash；若不满足，验证同名 HF dataset/对象存储及固定 revision manifest。
- 输出：最终 backend decision、`.gitattributes`/对象配置、pilot acceptance。
- 验收：普通 Git 无大 blob；所有 pointer 有对象；代表性对象可从全新环境回读且 hash 一致。
- 提交：`build(step-25): configure release object storage`。
- 失败恢复：删除/撤回仅限明确 pilot 对象；切换后端须保留决策记录和旧 pilot disposition。

### 步骤 26：提升 staging 并生成 Release Candidate

- 依赖：步骤 24～25 及前序所有阶段闸门。
- 只读输入：已验证 staging 与 release manifest 草案。
- 允许写入：目标正式目录和 RC tag 所需 manifest；尚不公开上传。
- 动作：原子化提升 41 corpus、19 target、中间资产、pipeline、provenance 与 reports；生成最终文件数、总字节、分片、hash 和状态汇总。
- 输出：本地 release candidate。
- 验收：目标树无 staging 临时引用；release root hash 稳定；Git/LFS/object 状态完整。
- 提交：可按对象分片提交，最后 `build(step-26): assemble release candidate`。
- 失败恢复：保留已验收对象，撤销本次提升映射；不得重打已存在的不可变 RC tag。

### 步骤 27：运行发布前全量验收

- 依赖：步骤 26。
- 只读输入：完整 RC。
- 允许写入：`reports/release-acceptance/` 最终报告。
- 动作：运行计数、schema、JSON、hash、link、license、secret/PII、路径、对象可取回、幂等和 provenance 检查。
- 输出：机器可读 summary 与 Markdown 报告。
- 验收：所有 blocking check 为 0；warning 有 owner/reason；第 12 节测试矩阵全部满足。
- 提交：`test(step-27): accept release candidate`。
- 失败恢复：RC 标记 rejected，修复具体步骤并重算受影响 hash；不带失败报告进入正式发布。

### 阶段 F 闸门 / 里程碑 M6

- 本地 RC 完整且全量验收通过。
- 大对象后端已通过回读 pilot。
- 远端、版本、首发内容选择成为仅剩的用户授权项。

## 10. 阶段 G：授权上传与公开回读

### 步骤 28：获取发布授权并冻结 release 决策

- 依赖：M6。
- 需要用户明确确认：远端 URL/owner、release 版本、后端/额度、`_needs_review` 首发范围、partial/blocked target 展示方式。
- 允许写入：release decision record；不在授权前执行远端写入。
- 输出：带时间和操作者的 go/no-go 决策。
- 验收：五项选择均明确，凭证通过安全渠道存在但不入库。
- 提交：`docs(step-28): record release decision`。
- 失败恢复：未授权即保持本地 RC，不视为构建失败。

### 步骤 29：上传并创建不可变 release

- 依赖：步骤 28 的 go 决策。
- 只读输入：已验收 RC、upload manifest。
- 允许写入：用户授权的目标远端、release tag/对象后端。
- 动作：先小文件与 manifest，后分片大对象；逐对象校验；最后创建 tag/release，不强推、不覆盖同版本。
- 输出：公开或指定可见性的项目、对象 revision、release URL。
- 验收：远端 commit/tag 与 manifest 一致；所有 object 可取回；上传对象数/字节/hash 对账。
- 提交：本地记录 `release(step-29): publish <version>`；远端 tag 不可变。
- 失败恢复：停止未完成队列并保留 upload checkpoint；不覆盖已成功对象，按 manifest 断点续传。若需撤回，发布撤回说明而不伪造历史。

### 步骤 30：无缓存回读与重建验收

- 依赖：步骤 29。
- 只读输入：公开远端与 source URLs。
- 允许写入：独立临时环境、最终验收报告。
- 动作：从无本地缓存环境 clone/下载 catalog、小数据集、最大数据集分片和一个完整 target；验证 lineage；运行 sample rebuild。
- 输出：remote-readback report、最终 root hash 对账。
- 验收：远端 root hash 与 RC 一致；下载说明可执行；source links 可访问；样本重建一致。
- 提交：`test(step-30): verify published release`。
- 失败恢复：标记 release degraded/withdrawn，修复下载/对象问题后发布补丁版本；不覆盖原 tag。

### 步骤 31：项目收尾与维护基线

- 依赖：步骤 30。
- 允许写入：维护说明、issue/backlog、下一版变更策略。
- 动作：记录最终计数、版本、已知 partial/blocked、待审 backlog、更新 ORD revision 的流程和兼容策略。
- 输出：closeout summary、maintenance runbook。
- 验收：所有步骤状态明确；无未归属 blocking issue；后续增量 release 可复用 pipeline/provenance。
- 提交：`docs(step-31): close initial ord-datasets release`。
- 失败恢复：未完成维护项进入有 owner 的 backlog，不虚假标记项目完成。

### 阶段 G 闸门 / 里程碑 M7

- 远端 release 可下载、可校验、可追溯、可引用。
- clean-room 回读和重建通过。
- 初始版本具备明确维护入口。

## 11. 决策闸门

以下决策不阻塞计划书完成，但会阻塞对应实施步骤：

| ID | 最晚决策点 | 必须由用户/项目所有者确认 |
|---|---|---|
| D1 | 步骤 25 前 | GitHub Git LFS、Hugging Face dataset 或其他对象后端及额度 |
| D2 | 步骤 28 | 远端仓库 URL、owner、visibility 与授权账号 |
| D3 | 步骤 26/28 | `_needs_review` 是随首发隔离发布，还是仅发布 manifest 后延期对象 |
| D4 | 步骤 24/28 | partial/blocked target 是否随首发发布；若发布，必须保留显著状态 |
| D5 | 步骤 28 | 初始语义版本、tag 和 release 名称 |

默认安全行为：没有决定就停在本地已验收 RC，不执行远端写入，也不将待审对象自动转为公开。

## 12. 测试矩阵

| 测试域 | 单元/fixture | 分片 smoke | 全量 RC | 远端回读 |
|---|---|---|---|---|
| physical source 数与 hash | 解析 1 条 source record | 下载 1 个小源文件 | 53/53 hash/URL | 抽样 source URL |
| corpus 数与行数 | schema fixture | 1 个单成员 + 1 个多成员 logical | 41 表、2,428,291 行 | 小/最大分片读取 |
| physical→logical membership | 规则 fixture | 多成员组 | 53 membership 唯一 | catalog 查询 |
| model-ready target | target fixture | 至少 yield + conversion | 15 package/19 target | 下载并加载 1 target |
| included/excluded | 决策 fixture | 含排除 target | 19 target 全对账 | row-map 抽样 |
| 语义命名 | slug/collision 单测 | DOI 与 physical 后缀例 | 41+19 唯一 | 大小写路径验证 |
| schema/JSON/CSV | 合法/非法 fixture | 代表性多值行 | 全文件验证 | 客户端解析 |
| 行级 lineage | 两跳 fixture | included + excluded | 孤儿/越界为 0 | 远端两跳示例 |
| transformation graph | 小 DAG | 单 target 链 | 所有 artifact 可达 | root hash 对账 |
| 许可/署名 | license enum | 代表性 data/code | unknown/restricted=0 | README/NOTICE 可见 |
| secret/PII | 合成 secret fixture | 候选目录 | blocking finding=0 | 发布树复扫 |
| 大文件存储 | pointer fixture | pilot push/pull | object 全可取回 | clean clone/download |
| 幂等重建 | 小输入两次运行 | 单 logical/target | 可复算 hash 摘要 | clean-room sample |

所有全量测试都必须产生机器可读结果；只在终端打印“通过”不构成验收证据。

## 13. 里程碑总览

| 里程碑 | 交付结果 | 放行条件 |
|---|---|---|
| M0 | 目标与计划已提交 | goal/plan 无冲突，当前仍无数据搬运 |
| M1 | 输入冻结与零遗漏 inventory | 53 source、dataset 全树、disposition 对账 |
| M2 | 许可与语义契约 | license/secret gate 通过，41+19 名称与 schema 冻结 |
| M3 | 数据集 staging | 41 corpus、19 target 分别验收 |
| M4 | 中间资产与 pipeline | 每步中间件有去向，clean-room smoke 通过 |
| M5 | 四级 provenance | 文件/数据集/步骤/行 lineage 闭合 |
| M6 | 本地 RC | 大文件 pilot 与全量验收通过 |
| M7 | 公开 release | 授权上传、无缓存回读与重建通过 |

## 14. 最终 Definition of Done

项目只有同时满足以下条件才能标记初始版本完成：

1. `datasets/corpus/` 有且仅有 41 个语义数据集，覆盖 53 个 physical ID 和全部 2,428,291 条 Reaction。
2. `datasets/model-ready/` 有 19 个 target，15 个 package 的 included/excluded、label 语义、schema、config 和 status 与原 manifest 对账。
3. corpus 与 model-ready 在目录、catalog、计数和验收中保持独立契约，没有把任务筛选结果冒充全量语料。
4. `dataset/` 原有每个文件都有 disposition；`_needs_review` 全部审计且未污染 authoritative 层。
5. 所有发布数据/数据元数据符合 CC BY-SA 4.0 署名、修改和 ShareAlike 条件；代码为 Apache-2.0；第三方对象有独立许可。
6. 53 个原 ORD Parquet 均有公开、不可变、经 hash 验证的 source file URL；没有只指向 `main` 或只给 DOI 的源记录。
7. 任一最终行可在两跳内回到 physical dataset、源文件、source row/reaction 和固定 URL；included 与 excluded 均覆盖。
8. pipeline 可在干净环境从固定源链接重建代表性 physical→logical→target 链，版本与 hash 可复核。
9. 所有大文件通过已验证的 LFS/object backend 提供，普通 Git 无超限 blob，远端回读 root hash 与本地 RC 一致。
10. release manifest、catalog、NOTICE、CITATION、README、许可、数据质量和验收报告完整；partial/blocked 状态没有被篡改。
11. secret、credential、未授权第三方整文件和无必要个人信息不在 upload manifest。
12. 用户已确认远端、版本、存储与首发范围；release tag 不可变，clean-room 回读通过。

## 15. Planner 阶段完成边界

本计划书提交即代表 planner 阶段完成。下一步应由 builder 按步骤 01 开始实施，并在每一步完成后更新构建日志和提交对应产物。本计划本身不授权删除来源数据、上传远端、购买存储额度、公开待审对象或改变目标书中的 53/41/15/19 基线。
