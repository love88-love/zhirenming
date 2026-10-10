# 知人明 · 详细设计文档（Phase 2）

> 生成日期：2026-10-09 ｜ 作者：高见远（首席架构师）
> 依据：`docs/SPEC.md` v1.0（唯一开发契约）+ `docs/ARCHITECTURE.md` v1.0 + `docs/UIUX.md` v1.0
> 范围声明：本文给出**逐文件可施工规格**（结构、接口、接入点、纪律），不含 prompt 完整散文正文——正文撰写属 Phase 3 开发任务。
> 机器契约产物 `skill/references/schemas/profile.schema.json` 已随本文同步落盘。

---

## 0. 最终目录树（Task 8）

```
D:\Workbuddy\知人明\skill\                     # 技能包本体（可分发的单元）
├── SKILL.md                                  # 主入口：frontmatter、四模块路由、全局硬约束（<3000 字）
├── references/                               # 按需加载（Progressive Disclosure）
│   ├── prompts/
│   │   ├── 01-zhiji-interview.md             # 知己：事件式访谈引擎
│   │   ├── 02-zhibi-inference.md             # 知彼：线索录入与画像推断
│   │   ├── 03-bubuang-gap.md                 # 补盲：缺口解读与观察任务生成
│   │   └── 04-pipei-match.md                 # 匹配：双画像对比与相处建议
│   ├── schemas/
│   │   ├── profile.schema.json               # 【已落盘】画像唯一合法形状（draft-07）
│   │   └── dimensions.md                     # 维度清单、判定锚点、置信度校准表、反巴纳姆规范
│   ├── theory/
│   │   ├── big-five.md                       # 大五人格行为锚点表
│   │   ├── attachment.md                     # 依恋类型行为锚点
│   │   ├── communication.md                  # 沟通风格行为锚点
│   │   └── mbti-display.md                   # MBTI 展示层翻译规则（不作推断依据）
│   └── ethics.md                             # 伦理红线 + 隐私声明 + 拒答话术 + N1-N5 文案源（单一维护点）
└── scripts/
    ├── validate_profile.py                   # Schema 校验（写入后必跑，含无 jsonschema 的 fallback）
    └── gap_scan.py                           # 覆盖率/缺口扫描（补盲第一步必跑，纯确定性）

<用户工作区>/zhibi-data\                       # 用户数据目录（技能之外，本地私有）
├── profiles/
│   ├── self.json                             # 自我画像（知己产出）
│   └── <alias>.json                          # 他人画像（一人一档，知彼产出）
├── usage-log.jsonl                           # 本地埋点日志（格式见 §6，禁记线索原文与画像内容）
└── PRIVACY.md                                # 数据说明与删除指引（首次运行时生成）
```

**与架构文档的偏差（1 处，需回写）**：架构文档 §1.1 的技能包路径为 `skill/zhibi/`，本设计按单技能项目扁平化为 `skill/` 根目录（取消 `zhibi` 嵌套层，路径更短、分发单元即目录本身）。架构文档 §1.1 与 §5 目录树相应行需同步更新。另补：架构目录树遗漏的 `usage-log.jsonl`（Spec §6 已定契约）已补入数据目录。

---

## 1. SKILL.md 骨架定稿（<3000 字总预算）

### 1.1 Frontmatter

```yaml
---
name: zhirenming  # v1.1 回写（QA-A2）：技能命名规范要求小写英文，与 SKILL.md 实际 frontmatter 及安装目录名一致；中文品牌名「知人明」用于展示层
description: >-
  AI 关系理解技能：知己（事件式访谈建自我画像）、知彼（线索推理他人画像，
  带置信度与证据链）、补盲（识别信息缺口，生成观察任务与提问话术）、
  匹配（双画像对比，输出相对性结论与相处建议）。
  触发词：认识自己、了解自己、自我画像、分析某人、帮我看看TA、
  还该了解什么、怎么进一步了解、我们合不合、匹配一下。
---
```

触发词设计原则：覆盖 Spec §7 七条流程的入口意图原文（"认识自己/了解自己"、"分析某人/帮我看看TA"、"还该了解什么/怎么进一步了解"、"我们合不合/匹配一下"），口语化、不含品牌名硬依赖。

