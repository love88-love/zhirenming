# 更新日志

## v1.4（2026-10-13）

记忆锚点触发机制 + 跨平台适配层（解决"该调没调"——技能装多了语义匹配漏触发，2026-10-12 实测翻车案例驱动）：

- **记忆锚点**：新增 `references/TRIGGER-RULE.md`（带 `ZHIRENMING-TRIGGER-RULE` v1 BEGIN/END 锚点；条件式措辞——技能卸载后残留规则自然落空，无副作用）；SKILL.md 新增 §0.6 记忆锚点确保（每次加载幂等检查：缺失→置顶插入、版本旧→整块替换、一致→跳过），把"模型扫技能列表做语义匹配"升级为"读记忆规则做确定性匹配"；写入后强制告知用户内容
- **跨平台适配层**：新增 `references/docs/PORTING.md`——三层解耦（L0 核心/L1 发现清单/L2 锚点适配）+ 平台探测算法 + 适配表（WorkBuddy→`user-*-personal/MEMORY.md` / Claude Code→`~/.claude/CLAUDE.md` / Codex→`~/.codex/AGENTS.md`，多平台共存各写一份）+ 豆包/DeepSeek 降级策略（无技能机制时移植为智能体人设/系统提示词，Python 脚本与本地画像降级方案）+ 移植验收清单；§0.6 第 1 步从写死 WorkBuddy 路径改为平台探测
- **INSTALL.md**：新增「触发规则锚点」节（代理代装立即写入 / 手动安装首触自举 / 卸载残留无害说明）+ 头部多平台安装指引
- **平台机制核实**（2026-10-13 联网）：Claude Code 支持 SessionStart hooks 可做真安装钩子（可选增强）；Codex 沙箱可能拦截写 home 目录、AGENTS.md 仅启动时读（写完须重启会话）；豆包/扣子无 SKILL.md 机制（触发问题在智能体形态下天然消失）

回归：本批次纯 markdown 改动，无脚本/schema 变更，20 夹具校验结论沿用 v1.3（退出码模式一致）。

## v1.3（2026-10-12）

触发与交互机制重设计（对应商业化第 0 步"服务化代跑"形态，需求反馈见 WorkBuddy 会话记录）：

- **自动触发矩阵**：frontmatter `description` 按"场景×人群"扩写（暧昧/相亲/crush/伴侣/同事/老板/朋友/室友/家人 × 拿不准/靠谱吗/怎么想的/怎么了解），新增突发场景（吵架想不明白/突然冷淡/这话什么意思）与"粘贴聊天记录求解读"入口；明确两类软边界（星座/算命/MBTI 可响应但"认可—声明—引导"不作推断依据；纯情绪倾诉先共情再轻引导、不拒答）与一类硬边界（操控/拿捏/挽回话术维持 §2 拒答）
- **§0.5 启动状态机（SKILL.md 新增）**：self.json 不存在时进入"知己优先"序列——主动读取设备记忆档案（WorkBuddy 用户级/工作区记忆、其他 AI 应用记忆文件、会话检索），不等预授权、仅敏感内容当场请求授权；记忆证据标 `memory_archive`、confidence 上限 medium（反巴纳姆纪律延伸）；降级访谈不承诺固定轮次，按回答信息量灵活追问，先采 3 核心维度出骨架
- **材料入口标准化**（02 号新增 §2.1）：叙述式 / 粘贴式（先证据抽取、复述确认再推断）/ 本机直读三分支；本机直读依赖用户自装的 `wechat-wcdb-local-extract`，未装可推荐安装，**必须用户本人设备 + 当场明确授权后才执行读取**
- **双向补盲**（03 号新增 §7.1 感受回采）：每条观察回填后必追问"当时你的感受与反应"，答案以 `self_reflection` 写入 self.json，匹配双侧画像在使用中自然长厚
- **匹配双侧闸门 + 证据底盘**：04 号前置检查新增 self 侧最低厚度（3 维度各 ≥1 条 medium 及以上）；报告 N4 前新增"证据底盘声明"（基于 X 条证据：你 Y 条、TA Z 条，实数不估算）
- **schema/脚本同步**：evidence.source 枚举 +`memory_archive`/`self_reflection`；`validate_profile.py` 双路径枚举同步，`--strict` 新增告警（active 推断标 high 但证据含 memory_archive）

回归验证：20 夹具全量校验退出码与改动前一致；memory_archive+medium 通过、+high 触发 strict 告警 1 条（软告警不阻断）。

备份：改动前文件备份于技能目录 `backups/20261012-pre-redesign/`（SKILL.md 存为 .bak 防索引抢占），回滚整目录覆盖。

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
