#!/usr/bin/env python3
"""Offline drift check for Dennis browser-backed interface assets.

This checker compares the adjacent browser-backed service ACTION_ALLOWLIST with
Dennis' browser_backed_interface_asset_table_v1.yaml. It does not start the
service, call platforms, call DataAgent/Hive, or execute any runtime source.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ASSET_TABLE = REPO_ROOT / "computer_use_poc" / "browser_backed_interface_asset_table_v1.yaml"
DEFAULT_SERVICE_ACTIONS_JS = Path("/Users/pengcheng/dennis-local/browser-backed-api-poc/src/actions.js")
DEFAULT_SERVICE_REGISTRY = Path("/Users/pengcheng/dennis-local/browser-backed-api-poc/ACTION_REGISTRY.md")

REQUIRED_ASSET_FIELDS = (
    "observation_domain",
    "default_call_role",
    "required_anchor",
    "possible_outputs",
    "cap_policy",
    "stop_reason_policy",
    "prohibited_usage",
    "status",
    "notes",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _extract_action_allowlist(actions_js: str) -> list[str]:
    match = re.search(r"ACTION_ALLOWLIST\s*=\s*Object\.freeze\(\[(.*?)\]\)", actions_js, re.S)
    if not match:
        raise ValueError("ACTION_ALLOWLIST block not found in service actions.js")
    names = re.findall(r'"([a-z][a-z0-9_]*)"', match.group(1))
    return sorted(set(names))


def _extract_declared_registry_count(registry_text: str) -> int | None:
    match = re.search(r"Current callable action count:\s*(\d+)", registry_text)
    return int(match.group(1)) if match else None


def _extract_asset_entries(asset_text: str) -> list[dict[str, Any]]:
    chunks = asset_text.split("\n  - interface_name: ")[1:]
    entries: list[dict[str, Any]] = []
    for chunk in chunks:
        lines = chunk.splitlines()
        if not lines:
            continue
        name = lines[0].strip()
        body = "\n".join(lines[1:])
        fields: dict[str, Any] = {"interface_name": name}
        for field in REQUIRED_ASSET_FIELDS:
            fields[field] = bool(re.search(rf"^\s{{4}}{re.escape(field)}:", body, re.M))
        entries.append(fields)
    return entries


def run_check(asset_table: Path, service_actions_js: Path, service_registry: Path | None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "schema_version": "interface_asset_table_check_v1",
        "service_actions_js": str(service_actions_js),
        "service_registry": str(service_registry) if service_registry else None,
        "asset_table": str(asset_table),
        "service_called": False,
        "platform_called": False,
        "dataagent_called": False,
        "runtime_runner_changed": False,
    }

    failures: list[str] = []
    if not service_actions_js.exists():
        failures.append("service_actions_js_missing")
        result["validation_pass"] = False
        result["failures"] = failures
        return result
    if not asset_table.exists():
        failures.append("asset_table_missing")
        result["validation_pass"] = False
        result["failures"] = failures
        return result

    allowlist = _extract_action_allowlist(_read(service_actions_js))
    asset_entries = _extract_asset_entries(_read(asset_table))
    asset_names = sorted(entry["interface_name"] for entry in asset_entries)

    declared_count = None
    if service_registry and service_registry.exists():
        declared_count = _extract_declared_registry_count(_read(service_registry))

    missing_required_fields = [
        {
            "interface_name": entry["interface_name"],
            "missing_fields": [field for field in REQUIRED_ASSET_FIELDS if not entry[field]],
        }
        for entry in asset_entries
        if any(not entry[field] for field in REQUIRED_ASSET_FIELDS)
    ]

    missing_in_asset = sorted(set(allowlist) - set(asset_names))
    extra_in_asset = sorted(set(asset_names) - set(allowlist))
    duplicate_asset_names = sorted({name for name in asset_names if asset_names.count(name) > 1})

    if declared_count is not None and declared_count != len(allowlist):
        failures.append("registry_declared_count_mismatch_allowlist")
    if len(asset_names) != len(allowlist):
        failures.append("asset_table_count_mismatch_service_allowlist")
    if missing_in_asset:
        failures.append("service_actions_missing_in_asset_table")
    if extra_in_asset:
        failures.append("asset_table_has_unknown_interfaces")
    if duplicate_asset_names:
        failures.append("asset_table_duplicate_interface_names")
    if missing_required_fields:
        failures.append("asset_table_missing_required_fields")

    result.update(
        {
            "registry_declared_count": declared_count,
            "service_allowlist_count": len(allowlist),
            "asset_table_count": len(asset_names),
            "required_asset_fields": list(REQUIRED_ASSET_FIELDS),
            "missing_in_asset": missing_in_asset,
            "extra_in_asset": extra_in_asset,
            "duplicate_asset_names": duplicate_asset_names,
            "missing_required_fields": missing_required_fields,
            "validation_pass": not failures,
            "failures": failures,
        }
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Dennis interface asset table against service ACTION_ALLOWLIST.")
    parser.add_argument("--asset-table", default=str(DEFAULT_ASSET_TABLE))
    parser.add_argument("--service-actions-js", default=str(DEFAULT_SERVICE_ACTIONS_JS))
    parser.add_argument("--service-registry", default=str(DEFAULT_SERVICE_REGISTRY))
    parser.add_argument("--format", choices=("json", "pretty"), default="pretty")
    args = parser.parse_args()

    result = run_check(Path(args.asset_table), Path(args.service_actions_js), Path(args.service_registry))
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        status = "PASS" if result.get("validation_pass") else "FAIL"
        print(f"interface_asset_table_check: {status}")
        print(f"service_allowlist_count={result.get('service_allowlist_count')}")
        print(f"asset_table_count={result.get('asset_table_count')}")
        print(f"failures={','.join(result.get('failures', [])) or 'none'}")
    return 0 if result.get("validation_pass") else 1


if __name__ == "__main__":
    sys.exit(main())
