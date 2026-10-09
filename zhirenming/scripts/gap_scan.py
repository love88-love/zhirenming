#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""知人明 · 画像覆盖率/缺口扫描脚本

用法：
    python gap_scan.py <profile_json_path> [--format text|json]

行为契约（DETAIL-DESIGN §5.2）：
    - 三级判定写死在脚本：缺口=0 active；薄弱=active>0 且
      （全部 low 或总证据 <2 条）；其余=覆盖良好
    - match_ready = high 置信 active 推断 >= 3（匹配前置检查 AC-08）
    - 退出码：0=扫描成功（有无缺口都是 0） 2=文件不存在/解析失败
    - 只读不写；不依赖 jsonschema；单条坏 assessment 跳过并 stderr 告警
"""

import argparse
import json
import sys
from pathlib import Path

# 9 个维度槽位（点路径即报告中的展示名）
DIMENSION_SLOTS = [
    "big_five.openness",
    "big_five.conscientiousness",
    "big_five.extraversion",
    "big_five.agreeableness",
    "big_five.neuroticism",
    "attachment",
    "communication_style",
    "lifestyle_rhythm",
    "values",
]
VALID_CONFIDENCE = {"high", "medium", "low"}
CONFIDENCE_ORDER = ["high", "medium", "low"]
MATCH_READY_THRESHOLD = 3


def _warn(message):
    print("警告：%s" % message, file=sys.stderr)


def _scan_dimension(dim_val, slot):
    """扫描单个维度槽位，返回统计 dict（坏条目跳过并告警）"""
    stats = {"active": 0, "high": 0, "medium": 0, "low": 0, "evidence_count": 0}
    if not isinstance(dim_val, dict):
        if dim_val is not None:
            _warn("%s 不是对象，按 0 active 处理" % slot)
        return stats
    assessments = dim_val.get("assessments")
    if not isinstance(assessments, list):
        if assessments is not None:
            _warn("%s.assessments 不是数组，按 0 active 处理" % slot)
        return stats
    for idx, item in enumerate(assessments):
        if not isinstance(item, dict):
            _warn("%s.assessments[%d] 不是对象，已跳过" % (slot, idx))
            continue
        if item.get("status") != "active":
            continue  # revised 归档或缺 status 均不计入活跃区
        confidence = item.get("confidence")
        if confidence not in VALID_CONFIDENCE:
            _warn("%s.assessments[%d] confidence 非法（%r），已跳过"
                  % (slot, idx, confidence))
            continue
        stats["active"] += 1
        stats[confidence] += 1
        evidence = item.get("evidence")
        if isinstance(evidence, list):
            stats["evidence_count"] += len(evidence)
        else:
            _warn("%s.assessments[%d] evidence 不是数组，证据按 0 条计"
                  % (slot, idx))
    return stats


def _judge(stats):
    """三级判定：gap / weak / ok"""
    if stats["active"] == 0:
        return "gap"
    all_low = stats["low"] == stats["active"]
    if all_low or stats["evidence_count"] < 2:
        return "weak"
    return "ok"


def scan_profile(data):
    """全量扫描，返回 (alias, updated_at, dimensions, summary)"""
    dimensions_data = data.get("dimensions") if isinstance(data, dict) else None
    if not isinstance(dimensions_data, dict):
        dimensions_data = {}
    big_five = dimensions_data.get("big_five")
    if not isinstance(big_five, dict):
        big_five = {}

    dimensions = {}
    for slot in DIMENSION_SLOTS:
        if slot.startswith("big_five."):
            dim_val = big_five.get(slot.split(".", 1)[1])
        else:
            dim_val = dimensions_data.get(slot)
        stats = _scan_dimension(dim_val, slot)
        stats["status"] = _judge(stats)
        dimensions[slot] = stats

    high_active = sum(d["high"] for d in dimensions.values())
    summary = {
        "gap": sum(1 for d in dimensions.values() if d["status"] == "gap"),
        "weak": sum(1 for d in dimensions.values() if d["status"] == "weak"),
        "ok": sum(1 for d in dimensions.values() if d["status"] == "ok"),
        "high_confidence_active": high_active,
        "match_ready": high_active >= MATCH_READY_THRESHOLD,
    }
    alias = data.get("subject", {}).get("alias", "<未知>") \
        if isinstance(data.get("subject"), dict) else "<未知>"
    return alias, data.get("updated_at", "<未知>"), dimensions, summary


def render_text(alias, updated_at, dimensions, summary):
    """text 模式报告（直接呈现给用户）"""
    width = max(len(s) for s in DIMENSION_SLOTS)
    lines = ["画像缺口扫描：%s（%s）" % (alias, updated_at), ""]
    status_label = {"gap": "【缺口】", "weak": "【薄弱】", "ok": "覆盖良好"}
    for slot in DIMENSION_SLOTS:
        d = dimensions[slot]
        name = slot.ljust(width)
        if d["active"] == 0:
            lines.append("%s : 0 active → 【缺口】" % name)
        else:
            parts = ", ".join("%s×%d" % (c, d[c])
                              for c in CONFIDENCE_ORDER if d[c] > 0)
            lines.append("%s : %d active (%s), 证据 %d 条 → %s"
                         % (name, d["active"], parts, d["evidence_count"],
                            status_label[d["status"]]))
    lines += [
        "",
        "汇总：缺口 %d 个 / 薄弱 %d 个 / 覆盖良好 %d 个"
        % (summary["gap"], summary["weak"], summary["ok"]),
        "high 置信 active 推断共 %d 条（匹配前置要求 ≥%d）"
        % (summary["high_confidence_active"], MATCH_READY_THRESHOLD),
    ]
    return "\n".join(lines)


def render_json(alias, dimensions, summary):
    """json 模式报告（供匹配模块前置检查复用）"""
    ordered_dims = {}
    for slot in DIMENSION_SLOTS:
        d = dimensions[slot]
        ordered_dims[slot] = {
            "status": d["status"], "active": d["active"],
            "high": d["high"], "medium": d["medium"], "low": d["low"],
            "evidence_count": d["evidence_count"],
        }
    return json.dumps({"alias": alias, "dimensions": ordered_dims,
                       "summary": summary}, ensure_ascii=False)


def main():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="知人明画像缺口扫描")
    parser.add_argument("profile", help="画像 JSON 路径")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    profile_path = Path(args.profile)
    if not profile_path.is_file():
        print("错误：画像文件不存在：%s" % profile_path, file=sys.stderr)
        sys.exit(2)
    try:
        data = json.loads(profile_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        print("错误：画像 JSON 解析失败：%s" % exc, file=sys.stderr)
        sys.exit(2)
    if not isinstance(data, dict):
        print("错误：画像根节点不是对象", file=sys.stderr)
        sys.exit(2)

    alias, updated_at, dimensions, summary = scan_profile(data)
    if args.format == "json":
        sys.stdout.write(render_json(alias, dimensions, summary) + "\n")
    else:
        sys.stdout.write(render_text(alias, updated_at, dimensions, summary) + "\n")
    print("扫描完成：缺口 %d / 薄弱 %d / 良好 %d，match_ready=%s"
          % (summary["gap"], summary["weak"], summary["ok"],
             summary["match_ready"]), file=sys.stderr)
    sys.exit(0)


if __name__ == "__main__":
    main()
