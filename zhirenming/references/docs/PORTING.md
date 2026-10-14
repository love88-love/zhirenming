# 知人明 · 跨平台移植指南（PORTING）

> 地位：本文件是「记忆锚点」跨平台适配的唯一维护点。SKILL.md §0.6 的锚点确保算法是平台无关的，平台差异全部收敛到本文件的适配表。
> 核实日期：2026-10-13（Claude Code / Codex 官方文档，扣子平台公开资料）。平台机制变化快，改动前重新核实。

---

## 1. 统一抽象层（三层解耦）

| 层 | 内容 | 可移植性 |
|----|------|----------|
| L0 核心能力 | SKILL.md 正文 + references/ + schema + Python 脚本 | **天然可移植**——全是 markdown/JSON/Python，无任何平台私有 API |
| L1 发现清单 | SKILL.md frontmatter（name + description） | **事实标准**：WorkBuddy / Claude Code / Codex / Cursor / OpenClaw 通用同一格式。纪律：frontmatter 不加任何平台专属字段（如 Codex 的 openai.yaml 另文件存放，可缺省） |
| L2 记忆锚点 | TRIGGER-RULE.md + §0.6 锚点确保算法 | **算法平台无关，目标文件按 §3 适配表替换** |

关键洞察：**"触发难"是"通用 Agent + 技能列表"形态特有的问题**。在豆包智能体/Coze Bot 这类"用户直接进入专属智能体"的形态里，触发问题不存在——用户打开智能体即触发。所以 L2 只在通用 Agent 平台需要。

---

## 2. 平台差异矩阵

| 平台 | 技能发现 | 自动注入的记忆文件 | 显式调用 | 锚点写入限制 |
|------|----------|--------------------|----------|--------------|
| WorkBuddy | `~/.workbuddy/skills/<name>/SKILL.md` | `~/.workbuddy/user-*-personal/MEMORY.md`（会话启动注入系统提示，超长截断） | 无斜杠命令，靠语义/规则 | 每会话写入预算约 4000 字符 |
| Claude Code | `~/.claude/skills/<name>/SKILL.md`（个人）/ `.claude/skills/`（项目） | `~/.claude/CLAUDE.md`（个人级，全项目每会话自动加载） | `/zhirenming` | 无；另支持 settings.json hooks（可做真安装钩子，见 §4.2） |
| Codex CLI | `~/.codex/skills/`（个人）/ `.codex/skills/`、`.agents/skills/`（项目） | `~/.codex/AGENTS.md`（启动时读取）+ 仓库根 AGENTS.md | `$zhirenming` | 沙箱/审批模式可能拦截写 home 目录；AGENTS.md 仅启动时读，写完需重启会话 |
| 豆包桌面版（2.x） | `.user_skills\<name>\`（2026-10-13 实测确认支持文件技能） | **无本地可写记忆文件**（云端画像，平台管理） | 输入栏「技能」面板手动选 / 对话中点名 | 见 §4.4：锚点降级为"用户发一句平台记忆指令" |
| 豆包（消费端智能体/扣子） | 无 SKILL.md 机制 | 无文件级记忆（平台自动画像 + 智能体人设） | 用户直接进入智能体 | 锚点机制不适用，见 §4.4 |
| DeepSeek（API/Harness） | 无官方标准 | 取决于所用 Harness | — | 见 §4.5 |

---

## 3. 锚点写入算法（平台无关）+ 适配表

**算法（§0.6 的展开，四步不变）：**

1. **平台探测**（按序，多命中则每个平台各写一份——锚块幂等，互不干扰）：
   - 环境变量 `CLAUDE_CONFIG_DIR` 或目录 `~/.claude` 存在 → Claude Code
   - 环境变量 `CODEX_HOME` 或目录 `~/.codex` 存在 → Codex
   - 目录 `~/.workbuddy` 存在 → WorkBuddy
   - 都探测不到 → 跳过写入，告知用户："把 `references/TRIGGER-RULE.md` 的内容粘贴到你所用平台的自定义指令/记忆入口即可。"
2. **定位目标文件**（按适配表）；不存在则按模板新建。
3. **查 `ZHIRENMING-TRIGGER-RULE` 锚点**：缺失→插入（置顶区域）；版本旧→整块替换；一致→跳过。
4. **告知用户**写了什么、怎么删。

**适配表（平台 → 目标文件 + 插入点 + 新建模板）：**

| 平台 | 目标文件 | 插入点 | 文件不存在时新建模板 |
|------|----------|--------|----------------------|
| WorkBuddy | glob `~/.workbuddy/user-*-personal/MEMORY.md`（多匹配取最近修改） | 第一个 `# ` 标题行之后 | `# 用户长期记忆` |
| Claude Code | `~/.claude/CLAUDE.md`（`CLAUDE_CONFIG_DIR` 优先） | 文件最顶部 | `# Personal Instructions` |
| Codex CLI | `~/.codex/AGENTS.md`（`CODEX_HOME` 优先） | 文件最顶部 | `# AGENTS.md` |

---

## 4. 各平台适配要点与限制

### 4.1 WorkBuddy（原生平台）

- 安装：复制目录到 `~/.workbuddy/skills/zhirenming/`，重启会话。
- 锚点注入保证：用户级 MEMORY.md 会话启动注入系统提示；超长截断 → 锚块必须置顶且 ≤10 行。
- 已知限制：无斜杠命令，显式调用靠点名（"用知人明分析TA"）；每会话记忆写入预算约 4000 字符。

### 4.2 Claude Code

