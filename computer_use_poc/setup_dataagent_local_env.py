#!/usr/bin/env python3
"""Create or check non-sensitive local DataAgent env configuration.

This helper never reads or stores cookie, token, session, header, password, or
SSO state content. It writes only non-sensitive local endpoint/request identity
settings for DataAgent dry-run parity testing.
"""

from __future__ import annotations

import argparse
import os
import stat
from pathlib import Path
from typing import Any


ENV_DIR = Path.home() / ".dennis-agent"
ENV_FILE = ENV_DIR / "dataagent.env"
SOURCE_COMMAND = "source ~/.dennis-agent/dataagent.env"
REQUIRED_KEYS = [
    "DATAAGENT_BASE_URL",
    "DATAAGENT_ENDPOINT_PATH",
    "DATAAGENT_USER_ID",
    "DATAAGENT_X_FORWARDED_USER",
    "DATAAGENT_HTTP_TIMEOUT_SECONDS",
]
DEFAULT_CONFIG = {
    "DATAAGENT_BASE_URL": "https://video-data.corp.kuaishou.com",
    "DATAAGENT_ENDPOINT_PATH": "/v1/chat/completions/full",
    "DATAAGENT_USER_ID": "muguangwu",
    "DATAAGENT_X_FORWARDED_USER": "muguangwu",
    "DATAAGENT_HTTP_TIMEOUT_SECONDS": "60",
}
FORBIDDEN_KEY_PARTS = ("cookie", "token", "session", "header", "password", "state")


def shell_quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def render_env(config: dict[str, str]) -> str:
    lines = [
        "# Dennis DataAgent local non-sensitive config.",
        "# Do not store cookie/token/session/header/password/state in this file.",
    ]
    for key in REQUIRED_KEYS:
        lines.append(f"export {key}={shell_quote(config[key])}")
    return "\n".join(lines) + "\n"


def is_safe_mode(path: Path, expected_mode: int) -> bool:
    try:
        mode = stat.S_IMODE(path.stat().st_mode)
    except FileNotFoundError:
        return False
    return mode == expected_mode


def parse_env_keys(path: Path) -> tuple[set[str], list[str]]:
    keys: set[str] = set()
    forbidden_keys: list[str] = []
    if not path.exists():
        return keys, forbidden_keys
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        key = line.split("=", 1)[0].strip()
        keys.add(key)
        lowered = key.lower()
        if any(part in lowered for part in FORBIDDEN_KEY_PARTS):
            forbidden_keys.append(key)
    return keys, forbidden_keys


def redacted_config_status(keys: set[str]) -> dict[str, str]:
    return {key: "<set>" if key in keys else "<missing>" for key in REQUIRED_KEYS}


def check_env() -> dict[str, Any]:
    dir_exists = ENV_DIR.exists()
    file_exists = ENV_FILE.exists()
    keys, forbidden_keys = parse_env_keys(ENV_FILE)
    missing_keys = [key for key in REQUIRED_KEYS if key not in keys]
    dir_mode_safe = is_safe_mode(ENV_DIR, 0o700) if dir_exists else False
    file_mode_safe = is_safe_mode(ENV_FILE, 0o600) if file_exists else False
    ok = (
        dir_exists
        and file_exists
        and dir_mode_safe
        and file_mode_safe
        and not missing_keys
        and not forbidden_keys
    )
    return {
        "status": "OK" if ok else "FAIL_CLOSED",
        "env_dir": str(ENV_DIR),
        "env_file": str(ENV_FILE),
        "env_dir_exists": dir_exists,
        "env_file_exists": file_exists,
        "env_dir_mode": "<set>" if dir_mode_safe else "<missing>",
        "env_file_mode": "<set>" if file_mode_safe else "<missing>",
        "required_env": redacted_config_status(keys),
        "missing_required_keys": missing_keys,
        "forbidden_fields_present": bool(forbidden_keys),
        "forbidden_field_names": forbidden_keys,
        "sensitive_content_printed": False,
        "remediation": "delete forbidden fields and rerun setup with --force" if forbidden_keys else None,
    }


def create_or_update_env(force: bool) -> dict[str, Any]:
    ENV_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(ENV_DIR, 0o700)
    if ENV_FILE.exists() and not force:
        result = check_env()
        result.update(
            {
                "action": "not_overwritten",
                "reason": "dataagent.env exists; pass --force to overwrite non-sensitive defaults",
            }
        )
        return result

    fd = os.open(str(ENV_FILE), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(render_env(DEFAULT_CONFIG))
    os.chmod(ENV_FILE, 0o600)
    result = check_env()
    result.update({"action": "created_or_updated"})
    return result


def print_check(result: dict[str, Any]) -> None:
    print(f"status={result['status']}")
    print(f"env_dir_exists={'<set>' if result['env_dir_exists'] else '<missing>'}")
    print(f"env_file_exists={'<set>' if result['env_file_exists'] else '<missing>'}")
    print(f"env_dir_mode={result['env_dir_mode']}")
    print(f"env_file_mode={result['env_file_mode']}")
    required_env = result["required_env"]
    for key in REQUIRED_KEYS:
        print(f"{key}={required_env[key]}")
    print(f"forbidden_fields_present={'<set>' if result['forbidden_fields_present'] else '<missing>'}")
    if result["forbidden_fields_present"]:
        print("fail_closed=delete forbidden fields; values were not printed")
    if result.get("action"):
        print(f"action={result['action']}")
    if result.get("reason"):
        print(f"reason={result['reason']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Set up local non-sensitive DataAgent env config.")
    parser.add_argument("--check", action="store_true", help="Check local env config safety.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing non-sensitive config.")
    parser.add_argument("--print-source-command", action="store_true", help="Print shell source command.")
    args = parser.parse_args(argv)

    if args.print_source_command:
        print(SOURCE_COMMAND)
        return 0

    result = check_env() if args.check else create_or_update_env(args.force)
    print_check(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
