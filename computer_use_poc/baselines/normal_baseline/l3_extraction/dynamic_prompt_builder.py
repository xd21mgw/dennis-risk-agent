"""Prompt assembly for dynamic semantic discovery.

The builder assembles prompts only. It does not call a runtime LLM.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from action_catalog_builder import FAMILY_PROMPTS, card_for_action

PROMPT_DIR = Path(__file__).resolve().parent / "prompts"
CANONICAL_LENS_PATH = Path(__file__).resolve().parent / "dennis_risk_semantic_lens.md"
ORACLE_TERMS = ("色情", "擦边", "二维码", "网址钩子", "访问他人主页", "吸引回关", "异常工具类应用")


def _read_prompt(name: str) -> str:
    return (PROMPT_DIR / name).read_text(encoding="utf-8")


def _read_canonical_lens() -> str:
    return CANONICAL_LENS_PATH.read_text(encoding="utf-8")


def assemble_per_action_prompt(action_name: str, action_summary: dict[str, Any]) -> str:
    card = card_for_action(action_name)
    family = card["primary_family"]
    parts = [
        _read_prompt("base_blind_discovery_prompt.md"),
        _read_canonical_lens(),
        f"# Action Family Guidance\n{FAMILY_PROMPTS.get(family, '')}",
        "# Action Semantic Card",
        f"action_name: {action_name}",
        f"primary_family: {family}",
        f"physical_meaning: {card.get('physical_meaning', '')}",
        f"important_fields: {card.get('important_fields', [])}",
        "# Current Action Raw Summary",
        repr(action_summary),
    ]
    return "\n\n".join(parts)


def assemble_family_prompt(family: str, family_summary: dict[str, Any]) -> str:
    return "\n\n".join([
        _read_prompt("base_blind_discovery_prompt.md"),
        _read_canonical_lens(),
        f"# Family Guidance\n{FAMILY_PROMPTS.get(family, '')}",
        "# Family Feature/Signal Summary",
        repr(family_summary),
    ])


def assemble_cross_source_prompt(candidates_summary: dict[str, Any]) -> str:
    return "\n\n".join([
        _read_prompt("base_blind_discovery_prompt.md"),
        _read_canonical_lens(),
        _read_prompt("cross_source_discovery_prompt.md"),
        "# High-value Per-action/Family Inputs",
        repr(candidates_summary),
    ])


def assemble_oracle_eval_prompt(discovery_summary: dict[str, Any]) -> str:
    return "\n\n".join([
        _read_prompt("oracle_posthoc_evaluation_prompt.md"),
        "# Discovery Summary",
        repr(discovery_summary),
    ])


def discovery_prompt_contains_oracle(prompt: str) -> bool:
    return any(term in prompt for term in ORACLE_TERMS)
