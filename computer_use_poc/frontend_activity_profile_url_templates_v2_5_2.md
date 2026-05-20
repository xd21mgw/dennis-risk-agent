# Frontend Activity Profile URL Templates v2.5.2

## 1. 基础入口

平台：

```text
埋点分析 → 分析工具 → 用户洞查 → 用户细查详情
```

基础域名：

```text
https://track-analysis.corp.kuaishou.com
```

基础路径：

```text
/app/sys/analytics_tool/sequence_list
```

## 2. 参数定义

| 参数 | 说明 | 当前支持 |
| --- | --- | --- |
| `funcType` | 查询功能 | `USER_PROFILE_QUERY` |
| `appName` | App 名称 | `KUAISHOU` / `NEBULA` |
| `filtersType` | 查询对象类型 | `userId` / `deviceId` |
| `filtersValue` | 查询对象值 | 用户 ID 或设备 ID |
| `isTableQuery` | 表格查询标记 | userId 示例中可见，按原 URL 保留 |
| `actionType` | 页面动作 | `detail` |
| `cacheGroup` | 缓存参数 | 按原 URL 保留 |
| `cacheAppName` | 缓存参数 | 按原 URL保留 |
| `cacheBucket` | 缓存参数 | 按原 URL 保留 |
| `sid` | session / 页面参数 | 示例中可见，是否必需待验证 |

## 3. KUAISHOU + userId

模板：

```text
https://track-analysis.corp.kuaishou.com/app/sys/analytics_tool/sequence_list?funcType=USER_PROFILE_QUERY&appName={appName}&filtersType=userId&filtersValue={userId}&isTableQuery=1&actionType=detail&cacheGroup=-2&cacheAppName=&cacheBucket=&sid={sid}
```

示例：

```text
https://track-analysis.corp.kuaishou.com/app/sys/analytics_tool/sequence_list?funcType=USER_PROFILE_QUERY&appName=KUAISHOU&filtersType=userId&filtersValue=444946196&isTableQuery=1&actionType=detail&cacheGroup=-2&cacheAppName=&cacheBucket=&sid=127437
```

## 4. NEBULA + userId

模板：

```text
https://track-analysis.corp.kuaishou.com/app/sys/analytics_tool/sequence_list?funcType=USER_PROFILE_QUERY&appName={appName}&filtersType=userId&filtersValue={userId}&isTableQuery=1&actionType=detail&cacheGroup=-2&cacheAppName=&cacheBucket=&sid={sid}
```

示例：

```text
https://track-analysis.corp.kuaishou.com/app/sys/analytics_tool/sequence_list?funcType=USER_PROFILE_QUERY&appName=NEBULA&filtersType=userId&filtersValue=444946196&isTableQuery=1&actionType=detail&cacheGroup=-2&cacheAppName=&cacheBucket=&sid=127437
```

## 5. KUAISHOU / NEBULA + deviceId

模板：

```text
https://track-analysis.corp.kuaishou.com/app/sys/analytics_tool/sequence_list?funcType=USER_PROFILE_QUERY&appName={appName}&filtersType=deviceId&filtersValue={deviceId}&actionType=detail&cacheGroup=-2&cacheAppName=&cacheBucket=
```

示例：

```text
https://track-analysis.corp.kuaishou.com/app/sys/analytics_tool/sequence_list?funcType=USER_PROFILE_QUERY&appName=KUAISHOU&filtersType=deviceId&filtersValue=HARMONY_4cc91f8f0ba877b6&actionType=detail&cacheGroup=-2&cacheAppName=&cacheBucket=
```

## 6. 构造规则

```yaml
url_template_inputs:
  appName:
    allowed_values:
      - KUAISHOU
      - NEBULA
  filtersType:
    allowed_values:
      - userId
      - deviceId
  filtersValue:
    required: true
  funcType:
    fixed: USER_PROFILE_QUERY
  actionType:
    fixed: detail
```

## 7. 待验证项

- `sid` 是否必需。
- `isTableQuery=1` 是否只对 userId 必需。
- NEBULA + deviceId 是否与 KUAISHOU + deviceId 完全同构。
- 直联 URL 在不同 browser profile 下是否需要登录态或额外权限。
