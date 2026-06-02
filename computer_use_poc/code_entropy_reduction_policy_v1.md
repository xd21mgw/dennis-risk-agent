# Code Entropy Reduction Policy v1

默认先扫旧规则、旧代码、旧 fixture、旧文档，并分类：`delete_now`、`merge_into_existing`、`replace_with_current_rule`、`keep_debug_only`、`keep_historical_only`、`uncertain_need_user_review`。

优先删除、合并、替换冲突口径；只有现有结构无法承载时才新增。新增代码必须说明为何不能复用或合并。

验收必须写明净新增/删除行数、删除了什么、合并了什么、替换了什么、保留了什么，以及保留原因。
