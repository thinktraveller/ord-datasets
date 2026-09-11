# 步骤 07：敏感信息与危险内容发布闸门

## 结论

扫描了许可证初审通过的 455 个候选文件，并对每个文件复核冻结 SHA-256。
未发现凭证格式、credential/key 文件名或 source hash 漂移。发现 94 个原始
CSV 含 literal email 信号；它们集中在 53 个物理反应导出及其 41 个 logical corpus 表中。
原始 CSV 保持 deny，不能进入 upload allowlist。

这不是通过删除 provenance 或静默忽略 PII 来“放行”。项目已冻结结构化脱敏契约：后续
构建只可使用 sanitizer 生成的 derivative，并必须验证行数、列顺序、reaction ID、输入/输出
hash、聚合 JSON key-path 计数及无邮箱复扫。创建/修改时间和不含邮箱的 attribution name
均保留；只有值本身是 email 的 JSON dictionary field 或 list item 被移除。

## 检查范围与保密方式

- 候选文件：455；冻结 source hash 已验证：455。
- credential/token/private-key/credential URL 与 source drift finding：0。
- 无邮箱信号的文件：361；它们处于 eligible_pending_remaining_release_gates，仍非上传许可。
- 需要结构化邮箱脱敏的原始文件：94；状态为
  deny_until_sanitized_derivative_verified。
- 测试 fixture 的合成邮箱信号：1；不保存地址、
  片段、行文本或次数。

扫描器只处理命中文件路径。JSON 和本报告不保留 token、邮箱、上下文、行文本、匹配值、
本机绝对路径或每文件的命中次数。化学反应记录属于领域数据；本闸门不会把化学名称、
SMILES、条件或产率归为凭证或公开可操作的危险指令。

## 强制后续动作

1. 按 pipeline/policies/sensitive-data-redaction-policy.md 使用
   pipeline/scripts/sanitize_reaction_json_csv.py 生成物理与 corpus 的 redacted staging CSV。
2. 为每一份 derivative 保存无值 transformation audit，复扫后才从原始 deny 转为
   eligible_pending_remaining_release_gates。
3. 保持 provenance 中的冻结 source hash 与上游链接，以在不发布邮箱的前提下保留行级来源。
4. 继续接受步骤 08--25 的命名、schema、质量、溯源、存储和人工 release gates。
