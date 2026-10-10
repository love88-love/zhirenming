# 更新日志

## v1.2（2026-10-10）

第二轮审查后的修复批次（审查对话见 WorkBuddy 会话记录）：

- **悬空引用清零**：prompts/ethics/scripts 引用的 COPY-LIB、UIUX、SPEC、DETAIL-DESIGN 四份文档原不在技能包内，few-shot 与语言规范是死引用。四文档现随技能发布于 `references/docs/`；SKILL.md §5 索引补 4 行加载时机；四个 prompt 头部引用补全相对路径
- **脚本路径基准写死**（SKILL.md §3 新增「路径基准」）：`scripts/` 在技能安装目录（须用绝对路径），`zhibi-data/` 才相对当前工作区——此前 prompt 写 `python scripts/...` 相对路径，在工作区直接执行必报找不到文件
- **P1-4 日志机器化**：新增 `scripts/log_event.py`——10 个事件名枚举写死、只接受事件名+枚举参数（线索原文/claim/alias 在机制上写不进来）、JSONL 追加写、退出码 0/2。SKILL.md §3 与 prompts 01-04、ethics §2 的"记录日志"全部改为调脚本，禁手记
- **P1-3 依恋标签结构化**：schema 的 assessment 新增可选 `label` 字段（secure/anxious/avoidant/disorganized），仅 attachment 维度可用；jsonschema 与 fallback 双路径同步校验（位置限制由 `_label_placement_errors` 补齐，两模式结论一致）；dimensions.md 与 02 号 prompt 补用法说明
- **回归**：fixtures 17 → 20（新增 valid_attachment_label / mut_bad_label / mut_label_wrong_dim），jsonschema 与 fallback 两种模式 20/20 退出码符合预期

备份：改动前三处技能目录已整体备份至 `backups/2026-10-10-pre-p13-p14/`（117 文件），回滚直接整目录覆盖。

## v1.1（2026-10-09）

落实 QA 签发报告全部 5 项 advisory（A1-A5），并修复 1 处文案不一致：

- **A1 · AC-15 机器级兜底**：`validate_profile.py` 新增 `--strict` 软校验——active 推断标 `high` 但证据 <2 条且无 `user_observation` 直接观察时，stderr 告警并在 stdout 附带 `warnings` 数组；只告警不阻断，退出码不变
- **A2 · 消除文档漂移**：DETAIL-DESIGN §1.1 frontmatter `name` 回写为 `zhirenming`，与 SKILL.md 实际值及安装目录名一致
- **A3 · 埋点补全**：usage-log 十事件枚举中 `skill_triggered`（会话首次进入技能）与 `module_entered`（进入知己/知彼/补盲/匹配）在 SKILL.md §3 写死触发点
- **A4 · 消除双维护点**：知彼无线索拒答文案迁入 `ethics.md` §4 `EMPTY-ZHIBI` 锚点，02 号 prompt 改为原样注入；COPY-LIB §4.1 标注为设计稿存档
- **A5 · 回归集持久化**：QA 自造的 5 边界 + 5 变异用例从 `docs/qa-tmp/` 迁入 `skill/scripts/fixtures/`（夹具总数 7 → 17，只增不删）
- **附带修复**：COPY-LIB §3 匹配示范对话中 N4 分隔线与锚点不一致（7 vs 8 字符），统一为锚点版

回归验证：17 夹具全量校验退出码符合预期（含 `--strict` 对 mut_ac15 告警 1 条、valid_full 告警 0 条）；gap_scan match_ready 双向正确（true/false）。

## v1.0（2026-10-09）

首个交付版本。四模块（知己/知彼/补盲/匹配）+ N1-N5 定位提示系统 + 推断三元组数据模型（claim/confidence/evidence）+ 双脚本机器校验（validate_profile / gap_scan）。QA 两轮测试签发无条件交付：P0=0 / P1=0，AC 15/15 通过；安全审计 P2（零外发、零密钥、零网络行为）。
