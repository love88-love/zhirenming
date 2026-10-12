#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""知人明 · 画像 Schema 校验脚本

用法：
    python validate_profile.py <profile_json_path> [--schema <schema_path>]

行为契约（DETAIL-DESIGN §5.1）：
    - stdout 只输出单行 JSON：{"valid": bool, "file": str, "errors": [...]}
      fallback 模式额外带 "validator": "fallback"
    - 人类可读进度一律写 stderr，不污染 stdout
    - 退出码：0=通过 1=校验失败 2=文件/参数/schema 错误
    - 优先使用 jsonschema（Draft7 + FormatChecker），缺失时自动降级
      为内置精简校验器（覆盖必需字段/枚举/格式/minItems/条件必填）
    - --strict（v1.1，QA-A1）：追加置信度软校验——active 推断标 high
      但证据 <2 条且无 user_observation 直接观察时，stderr 告警并在
      stdout 附带 "warnings" 数组；只告警不阻断，退出码不变
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    from jsonschema import Draft7Validator, FormatChecker
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

# ---- 固定契约常量（与 profile.schema.json 一一对应，改动需同步） ----

TOP_REQUIRED = [
    "schema_version", "profile_id", "profile_type", "subject",
    "dimensions", "created_at", "updated_at",
]
DIMENSION_FAMILIES = ["big_five", "attachment", "communication_style",
                      "lifestyle_rhythm", "values"]
BIG_FIVE_SUB = ["openness", "conscientiousness", "extraversion",
                "agreeableness", "neuroticism"]
ASSESSMENT_REQUIRED = ["id", "claim", "confidence", "evidence", "status", "created_at"]
EVIDENCE_REQUIRED = ["quote", "source", "date"]

ENUM_PROFILE_TYPE = {"self", "other"}
ENUM_ROLE = {"friend", "colleague", "leader", "romantic", "family", "other"}
ENUM_TENDENCY = {"high", "medium", "low", "unclear"}
ENUM_LABEL = {"secure", "anxious", "avoidant", "disorganized"}
ENUM_CONFIDENCE = {"high", "medium", "low"}
ENUM_SOURCE = {"user_report", "user_observation", "chat_record", "self_report",
               "memory_archive", "self_reflection"}
ENUM_STATUS = {"active", "revised"}

RE_SCHEMA_VERSION = re.compile(r"^1\.")
RE_ASSESSMENT_ID = re.compile(r"^a_[0-9]{3,}$")
RE_UUID = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


def _is_date(value):
    """格式校验：YYYY-MM-DD 且为真实日期"""
    if not isinstance(value, str):
        return False
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def _is_datetime(value):
    """格式校验：ISO 8601 date-time（须含时间部分）"""
    if not isinstance(value, str) or ("T" not in value and " " not in value):
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def _iter_dimension_slots(dimensions):
    """遍历 9 个维度槽位，产出 (点路径, 维度值)"""
    if not isinstance(dimensions, dict):
        return
    big_five = dimensions.get("big_five")
    if isinstance(big_five, dict):
        for sub in BIG_FIVE_SUB:
            if sub in big_five:
                yield "dimensions.big_five." + sub, big_five[sub]
    for fam in DIMENSION_FAMILIES[1:]:
        if fam in dimensions:
            yield "dimensions." + fam, dimensions[fam]


def fallback_validate(data):
    """内置精简校验器（无 jsonschema 时降级使用）

    覆盖范围严格对齐 DETAIL-DESIGN §5.1：必需字段 / 枚举 / 格式 /
    minItems / 条件必填。不做 schema 全量语义校验。
    """
    errors = []

    def err(path, message):
        errors.append({"path": path if path else "$", "message": message})

    if not isinstance(data, dict):
        err("$", "root must be an object")
        return errors

    # 顶层必需字段（7 项）
    for field in TOP_REQUIRED:
        if field not in data:
            err("$", "missing required field: '%s'" % field)

    # 顶层枚举与格式
    if "schema_version" in data and not (
        isinstance(data["schema_version"], str)
        and RE_SCHEMA_VERSION.match(data["schema_version"])
    ):
        err("schema_version", "must match pattern ^1\\.")
    if "profile_id" in data and not (
        isinstance(data["profile_id"], str) and RE_UUID.match(data["profile_id"])
    ):
        err("profile_id", "must be a UUID shape string")
    if "profile_type" in data and data["profile_type"] not in ENUM_PROFILE_TYPE:
        err("profile_type", "%r not in enum %s"
            % (data["profile_type"], sorted(ENUM_PROFILE_TYPE)))
    for field in ("created_at", "updated_at"):
        if field in data and not _is_datetime(data[field]):
            err(field, "must be ISO date-time format")

    # subject：alias 必填；role 枚举；profile_type=other 时 role 条件必填
    subject = data.get("subject")
    if isinstance(subject, dict):
        if "alias" not in subject:
            err("subject", "missing required field: 'alias'")
        if "role" in subject and subject["role"] not in ENUM_ROLE:
            err("subject.role", "%r not in enum %s"
                % (subject["role"], sorted(ENUM_ROLE)))
        if data.get("profile_type") == "other" and "role" not in subject:
            err("subject.role", "required when profile_type is 'other'")

    # dimensions：五族必填 + big_five 五子维度必填
    dimensions = data.get("dimensions")
    if isinstance(dimensions, dict):
        for fam in DIMENSION_FAMILIES:
            if fam not in dimensions:
                err("dimensions", "missing required field: '%s'" % fam)
        big_five = dimensions.get("big_five")
        if isinstance(big_five, dict):
            for sub in BIG_FIVE_SUB:
                if sub not in big_five:
                    err("dimensions.big_five", "missing required field: '%s'" % sub)

    # 各维度 assessments 逐条校验
    for dim_path, dim_val in _iter_dimension_slots(dimensions):
        if not isinstance(dim_val, dict):
            err(dim_path, "must be an object")
            continue
        if "assessments" not in dim_val:
            err(dim_path, "missing required field: 'assessments'")
            continue
        assessments = dim_val["assessments"]
        if not isinstance(assessments, list):
            err(dim_path + ".assessments", "must be an array")
            continue
        for idx, item in enumerate(assessments):
            a_path = "%s.assessments[%d]" % (dim_path, idx)
            _validate_assessment(item, a_path, err)

    return errors


