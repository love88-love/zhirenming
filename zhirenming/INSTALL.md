# 知人明 · 安装说明

> **多平台用户**：本说明以 WorkBuddy 为例。Claude Code / Codex CLI / 豆包（扣子）/ DeepSeek 的安装路径、锚点目标与降级策略见 `references/docs/PORTING.md`（跨平台移植指南）——核心结论：技能目录换成对应平台的 skills 目录即可，Claude Code 是 `~/.claude/skills/zhirenming/`，Codex 是 `~/.codex/skills/zhirenming/`，豆包/DeepSeek 无技能机制时把 SKILL.md 作为智能体人设/系统提示词使用。

把本目录装成 WorkBuddy 用户级技能，全程约一分钟。无需联网下载任何额外组件。

## 环境要求

| 依赖 | 要求 | 检查方法 |
|------|------|----------|
| WorkBuddy 桌面端 | 最新版 | — |
| Python | 3.10 或更高 | `python --version` |
| jsonschema（可选） | 任意 4.x | `pip install jsonschema` 获得完整 Draft-07 校验；不装也能用——脚本会自动降级为内置精简校验，两种模式的校验结论经 QA 实测一致 |

## 安装步骤

1. 找到 WorkBuddy 用户级技能目录：

   ```
   C:\Users\<你的用户名>\.workbuddy\skills\
   ```

2. 把本目录（含 `SKILL.md`、`references/`、`scripts/` 的全部内容）复制为：

   ```
   C:\Users\<你的用户名>\.workbuddy\skills\zhirenming\
   ```

   目录名必须是 `zhirenming`——`SKILL.md` frontmatter 中的 `name: zhirenming` 要与目录名一致，否则技能无法被识别。复制完成后目录结构应为：

   ```
   skills/
   └── zhirenming/
       ├── SKILL.md
       ├── INSTALL.md
       ├── references/
       └── scripts/
   ```

3. **重启 WorkBuddy 会话**，新技能才会被加载。

没有安装程序、不写注册表、不动系统环境——复制即安装，删除即卸载。

## 触发规则锚点（推荐，装完触发率翻倍）

本技能靠"模型扫技能列表做语义匹配"触发——技能装多了以后，这条匹配路径会漏（列表靠后、名字是拼音都可能被跳过）。解法是在你的**用户级长期记忆**里写一条显式触发规则，把语义匹配升级为规则匹配：

- **通过 AI 助手安装时**（如对 WorkBuddy 说"帮我安装知人明"）：复制完文件后，助手应把 `references/TRIGGER-RULE.md` 的全文（含 `ZHIRENMING-TRIGGER-RULE` BEGIN/END 锚点）插入到 `~/.workbuddy/user-*-personal/MEMORY.md` 第一个 `# ` 标题行之后；文件不存在就新建（首行 `# 用户长期记忆`）。重复安装时锚点已存在则跳过，版本旧则整块替换——幂等，不产生重复内容。
- **手动复制安装时**：不用手动操作——首次触发本技能后，技能会自动完成上面这一步（SKILL.md §0.6），完成后会明确告知你写了什么。
- 规则内容见 `references/TRIGGER-RULE.md`，仅 3 行，只操作锚点块、不动你记忆里的任何既有内容；不需要时删除该标记块即可。

## 首次使用

重启会话后，对 WorkBuddy 说任意一句触发词即可启动：

- 「认识自己」/「了解自己」→ 进入知己访谈
- 「帮我看看 TA」/「分析某人」→ 进入知彼建档
- 「还该了解什么」→ 进入补盲（需已有画像）
- 「我们合不合」/「匹配一下」→ 进入匹配（需双画像齐备）

首次触发时会先看到一段定位声明（本工具是参考不是结论、真实相处不可替代、主动权在你），随后是四模块导览。同一会话中首次运行会自动在你的工作区创建 `zhibi-data/` 目录和其中的 `PRIVACY.md`（隐私声明）。

## 你的数据在哪里

| 内容 | 位置 |
|------|------|
| 画像文件（自我 + 他人） | `<你的工作区>\zhibi-data\profiles\` |
| 运行日志（只记事件名+时间，不记内容） | `<你的工作区>\zhibi-data\usage-log.jsonl` |
| 隐私声明 | `<你的工作区>\zhibi-data\PRIVACY.md` |

全部数据只存在你本机，技能不发起任何网络请求，不向任何外部服务上传内容。给他人建档时会建议你使用化名。

**彻底删除数据**：删除 `zhibi-data/` 整个目录即可，没有残留副本。

## 卸载

1. 删除技能目录 `C:\Users\<你的用户名>\.workbuddy\skills\zhirenming\`。
2. （可选）删除你的画像数据 `zhibi-data/` 目录。
3. （可选）删除 `~/.workbuddy/user-*-personal/MEMORY.md` 中 `ZHIRENMING-TRIGGER-RULE` 锚点块。**不删也无害**——规则是条件式的（"若技能列表中存在 zhirenming"），技能卸载后规则自然落空，不会产生任何行为。
4. 重启会话。

前几步都做完，本技能在你机器上不留下任何痕迹。

## 常见问题

**`python` 命令找不到？** 确认 Python 3.10+ 已安装且加入 PATH。技能核心的访谈与推理不依赖 Python，但画像校验与缺口扫描脚本需要它——没有 Python 时画像写入将缺少机器校验兜底，不建议跳过。

**jsonschema 装不上？** 可以不管。脚本检测到缺失会自动走内置校验器，功能与判定结论一致，仅在错误提示的措辞上略有差异。

**技能没出现在会话里？** 依次检查：目录名是否为 `zhirenming`；`SKILL.md` 是否直接位于该目录下（不要多套一层文件夹）；是否已重启会话。
