# Frontend Activity Profile Test Cases v2.5.2

## 1. KUAISHOU userId 有明显使用时长

用户问题：

```text
这个 userId 在 KUAISHOU 下有没有前端活跃痕迹？
```

输入：

```yaml
appName: KUAISHOU
filtersType: userId
filtersValue: sample_user_id
```

预期：

- 如果“用户属性及时长”区域显示活跃天数和使用时长趋势，判断存在前端活跃信号。
- 只能说明存在前端活跃痕迹，不能证明真人 / 本人 / 具体动作。

状态：validated in v2.5.4 matrix。KUAISHOU + userId 样例显示明显使用时长，前端活跃信号强。

## 2. NEBULA userId 无明显使用时长

用户问题：

```text
这个 userId 在 NEBULA 下是不是没什么前端活跃？
```

输入：

```yaml
appName: NEBULA
filtersType: userId
filtersValue: sample_user_id
```

预期：

- 如果使用时长为空或活跃天数弱，判断前端活跃信号弱或无。
- 不得解释为用户没有任何行为，也不得解释为无风险。

状态：validated in v2.5.4 matrix。NEBULA + userId 样例使用时长接近 0，前端活跃信号弱。

## 3. deviceId 查询存在活跃趋势

用户问题：

```text
这个设备有没有前端活跃？
```

输入：

```yaml
appName: KUAISHOU
filtersType: deviceId
filtersValue: sample_device_id
```

预期：

- 如果存在使用时长趋势，说明设备维度存在前端活跃信号。
- 不能直接归因到具体用户操作。

状态：validated in v2.5.4 matrix。deviceId 查询可进入“用户属性及时长”区域，但不能直接归因到具体用户操作或证明稳定设备绑定。

## 4. 后端有业务动作但前端活跃画像为空

用户问题：

```text
后端看到有动作，但前端活跃画像为空，怎么解释？
```

预期：

- 不能直接说用户无前端行为。
- 需要进一步查行为序列、后端业务日志、登录日志和设备 SDK。
- 可能原因包括采集缺失、App / 端类型差异、时间窗不一致、查询对象不一致。

状态：pending browser validation。

## 5. 前端活跃强但登录日志 / 设备 SDK 异常

用户问题：

```text
前端活跃挺强，但登录日志和设备 SDK 都异常，能说明是正常真人吗？
```

预期：

- 不能直接判定正常真人。
- 前端活跃强只说明有前端使用痕迹。
- 登录异常、设备风险、自动化环境仍需独立评估。

状态：pending browser validation。

## 6. 用户申诉未操作但前端活跃画像存在

用户问题：

```text
用户申诉说没操作，但前端活跃画像有使用时长，这能反驳用户吗？
```

预期：

- 只能作为中弱证据。
- 不能直接证明用户本人操作。
- 需要查具体行为序列、登录日志、设备一致性和后端动作。

状态：pending browser validation。

## 7. v2.5.4 四组合矩阵验证状态

```yaml
matrix_validation:
  app_names:
    - KUAISHOU
    - NEBULA
  query_subject_types:
    - userId
    - deviceId
  total_cases: 4
  success_cases: 4
  failed_cases: 0
  validation_status: matrix_validation_passed_by_internal_agent
```

证据边界：

- 四组合可直联查询“用户属性及时长”区域。
- 该手脚适合提供前端活跃存在性证据。
- 不能单独证明真人操作、本人操作、具体业务动作发生或设备稳定绑定关系。
- 下方行为记录、行为回放、行为序列、行为统计仍未读取。
