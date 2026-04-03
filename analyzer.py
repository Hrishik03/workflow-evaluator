import json
import os
import re
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from groq import Groq


load_dotenv()


DEFAULT_MODEL = "llama-3.1-8b-instant"

DEFAULT_WEIGHTS = {
    "prompt_clarity": 0.25,
    "iteration_quality": 0.25,
    "debugging_approach": 0.25,
    "ai_utilization": 0.25,
}

PHASES = [
    "problem_framing",
    "planning",
    "implementation",
    "debugging",
    "testing",
    "refinement",
]


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _compute_signal_quality_factor(turns: List[Dict[str, str]]) -> float:
    """
    Heuristic transcript quality signal in [0, 1].
    Higher is better evidence for reliable scoring.
    """
    total_turns = len(turns)
    user_turns = sum(1 for t in turns if t.get("role") == "user")
    assistant_turns = sum(1 for t in turns if t.get("role") == "assistant")
    total_chars = sum(len((t.get("content") or "").strip()) for t in turns)

    # Saturating factors.
    turn_factor = _clamp(total_turns / 8.0, 0.0, 1.0)
    length_factor = _clamp(total_chars / 3000.0, 0.0, 1.0)
    user_presence_factor = 1.0 if user_turns > 0 else 0.0

    # Prefer some balance between user and assistant turns.
    if user_turns == 0 or assistant_turns == 0:
        balance_factor = 0.4
    else:
        ratio = min(user_turns, assistant_turns) / max(user_turns, assistant_turns)
        balance_factor = _clamp(ratio, 0.0, 1.0)

    score = (
        0.35 * turn_factor
        + 0.30 * length_factor
        + 0.20 * balance_factor
        + 0.15 * user_presence_factor
    )
    return round(_clamp(score, 0.0, 1.0), 4)


def parse_transcript(transcript: str) -> List[Dict[str, str]]:
    """
    Parse raw transcript text into ordered chat turns.

    Expected format (flexible):
      user: ...
      assistant: ...
      ai: ...
      human: ...
    """
    if not transcript or not transcript.strip():
        return []

    lines = transcript.splitlines()
    # Supports:
    # - user: hello
    # - **User:** hello
    # - ## User
    #   hello
    # - > Assistant: hello
    inline_role_pattern = re.compile(
        r"^\s*(?:[#>\-\*\s]*)?(?:\*\*)?(user|human|assistant|ai|chatgpt|model)(?:\*\*)?\s*[:\-]\s*(.*)$",
        re.IGNORECASE,
    )
    heading_role_pattern = re.compile(
        r"^\s*(?:#{1,6}\s+)?(?:\*\*)?(user|human|assistant|ai|chatgpt|model)(?:\*\*)?\s*$",
        re.IGNORECASE,
    )

    turns: List[Dict[str, str]] = []
    current_role: Optional[str] = None
    current_parts: List[str] = []

    def flush_current() -> None:
        nonlocal current_role, current_parts
        if current_role and current_parts:
            content = "\n".join(current_parts).strip()
            if content:
                turns.append({"role": current_role, "content": content})
        current_role = None
        current_parts = []

    for line in lines:
        inline_match = inline_role_pattern.match(line)
        heading_match = heading_role_pattern.match(line)

        if inline_match:
            flush_current()
            raw_role = inline_match.group(1).lower()
            first_content = inline_match.group(2).strip()
            normalized_role = "user" if raw_role in {"user", "human"} else "assistant"
            current_role = normalized_role
            current_parts = [first_content] if first_content else []
        elif heading_match:
            flush_current()
            raw_role = heading_match.group(1).lower()
            normalized_role = "user" if raw_role in {"user", "human"} else "assistant"
            current_role = normalized_role
            current_parts = []
        else:
            # Continue current message block. If no role has started yet, ignore stray lines.
            if current_role is not None:
                current_parts.append(line)

    flush_current()
    return turns


