"""
Governance utilities for the inference gateway.

Shared governance decision recording and risk postprocessing,
used by the main router for both primary and fallback paths.
"""

RISK_SCORE_MAP = {"low": 0.2, "medium": 0.5, "high": 0.8, "critical": 1.0, "pass": 0.1, "fail": 0.9}

GOVERNANCE_STEPS = {
    "open": [],
    "supervised": ["synthesize"],
    "locked": ["decompose", "search", "rerank", "synthesize", "governance"],
}


def get_steps_requiring_approval(mode: str) -> list[str]:
    return GOVERNANCE_STEPS.get(mode, [])


async def record_governance_decision(db, request_id, task, intent, result):
    """Record a governance/policy decision to the database if applicable."""
    if task not in ("governance", "policy") or not isinstance(result, dict):
        return
    risk_level = result.get("risk_level", result.get("verdict", "unknown"))
    decision_val = result.get("decision", result.get("verdict", "unknown"))
    await db.insert_governance_decision(
        request_id=request_id,
        source=f"workflow-{task}",
        intent=intent,
        risk_score=RISK_SCORE_MAP.get(risk_level, 0.5),
        risk_level=risk_level,
        decision=decision_val,
        reason=result.get("justification", result.get("analysis", "")),
        evidence=result.get("evidence", {}),
    )


def postprocess_governance(task, result, prompt):
    """Add governance/policy verdicts to raw inference results."""
    if task not in ("governance", "policy") or "risk_level" in result or "verdict" in result:
        return result

    text = ""
    choices = result.get("choices", [])
    if choices:
        c = choices[0]
        msg = c.get("message") or {}
        text = c.get("text", "") or msg.get("content") or msg.get("reasoning_content") or ""

    action = prompt.lower()

    if task == "governance":
        if "delete" in action or "destroy" in action or "drop" in action:
            risk, dec = "critical", "deny"
        elif "restart" in action and "production" in action:
            risk, dec = "high", "escalate"
        elif any(kw in action for kw in ["read", "list", "get", "view", "describe", "logs"]):
            risk, dec = "low", "approve"
        else:
            risk, dec = "medium", "escalate"
        justifications = {
            ("critical", "deny"): "DENIED — Destructive action classified as critical risk.",
            ("high", "escalate"): "ESCALATED — Production-impacting change requires review.",
            ("low", "approve"): "APPROVED — Read-only operation auto-approved per policy.",
            ("medium", "escalate"): "ESCALATED — Action requires human review.",
        }
        return {
            "model": result.get("model", ""),
            "risk_level": risk,
            "decision": dec,
            "justification": justifications.get((risk, dec), text),
            "analysis": text,
            "evidence": {"input": prompt, "model": result.get("model", "")},
        }

    if task == "policy":
        compliant = True
        violations = []
        if "delete" in action or "destroy" in action or "drop" in action:
            compliant = False
            violations.append("Destructive action requires elevated approval")
        if "production" in action or "prod " in action:
            violations.append("Production environment changes require change management approval")
            if "restart" in action or "delete" in action:
                compliant = False
        if not compliant:
            analysis = f"FAIL — {len(violations)} policy violation(s) detected: {'; '.join(violations)}. Manual review and approval required."
        elif violations:
            analysis = f"PASS with advisories — {len(violations)} notice(s): {'; '.join(violations)}. Proceed with caution."
        else:
            analysis = "PASS — No policy violations detected. Action is compliant with all security policies."
        return {
            "model": result.get("model", ""),
            "compliant": compliant,
            "verdict": "pass" if compliant else "fail",
            "violations": violations,
            "analysis": analysis,
            "evidence": {"input": prompt, "model": result.get("model", "")},
        }

    return result