def _validate_assessment(item, a_path, err):
    """单条 assessment 的精简校验（六必需 + 枚举 + 格式 + evidence）"""
    if not isinstance(item, dict):
        err(a_path, "must be an object")
        return
    for field in ASSESSMENT_REQUIRED:
        if field not in item:
            err(a_path, "missing required field: '%s'" % field)
    if "id" in item and not (
        isinstance(item["id"], str) and RE_ASSESSMENT_ID.match(item["id"])
    ):
        err(a_path + ".id", "must match pattern ^a_[0-9]{3,}$")
    if "tendency" in item and item["tendency"] not in ENUM_TENDENCY:
        err(a_path + ".tendency", "%r not in enum %s"
            % (item["tendency"], sorted(ENUM_TENDENCY)))
    if "label" in item:
        if item["label"] not in ENUM_LABEL:
            err(a_path + ".label", "%r not in enum %s"
                % (item["label"], sorted(ENUM_LABEL)))
        elif not a_path.startswith("dimensions.attachment."):
            err(a_path + ".label",
                "label 仅允许出现在 dimensions.attachment 下")
    if "confidence" in item and item["confidence"] not in ENUM_CONFIDENCE:
        err(a_path + ".confidence", "%r not in enum %s"
            % (item["confidence"], sorted(ENUM_CONFIDENCE)))
    if "status" in item and item["status"] not in ENUM_STATUS:
        err(a_path + ".status", "%r not in enum %s"
            % (item["status"], sorted(ENUM_STATUS)))
    for field in ("created_at", "updated_at"):
        if field in item and not _is_datetime(item[field]):
            err(a_path + "." + field, "must be ISO date-time format")

    evidence = item.get("evidence")
    if evidence is None:
        return  # 缺失已在必填检查报过
    if not isinstance(evidence, list):
        err(a_path + ".evidence", "must be an array")
        return
    if len(evidence) < 1:
        err(a_path + ".evidence", "minItems 1 violated: empty array")
    for eidx, ev in enumerate(evidence):
        e_path = "%s.evidence[%d]" % (a_path, eidx)
        if not isinstance(ev, dict):
            err(e_path, "must be an object")
            continue
        for field in EVIDENCE_REQUIRED:
            if field not in ev:
                err(e_path, "missing required field: '%s'" % field)
        if "source" in ev and ev["source"] not in ENUM_SOURCE:
            err(e_path + ".source", "%r not in enum %s"
                % (ev["source"], sorted(ENUM_SOURCE)))
        if "date" in ev and not _is_date(ev["date"]):
            err(e_path + ".date", "must be date format YYYY-MM-DD")


def _label_placement_errors(data):
    """label 位置校验（两种校验器共用）：attachment 以外的维度禁填 label。

    jsonschema 路径只查枚举，位置限制由本函数补齐，保证 fallback 与
    jsonschema 两种模式结论一致。
    """
    errors = []
    if not isinstance(data, dict):
        return errors
    for dim_path, dim_val in _iter_dimension_slots(data.get("dimensions")):
        if dim_path.startswith("dimensions.attachment"):
            continue
        if not isinstance(dim_val, dict):
            continue
        assessments = dim_val.get("assessments")
        if not isinstance(assessments, list):
            continue
        for idx, item in enumerate(assessments):
            if isinstance(item, dict) and "label" in item:
                errors.append({
                    "path": "%s.assessments[%d].label" % (dim_path, idx),
                    "message": "label 仅允许出现在 dimensions.attachment 下",
                })
    return errors