def _build_eval_prompt(turns: List[Dict[str, str]]) -> str:
    transcript_text = []
    for t in turns:
        speaker = "User" if t["role"] == "user" else "AI"
        transcript_text.append(f"{speaker}: {t['content']}")

    joined = "\n\n".join(transcript_text)
    return (
        "You are an expert conversation quality evaluator.\n"
        "Evaluate this chat and return ONLY strict JSON with this exact schema:\n"
        "{\n"
        '  "prompt_clarity": <number 1-10>,\n'
        '  "iteration_quality": <number 1-10>,\n'
        '  "debugging_approach": <number 1-10>,\n'
        '  "ai_utilization": <number 1-10>,\n'
        '  "phases_detected": [<string from allowed list>, ...],\n'
        '  "phase_distribution": {\n'
        '    "problem_framing": <number 0-1>,\n'
        '    "planning": <number 0-1>,\n'
        '    "implementation": <number 0-1>,\n'
        '    "debugging": <number 0-1>,\n'
        '    "testing": <number 0-1>,\n'
        '    "refinement": <number 0-1>\n'
        "  },\n"
        '  "model_confidence": <number 0-1>,\n'
        '  "strengths": [<string>, ...],\n'
        '  "improvements": [<string>, ...],\n'
        '  "summary": <string>\n'
        "}\n\n"
        "Scoring rules:\n"
        "- 1 is very poor, 10 is excellent.\n"
        "- Use the full range when justified.\n"
        "- Judge iteration_quality by whether the engineer refines prompts / follows up vs accepting first answer.\n"
        "- Allowed phases: problem_framing, planning, implementation, debugging, testing, refinement.\n"
        "- phase_distribution values should be between 0 and 1 and approximately sum to 1.\n"
        "- model_confidence is your confidence in this evaluation between 0 and 1.\n"
        "- Keep strengths/improvements concise and concrete.\n\n"
        "Conversation:\n"
        f"{joined}\n"
    )


def _safe_parse_json(content: str) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Fallback: try extracting a JSON object block from a wrapped response.
    start = content.find("{")
    end = content.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(content[start : end + 1])
        except json.JSONDecodeError:
            return None
    return None


