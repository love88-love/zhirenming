#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""知人明 · 运行日志统一写入脚本

用法：
    python log_event.py <event> [--role <role_type>] [--module <module>]
                        [--version <技能版本>] [--log <日志路径>]

行为契约（v1.2 新增，对齐 DETAIL-DESIGN 日志口径）：
    - 事件名写死枚举，不在清单内的一律拒绝（退出码 2），防止 LLM 自造事件名
    - 每行 JSONL 只含 4+1 个字段：event / time / version / role_type
      （module_entered 额外带 module）。脚本不接受任何自由文本参数——
      线索原文、claim、evidence、alias 在机制上写不进来，这是隐私红线的
      机器级兜底，不靠 prompt 自觉
    - time 由脚本取当前本地时间（ISO 8601 带时区），调用方不得传时间
    - 日志文件默认 <当前工作目录>/zhibi-data/usage-log.jsonl，目录不存在自动建
    - 追加写，永不覆盖；写入失败（权限/磁盘）退出码 2，不静默
    - stdout 只输出单行 JSON：{"logged": true, "event": ..., "file": ...}
      人类可读进度一律写 stderr
    - 退出码：0=写入成功 2=参数错误/写入失败

事件清单（全项目唯一维护点，新增事件先改这里再同步文档）：
    skill_triggered        会话首次进入本技能
    module_entered         进入知己/知彼/补盲/匹配任一模块（须带 --module）
    refusal_triggered      触发操控类拒答（role_type 记 null）
    profile_created        新建画像落盘成功
    profile_updated        画像局部更新落盘成功
    profile_validated      画像写入后校验通过
    validation_failed      画像写入后校验失败
    gap_scan_run           补盲/匹配前置的缺口扫描完成
    match_rejected_to_gap  匹配因 high 置信不足被拒、路由补盲
    match_generated        匹配报告生成完成
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

EVENTS = {
    "skill_triggered", "module_entered", "refusal_triggered",
    "profile_created", "profile_updated", "profile_validated",
    "validation_failed", "gap_scan_run", "match_rejected_to_gap",
    "match_generated",
}
ROLE_TYPES = {"self", "friend", "colleague", "leader", "romantic",
              "family", "other", "null"}
MODULES = {"zhiji", "zhibi", "bubuang", "pipei"}
DEFAULT_VERSION = "1.2.0"


def _fatal(message):
    print("错误：%s" % message, file=sys.stderr)
    sys.stdout.write(json.dumps(
        {"logged": False, "error": message}, ensure_ascii=False) + "\n")
    sys.exit(2)


def main():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="知人明运行日志写入")
    parser.add_argument("event", help="事件名（枚举，见脚本头注释）")
    parser.add_argument("--role", default="null",
                        help="role_type：self/friend/colleague/leader/"
                             "romantic/family/other/null，默认 null")
    parser.add_argument("--module", default=None,
                        help="module_entered 必填：zhiji/zhibi/bubuang/pipei")
    parser.add_argument("--version", default=DEFAULT_VERSION,
                        help="技能版本号，默认 %s" % DEFAULT_VERSION)
    parser.add_argument("--log", default=None,
                        help="日志路径，默认 ./zhibi-data/usage-log.jsonl")
    args = parser.parse_args()

    if args.event not in EVENTS:
        _fatal("未知事件名 %r（合法值：%s）"
               % (args.event, ", ".join(sorted(EVENTS))))
    if args.role not in ROLE_TYPES:
        _fatal("非法 role_type %r（合法值含 null）" % args.role)
    if args.event == "module_entered":
        if args.module not in MODULES:
            _fatal("module_entered 必须带 --module（zhiji/zhibi/"
                   "bubuang/pipei）")
    elif args.module is not None:
        _fatal("只有 module_entered 允许带 --module")

    record = {
        "event": args.event,
        "time": datetime.now(timezone.utc).astimezone().isoformat(
            timespec="seconds"),
        "version": args.version,
        "role_type": None if args.role == "null" else args.role,
    }
    if args.event == "module_entered":
        record["module"] = args.module

    log_path = Path(args.log) if args.log else (
        Path.cwd() / "zhibi-data" / "usage-log.jsonl")
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError as exc:
        _fatal("日志写入失败：%s" % exc)

    print("已记录：%s（%s）" % (args.event, log_path.name), file=sys.stderr)
    sys.stdout.write(json.dumps(
        {"logged": True, "event": args.event,
         "file": str(log_path)}, ensure_ascii=False) + "\n")
    sys.exit(0)


if __name__ == "__main__":
    main()
