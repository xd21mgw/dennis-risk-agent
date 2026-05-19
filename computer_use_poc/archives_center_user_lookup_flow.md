# 档案中心 User ID 只读查询流程

## 1. 输入

必需输入：

- `user_id`

输入要求：

- 单个用户 ID。
- 不接受批量 ID。
- 不接受空值。
- 非 user_id 输入应直接返回 `invalid_query_object`。

## 2. 操作流程

```text
输入 user_id
→ 打开档案中心 URL
→ 检查是否登录
→ 检查是否有权限
→ 定位用户搜索入口
→ 输入 user_id
→ 点击查询
→ 判断是否进入用户主页
→ 识别可见 Tab / 模块
→ 记录关键字段是否可见
→ 返回结构化 observation
```

## 3. 只读检查点

每一步都必须满足：

- 不点击写操作按钮。
- 不触发处置、审批、保存、导出。
- 不绕过权限。
- 不记录高敏字段明文。

## 4. 页面状态判断

| 状态 | 判断方式 | 返回 |
|---|---|---|
| 未登录 | 出现登录页或登录态过期提示 | `login_status=not_logged_in` |
| 无权限 | 出现无权限、403、权限申请提示 | `permission_status=no_permission` |
| 页面加载失败 | 超时、白屏、网络错误 | `page_status=load_failed` |
| 搜索无结果 | 页面明确提示无用户或无记录 | `page_status=no_result` |
| 用户主页可见 | 展示用户基础信息或用户 Tab | `page_status=user_home_visible` |

## 5. 需要识别的可见模块

可见则记录模块名，不可见则写入 `hidden_or_missing_modules`：

- 用户基础信息
- 账号状态
- 风控状态 / 处罚状态
- 设备信息
- 登录信息
- 内容 / 作品信息
- 审核记录
- 举报记录
- 同设备 / 关联账号
- 操作日志

## 6. 关键字段可见性

只记录字段是否可见，不记录高敏明文：

- user_id
- account_status
- punish_status
- risk_label
- device_id / did
- last_login_time
- last_login_ip
- register_time
- operation_type
- audit_record
- report_record

## 7. 输出

输出必须符合 `observation_schema.md`。

查询结果只能作为页面 observation，不能直接生成最终风险结论。