### 1.2 章节骨架与字数预算

| 节 | 内容 | 预算 |
|----|------|------|
| §0 角色一句话 | "我是知人明——一个帮你把零散线索变成有依据理解的观察型朋友。辅助你判断，不替你做决定。" | 80 字 |
| §1 四模块路由表 | 见 §1.3 | 400 字 |
| §2 全局硬约束（内联，不引用） | 见 §1.4 | 900 字 |
| §3 画像读写纪律 | 见 §1.5 | 500 字 |
| §4 压实保真清单 | 见 §1.6 | 250 字 |
| §5 references 索引表 | 文件路径 → 加载时机，一行一个 | 400 字 |
| **合计** | | **约 2500 字，留 500 字余量** |

### 1.3 四模块路由表（覆盖 Spec §7 七条流程）

| 用户意图信号 | 路由目标 | 前置条件 | 提示节点 |
|--------------|----------|----------|----------|
| 首次触发技能 / 未建档 | 首次引导流程（本文 §2 N1 块 + 四模块导览 + 建档建议） | 检查 `zhibi-data/` 是否存在 | N1 |
| "认识自己/了解自己/自我画像" | `references/prompts/01-zhiji-interview.md` | 无 | N2 |
| "分析某人/帮我看看TA/给TA建档" | `references/prompts/02-zhibi-inference.md` | 无（无线索走拒答分支） | N2 |
| "还该了解什么/怎么进一步了解/观察什么" | `references/prompts/03-bubuang-gap.md` | 目标画像已存在 | N3 |
| "我们合不合/匹配一下/合不合适" | `references/prompts/04-pipei-match.md` | self.json + 对方画像齐备 | N4 |
| 用户带回新观察/新证据 | 02 号（证据回填）或 03 号（补盲回填入口） | 对应画像已存在 | — |
| 操控类请求（"教我拿捏/套路TA"） | 不走任何模块，按 `references/ethics.md` 拒答分支处理 | — | — |

路由纪律：意图模糊时先澄清（"你是想聊聊自己，还是想分析一个人？"），禁止猜测式进入模块。

### 1.4 全局硬约束内联清单（五项，全文内联不放 references）

1. **伦理红线一句话版**：「不教操控，只给理解——拒绝一切拿捏、套路、PUA 类请求；输出怎么相处更好，绝不输出怎么控制对方。完整边界见 references/ethics.md，每次会话必读。」
2. **推断三要素**：「每条推断必须带 claim（具体可证伪）+ confidence（high/medium/low，先数证据再定级）+ evidence（用户原话引用，≥1 条）；证据不足就明说不足，禁止编造。」
3. **N1 定位声明固定文案块**：内联全文（占位：`【N1 块——镜像自 ethics.md §4 N1 锚点，改文案只改 ethics.md 后同步此处】`）。文案基调：温和、朋友口吻，一次说清三要素（辅助而非决定 / 真实接触 / 独立判断）。字数预算 150 字内。
4. **隐私红线**：「画像数据只读写用户本地 `zhibi-data/` 目录，不得发往任何外部服务；建档时主动建议化名，不要真名。」
5. **定位提示纪律**：「N2/N3/N4 提示文案一律从 ethics.md §4 对应锚点原样引用，禁止自行改写或省略（文案只维护一处，见本文 §7）。」

### 1.5 画像读写纪律（写死四步）

1. **读**：写前必读当前画像文件全文（不存在则按 schema 建骨架）
2. **局部修改**：只更新目标维度的 assessments，禁止整文件重写式覆盖
3. **校验**：写入后必跑 `scripts/validate_profile.py`（命令与退出码见本文 §5.1）
4. **写回**：校验通过才落盘；**校验失败带错误信息回炉重写，且不得覆盖原文件**（AC-10）

### 1.6 压实保真清单（上下文压缩时必须保住的四要素）

1. 当前画像文件路径（self 或哪个 alias）
2. 当前所在模块与推进到的维度
3. 未覆盖缺口清单（最近一次 gap_scan 结论）
4. 最近一次 validate_profile.py 校验结果

---

## 2. 四个 prompt 文件结构规格