- 安装：复制到 `~/.claude/skills/zhirenming/`（全项目可用）或项目 `.claude/skills/`（随仓库分发）。
- 锚点目标：`~/.claude/CLAUDE.md`，每次会话自动加载。
- 技能内引用自身资源可用 `${CLAUDE_SKILL_DIR}` 变量（SKILL.md 里写相对路径亦可，两平台都按技能目录解析）。
- **进阶（可选）**：Claude Code 的 `settings.json` hooks 支持 SessionStart 事件执行脚本——这是全平台唯一能做"真安装钩子"的地方：可配一个 SessionStart hook 调用锚点写入脚本，实现装完即写、不依赖首次触发。需要 Python 环境和用户手动配置 settings.json，属增强而非必需。
- 显式调用 `/zhirenming` 可作 INSTALL.md 引导话术。

### 4.3 Codex CLI

- 安装：复制到 `~/.codex/skills/zhirenming/`（个人）或 `.agents/skills/`（随仓库）。
- 锚点目标：`~/.codex/AGENTS.md`，启动时读取——**写入后必须重启会话才生效**（INSTALL.md 对应平台话术要写这句）。
- 沙箱注意：默认沙箱/审批模式可能拦截对工作区外（home 目录）的写入——锚点写入前向用户说明并等批准；被拦截则降级为"请手动把 TRIGGER-RULE.md 内容追加到 ~/.codex/AGENTS.md"。
- 不要给技能加 openai.yaml（保持 frontmatter 纯净，跨平台兼容）；显式调用 `$zhirenming`。

### 4.4 豆包（桌面版 / 消费端智能体 / 扣子 Coze，三种形态差异大）

**形态 A · 豆包桌面版 2.x（`.user_skills` 文件技能，2026-10-13 实测确认）**：

- 安装：技能目录复制到 `.user_skills\zhirenming\`（豆包可从 GitHub 仓库自行拉取重装）；装完新开会话生效。
- **实测行为**：技能加载后 §0.5/§0.6 启动流程完整可跑（N1 对齐、zhibi-data 首触创建均正常）；但**首条消息未点名时不会主动触发**——语义匹配在轻量模型（如豆包 2.1 Lite）上漏调率明显偏高。
- **锚点降级（关键差异）**：豆包长期记忆为**云端管理、无本地可写文件**，§0.6 的平台探测会落空。替代三连：
  1. 装完后对豆包说一句「**记住：分析具体的人时，优先使用 zhirenming 技能**」——借平台云端记忆实现锚点同等效果；
  2. 提问时显式点名「用 zhirenming 技能分析 TA」，或用输入栏「技能」面板手动选中；
  3. 测试触发率时用旗舰模型，不要用 Lite 系列。
- 安装验证报告注意：豆包自报的版本号可能读自缓存（实测把 v1.4 报成 v1.3），以文件内容为准（§0.6 存在即 v1.4+）。

**形态 B · 消费端智能体（零成本分发）**：
- 把 SKILL.md 全文（§0-§5）+ `references/ethics.md` 全文合并粘贴为智能体"人设提示词"；把 `references/schemas/profile.schema.json` 的要点以文字形式并入（豆包不读附件文件）。
- **触发问题消失**：用户打开智能体即用，无需锚点机制。
- 限制：① Python 脚本不可运行——画像校验/缺口扫描失去机器兜底，只能保留提示词纪律，并在人设里注明"无机器校验，需更严格自查"；② 无本地文件系统——zhibi-data 改为"每份画像以 JSON 代码块输出，请用户自行保存，下次粘贴回来"；③ 平台记忆是自动画像标签，不可文件级写入，可引导用户对豆包说"记住：……"近似锚点效果。

**形态 C · Coze Bot（产品化分发）**：
- 人设与回复逻辑 = SKILL.md + ethics.md；知识库 = references/ 全文上传；长期记忆/变量 = 画像存储（替代 zhibi-data）；工作流 = 四模块可编排为固定流程节点。
- 这已不是"移植"而是"重构"，对应商业化第 1 步（轻量产品化），按需再做。

### 4.5 DeepSeek（API / 各类 Harness）

- DeepSeek 官方无技能/记忆文件标准。适配看所用 Harness：
  - **Harness 兼容 AGENTS.md/CLAUDE.md**（多数开源 Harness 认其中之一）→ 直接按 §3 适配表对应条目处理。
  - **纯 API 部署** → 无会话间持久记忆：把 TRIGGER-RULE.md 内容置于系统提示词模板顶部，SKILL.md 全文作为系统提示词主体；画像持久化由调用方自行实现（数据库/文件均可，schema 不变）。
- 限制：工具调用（Python 脚本执行）需部署方提供运行环境；无环境时降级同 4.4 形态 A。

---

## 5. 不可移植部分与降级策略（全平台通用）

| 组件 | 依赖 | 无依赖时的降级 |
|------|------|----------------|
| `scripts/*.py`（校验/缺口扫描/日志） | Python 3.10+ | 保留提示词纪律，明示"缺机器校验兜底"；jsonschema 缺失本就有内置 fallback |
| `zhibi-data/` 本地画像文件 | 文件系统 | 画像以 JSON 代码块交付用户自存，下次粘贴恢复（schema 不变） |
| 微信记录本机直读（02 §2.1 分支三） | Windows + 用户自装 wechat-wcdb 技能 | 该分支本就可选——跳过，回落叙述式/粘贴式 |
| 锚点写入 | 文件系统写权限 | 降级为"请手动粘贴 TRIGGER-RULE.md 内容到自定义指令" |

**移植验收清单**（任何平台装完后过一遍）：
1. 技能/智能体被成功触发（语义或点名）
2. 锚点写入或手动粘贴完成，新会话验证规则命中
3. 画像写入 + 校验通过（或有降级声明）
4. gap_scan 输出正常（或有降级声明）
