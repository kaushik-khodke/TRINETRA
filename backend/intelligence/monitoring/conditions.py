"""
TRINETRA Phase 7 — Controlled Monitor Condition Evaluator
Safe, deterministic condition evaluation without arbitrary code execution.
"""

from typing import Dict, Any, List


class ConditionEvaluator:
    """
    Evaluates schema-defined predicate logic (AND, OR, >, >=, <, <=, ==, !=, IN).
    Zero eval(), zero shell, zero arbitrary code.
    """

    OPERATORS = {
        ">": lambda a, b: float(a) > float(b),
        ">=": lambda a, b: float(a) >= float(b),
        "<": lambda a, b: float(a) < float(b),
        "<=": lambda a, b: float(a) <= float(b),
        "==": lambda a, b: str(a).upper() == str(b).upper(),
        "!=": lambda a, b: str(a).upper() != str(b).upper(),
        "in": lambda a, b: str(a).upper() in [str(x).upper() for x in b] if isinstance(b, list) else str(a) in str(b),
    }

    @classmethod
    def evaluate(cls, condition_tree: Dict[str, Any], context: Dict[str, Any]) -> bool:
        if not condition_tree:
            return True

        raw_op = condition_tree.get("operator") or condition_tree.get("op") or "AND"
        op = str(raw_op).upper()
        sub_conditions = condition_tree.get("conditions")

        if sub_conditions and isinstance(sub_conditions, list):
            if op == "AND":
                return all(cls.evaluate(sub, context) for sub in sub_conditions)
            elif op == "OR":
                return any(cls.evaluate(sub, context) for sub in sub_conditions)
            elif op == "NOT":
                return not cls.evaluate(sub_conditions[0], context) if sub_conditions else True

        # Leaf condition evaluation
        field = condition_tree.get("field")
        cmp_op = condition_tree.get("operator") or condition_tree.get("op") or "=="
        if str(cmp_op).lower() == "in":
            cmp_op = "in"
        expected_val = condition_tree.get("value")

        if not field:
            return True

        actual_val = context.get(field)
        if actual_val is None:
            # Check nested inside metrics or metadata
            if "metrics" in context and field in context["metrics"]:
                actual_val = context["metrics"][field]
            elif "confidence_dimensions" in context and field in context["confidence_dimensions"]:
                actual_val = context["confidence_dimensions"][field]

        if actual_val is None:
            return False

        eval_fn = cls.OPERATORS.get(cmp_op)
        if not eval_fn:
            return False

        try:
            return eval_fn(actual_val, expected_val)
        except Exception:
            return False


TriggerConditionEvaluator = ConditionEvaluator

