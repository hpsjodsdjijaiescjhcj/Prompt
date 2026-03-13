from __future__ import annotations

import re


def _token_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]", text))


def _contains_deadline(text: str) -> bool:
    patterns = [
        r"deadline",
        r"due",
        r"by\s+\w+",
        r"before\s+\w+",
        r"截至",
        r"截止",
        r"期限",
        r"最?晚",
        r"\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?",
        r"\d{1,2}月\d{1,2}日",
    ]
    return any(re.search(p, text, flags=re.IGNORECASE) for p in patterns)


def _contains_bullet_list(text: str) -> bool:
    for line in text.splitlines():
        s = line.strip()
        if re.match(r"^(?:-|\*|•)\s+", s):
            return True
        if re.match(r"^\d+[\.)]\s+", s):
            return True
    return False


def _tone_issue(tone: str, text: str) -> dict | None:
    lower = text.lower()
    if tone == "firm":
        markers = ["must", "urgent", "please", "kindly", "请", "尽快", "务必"]
        if not any(m in lower for m in markers):
            return {
                "type": "tone_mismatch",
                "message": "Tone is set to firm but the language lacks clear urgency/call-to-action markers.",
            }
    if tone == "friendly":
        markers = ["thanks", "thank you", "appreciate", "感谢", "谢谢"]
        if not any(m in lower for m in markers):
            return {
                "type": "tone_mismatch",
                "message": "Tone is set to friendly but gratitude/warmth markers are weak.",
            }
    return None


def validate_email_output(spec: dict, output: str) -> dict:
    constraints = spec.get("constraints", {})
    issues = []

    wc = _token_count(output)
    limit = int(constraints.get("word_limit", 200) or 200)
    if wc > limit:
        issues.append(
            {
                "type": "word_limit_exceeded",
                "message": f"Word/token count {wc} exceeds configured limit {limit}.",
            }
        )

    if constraints.get("must_include_deadline") and not _contains_deadline(output):
        issues.append(
            {
                "type": "missing_deadline",
                "message": "Spec requires a clear deadline, but none was detected.",
            }
        )

    if constraints.get("must_include_bullets") and not _contains_bullet_list(output):
        issues.append(
            {
                "type": "missing_bullets",
                "message": "Spec requires a bullet list, but none was detected.",
            }
        )

    tone = spec.get("tone", "professional")
    tone_issue = _tone_issue(tone, output)
    if tone_issue:
        issues.append(tone_issue)

    pass_check = len(issues) == 0

    suggested_fix_prompt = ""
    if not pass_check:
        issue_lines = "\n".join(f"- {i['type']}: {i['message']}" for i in issues)
        suggested_fix_prompt = (
            "Revise the email to satisfy the original spec and fix these validation issues:\n"
            f"{issue_lines}\n"
            "Return only the revised final email."
        )

    return {
        "pass": pass_check,
        "issues": issues,
        "suggested_fix_prompt": suggested_fix_prompt,
    }


def validate_code_output(spec: dict, output: str) -> dict:
    issues = []
    if not output.strip():
        issues.append(
            {"type": "empty_output", "message": "No output returned from executor."}
        )

    hints = ["diff --git", "+++", "---", "@@", "```", "changed files", "patch"]
    if output.strip() and not any(h in output for h in hints):
        issues.append(
            {
                "type": "format_weak",
                "message": "Output does not look like patch/diff or structured implementation details.",
            }
        )

    pass_check = len(issues) == 0
    suggested_fix_prompt = ""
    if not pass_check:
        suggested_fix_prompt = (
            "Revise the answer to provide either a unified diff/patch or explicit file-by-file code changes "
            "that satisfy the acceptance criteria."
        )

    return {
        "pass": pass_check,
        "issues": issues,
        "suggested_fix_prompt": suggested_fix_prompt,
    }
