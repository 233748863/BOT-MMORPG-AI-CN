# 设计文档

## 概述

通过在应用程序启动时设置支持 emoji 的全局字体，解决 emoji 显示为方框的问题。

## 架构

### 解决方案

在 Windows 系统上，默认字体不支持 emoji 渲染。解决方案是：

1. 在 `QApplication` 创建后立即设置全局字体
2. 使用 `Segoe UI Emoji` 字体（Windows 内置，支持 emoji）
3. 配合 `Microsoft YaHei` 确保中文显示

### 字体回退链

```
Microsoft YaHei UI, Segoe UI Emoji, Segoe UI Symbol, sans-serif
```

- **Microsoft YaHei UI**: 中文显示
- **Segoe UI Emoji**: emoji 彩色显示
- **Segoe UI Symbol**: emoji 黑白备选
- **sans-serif**: 最终回退

## 组件和接口

### 修改 1: 主题模块 (界面/样式/主题.py)

添加全局字体配置函数：

```python
def 应用全局字体(app: QApplication):
    """应用支持 emoji 的全局字体
    
    Args:
        app: QApplication 实例
    """
    from PySide6.QtGui import QFont
    
    # 创建支持 emoji 的字体
    字体 = QFont()
    字体.setFamilies(["Microsoft YaHei UI", "Segoe UI Emoji", "Segoe UI Symbol"])
    字体.setPointSize(9)
    
    app.setFont(字体)
```

### 修改 2: 启动入口 (启动GUI.py)

在创建 QApplication 后调用字体设置：

```python
from PySide6.QtWidgets import QApplication
from 界面.样式.主题 import 应用全局字体

app = QApplication(sys.argv)
应用全局字体(app)  # 在创建任何窗口之前
```

### 修改 3: 主程序 (界面/主程序.py)

同样在 QApplication 创建后应用字体。

## 正确性属性

### Property 1: Emoji 显示正确性

*对于任意* 包含 emoji 字符的文本，在应用全局字体后，emoji 应正常显示而非方框

**验证: 需求 1.4**

### Property 2: 中文显示正确性

*对于任意* 包含中文字符的文本，在应用全局字体后，中文应正常显示

**验证: 需求 2.4**

## 错误处理

| 错误场景 | 处理方式 |
|---------|---------|
| 字体不存在 | 使用系统默认字体回退 |
| QApplication 未创建 | 跳过字体设置，记录警告 |

## 测试策略

### 手动测试

1. 启动 GUI，检查所有 emoji 是否正常显示
2. 检查窗口标题栏 emoji
3. 检查按钮文字 emoji
4. 检查对话框 emoji
