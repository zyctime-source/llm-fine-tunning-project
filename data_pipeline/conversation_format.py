"""
Dialogue text formatting, translation prompt construction, and model JSON handling.

Responsibilities:

- Serialize ``brainstorm_vicuna_10k``-style ``conversations`` (``human`` / ``gpt``) to plain text for the translator.
- Build the user message for Qwen per ``_docs/shaping/7_data_CN.md`` section 7.2.1 (Chinese instructions; must stay Chinese).
- Parse model output (strip optional Markdown ```json fences) and validate turn alignment.
- Optionally copy ``from`` labels from the English source onto translated turns to fix typos like ``gtp`` vs ``gpt``.

This module performs no network I/O.
"""

from __future__ import annotations

import json
import re
from typing import Any


def conversations_to_plain_text(conversations: list[dict[str, Any]]) -> str:
    """
    Serialize multi-turn ``conversations`` to one line per turn: ``role: text``.

    Args:
        conversations: List of turns, each usually with ``from`` and ``value``.

    Returns:
        Multi-line plain text, e.g. ``human: ...\\ngpt: ...``.

    Note:
        Missing ``from`` / ``value`` become empty strings; upstream data should be clean.
    """
    dialogue_lines: list[str] = []
    for turn in conversations:
        speaker = str(turn.get("from", "")).strip()
        utterance = str(turn.get("value", "")).strip()
        dialogue_lines.append(f"{speaker}: {utterance}")
    return "\n".join(dialogue_lines)


def build_translation_user_content(plain_english_dialogue: str) -> str:
    """
    Build the full **user** message for Qwen: Chinese instructions + English dialogue + JSON-only contract.

    The natural-language instructions must remain Chinese to match project shaping (7.2.1);
    only ``value`` fields should be translated by the model.

    Args:
        plain_english_dialogue: Output of ``conversations_to_plain_text``.

    Returns:
        String suitable as Chat Completions ``messages[0].content`` for role ``user``.
    """
    return (
        "请将以下英文头脑风暴对话翻译成中文。\n"
        "要求：\n"
        "1. 保持对话的自然流畅\n"
        "2. 保留追问和发散的语气\n"
        "3. 人名、地名可适当保留或音译\n"
        "4. 输出格式与原数据一致（human/gpt 交替）\n\n"
        "原文：\n"
        f"{plain_english_dialogue}\n\n"
        "请只输出一个 JSON 对象，不要 Markdown 代码围栏，不要解释性文字。"
        '格式严格为：{"conversations":[{"from":"human","value":"..."},'
        '{"from":"gpt","value":"..."}, ...]}'
        "。其中 from 的顺序与原文完全一致，仅翻译 value。"
    )


def parse_model_json_text(model_text: str) -> dict[str, Any]:
    """
    Parse a JSON object from the model's raw text response.

    Args:
        model_text: Raw ``message.content`` from the assistant.

    Returns:
        Parsed dict; typically contains a ``conversations`` key.

    Raises:
        json.JSONDecodeError: If text is not valid JSON after stripping fences.
    """
    cleaned_text = model_text.strip()
    fence_match = re.match(
        r"^```(?:json)?\s*([\s\S]*?)\s*```$", cleaned_text, re.IGNORECASE
    )
    if fence_match:
        cleaned_text = fence_match.group(1).strip()
    return json.loads(cleaned_text)


def apply_original_speaker_roles_to_translated_turns(
    original_turns: list[dict[str, Any]],
    translated_turns: list[dict[str, Any]],
) -> None:
    """
    Overwrite each translated turn's ``from`` with the matching English turn's ``from`` (in place).

    Cloud models sometimes typo ``gpt`` as ``gtp``. Per shaping we only require translated ``value``;
    speaker labels should match the HF source. Call this before ``validate_translated_conversations``.

    Args:
        original_turns: English ``conversations``.
        translated_turns: Parsed Chinese ``conversations``; ``from`` fields are mutated.

    Returns:
        None

    Raises:
        ValueError: If turn counts differ or a translated turn is not a ``dict``.
    """
    if len(translated_turns) != len(original_turns):
        raise ValueError(
            f"Turn count mismatch: original {len(original_turns)} vs translated {len(translated_turns)}"
        )
    for turn_index, source_turn in enumerate(original_turns):
        target_turn = translated_turns[turn_index]
        if not isinstance(target_turn, dict):
            raise ValueError(f"Translated turn {turn_index} is not a JSON object")
        speaker = str(source_turn.get("from", "")).strip()
        target_turn["from"] = speaker


def validate_translated_conversations(
    original_turns: list[dict[str, Any]],
    translated_turns: list[dict[str, Any]],
) -> None:
    """
    Ensure translated ``conversations`` align with the original list length and ``from`` roles.

    Args:
        original_turns: English ``conversations``.
        translated_turns: Parsed translated ``conversations``. If
            ``apply_original_speaker_roles_to_translated_turns`` ran first, ``from`` values should match.

    Returns:
        None

    Raises:
        ValueError: On length mismatch or ``from`` mismatch.
    """
    if len(translated_turns) != len(original_turns):
        raise ValueError(
            f"Turn count mismatch: original {len(original_turns)} vs translated {len(translated_turns)}"
        )
    for turn_index, (source_turn, target_turn) in enumerate(
        zip(original_turns, translated_turns)
    ):
        source_role = str(source_turn.get("from", "")).strip()
        target_role = str(target_turn.get("from", "")).strip()
        if source_role != target_role:
            raise ValueError(
                f"Role mismatch at turn {turn_index}: {source_role!r} vs {target_role!r}"
            )
