# 更新日志

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
