# 步骤 06：许可证边界审计

## 结论

本项目不能用一个总许可证覆盖所有输入。已冻结的 ORD 上游仓库 revision
26e17b78d9ab44a46a4b4327aa55c53549ec0596 明确将 data/ 与描述性元数据置于 CC BY-SA 4.0，将 scripts/
与 .github/ 置于 Apache-2.0。已处理数据及其派生元数据必须保留 CC BY-SA
4.0 的署名、链接、修改说明与相同方式共享要求；经明确文件头证明的代码可按
Apache-2.0 再分发。本记录是项目内的发布边界，不是针对单个第三方材料的法律意见。

本次审计不上传、不创建远端仓库或对象，也不将隔离材料提升为可发布。

## 固定证据

| 证据 | 固定位置 | SHA-256 |
| --- | --- | --- |
| ORD 数据许可证 | https://github.com/open-reaction-database/ord-data/blob/26e17b78d9ab44a46a4b4327aa55c53549ec0596/LICENSE | 5e436ff8ffbb77d8607220e9bce20c8915d860010feeb6c1ebef5a85688e9b39 |
| ORD 代码许可证 | https://github.com/open-reaction-database/ord-data/blob/26e17b78d9ab44a46a4b4327aa55c53549ec0596/LICENSE-CODE | c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4 |
| 上游双许可证说明 | https://github.com/open-reaction-database/ord-data/blob/26e17b78d9ab44a46a4b4327aa55c53549ec0596/README.md#license | 见冻结上游 revision |

完整逐对象裁决在 provenance/license-inventory.csv。输入 inventory SHA-256 为
5f12f84351a860121a4ad191cece809de01f992dac00cee453d155655cdb9dcc；它是步骤 04 的只读闭集，本步不改写其原始分类。

## 审计结果

- 审计对象：6050；普通文件：4349；活动候选文件：482。
- CC-BY-SA-4.0 数据或派生元数据、待步骤 07 敏感信息审计：440 个。
- 具有明确 Open Reaction Database Project Apache-2.0 文件头、待步骤 07 的代码：15 个。
- 缺乏文件头与内容同一上游证据的活动工作区代码：27 个；已拒绝进入 allowlist，等待权利人确认或不可变上游链接。
- 隔离材料：3855 个对象，均为 deny；excluded 与 superseded 对象也不在发布范围。
- 逐对象 allowlist 状态：pending_step_07 = 455；deny = 5595。前者不是上传许可。

## 发布规则

1. 数据、派生表、行级溯源和描述性元数据使用 LICENSE-DATA 的 CC BY-SA 4.0；保留 ORD Project 署名、上游固定链接、许可证链接和明确修改说明。
2. 仅明确 Apache 文件头证明的代码可使用 LICENSE-CODE；保留版权与 Apache notice。
3. NOASSERTION、withhold_unverified_workspace_code、quarantined、cache、第三方论文/图片/权重/未知二进制及 superseded 对象均为 deny，不能被项目根目录许可证覆盖。
4. 步骤 07 通过后才能生成受本边界约束的具体 upload allowlist；真正发布仍受质量、溯源、后端与人工 release gate 约束。

## 复制的许可证文本

- LICENSE-DATA 是冻结上游 LICENSE 的逐字副本。
- LICENSE-CODE 是冻结上游 LICENSE-CODE 的逐字副本。
- NOTICE 说明本项目的适用范围、归属和修改披露要求；它不授予未审计材料的权利。
