# Dennis Risk Semantic Lens for P1.1 Commonality Discovery

This lens is a soft guide for commonality proposal generation. It is not a
hard whitelist and it is not a production rule. A proposal may go beyond these
semantic areas, but it must explain why the commonality has risk relevance.

P1.1 candidates must be risk-sample commonality features, not API response
schema commonality. Shared field presence, fixed API key sets, and ordinary
string/numeric/list/dict shapes are diagnostics only unless they expose a
non-standard client, missing expected business field, abnormal value relation,
or other explicit risk semantics.

## Risk Semantic Areas

- Account/login risk: low client version, abnormal login type, token-login
  path, trusted-device gap, new-device login, login-device-UA-IP switching,
  sensitive action after login.
- Account mutation chain: profile set/modify, private-message setting change,
  password reset, mobile rebind, trust-device operation, third-platform check,
  token refresh, logout, and login-device list checks that repeat across risk
  samples with a shared client/device/network environment. The sequence is the
  risk semantic object; individual normal endpoints are not enough alone.
- Device/environment risk: trusted-device anomaly, root/hook/frida/proxy/
  emulator, no SIM, no lock screen, low launch/low activity, sensor or SDK
  environment anomaly, similar device environment.
- Device runtime fingerprint template: repeated real-time `weaponDecodeHeader`
  values, storage/screen/brightness/lock/sim/camera/microphone fingerprints,
  appVersion/sdkVersion/osVersion, boot/start/launch counters, network geo/ISP/
  IDC context, Track device profile, Track use-duration, accessibility or
  remote-control services. This must be judged as a per-device event and then
  rolled up to users by any-device hit; ordinary field names do not make a
  repeated value combination schema-only.
- Protocol/client anomaly: downgraded protocol, non-standard requestParam,
  missing normal client parameters, script-like parameter structure,
  inconsistent client fields, abnormal source/action call chain.
- Profile/content lure submission: current or historical profile description,
  nickname, bio, moment, content title/description, or private-message text that
  contains coded contact instructions, external domains, evasive browser/search
  wording, or repeated lure templates. Historical edit payloads and audit logs
  must be considered together with current profile state; a currently empty
  profile can still be part of a lure-submission pattern.
- Action environment shift: suspicious profile/content/social action submitted
  from concentrated or shifted client environment, such as HK/overseas
  country_code or IP city, concentrated board platform, repeated oDid/device,
  MYAPP/channel cluster, repeated app/client/sdk version, or proxy/automation
  package context. These fields are supporting risk commonality unless tied to a
  risk-bearing action.
- Content/publish chain: upload method, publish device, content source,
  publish-before/after behavior, templated content fields, publish plus device
  or login or policy-hit relation.
- Policy/hit path: shared policy hit or risk label can explain a path, but it
  may be label leakage and must not be a primary feature by itself.
- Group/batch commonality: same device family, IP segment, environment,
  time window, registration/login/publish rhythm, operation template, toolchain
  trace.
- Automation/toolchain: unusually low cost, fixed parameter template,
  missing normal frontend fields, overly short operation chain, consistent
  behavior rhythm, accessibility/automation trace.
- Accessibility/toolchain subcluster: repeated non-system accessibility package,
  service component, enabled-service list, `accessibilitySvc` capability bits,
  or `remoteControl` capability bits. Generic closed/disabled states remain weak
  diagnostics unless paired with a concrete package/service identity.

## Hard Boundary

`source_schema_commonality` and `no_risk_semantic_signal` are report-only. They
must not enter L3 candidate, L4 discovery_only, or L5 visible output.