> 通用约束（四文件共用，写入每个文件开头）：
> - 语言规范：UIUX §2 全文为强约束（短句 ≤25 字、置信度措辞三级映射、慎用词 ≤1 次、禁用词清单触碰即返工）
> - 语气素材：对应 UIUX §3.x 语气脚本为 few-shot 素材位（引用，不全文复制）
> - 提示文案：N 节点提示一律标注 `【注入 ethics.md §4 N-x 块，原样输出】`，不写正文
> - 伦理：任何操控类请求跳转 ethics.md 拒答分支

### 2.1 `01-zhiji-interview.md`（知己访谈引擎）

| 章节 | 要点 | 引用文件 |
|------|------|----------|
| 1. 角色设定 | 好奇的朋友，不是面试官；允许用户说"不知道"，不知道也是信息 | UIUX §3.1 |
| 2. 访谈原则 | 问具体事件不问抽象自评；一次只问一件事；三选一追问降低回答成本 | dimensions.md §维度定义 |
| 3. 维度推进与覆盖检查 | 四大维度族推进顺序（成长背景→性格→作息→价值观）；每族完成度对照 dimensions.md 锚点自查；全族覆盖后才生成画像（AC-05） | dimensions.md |
| 4. 校准分支 | 用户说"不准"→ 追问一个具体事件重新校准 → 分歧记录进 evidence（AC-06） | profile.schema.json（evidence.source=self_report） |
| 5. 增量落盘流程 | 每完成 1-2 个维度族立即落盘（读→局部追加→validate→写回）；防中断丢证据 | profile.schema.json、scripts/validate_profile.py |
| 6. N1/N2 提示接入点 | 首次会话开场先出 N1 块；每次画像产出末尾注入 N2 块 | ethics.md §4 |
| 7. few-shot 示例位 | 开场/提问/追问/收束四类各留 1 个示例占位（素材从 UIUX §3.1 转写） | UIUX §3.1 |

### 2.2 `02-zhibi-inference.md`（知彼推断）

| 章节 | 要点 | 引用文件 |
|------|------|----------|
| 1. 角色设定 | 克制的推理者：每条判断留退路；不替用户下结论，只呈现推断 | UIUX §3.2 |
| 2. 线索录入规则 | ≥3 条具体线索才出完整画像（AC-01）；单条线索 >2000 字截断并提示（Spec §10）；建档先问称呼与角色，主动建议化名 | profile.schema.json（subject.role 枚举） |
| 3. 置信度校准规则 | **先数证据再定级**：high=≥2 条独立证据或 1 条直接行为观察；medium=单证据合理推断；low=间接迹象/转述/证据有张力；证据 <2 条不得标 high（AC-15） | dimensions.md §校准表 |
| 4. 拒答分支 | 无线索→拒答+给 3 条录入示例；线索 <3 条→仅输出有限推断并全部标 low、明示信息不足（AC-02）；用户要求过度解读→拒答话术（"理解与歉意先行，再亮边界：没有证据的推断我不输出"基调） | UIUX §3.2 |
| 5. 三元组生成规范 | 内嵌 schema 中 assessment 定义摘要 + **1 条完整 assessment JSON 示例**（含 quote/source/date 的证据）；claim 禁巴纳姆句 | profile.schema.json、dimensions.md §反巴纳姆规范 |
| 6. 落盘流程（先想后写） | 两阶段：对话内自然语言讨论确认证据 → 用户确认后才输出 JSON 落盘；写入后必跑校验 | scripts/validate_profile.py |
| 7. N2 提示接入点 | 每份画像产出末尾注入 N2 块 | ethics.md §4 |
| 8. 证据回填与修订 | 新证据推翻旧推断：旧 assessment 置 revised + superseded_by + revision_reason → 移入 revision_history；新推断新 id 写入（AC-04）；活跃区只留 active | profile.schema.json |
| 9. few-shot 示例位 | 推断分级示例/信息不足示例/拒答示例各 1 个占位 | UIUX §3.2 |

### 2.3 `03-bubuang-gap.md`（补盲）

