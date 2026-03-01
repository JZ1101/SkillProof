WEIGHTS = {"safety": 0.3, "technique": 0.4, "result": 0.3}
PASS_THRESHOLD = 70
SAFETY_PASS_THRESHOLD = 60


def aggregate(assessment: dict) -> dict:
    safety_score = assessment["safety"]["score"]
    technique_score = assessment["technique"]["score"]
    result_score = assessment["result"]["score"]

    weighted_total = (
        safety_score * WEIGHTS["safety"]
        + technique_score * WEIGHTS["technique"]
        + result_score * WEIGHTS["result"]
    )

    safety_passed = safety_score >= SAFETY_PASS_THRESHOLD
    overall_passed = weighted_total >= PASS_THRESHOLD and safety_passed

    if not safety_passed:
        fail_reason = f"Safety score {safety_score} is below minimum threshold of {SAFETY_PASS_THRESHOLD}."
    elif weighted_total < PASS_THRESHOLD:
        fail_reason = f"Overall score {weighted_total:.1f} is below pass threshold of {PASS_THRESHOLD}."
    else:
        fail_reason = None

    return {
        "scores": {
            "safety": safety_score,
            "technique": technique_score,
            "result": result_score,
        },
        "weighted_total": round(weighted_total, 1),
        "passed": overall_passed,
        "safety_passed": safety_passed,
        "fail_reason": fail_reason,
        "feedback": assessment.get("feedback", ""),
    }