def evaluate_transcript_with_groq(
    turns: List[Dict[str, str]],
    model: str = DEFAULT_MODEL,
    api_key: Optional[str] = None,
    weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Evaluate parsed chat turns using Groq and return structured scores.
    """
    w = weights or DEFAULT_WEIGHTS
    weight_sum = float(sum(w.values())) if w else 0.0
    if weight_sum <= 0:
        w = DEFAULT_WEIGHTS
        weight_sum = float(sum(w.values()))
    # Normalize weights to sum to 1.0
    w = {k: float(v) / weight_sum for k, v in w.items()}

    empty_phase_distribution = {phase: 0.0 for phase in PHASES}
    signal_quality_factor = _compute_signal_quality_factor(turns)

    if not turns:
        return {
            "prompt_clarity": 0,
            "iteration_quality": 0,
            "debugging_approach": 0,
            "ai_utilization": 0,
            "overall_score": 0.0,
            "confidence_score": 0.0,
            "model_confidence": 0.0,
            "signal_quality_factor": signal_quality_factor,
            "phases_detected": [],
            "phase_distribution": empty_phase_distribution,
            "strengths": [],
            "improvements": ["No valid transcript turns were parsed."],
            "summary": "No analyzable conversation content found.",
            "error": "empty_transcript",
        }

    resolved_key = api_key or os.getenv("GROQ_API_KEY")
    if not resolved_key:
        return {
            "prompt_clarity": 0,
            "iteration_quality": 0,
            "debugging_approach": 0,
            "ai_utilization": 0,
            "overall_score": 0.0,
            "confidence_score": 0.0,
            "model_confidence": 0.0,
            "signal_quality_factor": signal_quality_factor,
            "phases_detected": [],
            "phase_distribution": empty_phase_distribution,
            "strengths": [],
            "improvements": ["Set GROQ_API_KEY in environment or pass api_key."],
            "summary": "Evaluation skipped due to missing API key.",
            "error": "missing_api_key",
        }

    client = Groq(api_key=resolved_key)
    prompt = _build_eval_prompt(turns)

    response = client.chat.completions.create(
        model=model,
        temperature=0.2,
        messages=[
            {"role": "system", "content": "Return only valid JSON. No markdown."},
            {"role": "user", "content": prompt},
        ],
    )
    content = response.choices[0].message.content or ""
    parsed = _safe_parse_json(content)

    if not parsed:
        return {
            "prompt_clarity": 0,
            "iteration_quality": 0,
            "debugging_approach": 0,
            "ai_utilization": 0,
            "overall_score": 0.0,
            "confidence_score": 0.0,
            "model_confidence": 0.0,
            "signal_quality_factor": signal_quality_factor,
            "phases_detected": [],
            "phase_distribution": empty_phase_distribution,
            "strengths": [],
            "improvements": ["Model response was not valid JSON."],
            "summary": "Evaluation failed due to malformed model output.",
            "error": "invalid_model_response",
            "raw_response": content,
        }

    prompt_clarity = float(parsed.get("prompt_clarity", 0) or 0)
    iteration_quality = float(parsed.get("iteration_quality", 0) or 0)
    debugging_approach = float(parsed.get("debugging_approach", 0) or 0)
    ai_utilization = float(parsed.get("ai_utilization", 0) or 0)
    try:
        model_confidence = float(parsed.get("model_confidence", 0) or 0)
    except (TypeError, ValueError):
        model_confidence = 0.0
    model_confidence = _clamp(model_confidence, 0.0, 1.0)

    overall = (
        prompt_clarity * w.get("prompt_clarity", 0.0)
        + iteration_quality * w.get("iteration_quality", 0.0)
        + debugging_approach * w.get("debugging_approach", 0.0)
        + ai_utilization * w.get("ai_utilization", 0.0)
    )

    parsed_phases = parsed.get("phases_detected", [])
    phases_detected = [p for p in parsed_phases if isinstance(p, str) and p in PHASES]
    # Keep order, deduplicate.
    phases_detected = list(dict.fromkeys(phases_detected))

    raw_distribution = parsed.get("phase_distribution", {})
    phase_distribution: Dict[str, float] = {}
    for phase in PHASES:
        value = raw_distribution.get(phase, 0) if isinstance(raw_distribution, dict) else 0
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            numeric = 0.0
        # Clamp each value to [0, 1] to keep UI-safe output.
        phase_distribution[phase] = max(0.0, min(1.0, numeric))

    dist_sum = sum(phase_distribution.values())
    if dist_sum > 0:
        phase_distribution = {k: round(v / dist_sum, 4) for k, v in phase_distribution.items()}
    elif phases_detected:
        equal_share = round(1.0 / len(phases_detected), 4)
        phase_distribution = {k: (equal_share if k in phases_detected else 0.0) for k in PHASES}

    confidence_score = model_confidence * signal_quality_factor

    
    return {
        "prompt_clarity": prompt_clarity,
        "iteration_quality": iteration_quality,
        "debugging_approach": debugging_approach,
        "ai_utilization": ai_utilization,
        "overall_score": round(float(overall), 2),
        "confidence_score": round(confidence_score * 100.0, 2),
        "model_confidence": round(model_confidence, 4),
        "signal_quality_factor": signal_quality_factor,
        "phases_detected": phases_detected,
        "phase_distribution": phase_distribution,
        "summary": parsed.get("summary", ""),
        "strengths": parsed.get("strengths", []),
        "improvements": parsed.get("improvements", []),
    }


def analyze_transcript(
    transcript: str,
    model: str = DEFAULT_MODEL,
    api_key: Optional[str] = None,
    weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    End-to-end helper for app.py:
    1) parse transcript
    2) evaluate with Groq
    3) return a display-friendly structured object
    """
    turns = parse_transcript(transcript)
    return evaluate_transcript_with_groq(
        turns=turns, model=model, api_key=api_key, weights=weights
    )
    