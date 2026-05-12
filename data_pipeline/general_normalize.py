"""
Normalize heterogeneous Hugging Face instruction rows to a single JSONL-friendly schema.

Supports:

- ShareGPT-style ``conversations`` with ``from`` / ``value`` (or ``role`` / ``content``).
- Alpaca-style ``instruction`` + ``output`` with optional ``input``, plus common field-name variants.

Output records include ``messages`` (OpenAI-style ``role`` / ``content``) and a ``schema`` tag for downstream training.

Rows that cannot be normalized return ``None`` and are skipped by the sampler loop.
"""

from __future__ import annotations

import json
from typing import Any, Mapping


def _messages_from_sharegpt_turns(
    turns: list[Mapping[str, Any]],
) -> list[dict[str, str]] | None:
    """
    Convert a ShareGPT-style turn list to ``[{"role":"user"|"assistant","content":...}, ...]``.

    Args:
        turns: Raw ``conversations`` sub-list.

    Returns:
        Non-empty messages on success; ``None`` if a role is unknown or content is empty.
    """
    normalized_messages: list[dict[str, str]] = []
    for turn in turns:
        role_raw = str(turn.get("from") or turn.get("role") or "").strip().lower()
        content = str(turn.get("value") or turn.get("content") or "").strip()
        if not content:
            return None
        if role_raw in {"human", "user", "human_value"}:
            normalized_messages.append({"role": "user", "content": content})
        elif role_raw in {"gpt", "assistant", "chatgpt", "model"}:
            normalized_messages.append({"role": "assistant", "content": content})
        else:
            return None
    return normalized_messages or None


def normalize_general_row(
    *,
    source_repo: str,
    language_code: str,
    stable_row_id: str,
    hf_row: Mapping[str, Any],
) -> dict[str, Any] | None:
    """
    Normalize one Hugging Face dataset row to a common dict, or ``None`` if unsupported.

    Args:
        source_repo: Hub dataset id, e.g. ``"tatsu-lab/alpaca"``.
        language_code: Tag such as ``"en"`` or ``"zh"``.
        stable_row_id: Primary key for JSONL output (include repo + row index to avoid collisions).
        hf_row: Single row mapping from ``datasets``.

    Returns:
        Normalized record, or ``None`` if the row cannot be parsed.

    Note:
        Output contains ``id``, ``lang``, ``source_repo``, ``schema``, ``messages``, ``raw_subset``.
        ``raw_subset`` keeps only essential raw fields to limit size.
    """
    if "conversations" in hf_row and hf_row["conversations"]:
        turn_list = list(hf_row["conversations"])
        messages = _messages_from_sharegpt_turns(turn_list)
        if not messages:
            return None
        return {
            "id": stable_row_id,
            "lang": language_code,
            "source_repo": source_repo,
            "schema": "sharegpt_conversations",
            "messages": messages,
            "raw_subset": {"conversations": turn_list},
        }

    instruction = (
        hf_row.get("instruction")
        or hf_row.get("Instruction")
        or hf_row.get("query")
        or hf_row.get("Query")
        or hf_row.get("question")
        or hf_row.get("Question")
    )
    output_text = (
        hf_row.get("output")
        or hf_row.get("Output")
        or hf_row.get("response")
        or hf_row.get("Response")
        or hf_row.get("answer")
        or hf_row.get("Answer")
    )
    if instruction is None or output_text is None:
        return None
    optional_input = hf_row.get("input") or hf_row.get("Input") or ""
    instruction_stripped = str(instruction).strip()
    output_stripped = str(output_text).strip()
    input_stripped = str(optional_input).strip()
    if not instruction_stripped or not output_stripped:
        return None
    user_message = (
        instruction_stripped
        if not input_stripped
        else f"{instruction_stripped}\n{input_stripped}"
    )
    return {
        "id": stable_row_id,
        "lang": language_code,
        "source_repo": source_repo,
        "schema": "alpaca_triplet",
        "messages": [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": output_stripped},
        ],
        "raw_subset": {
            "instruction": instruction_stripped,
            "input": input_stripped,
            "output": output_stripped,
        },
    }


def dumps_jsonl_line(record: dict[str, Any]) -> str:
    """
    Serialize one record to a single JSON line (UTF-8, ``ensure_ascii=False``) plus newline.

    Args:
        record: Object to write as one JSONL line.

    Returns:
        One-line JSON string ending with ``\\n``.
    """
    return json.dumps(record, ensure_ascii=False) + "\n"