def jsonschema_validate(data, schema):
    """jsonschema 全量校验（Draft7 + 格式检查）"""
    validator = Draft7Validator(schema, format_checker=FormatChecker())
    errors = []
    for e in validator.iter_errors(data):
        path = "$"
        if e.absolute_path:
            parts = []
            for seg in e.absolute_path:
                if isinstance(seg, int):
                    parts[-1] += "[%d]" % seg
                else:
                    parts.append(str(seg))
            path = ".".join(parts)
        errors.append({"path": path, "message": e.message})
    return errors


def strict_warnings(data):
    """--strict 软校验（v1.1，QA-A1；v1.3 追加 memory_archive 规则）

    规则一（对齐 02 号 prompt §3）：active 推断 confidence=high 时，
    须满足「证据 ≥2 条」或「含 1 条 user_observation 直接行为观察」。
    规则二（v1.3，对齐 SKILL.md §0.5）：active 推断 confidence=high 时，
    证据中不得含 memory_archive（记忆档案为二手转述，上限 medium）。
    违反只产生告警，不影响 valid 与退出码——定级裁量仍在 prompt 层。
    """
    warnings = []
    if not isinstance(data, dict):
        return warnings
    for dim_path, dim_val in _iter_dimension_slots(data.get("dimensions")):
        if not isinstance(dim_val, dict):
            continue
        assessments = dim_val.get("assessments")
        if not isinstance(assessments, list):
            continue
        for idx, item in enumerate(assessments):
            if not isinstance(item, dict):
                continue
            if item.get("confidence") != "high":
                continue
            if item.get("status", "active") != "active":
                continue
            evidence = item.get("evidence")
            if not isinstance(evidence, list):
                continue
            has_direct_obs = any(
                isinstance(ev, dict) and ev.get("source") == "user_observation"
                for ev in evidence
            )
            if len(evidence) < 2 and not has_direct_obs:
                warnings.append({
                    "path": "%s.assessments[%d]" % (dim_path, idx),
                    "message": "confidence=high but evidence<2 and no "
                               "user_observation (AC-15 soft check)",
                })
            has_memory_archive = any(
                isinstance(ev, dict) and ev.get("source") == "memory_archive"
                for ev in evidence
            )
            if has_memory_archive:
                warnings.append({
                    "path": "%s.assessments[%d]" % (dim_path, idx),
                    "message": "confidence=high but evidence contains "
                               "memory_archive (SKILL.md §0.5: 记忆档案证据 "
                               "上限 medium)",
                })
    return warnings


def _emit(payload, code):
    """stdout 单行 JSON + 退出码"""
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    sys.exit(code)


def _fatal(message, file_name=None):
    """退出码 2 的统一出口"""
    payload = {"valid": False, "errors": [{"path": "$", "message": message}]}
    if file_name:
        payload["file"] = file_name
    print("错误：%s" % message, file=sys.stderr)
    _emit(payload, 2)


def main():
    # Windows 控制台默认 GBK，统一改为 UTF-8 保证机器可读
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="知人明画像 Schema 校验")
    parser.add_argument("profile", help="待校验画像 JSON 路径")
    parser.add_argument("--schema", default=None, help="schema 路径（可选）")
    parser.add_argument("--strict", action="store_true",
                        help="追加 AC-15 置信度软告警（不阻断）")
    args = parser.parse_args()

    profile_path = Path(args.profile)
    schema_path = Path(args.schema) if args.schema else (
        Path(__file__).resolve().parent.parent
        / "references" / "schemas" / "profile.schema.json"
    )
    file_name = profile_path.name

    if not profile_path.is_file():
        _fatal("profile file not found: %s" % profile_path, file_name)
    try:
        data = json.loads(profile_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        _fatal("profile JSON parse failed: %s" % exc, file_name)

    if HAS_JSONSCHEMA:
        if not schema_path.is_file():
            _fatal("schema file not found: %s" % schema_path, file_name)
        try:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            Draft7Validator.check_schema(schema)
        except Exception as exc:
            _fatal("schema load failed: %s" % exc, file_name)
        print("校验器：jsonschema（Draft7 + FormatChecker）", file=sys.stderr)
        errors = jsonschema_validate(data, schema)
        errors += _label_placement_errors(data)
        payload = {"valid": not errors, "file": file_name, "errors": errors}
    else:
        print("校验器：内置 fallback（未检测到 jsonschema）", file=sys.stderr)
        errors = fallback_validate(data)
        payload = {"valid": not errors, "file": file_name,
                   "errors": errors, "validator": "fallback"}

    errors.sort(key=lambda e: (e["path"], e["message"]))
    print("校验结果：%s，错误 %d 条"
          % ("通过" if not errors else "失败", len(errors)), file=sys.stderr)

    if args.strict:
        warnings = strict_warnings(data)
        for w in warnings:
            print("严格模式告警：%s: %s" % (w["path"], w["message"]),
                  file=sys.stderr)
        print("严格模式：告警 %d 条（不阻断）" % len(warnings),
              file=sys.stderr)
        payload["warnings"] = warnings

    _emit(payload, 0 if not errors else 1)


if __name__ == "__main__":
    main()
