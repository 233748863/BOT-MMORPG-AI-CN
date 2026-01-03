---
name: Spec 自动提交
description: 每次更新 spec 文件后自动提交到 git 本地仓库
version: "1.0"
triggers:
  - type: on_file_save
    pattern: ".kiro/specs/**/*.md"
actions:
  - type: shell
    command: git add .kiro/specs/ && git commit -m "更新 spec: ${KIRO_TRIGGER_FILE}"
---

# Spec 自动提交 Hook

当 `.kiro/specs/` 目录下的任何 markdown 文件被保存时，自动执行 git 提交。

## 触发条件

- 文件保存事件
- 文件路径匹配 `.kiro/specs/**/*.md`

## 执行动作

1. 将 `.kiro/specs/` 目录下的所有更改添加到暂存区
2. 提交更改，提交信息包含触发文件名
