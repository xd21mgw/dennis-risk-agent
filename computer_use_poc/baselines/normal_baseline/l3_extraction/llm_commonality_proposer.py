"""LLM-guided commonality proposal preparation and fixture adapter.

This module does not call an external LLM by itself. It prepares source-scoped
inputs and supports fixture/mock proposals so the L3->L5 contract can be tested
without network or model access.
"""

from __future__ import annotations

import json
import os
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from proposal_record_utils import coerce_observation_records, flatten_payload, load_json, payload_for_record, source_key


PROMPT_PATH = Path(__file__).with_name("llm_commonality_proposer_prompt.md")
REAL_LLM_REQUIRED_CONFIG = ("provider", "model", "adapter")


def load_runtime_prompt(path: str | Path | None = None) -> str:
    return Path(path or PROMPT_PATH).read_text(encoding="utf-8")


def build_source_observation_groups(raw_observation_path: str | Path) -> dict[str, dict[str, Any]]:
    records = coerce_observation_records(load_json(raw_observation_path))
    groups: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "action_or_source": "",
        "user_ids": set(),
        "records": [],
        "field_path_stats": Counter(),
        "sample_values": defaultdict(list),
    })
    for idx, record in enumerate(records):
        key = source_key(record)
        user_id = str(record.get("user_id") or record.get("uid") or f"record_{idx}")
        group = groups[key]
        group["action_or_source"] = key
        group["user_ids"].add(user_id)
        group["records"].append(record)
        for field_path, value in flatten_payload(payload_for_record(record)):
            group["field_path_stats"][field_path] += 1
            values = group["sample_values"][field_path]
            if len(values) < 5:
                values.append(value)

    normalized: dict[str, dict[str, Any]] = {}
    for key, group in groups.items():
        normalized[key] = {
            "action_or_source": key,
            "user_ids": sorted(group["user_ids"]),
            "record_count": len(group["records"]),
            "field_path_stats": dict(group["field_path_stats"].most_common(200)),
            "sample_values": {
                path: values
                for path, values in list(group["sample_values"].items())[:200]
            },
            "raw_records_available": True,
        }
    return normalized


def real_llm_preflight(
    *,
    enable_real_llm: bool = False,
    provider: str | None = None,
    model: str | None = None,
    adapter: str | None = None,
    endpoint: str | None = None,
    api_key_env: str | None = None,
) -> dict[str, Any]:
    """Return explicit real-LLM readiness without exposing secrets."""
    effective_provider = provider or os.environ.get("LLM_COMMONALITY_PROVIDER")
    effective_model = model or os.environ.get("LLM_COMMONALITY_MODEL")
    effective_adapter = adapter or os.environ.get("LLM_COMMONALITY_ADAPTER")
    effective_endpoint = endpoint or os.environ.get("LLM_COMMONALITY_ENDPOINT")
    effective_api_key_env = api_key_env or os.environ.get("LLM_COMMONALITY_API_KEY_ENV")
    missing: list[str] = []
    if not effective_provider:
        missing.append("provider")
    if not effective_model:
        missing.append("model")
    if not effective_adapter:
        missing.append("adapter")
    if effective_adapter in {"http_json", "openai_responses"}:
        if not effective_endpoint:
            missing.append("endpoint")
        if not effective_api_key_env:
            missing.append("api_key_env")
        elif not os.environ.get(effective_api_key_env):
            missing.append(f"env:{effective_api_key_env}")
    return {
        "requested_llm_mode": "real_llm" if enable_real_llm else "mock_or_fixture",
        "effective_llm_mode": "real_llm" if enable_real_llm and not missing else "mock_or_fixture",
        "enable_real_llm": enable_real_llm,
        "provider": effective_provider,
        "model": effective_model,
        "adapter": effective_adapter,
        "endpoint_config_present": bool(effective_endpoint),
        "api_key_env_config_present": bool(effective_api_key_env),
        "config_present": not missing,
        "missing_config_fields": missing,
        "real_llm_called": False,
        "fallback_reason": "" if enable_real_llm and not missing else (
            "real_llm_not_requested" if not enable_real_llm else "config_missing"
        ),
    }