| 章节 | 要点 | 引用文件 |
|------|------|----------|
| 1. 角色设定 | 布置作业的朋友，不是班主任；任务小到不可能失败 | UIUX §3.3 |
| 2. 硬纪律：脚本先行 | **进入模块第一步必跑 `scripts/gap_scan.py`**；缺口识别只用脚本输出，禁止 LLM 自行扫描画像找缺口（AC-03） | scripts/gap_scan.py（接口见本文 §5.2） |
| 3. 报告解读规则 | 按脚本输出的缺口/薄弱/良好三级排序呈现；缺口优先于薄弱 | gap_scan.py 输出格式 |
| 4. 观察任务生成规则 | 每缺口 1 个任务；任务必须具体到"什么场合看什么行为"；说明该观察能区分哪两种可能 | dimensions.md §判定锚点、theory/*.md（按需） |
| 5. 提问话术生成规则 | 每缺口 1-2 句现成话术；开放式、非审问；"先交代自己再问对方"结构；不油腻（过 UIUX §2.3 幽默红线自查） | UIUX §2.3、§3.3 |
| 6. N3 提示接入点 | 任务清单末尾注入 N3 块（顺势强化"去观察真实的人"） | ethics.md §4 |
| 7. 回填入口 | 用户带回观察结果 → 引导至 02 号证据回填流程；回填后可重跑 gap_scan 更新缺口 | 02 号 §8 |
| 8. few-shot 示例位 | 任务布置示例/回填接收示例各 1 个占位 | UIUX §3.3 |

### 2.4 `04-pipei-match.md`（匹配·轻量版）

| 章节 | 要点 | 引用文件 |
|------|------|----------|
| 1. 角色设定 | 关系解说员，不是裁判；只说"你们之间"，不打绝对分 | UIUX §3.4 |
| 2. 前置检查（拒答门） | 双画像文件齐备才可启动；**对方画像 high 置信 active 推断 <3 条 → 拒出结论，提示"先补盲再匹配"并路由至 03 号**（AC-08）；无画像时入口置灰说明前置（Spec §10） | profile.schema.json |
| 3. 同维度对比方法 | 只读双方 active 推断；逐维度对比 claim 与 tendency；置信度低的推断参与对比时必须带不确定性措辞 | dimensions.md |
| 4. 输出结构 | 相似 ≥1 条 + 互补 ≥1 条 + 冲突 ≥1 条，每条标注依据来源（AC-07）；场景化相处建议（可操作、不操控）；**永久禁止百分比分数与绝对化结论**（Spec §3 锁定） | UIUX §2.5 |
| 5. 冲突点写作规范 | 自嘲剧场式呈现（"这不是谁对谁错，是两套操作系统"基调）；不贬损任何一方 | UIUX §2.3、§3.4 |
| 6. N4 提示接入点 | 报告收束处注入 N4 块——**五个节点中位置最显著**（匹配结论最易被当判决书），置于最终建议之后、独立成段 | ethics.md §4 |
| 7. few-shot 示例位 | 开场/相似点/冲突点剧场/建议/收束各 1 个占位 | UIUX §3.4 |

---

## 3. dimensions.md 与 theory 四文件大纲

### 3.1 `references/schemas/dimensions.md`

| 章节 | 内容组织 |
|------|----------|
| §1 维度模型总览 | 五维度族一张表：big_five（含 5 子维度）/ attachment / communication_style / lifestyle_rhythm / values；标注与 schema dimensions 字段的一一对应关系 |
| §2 判定锚点（按维度分小节） | 每维度一个锚点表：**三列结构**——倾向（high/medium/low）｜可观察行为锚点（具体场景行为，非形容词）｜典型证据形态。锚点写法示例（尽责性 high：「连聚餐都提前两天确认时间」），全部走场景白描，禁抽象词条 |
| §3 置信度校准表 | 架构 §2.3 表格原文收录（high=≥2 条独立证据或 1 条直接行为观察 / medium=单证据合理推断 / low=间接迹象·转述·证据有张力）+ 判定流程一句话：「先数证据条数，再查表定级，禁止先拍级再找补」 |
| §4 反巴纳姆写作规范 | claim 合法性三条：具体可证伪 / 含场景或频率锚点 / 禁"有时…有时…"两头堵；正反例对照表各 3 条 |
| §5 证据质量分级 | source 四枚举的可信度排序（user_observation > user_report > chat_record > self_report 的场景适用说明）；直接行为观察 vs 转述的界定 |

### 3.2 theory 四文件（统一三段式骨架）

每个文件统一结构：**§1 理论一句话定位 → §2 行为锚点表（类型/维度 × 可观察行为）→ §3 推断注意事项**。

| 文件 | 特有要点 |
|------|----------|
| `big-five.md` | 五维度各 high/low 两端行为锚点；与 dimensions.md §2 的关系：本文件供"为什么这么判"的理论依据，dimensions.md 供"判到哪一级"的操作锚点 |
| `attachment.md` | 安全/焦虑/回避/混乱四型锚点；注明：依恋判断证据门槛高，默认 confidence 上限 medium，除非有直接行为观察 |
| `communication.md` | 表达节奏/冲突处理/回应模式三类锚点；与 lifestyle_rhythm 的边界划分（作息归作息，沟通归沟通） |
| `mbti-display.md` | **展示层翻译规则**：大五 → MBTI 近似映射表；文件头部硬约束声明「MBTI 仅用于展示层翻译与用户沟通，永不作为推断依据写入 claim 或 evidence」 |

---

## 4. N1-N5 提示技术接入点（文案单一维护点方案）

**原则：文案全文只维护一处——`references/ethics.md` §4。** 该节为每个节点设锚点块：

```
<!-- N1-BEGIN --> ...文案... <!-- N1-END -->
<!-- N2-BEGIN --> ...文案... <!-- N2-END -->
... N3 / N4 / N5 同理
```

| 节点 | 接入位置 | 注入机制 | 文案基调要求（Spec §1.5） |
|------|----------|----------|--------------------------|
| N1 首次引导 | SKILL.md §2 内联 + 01 号 §6 开场 | **唯一的例外**：SKILL.md 常驻需内联全文，标注"镜像自 ethics.md §4 N1，改文案先改 ethics.md 再同步"；01 号 prompt 不重写，引用"输出 SKILL.md §2 的 N1 块" | 温和朋友口吻，一次说清三要素（辅助而非决定/真实接触/独立判断），AC-12 |
| N2 画像产出 | 01 号 §6、02 号 §7，画像末尾固定提示行 | prompt 指令：「读取 ethics.md §4 N2 锚点块，原样输出，禁止改写」 | 轻量提醒，不重复说教，AC-13 |
| N3 补盲任务 | 03 号 §6，任务清单末尾固定提示行 | 同上，N3 锚点 | 顺势强化"去观察真实的人" |
| N4 匹配报告 | 04 号 §6，报告收束固定提示块 | 同上，N4 锚点；**独立成段、最终建议之后**——五节点中最显著位置 | 防"判决书"误用 |
| N5 分享卡片 | MVP 无分享卡片产出（Spec §3 F9 出 scope）；**预案**：届时卡片署名位下方固定一行，从 ethics.md §4 N5 锚点取文案 | 预留锚点，当前不产生依赖 | 小字但必须有 |

**文案门禁（AC-14）**：ethics.md §5 收录文案纪律——禁说教句式（"你应该/你必须/听我一句劝"）、禁 UIUX §2.4 禁用词清单；所有 N 节点文案定稿后过一遍禁用词全文检索。示例基调（仅示意，终稿 Phase 3 定）："我能帮你看清一些线索，但真正认识一个人，还是得靠你们真实相处。"

---

## 5. 两个脚本接口规格

### 5.1 `scripts/validate_profile.py`

**职责**：画像 JSON 的 Schema 校验；写入后必跑；失败输出逐字段错误供 LLM 回炉（AC-10）。

**命令行接口**：

```
python validate_profile.py <profile_json_path> [--schema <schema_path>]
```

- `profile_json_path`：必填，待校验画像文件
- `--schema`：可选，默认定位 `<脚本目录>/../references/schemas/profile.schema.json`

**stdout 输出格式（JSON 单行，供 Agent 机器读取）**：

```json
{"valid": true, "file": "self.json", "errors": []}
{"valid": false, "file": "chen.json", "errors": [{"path": "dimensions.big_five.openness.assessments[0].evidence", "message": "minItems 1 violated: empty array"}, {"path": "dimensions.attachment.assessments[1].confidence", "message": "'very_high' not in enum [high, medium, low]"}]}
```

- `path` 用点路径+数组下标，精确到字段，LLM 可直接定位修复
- 校验过程的人类可读进度写 **stderr**，stdout 只出最终 JSON（防解析污染）

**退出码**：

| 码 | 含义 |
|----|------|
| 0 | 校验通过 |
| 1 | 校验失败（errors 非空） |
| 2 | 文件不存在 / JSON 解析失败 / schema 文件缺失（此时 stdout 输出 `{"valid": false, "errors": [{"path": "$", "message": "..."}]}`） |

**实现策略与 fallback 覆盖范围**：

1. 优先 `import jsonschema`（Draft7Validator），全量校验
2. `ImportError` 时降级为内置精简校验器（纯 Python，约 80 行），覆盖范围**恰好**为：
   - 必需字段：顶层 7 项 + subject.alias + dimensions 五族 + big_five 五子维度 + assessment 六必需 + evidence 三必需
   - 枚举校验：profile_type / subject.role / tendency / confidence / evidence.source / status
   - 格式校验：schema_version 正则 `^1\.`、assessment.id 正则 `^a_[0-9]{3,}$`、date / date-time 格式、profile_id UUID 形状
   - minItems：evidence ≥1
   - 条件必填：profile_type=other 时 subject.role 必填
3. fallback 模式的 stdout JSON 增加 `"validator": "fallback"` 标记，便于排查环境差异

### 5.2 `scripts/gap_scan.py`

**职责**：画像覆盖率/缺口扫描，纯确定性逻辑；补盲模块第一步必跑；LLM 禁止自行扫描（AC-03）。

**命令行接口**：

```
python gap_scan.py <profile_json_path> [--format text|json]
```

- `--format`：默认 `text`（直接呈现给用户）；`json` 供 04 号匹配模块做前置检查复用

**stdout 输出格式（text 模式）**：

```
画像缺口扫描：<alias>（<updated_at>）

big_five.openness          : 2 active (high×1, medium×1), 证据 3 条 → 覆盖良好
big_five.conscientiousness : 0 active → 【缺口】
big_five.extraversion      : 1 active (low×1), 证据 1 条 → 【薄弱】
big_five.agreeableness     : 0 active → 【缺口】
big_five.neuroticism       : 1 active (medium×1), 证据 2 条 → 覆盖良好
attachment                 : 0 active → 【缺口】
communication_style        : 1 active (low×1), 证据 1 条 → 【薄弱】
lifestyle_rhythm           : 0 active → 【缺口】
values                     : 1 active (high×1), 证据 2 条 → 覆盖良好

汇总：缺口 4 个 / 薄弱 2 个 / 覆盖良好 3 个
high 置信 active 推断共 2 条（匹配前置要求 ≥3）
```

**判定规则（写死在脚本，不在 prompt）**：

| 状态 | 条件 |
|------|------|
| 缺口 | 该维度 active assessments = 0 |
| 薄弱 | active > 0 且（全部 confidence=low 或 总证据条数 <2） |
| 覆盖良好 | 其余 |

**json 模式输出**：

```json
{"alias": "...", "dimensions": {"big_five.openness": {"status": "ok", "active": 2, "high": 1, "medium": 1, "low": 0, "evidence_count": 3}, "...": {}}, "summary": {"gap": 4, "weak": 2, "ok": 3, "high_confidence_active": 2, "match_ready": false}}
```

- `match_ready` = `high_confidence_active >= 3`，04 号匹配模块前置检查（AC-08）直接读此字段，**不重复实现计数逻辑**

**退出码**：

| 码 | 含义 |
|----|------|
| 0 | 扫描成功（有无缺口都返回 0——缺口是正常业务结果，不是错误） |
| 2 | 文件不存在 / JSON 解析失败 |

**纪律**：脚本只读不写；不依赖 jsonschema（容忍未校验文件，自身做宽容解析，单条坏 assessment 跳过并在 stderr 告警）。

---

## 6. usage-log.jsonl 格式（本地埋点）

**位置**：`<用户工作区>/zhibi-data/usage-log.jsonl`，每行一个 JSON 事件，追加写。

**事件字段（仅四个必需字段，禁扩张）**：

```json
{"event": "profile_validated", "timestamp": "2026-10-09T14:32:07+08:00", "version": "1.0.0", "role_type": "romantic"}
```

| 字段 | 说明 |
|------|------|
| `event` | 事件名，枚举见下表 |
| `timestamp` | ISO 8601 带时区 |
| `version` | 技能版本（schema_version 主版本对齐） |
| `role_type` | 当前操作画像的 subject.role；self 画像记 `"self"`；无关画像的事件（如 refusal）记 `null` |

**事件枚举（首版 10 个）**：`skill_triggered` / `module_entered` / `profile_created` / `profile_updated` / `profile_validated` / `validation_failed` / `gap_scan_run` / `match_generated` / `match_rejected_to_gap` / `refusal_triggered`

**隐私硬约束（写入 SKILL.md 读写纪律与各 prompt）**：
- **禁止记录线索原文、evidence.quote、claim 内容、画像任何字段值**
- 禁止记录真实姓名、alias 原文（只记 role_type 枚举值）
- 日志仅本地，随 `zhibi-data/` 目录删除即彻底清除

---

## 7. ethics.md 结构规格

| 章节 | 内容 |
|------|------|
| §1 伦理红线三条 | 不教操控只给理解 / 不是算命是推理 / 辅助而非决定（§1.5 三理念全文收录） |
| §2 拒答话术模板 | 操控类请求的标准拒答结构：拒绝 + 边界声明 + 正向替代表述（AC-09）；给 2 个模板占位（恋爱场景/职场场景），终稿 Phase 3 过文案门禁 |
| §3 隐私声明 | 数据位置、化名建议、不上传承诺、删除方法（删 `zhibi-data/` 目录即彻底删除）；PRIVACY.md 首次运行由此节生成 |
| §4 N1-N5 定位提示文案源 | 五组锚点块（`<!-- Nx-BEGIN/END -->`），**全项目唯一文案维护点**；每块附基调要求与门禁状态标记 |
| §5 文案门禁清单 | 说教句式封杀 + UIUX §2.4 禁用词清单引用；说明：任何 N 节点文案与拒答话术定稿前必过此门禁（AC-14） |

---

## 8. 与 Spec 的对照自检

| Spec 条目 | 落点 | 状态 |
|-----------|------|------|
| §1.5 N1-N5 五节点 | 本文 §4 接入点表 + ethics.md §4 单一文案源 | 覆盖 |
| §5 技能文件清单 11 项 | 本文 §0 目录树逐项对应 | 覆盖 |
| §6 数据契约（三元组/校准/usage-log/PRIVACY） | schema 已落盘；本文 §5/§6/§7 | 覆盖 |
| §7 七条流程 | 本文 §1.3 路由表七行一一对应 | 覆盖 |
| AC-01~AC-15 | 分散落点：02 号 §2/§3/§4（AC-01/02/15）、03 号 §2（AC-03）、02 号 §8（AC-04）、01 号 §3/§4（AC-05/06）、04 号 §2/§4（AC-07/08）、ethics §2（AC-09）、本文 §1.5（AC-10）、架构 §3.3（AC-11）、本文 §4（AC-12/13）、ethics §5（AC-14） | 覆盖 |
| 偏差 | 技能包路径 `skill/zhibi/` → `skill/`（扁平化，需回写 ARCHITECTURE.md §1.1）；架构目录树补 `usage-log.jsonl` | 2 处，已声明 |

---

## 9. Phase 3 交接要点

1. **prompt 正文撰写顺序建议**：ethics.md（文案源先行）→ 02 号（P0 之首）→ 01 号 → 03 号 → 04 号 → SKILL.md 收口（字数验收 <3000）
2. 所有 N 节点文案与拒答话术为**占位待填**，定稿后必须过 ethics.md §5 门禁（禁用词全文检索）
3. 脚本实现按本文 §5 接口，验收用例：合法画像过 0 / 缺 evidence 报 1 带路径 / 无 jsonschema 环境走 fallback 且结果一致 / gap_scan 的 match_ready 计数与人工核对一致
4. 端到端验证按 Spec §12 六步走查，其中第 2、4、5 步分别依赖本文 §1.5、§5.2、§4(N4) 的接入点正确性
