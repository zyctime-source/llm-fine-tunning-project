"""
Batch-translate brainstorm English dialogues via Alibaba Cloud DashScope (OpenAI-compatible API).

Behavior:

- Read ``brainstorm_source_jsonl`` line by line, call Qwen (e.g. ``qwen-max``) to translate ``conversations``.
- Append rows to ``translated_jsonl_path`` with both ``conversations_zh`` and ``conversations_en`` for bilingual QA.
- Resume: skip sample ``id`` values already present in the output file.
- Emit lightweight progress logs every ``TRANSLATE_LOG_EVERY_N`` new completions.

Retries are handled by ``tenacity`` on ``translate_one``. This module does not compute billing.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from data_pipeline.conversation_format import (
    apply_original_speaker_roles_to_translated_turns,
    build_translation_user_content,
    conversations_to_plain_text,
    parse_model_json_text,
    validate_translated_conversations,
)
from data_pipeline.settings import DataPipelineSettings


def _count_text_lines_in_file(file_path: Path) -> int:
    """
    Count newline-terminated lines in a text file (includes empty lines).

    Args:
        file_path: Path to any text file; read in binary mode to avoid encoding edge cases.

    Returns:
        Line count.
    """
    line_count = 0
    with file_path.open("rb") as binary_fp:
        for _ in binary_fp:
            line_count += 1
    return line_count


def read_completed_sample_ids_from_jsonl(output_jsonl_path: Path) -> set[str]:
    """
    Load all ``id`` values from an existing translation JSONL for resume support.

    Args:
        output_jsonl_path: Path such as ``brainstorm_vicuna_10k_zh.jsonl``; missing file => empty set.

    Returns:
        Set of completed sample ids.
    """
    if not output_jsonl_path.exists():
        return set()
    completed_ids: set[str] = set()
    with output_jsonl_path.open("r", encoding="utf-8") as output_fp:
        for raw_line in output_fp:
            stripped = raw_line.strip()
            if not stripped:
                continue
            record = json.loads(stripped)
            sample_id = str(record.get("id", "")).strip()
            if sample_id:
                completed_ids.add(sample_id)
    return completed_ids


def create_dashscope_openai_client(settings: DataPipelineSettings) -> OpenAI:
    """
    Build an ``OpenAI`` SDK client pointed at the DashScope-compatible base URL.

    Args:
        settings: Must include ``dashscope_api_key``, ``dashscope_base_url``, ``translate_timeout_sec``.

    Returns:
        Configured ``OpenAI`` client.

    Raises:
        RuntimeError: If ``dashscope_api_key`` is empty.
    """
    if not settings.dashscope_api_key:
        raise RuntimeError("Missing DASHSCOPE_API_KEY; set it in .env.")
    return OpenAI(
        api_key=settings.dashscope_api_key,
        base_url=settings.dashscope_base_url,
        timeout=settings.translate_timeout_sec,
    )


class QwenTranslator:
    """
    One Chat Completions call per English dialogue, returning parsed JSON.

    Attributes:
        settings: Translation-related settings (model, temperature, max_tokens, ...).
        client: OpenAI-compatible client instance.
    """

    def __init__(self, settings: DataPipelineSettings) -> None:
        """
        Initialize translator state.

        Args:
            settings: Full pipeline settings object.
        """
        self.settings = settings
        self.client = create_dashscope_openai_client(settings)

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        reraise=True,
    )
    def translate_one(self, plain_english_dialogue: str) -> dict[str, Any]:
        """
        Call the remote model once for a full English dialogue block and parse JSON.

        Args:
            plain_english_dialogue: Output of ``conversations_to_plain_text``.

        Returns:
            Parsed dict; should contain a ``conversations`` list (Chinese turns).

        Raises:
            RuntimeError: If the assistant message content is empty.
            json.JSONDecodeError: If the model output is not valid JSON.
            ValueError: For unexpected structure after parsing.
        """
        user_message_content = build_translation_user_content(plain_english_dialogue)
        response = self.client.chat.completions.create(
            model=self.settings.translate_model,
            temperature=self.settings.translate_temperature,
            max_tokens=self.settings.translate_max_tokens,
            messages=[{"role": "user", "content": user_message_content}],
        )
        assistant_message = response.choices[0].message
        assistant_text = (assistant_message.content or "").strip()
        if not assistant_text:
            raise RuntimeError("Model returned empty assistant content")
        return parse_model_json_text(assistant_text)


def translate_brainstorm_file(settings: DataPipelineSettings) -> dict[str, Any]:
    """
    Translate all pending samples from ``brainstorm_source_jsonl`` and append to the output JSONL.

    Args:
        settings: Full settings; key fields include ``brainstorm_source_jsonl``,
            ``translated_jsonl_path``, ``translate_max_items``, ``translate_request_interval_sec``,
            ``translate_log_every_n``.

    Returns:
        Summary dict with keys ``source``, ``output``, ``processed_new``,
        ``skipped_existing_or_invalid``, ``model``. Also writes ``translation_checkpoint_path``.

    Raises:
        FileNotFoundError: If the source JSONL does not exist.
        OSError: On file write errors.
        API / JSON validation errors from downstream calls.
    """
    source_jsonl_path = Path(settings.brainstorm_source_jsonl)
    if not source_jsonl_path.exists():
        raise FileNotFoundError(
            f"Source file not found: {source_jsonl_path}. Run: python -m data_pipeline download"
        )

    output_jsonl_path = Path(settings.translated_jsonl_path)
    output_jsonl_path.parent.mkdir(parents=True, exist_ok=True)

    completed_sample_ids = read_completed_sample_ids_from_jsonl(output_jsonl_path)
    translator = QwenTranslator(settings)

    processed_new_count = 0
    skipped_count = 0
    source_line_estimate = _count_text_lines_in_file(source_jsonl_path)
    print(
        f"[translate] Source: {source_jsonl_path} | ~{source_line_estimate} lines | "
        f"already in output (skip): {len(completed_sample_ids)} ids"
    )
    print(
        f"[translate] Output: {output_jsonl_path} | model: {settings.translate_model} | "
        f"log every TRANSLATE_LOG_EVERY_N={settings.translate_log_every_n} "
        "(also first item and when max-items cap hit)"
    )

    run_started_monotonic = time.monotonic()
    last_logged_processed_count = 0

    with source_jsonl_path.open("r", encoding="utf-8") as source_fp, output_jsonl_path.open(
        "a", encoding="utf-8"
    ) as output_fp:
        for raw_line in source_fp:
            stripped_line = raw_line.strip()
            if not stripped_line:
                continue
            source_record = json.loads(stripped_line)
            sample_id = str(source_record.get("id", "")).strip()
            if not sample_id:
                skipped_count += 1
                continue
            if sample_id in completed_sample_ids:
                skipped_count += 1
                continue

            english_turns = source_record.get("conversations")
            if not isinstance(english_turns, list):
                skipped_count += 1
                continue

            plain_english_dialogue = conversations_to_plain_text(english_turns)
            parsed_model_payload = translator.translate_one(plain_english_dialogue)
            chinese_turns = parsed_model_payload.get("conversations")
            if not isinstance(chinese_turns, list):
                raise ValueError("Model JSON missing 'conversations' array")

            # Models may typo `from` (e.g. gtp); trust English roles, only translated `value`.
            apply_original_speaker_roles_to_translated_turns(english_turns, chinese_turns)
            validate_translated_conversations(english_turns, chinese_turns)

            output_record = {
                "id": sample_id,
                "source_id": sample_id,
                "split": settings.translate_split,
                "conversations_zh": chinese_turns,
                "conversations_en": english_turns,
            }
            output_fp.write(json.dumps(output_record, ensure_ascii=False) + "\n")
            output_fp.flush()
            completed_sample_ids.add(sample_id)
            processed_new_count += 1

            elapsed_seconds = time.monotonic() - run_started_monotonic
            items_per_second = (
                (processed_new_count / elapsed_seconds) if elapsed_seconds > 0 else 0.0
            )
            reached_max_items = (
                settings.translate_max_items is not None
                and processed_new_count >= settings.translate_max_items
            )
            should_emit_progress_log = (
                processed_new_count == 1
                or processed_new_count % settings.translate_log_every_n == 0
                or reached_max_items
            )
            if should_emit_progress_log:
                print(
                    f"[translate] this run: {processed_new_count} new | "
                    f"{elapsed_seconds:.1f}s elapsed | {items_per_second:.3f} items/s | last id={sample_id}"
                )
                last_logged_processed_count = processed_new_count

            if settings.translate_request_interval_sec > 0:
                time.sleep(settings.translate_request_interval_sec)

            if reached_max_items:
                break

    if processed_new_count > 0 and last_logged_processed_count != processed_new_count:
        elapsed_seconds = time.monotonic() - run_started_monotonic
        items_per_second = (
            (processed_new_count / elapsed_seconds) if elapsed_seconds > 0 else 0.0
        )
        print(
            f"[translate] this run: {processed_new_count} new | {elapsed_seconds:.1f}s elapsed | "
            f"{items_per_second:.3f} items/s (final)"
        )

    summary: dict[str, Any] = {
        "source": str(source_jsonl_path),
        "output": str(output_jsonl_path),
        "processed_new": processed_new_count,
        "skipped_existing_or_invalid": skipped_count,
        "model": settings.translate_model,
    }
    checkpoint_path = Path(settings.translation_checkpoint_path)
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return summary
