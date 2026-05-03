# llm-fine-tunning-project

A personal sandbox repo: working with Cursor to take a project from zero to a **real-world deliverable centered on LLM fine-tuning**, with a **final target on Android**, while keeping a full paper trail.

## Background and motivation

I have a strong interest in LLM fine-tuning. High-quality small models are increasingly available (e.g., Gemma 2B / 4B, Qwen3 0.8B / 2B), which makes on-device and mobile deployment more realistic. This repo documents an experiment: **whether, within a bounded timeline, we can complete a credible path from fine-tuning to something shippable on Android**.

## Project goals (non-negotiables)

- The work **must include** a fine-tuning stage—not only RAG or a thin wrapper around a hosted API.
- **End state**: the model or inference stack should run on **Android phones**; the long-term aim is listing on **Android app stores** in China, with **WeChat Mini Program** kept as an optional variant.

## Collaboration and timeline

Target horizon is roughly **two to three months**, moving from idea to demo and then toward a release-ready slice; milestones will be revised as shaping and PoC results come in.

## Process log

Each collaboration session with Cursor—decisions, prompts, and outcomes—should be captured across **ideation → shaping → PoC → development → launch**. Detailed notes live mainly under `log/`, `shaping/`, and related folders for traceability.

## Current status

There is still a lot of **unknown territory**: product shape and domain focus are not fully fixed at the start and will be refined iteratively with Cursor. This README will evolve as the project progresses.
