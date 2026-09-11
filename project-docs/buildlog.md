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
