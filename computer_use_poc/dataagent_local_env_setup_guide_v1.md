# DataAgent Local Env Setup Guide v1

## Purpose

This guide describes the local non-sensitive DataAgent env setup used by Dennis full_runtime for network readiness and dry-run parity tests.

This is not username/password login. The file only stores local endpoint and request identity hints.

## Non-Sensitive Config

`~/.dennis-agent/dataagent.env` may contain:

```text
DATAAGENT_BASE_URL="https://video-data.corp.kuaishou.com"
DATAAGENT_ENDPOINT_PATH="/v1/chat/completions/full"
DATAAGENT_USER_ID="muguangwu"
DATAAGENT_X_FORWARDED_USER="muguangwu"
DATAAGENT_HTTP_TIMEOUT_SECONDS="60"
```

`DATAAGENT_USER_ID` and `DATAAGENT_X_FORWARDED_USER` are request identity labels. They are not authentication credentials.

Real authentication still depends on the local corporate network, AccessProxy, SSO, and DataAgent permissions. Do not store credentials in this env file.

## Forbidden

Never store these in `~/.dennis-agent/dataagent.env`:

- cookie
- token
- session
- header
- password
- SSO state

Do not put `~/.dennis-agent/dataagent.env` into:

- repo files
- `outputs/full_runtime`
- release packages
- git

## Setup Steps

1. Create or check the local env file:

```text
python3 computer_use_poc/setup_dataagent_local_env.py
```

2. Load it into the current shell:

```text
source ~/.dennis-agent/dataagent.env
```

3. Run network readiness:

```text
python3 computer_use_poc/dataagent_network_readiness_check.py --json
```

4. If readiness passes, run the authorized dry-run parity check:

```text
python3 computer_use_poc/dataagent_local_dryrun_parity_check.py --live-dry-run --allow-live-dry-run --case single_user_ato --json
```

## Local Safety Checks

Check the env file without printing values:

```text
python3 computer_use_poc/setup_dataagent_local_env.py --check
```

Print the source command:

```text
python3 computer_use_poc/setup_dataagent_local_env.py --print-source-command
```

The helper prints only `<set>` / `<missing>` status for env keys and fails closed if forbidden field names are present.
