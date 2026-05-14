"""
Package marker for ``data_pipeline``.

This package covers Sprint 1 data preparation:

1. Download ``brainstorm_vicuna_10k`` and a bilingual general-mix dataset from Hugging Face to JSONL.
2. Call Qwen via Alibaba Cloud DashScope (OpenAI-compatible API) to translate English brainstorm dialogues to Chinese.
3. Optionally export brainstorm validation JSONL aligned with the training head (`export-brainstorm-val`).

Submodules:

- ``settings``: load ``DataPipelineSettings`` from ``.env``.
- ``download_hf``: HF download and sampling.
- ``brainstorm_validation``: post-head validation export + zh alignment.
- ``general_normalize``: normalize Alpaca / ShareGPT-style rows.
- ``conversation_format``: dialogue text, prompts, JSON parse/validate.
- ``translate_qwen``: translation loop, resume, progress logs.
- ``__main__``: CLI entry ``download`` / ``translate`` / ``export-brainstorm-val``.

See ``README.md`` in this folder and ``_docs/shaping/7_data_CN.md`` for product context.
"""

from __future__ import annotations

__all__ = ["settings"]
