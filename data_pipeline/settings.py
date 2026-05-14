"""
Environment-backed configuration for the data pipeline.

Loads ``.env`` via ``python-dotenv`` when imported, then parses variables into a frozen
``DataPipelineSettings`` dataclass for use by ``download_hf``, ``translate_qwen``, etc.

Design:

- All tunables come from environment variables for reproducibility across machines.
- Missing numeric env vars fall back to defaults; invalid non-empty values still raise from ``int()`` / ``float()``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _parse_int_from_env(env_var_name: str, default_value: int) -> int:
    """
    Read an integer environment variable, or return default if unset/blank.

    Args:
        env_var_name: Name of the environment variable (e.g. ``"GENERAL_SEED"``).
        default_value: Value used when the variable is missing or empty.

    Returns:
        Parsed integer.

    Raises:
        ValueError: If the variable is set but not a valid integer.
    """
    raw_value = os.getenv(env_var_name)
    if raw_value is None or str(raw_value).strip() == "":
        return default_value
    return int(raw_value)


def _parse_float_from_env(env_var_name: str, default_value: float) -> float:
    """
    Read a float environment variable, or return default if unset/blank.

    Args:
        env_var_name: Name of the environment variable.
        default_value: Value used when the variable is missing or empty.

    Returns:
        Parsed float.

    Raises:
        ValueError: If the variable is set but not a valid float.
    """
    raw_value = os.getenv(env_var_name)
    if raw_value is None or str(raw_value).strip() == "":
        return default_value
    return float(raw_value)


def _truthy_env(var_name: str, default: bool = False) -> bool:
    raw_value = os.getenv(var_name)
    if raw_value is None or str(raw_value).strip() == "":
        return default
    return str(raw_value).strip().lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class DataPipelineSettings:
    """
    Immutable settings for download and translation.

    Fields are grouped by concern: paths, Hugging Face, brainstorm dataset,
    general mix, DashScope translation. See root ``.env.example`` for variable names.
    """

    # Paths (relative paths resolve from the process working directory, usually repo root)
    data_root: str
    brainstorm_raw_dir: str
    general_raw_dir: str
    translated_jsonl_path: str
    translation_checkpoint_path: str

    # Hugging Face Hub / datasets
    hf_token: str | None
    hf_home: str | None

    # brainstorm_vicuna_10k
    brainstorm_repo: str
    brainstorm_revision: str | None
    brainstorm_source_jsonl: str
    #: Lines to skip (valid JSON lines) before collecting validation English rows; aligns with spec §4.1 head.
    brainstorm_train_head_n: int
    #: English validation rows to take after the head (requires translated JSONL for zh export).
    brainstorm_val_export_n: int
    brainstorm_val_en_jsonl: str
    brainstorm_val_zh_jsonl: str
    brainstorm_validation_meta_json: str
    #: If True, abort when any validation ``id`` is missing from the translated file.
    brainstorm_val_require_full_zh: bool

    # General mix (sampled from two HF datasets: EN + ZH)
    general_total_n: int
    general_seed: int
    general_en_repo: str
    general_en_split: str
    general_en_n: int
    general_en_revision: str | None
    general_en_config_name: str | None
    general_zh_repo: str
    general_zh_split: str
    general_zh_n: int
    general_zh_revision: str | None
    general_zh_config_name: str | None
    # If >0: hold out this many rows (split evenly by language) to
    # general_mixed_validation.jsonl; train rows go to general_mixed_train.jsonl.
    # If 0: write a single general_mixed.jsonl (legacy).
    general_val_n: int

    # DashScope OpenAI-compatible API (Qwen translation)
    dashscope_api_key: str
    dashscope_base_url: str
    translate_model: str
    translate_split: str
    translate_max_items: int | None
    translate_request_interval_sec: float
    translate_max_tokens: int
    translate_temperature: float
    translate_timeout_sec: float
    translate_log_every_n: int

    @classmethod
    def from_env(cls) -> DataPipelineSettings:
        """
        Build settings from the current process environment (including loaded ``.env``).

        Returns:
            Frozen ``DataPipelineSettings`` instance.

        Note:
            Empty ``TRANSLATE_MAX_ITEMS`` means no cap for this run.
            ``TRANSLATE_LOG_EVERY_N`` is clamped to at least ``1``.
        """
        data_root = os.getenv("DATA_ROOT", "./data").strip() or "./data"
        brainstorm_raw_dir = os.getenv(
            "BRAINSTORM_RAW_DIR", f"{data_root}/raw/brainstorm_vicuna_10k"
        ).strip()
        general_raw_dir = os.getenv(
            "GENERAL_RAW_DIR", f"{data_root}/raw/general_mixed"
        ).strip()
        translated_jsonl_path = os.getenv(
            "TRANSLATED_JSONL_PATH",
            f"{data_root}/processed/brainstorm_vicuna_10k_zh.jsonl",
        ).strip()
        translation_checkpoint_path = os.getenv(
            "TRANSLATION_CHECKPOINT_PATH",
            f"{data_root}/processed/translation_checkpoint.json",
        ).strip()

        hf_token_raw = os.getenv("HF_TOKEN") or os.getenv("HUGGING_FACE_HUB_TOKEN")
        hf_token = hf_token_raw.strip() if hf_token_raw else None
        hf_home_raw = os.getenv("HF_HOME")
        hf_home = hf_home_raw.strip() if hf_home_raw else None

        brainstorm_repo = os.getenv(
            "BRAINSTORM_DATASET_REPO", "DevQuasar/brainstorm_vicuna_10k"
        ).strip()
        brainstorm_revision_raw = os.getenv("BRAINSTORM_DATASET_REVISION", "").strip()
        brainstorm_revision = brainstorm_revision_raw or None
        brainstorm_source_override = os.getenv("BRAINSTORM_SOURCE_JSONL", "").strip()
        brainstorm_source_jsonl = brainstorm_source_override or (
            f"{brainstorm_raw_dir}/train.jsonl"
        )

        brainstorm_train_head_n = _parse_int_from_env("BRAINSTORM_TRAIN_HEAD_N", 5000)
        brainstorm_val_export_n = _parse_int_from_env("BRAINSTORM_VAL_EXPORT_N", 3000)
        brainstorm_val_en_raw = os.getenv("BRAINSTORM_VAL_EN_JSONL", "").strip()
        brainstorm_val_en_jsonl = brainstorm_val_en_raw or (
            f"{brainstorm_raw_dir}/validation_en.jsonl"
        )
        brainstorm_val_zh_raw = os.getenv("BRAINSTORM_VAL_ZH_JSONL", "").strip()
        brainstorm_val_zh_jsonl = brainstorm_val_zh_raw or (
            f"{data_root}/processed/brainstorm_vicuna_10k_zh_validation.jsonl"
        )
        brainstorm_validation_meta_raw = os.getenv(
            "BRAINSTORM_VALIDATION_META_JSON", ""
        ).strip()
        brainstorm_validation_meta_json = brainstorm_validation_meta_raw or (
            f"{data_root}/processed/brainstorm_validation_meta.json"
        )
        brainstorm_val_require_full_zh = _truthy_env(
            "BRAINSTORM_VAL_REQUIRE_FULL_ZH", default=False
        )

        general_total_n = _parse_int_from_env("GENERAL_TOTAL_N", 4000)
        general_seed = _parse_int_from_env("GENERAL_SEED", 42)
        general_en_repo = os.getenv("GENERAL_EN_DATASET_REPO", "tatsu-lab/alpaca").strip()
        general_en_split = os.getenv("GENERAL_EN_DATASET_SPLIT", "train").strip()
        general_en_n = _parse_int_from_env("GENERAL_EN_SAMPLE_N", 2000)
        general_en_revision_raw = os.getenv("GENERAL_EN_DATASET_REVISION", "").strip()
        general_en_revision = general_en_revision_raw or None
        general_en_config_raw = os.getenv("GENERAL_EN_DATASET_CONFIG", "").strip()
        general_en_config_name = general_en_config_raw or None
        general_zh_repo = os.getenv(
            "GENERAL_ZH_DATASET_REPO", "FreedomIntelligence/evol-instruct-chinese"
        ).strip()
        general_zh_split = os.getenv("GENERAL_ZH_DATASET_SPLIT", "train").strip()
        general_zh_n = _parse_int_from_env("GENERAL_ZH_SAMPLE_N", 2000)
        general_zh_revision_raw = os.getenv("GENERAL_ZH_DATASET_REVISION", "").strip()
        general_zh_revision = general_zh_revision_raw or None
        general_zh_config_raw = os.getenv("GENERAL_ZH_DATASET_CONFIG", "").strip()
        general_zh_config_name = general_zh_config_raw or None
        general_val_n = _parse_int_from_env("GENERAL_VAL_N", 1000)

        dashscope_api_key = (os.getenv("DASHSCOPE_API_KEY") or "").strip()
        dashscope_base_url = os.getenv(
            "DASHSCOPE_OPENAI_BASE_URL",
            "https://dashscope.aliyuncs.com/compatible-mode/v1",
        ).strip()
        translate_model = os.getenv("TRANSLATE_MODEL", "qwen-max").strip()

        translate_split = os.getenv("TRANSLATE_SPLIT", "train").strip()
        translate_max_items_raw = os.getenv("TRANSLATE_MAX_ITEMS", "").strip()
        translate_max_items = (
            int(translate_max_items_raw) if translate_max_items_raw else None
        )
        translate_log_every_n = max(1, _parse_int_from_env("TRANSLATE_LOG_EVERY_N", 5))

        return cls(
            data_root=data_root,
            brainstorm_raw_dir=brainstorm_raw_dir,
            general_raw_dir=general_raw_dir,
            translated_jsonl_path=translated_jsonl_path,
            translation_checkpoint_path=translation_checkpoint_path,
            hf_token=hf_token,
            hf_home=hf_home,
            brainstorm_repo=brainstorm_repo,
            brainstorm_revision=brainstorm_revision,
            brainstorm_source_jsonl=brainstorm_source_jsonl,
            brainstorm_train_head_n=brainstorm_train_head_n,
            brainstorm_val_export_n=brainstorm_val_export_n,
            brainstorm_val_en_jsonl=brainstorm_val_en_jsonl,
            brainstorm_val_zh_jsonl=brainstorm_val_zh_jsonl,
            brainstorm_validation_meta_json=brainstorm_validation_meta_json,
            brainstorm_val_require_full_zh=brainstorm_val_require_full_zh,
            general_total_n=general_total_n,
            general_seed=general_seed,
            general_en_repo=general_en_repo,
            general_en_split=general_en_split,
            general_en_n=general_en_n,
            general_en_revision=general_en_revision,
            general_en_config_name=general_en_config_name,
            general_zh_repo=general_zh_repo,
            general_zh_split=general_zh_split,
            general_zh_n=general_zh_n,
            general_zh_revision=general_zh_revision,
            general_zh_config_name=general_zh_config_name,
            general_val_n=general_val_n,
            dashscope_api_key=dashscope_api_key,
            dashscope_base_url=dashscope_base_url,
            translate_model=translate_model,
            translate_split=translate_split,
            translate_max_items=translate_max_items,
            translate_request_interval_sec=_parse_float_from_env(
                "TRANSLATE_REQUEST_INTERVAL_SEC", 0.35
            ),
            translate_max_tokens=_parse_int_from_env("TRANSLATE_MAX_TOKENS", 8192),
            translate_temperature=_parse_float_from_env("TRANSLATE_TEMPERATURE", 0.2),
            translate_timeout_sec=_parse_float_from_env(
                "TRANSLATE_TIMEOUT_SEC", 120.0
            ),
            translate_log_every_n=translate_log_every_n,
        )