def _proposal_payload_from_llm_json(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if not isinstance(value, dict):
        return []
    if isinstance(value.get("proposal_payloads"), list):
        return [item for item in value["proposal_payloads"] if isinstance(item, dict)]
    if "proposals" in value or "action_or_source" in value:
        return [value]
    return []


def _extract_json_object(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return json.loads(text[start:end + 1])
    raise ValueError("LLM response did not contain parseable JSON")


class CommonalityProposer:
    """Adapter boundary for fixture/mock and future LLM modes."""

    def __init__(
        self,
        *,
        mode: str = "off",
        fixture_path: str | Path | None = None,
        raw_proposals_per_action_source: int = 20,
        enable_real_llm: bool = False,
        provider: str | None = None,
        model: str | None = None,
        adapter: str | None = None,
        endpoint: str | None = None,
        api_key_env: str | None = None,
    ):
        self.mode = mode
        self.fixture_path = Path(fixture_path) if fixture_path else None
        self.raw_proposals_per_action_source = raw_proposals_per_action_source
        self.enable_real_llm = enable_real_llm
        self.provider = provider
        self.model = model
        self.adapter = adapter
        self.endpoint = endpoint
        self.api_key_env = api_key_env

    def _cap_payload(self, payload: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        item = dict(payload)
        proposals = list(item.get("proposals", []) or [])
        warnings: list[dict[str, Any]] = []
        for proposal in proposals:
            missing = []
            for key in ("proposal_type", "commonality_claim", "source_fields", "recompute_rule", "logic_reason"):
                if proposal.get(key) in (None, "", []):
                    missing.append(key)
            if missing:
                warnings.append({
                    "proposal_id": proposal.get("proposal_id") or proposal.get("proposal_name"),
                    "warning_type": "missing_proposal_schema_fields",
                    "missing_fields": missing,
                })
        if len(proposals) > self.raw_proposals_per_action_source:
            warnings.append({
                "warning_type": "raw_proposal_cap_applied",
                "before_count": len(proposals),
                "after_count": self.raw_proposals_per_action_source,
                "action_or_source": item.get("action_or_source"),
            })
            proposals = proposals[: self.raw_proposals_per_action_source]
        item["proposals"] = proposals
        item["proposal_count"] = len(proposals)
        return item, warnings

    def _cap_payloads(self, payloads: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        output: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []
        for payload in payloads:
            capped, payload_warnings = self._cap_payload(payload)
            output.append(capped)
            warnings.extend(payload_warnings)
        return output, warnings

    def propose(self, raw_observation_path: str | Path) -> dict[str, Any]:
        groups = build_source_observation_groups(raw_observation_path)
        if self.mode == "off":
            return {
                "mode": "off",
                "source_groups": groups,
                "proposal_payloads": [],
                "notes": ["LLM commonality proposer disabled."],
            }
        if self.mode == "fixture":
            if not self.fixture_path:
                raise ValueError("fixture mode requires fixture_path")
            payload = load_json(self.fixture_path)
            proposal_payloads = payload if isinstance(payload, list) else [payload]
            proposal_payloads, warnings = self._cap_payloads(proposal_payloads)
            return {
                "mode": "fixture",
                "source_groups": groups,
                "proposal_payloads": proposal_payloads,
                "parse_warnings": warnings,
                "notes": [f"Loaded fixture proposals from {self.fixture_path}; no real LLM call."],
            }
        if self.mode == "real":
            preflight = real_llm_preflight(
                enable_real_llm=self.enable_real_llm,
                provider=self.provider,
                model=self.model,
                adapter=self.adapter,
                endpoint=self.endpoint,
                api_key_env=self.api_key_env,
            )
            if not self.enable_real_llm:
                return {
                    "mode": "real_not_enabled",
                    "source_groups": groups,
                    "proposal_payloads": [],
                    "parse_warnings": [],
                    **preflight,
                    "real_llm_called": False,
                    "notes": ["Real LLM mode requested but --enable-real-llm was not set; no external call made."],
                }
            if not preflight["config_present"]:
                return {
                    "mode": "real_unconfigured",
                    "source_groups": groups,
                    "proposal_payloads": [],
                    "parse_warnings": [],
                    **preflight,
                    "real_llm_called": False,
                    "notes": ["Real LLM explicitly requested but required config is missing; no external call made."],
                }
            return self._propose_with_real_adapter(groups, preflight)
        if self.mode in {"summary", "deep", "code_assisted"}:
            return {
                "mode": self.mode,
                "source_groups": groups,
                "proposal_payloads": [],
                "parse_warnings": [],
                "notes": [
                    f"{self.mode} mode prepared source groups but no real LLM adapter is configured in this offline run."
                ],
            }
        raise ValueError(f"unsupported llm commonality mode: {self.mode}")

    def _propose_with_real_adapter(self, groups: dict[str, dict[str, Any]], preflight: dict[str, Any]) -> dict[str, Any]:
        adapter = str(preflight.get("adapter") or "")
        if adapter in {"mock_real", "test_mock"}:
            payloads = self._mock_real_payloads(groups)
            payloads, warnings = self._cap_payloads(payloads)
            return {
                "mode": "real_llm",
                "source_groups": groups,
                "proposal_payloads": payloads,
                "parse_warnings": warnings,
                **preflight,
                "real_llm_called": True,
                "notes": ["Explicit mock_real adapter invoked for test/preflight path; no secret was read or logged."],
            }
        if adapter in {"http_json", "openai_responses"}:
            payloads = self._http_json_payloads(groups, preflight)
            payloads, warnings = self._cap_payloads(payloads)
            return {
                "mode": "real_llm",
                "source_groups": groups,
                "proposal_payloads": payloads,
                "parse_warnings": warnings,
                **preflight,
                "real_llm_called": True,
                "notes": ["Explicit real LLM HTTP adapter invoked against offline observation input."],
            }
        return {
            "mode": "real_adapter_unsupported",
            "source_groups": groups,
            "proposal_payloads": [],
            "parse_warnings": [],
            **preflight,
            "real_llm_called": False,
            "fallback_reason": "unsupported_adapter",
            "notes": [f"Unsupported real LLM adapter `{adapter}`; no external call made."],
        }

    def _mock_real_payloads(self, groups: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        payloads: list[dict[str, Any]] = []
        for action_or_source, group in list(groups.items())[:1]:
            fields = list((group.get("field_path_stats") or {}).keys())[:2]
            if len(fields) < 2:
                continue
            user_count = len(group.get("user_ids") or [])
            payloads.append({
                "action_or_source": action_or_source,
                "proposal_count": 1,
                "proposals": [{
                    "proposal_id": f"real_mock_{action_or_source.replace('.', '_')}",
                    "proposal_type": "field_presence_observation",
                    "derived_feature_name": f"real_mock_{action_or_source.replace('.', '_')}_field_presence",
                    "proposal_name": f"real_mock_{action_or_source.replace('.', '_')}_field_presence",
                    "commonality_claim": "Most risk samples share this recalculable field-presence coverage pattern.",
                    "commonality_family": "expanded_feature_commonality",
                    "value_type": "compatibility",
                    "description": "Mock-real proposal for explicit real adapter wiring test.",
                    "source_fields": fields,
                    "required_fields": fields,
                    "recompute_rule": "required_fields_present",
                    "calculation_logic": "required_fields_present",
                    "claimed_hit_users": group.get("user_ids") or [],
                    "claimed_hit_count": user_count,
                    "claimed_hit_rate": 1.0 if user_count else 0.0,
                    "estimated_risk_hit_count": user_count,
                    "estimated_risk_denominator": user_count,
                    "estimated_risk_hit_rate": 1.0 if user_count else 0.0,
                    "logic_reason": "Field presence only; validates explicit real adapter path without external secrets.",
                    "value_summary": "required fields present",
                    "commonality_evidence": "Generated by mock_real adapter for explicit proposal adapter wiring.",
                    "leakage_risk": "none",
                    "uniqueness_risk": "none",
                    "suggested_bucket_or_value": "required_fields_present",
                }],
                "no_proposal_reason": "",
            })
        return payloads

    def _http_json_payloads(self, groups: dict[str, dict[str, Any]], preflight: dict[str, Any]) -> list[dict[str, Any]]:
        endpoint = self.endpoint or os.environ.get("LLM_COMMONALITY_ENDPOINT") or ""
        api_key_env = self.api_key_env or os.environ.get("LLM_COMMONALITY_API_KEY_ENV") or ""
        api_key = os.environ.get(api_key_env)
        if not endpoint or not api_key:
            return []
        prompt = load_runtime_prompt()
        payloads: list[dict[str, Any]] = []
        for action_or_source, group in groups.items():
            body = {
                "provider": preflight.get("provider"),
                "model": preflight.get("model"),
                "prompt": prompt,
                "action_or_source": action_or_source,
                "observation_group": group,
                "raw_proposals_per_action_source": self.raw_proposals_per_action_source,
            }
            request = urllib.request.Request(
                endpoint,
                data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
                headers={
                    "content-type": "application/json",
                    "authorization": f"Bearer {api_key}",
                },
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=60) as response:  # nosec: explicit opt-in adapter
                response_body = response.read().decode("utf-8")
            parsed = _extract_json_object(response_body)
            payloads.extend(_proposal_payload_from_llm_json(parsed))
        return payloads


def write_proposer_input(path: str | Path, source_groups: dict[str, Any]) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(source_groups, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
