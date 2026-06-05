# User Login Log Readonly POC v2.4.8 Run 011

```yaml
test_stage: v2.4.8
test_type: unified_log_special_event_detail
validation_status: unified_log_special_event_detail_validated
user_id: "4700398885"

high_risk_api_detail:
  row_found: true
  detail_opened: true
  visible_json_keys:
    - serviceKess
    - serviceKsn
    - serviceIp
    - serviceCatalog
    - serviceRegion
    - callerKsn
    - callerIp
    - callerCatalog
    - method
    - request
    - id
    - bitIndex
    - timestamp
    - action
    - extra
    - userId
    - deviceId
    - "@timestamp"
  key_count: 18
  perspective: service_side_call_chain
  credential_fields:
    token field  not_found
    session field  not_found
    ticket: not_found
    authorization field  not_found
    refresh_token: not_found
    access_token: not_found
  readonly_safety: PASSED

multi_account_login_detail:
  row_found: true
  detail_opened: true
  key_count: 66
  perspective: client_login_environment
  representative_json_keys:
    - userId
    - timestamp
    - deviceId
    - userIp
    - userIpv6
    - serverIp
    - sysVer
    - appVer
    - uri
    - status
    - phoneMod
    - params
    - vague
    - earphoneMode
    - isp
    - language
    - deviceName
    - did_tag
    - egid
    - thermal
    - net
    - kcv
    - kpf
    - oDid
    - kpn
    - global_id
    - loginToken
    - raw
    - passport_account_image
    - country_code
    - uQaTag
    - __NS_xfalcon
    - giveUpAccountCancel
    - keyconfig_state
    - loginType
    - cdid_tag
    - __NStokensig
    - sig
    - client_key
    - cold_launch_time_ms
    - osVersion
    - sh
    - deviceBit
    - browseType
    - power_mode
    - is_background
    - c
    - videoModelCrowdTag
    - sw
    - ftt
    - userRecoBit
    - cs
    - icaver
    - __NS_sig3
    - grant_browse_type
    - rdid
    - darkMode
    - extra
    - tokenId
    - clientPageCode
    - socialBanned
    - trustDeviceOn
    - token
    - ksLogId
    - remotePort
    - "@timestamp"
  credential_fields:
    token field  present_redacted
    loginToken: present_redacted
    tokenId: present_redacted
    session field  not_found
    ticket: not_found
    authorization field  not_found
    refresh_token: not_found
    access_token: not_found
  readonly_safety: PASSED

limitations:
  - “查看详情”按钮 type=submit，默认点击可能触发表单提交导致页面跳转
  - 需使用 scoped row click，并阻止默认 submit 行为，或采用已验证的 modal 打开方式
  - modal 内容异步渲染，若首次仅显示 “{” 或 innerHTML 为空，需等待 3-5 秒后再提取 JSON key
  - 高危接口调用日志 JSON 结构与多账号登录不同：高危日志偏服务端调用链视角，多账号登录偏客户端登录环境视角
  - 本轮只提取 JSON key，不输出 JSON value，不做风险定性
```

## Contract Update Targets

- `high_risk_api_detail_observation`
- `multi_account_login_detail_observation`
- `credential_fields_present_redacted_policy`
- `modal_async_render_wait_strategy`
- `submit_button_prevent_default_guardrail`
