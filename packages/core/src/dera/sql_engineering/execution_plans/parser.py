"""Bounded JSON ingestion, independent of SQL parsers, connectors and evaluators."""

import json
import math

MAX_BYTES = 1_048_576
MAX_DEPTH = 64
MAX_VALUES = 50_000
MAX_NODES = 1_000
MAX_PLAN_DEPTH = 48


class PlanInputError(ValueError):
    """Safe public error: never contains submitted data."""


def fail():
    raise PlanInputError("Invalid, unsupported or over-limit imported execution plan.")


def canonical(value):
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":")
    )


def decode(text: str):
    try:
        if (
            not isinstance(text, str)
            or len(text) > MAX_BYTES
            or len(text.encode("utf-8")) > MAX_BYTES
        ):
            fail()
        # Bound raw container depth before invoking the JSON decoder. Braces in strings are data.
        depth = 0
        quoted = escaped = False
        for char in text:
            if quoted:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    quoted = False
            elif char == '"':
                quoted = True
            elif char in "[{":
                depth += 1
                if depth > MAX_DEPTH:
                    fail()
            elif char in "]}":
                depth -= 1

        def pairs(items):
            result = {}
            for key, value in items:
                if key in result:
                    fail()
                result[key] = value
            return result

        def constant(_):
            fail()

        result = json.loads(text, object_pairs_hook=pairs, parse_constant=constant)
        stack = [result]
        count = 0
        while stack:
            item = stack.pop()
            count += 1
            if count > MAX_VALUES:
                fail()
            if isinstance(item, dict):
                stack.extend(item.keys())
                stack.extend(item.values())
            elif isinstance(item, list):
                stack.extend(item)
            elif isinstance(item, str):
                if len(item.encode("utf-8")) > 16_384:
                    fail()
            elif isinstance(item, (int, float)) and not isinstance(item, bool):
                if not math.isfinite(item) or abs(item) > 1e15:
                    fail()
        return result
    except (ValueError, TypeError, RecursionError, OverflowError, UnicodeError):
        fail()


def number(data: dict, key: str, *, strings=False):
    value = data.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(
        value, (int, float, str) if strings else (int, float)
    ):
        fail()
    try:
        value = float(value)
    except (ValueError, OverflowError):
        fail()
    if not math.isfinite(value) or value < 0 or value > 1e15:
        fail()
    return value


def label(data, key):
    value = data.get(key)
    if value is not None and (not isinstance(value, str) or len(value) > 2048):
        fail()
    return value
