# 需求文档

## 简介

在配置界面中添加窗口选择功能，让用户可以从运行中的进程列表中选择目标窗口，或通过点击选择模式来选取窗口，自动填充窗口坐标和尺寸参数。

## 术语表

- **Window_Selector**: 窗口选择器，用于显示和选择运行中的窗口
- **Window_Finder**: 窗口查找器，核心模块中已有的窗口检测类
- **Config_Interface**: 配置界面，用户编辑配置参数的界面
- **Window_Preview**: 窗口预览控件，显示窗口区域的可视化预览
- **Click_Select_Mode**: 点击选择模式，用户点击目标窗口来选择

## 需求

### 需求 1: 窗口选择按钮

**用户故事:** 作为用户，我想要在配置界面中有一个选择窗口的按钮，以便快速选择目标游戏窗口。

#### 验收标准

1. WHEN 用户打开配置界面的窗口设置标签页 THEN THE Config_Interface SHALL 显示一个"🎯 选择窗口"按钮
2. WHEN 用户点击"选择窗口"按钮 THEN THE Config_Interface SHALL 打开窗口选择对话框
3. THE 选择窗口按钮 SHALL 位于窗口区域设置组内，与坐标输入框同行或相邻

### 需求 2: 窗口列表对话框

**用户故事:** 作为用户，我想要看到所有运行中的窗口列表，以便选择目标窗口。

#### 验收标准

1. WHEN 窗口选择对话框打开 THEN THE Window_Selector SHALL 显示所有可见窗口的列表
2. WHEN 显示窗口列表 THEN THE Window_Selector SHALL 显示每个窗口的标题、进程名和尺寸信息
3. WHEN 显示窗口列表 THEN THE Window_Selector SHALL 显示每个窗口的缩略图预览（如果可用）
4. WHEN 用户双击列表中的窗口项 THEN THE Window_Selector SHALL 选中该窗口并关闭对话框
5. WHEN 用户选中窗口并点击"确定"按钮 THEN THE Window_Selector SHALL 返回选中的窗口信息

### 需求 3: 窗口搜索过滤

**用户故事:** 作为用户，我想要通过关键词搜索窗口，以便快速找到目标窗口。

#### 验收标准

1. WHEN 窗口选择对话框打开 THEN THE Window_Selector SHALL 显示一个搜索输入框
2. WHEN 用户在搜索框中输入关键词 THEN THE Window_Selector SHALL 实时过滤窗口列表
3. WHEN 过滤窗口列表 THEN THE Window_Selector SHALL 匹配窗口标题和进程名
4. WHEN 搜索框为空 THEN THE Window_Selector SHALL 显示所有窗口

### 需求 4: 点击选择模式

**用户故事:** 作为用户，我想要通过点击目标窗口来选择，以便更直观地选取窗口。

#### 验收标准

1. WHEN 窗口选择对话框打开 THEN THE Window_Selector SHALL 显示一个"🖱️ 点击选择"按钮
2. WHEN 用户点击"点击选择"按钮 THEN THE Window_Selector SHALL 显示倒计时提示（3秒）
3. WHEN 倒计时结束 THEN THE Window_Selector SHALL 最小化自身并等待用户点击
4. WHEN 用户点击任意窗口 THEN THE Window_Selector SHALL 捕获该窗口信息并恢复显示
5. WHEN 捕获到窗口信息 THEN THE Window_Selector SHALL 在列表中高亮显示该窗口

### 需求 5: 自动填充配置

**用户故事:** 作为用户，我想要选择窗口后自动填充坐标参数，以便省去手动输入的麻烦。

#### 验收标准

1. WHEN 用户在窗口选择对话框中确认选择 THEN THE Config_Interface SHALL 自动填充窗口X坐标
2. WHEN 用户确认选择 THEN THE Config_Interface SHALL 自动填充窗口Y坐标
3. WHEN 用户确认选择 THEN THE Config_Interface SHALL 自动填充窗口宽度
4. WHEN 用户确认选择 THEN THE Config_Interface SHALL 自动填充窗口高度
5. WHEN 自动填充完成 THEN THE Window_Preview SHALL 立即更新预览显示
6. WHEN 自动填充完成 THEN THE Config_Interface SHALL 标记配置为已修改状态

### 需求 6: 刷新窗口列表

**用户故事:** 作为用户，我想要刷新窗口列表，以便看到新打开的窗口。

#### 验收标准

1. WHEN 窗口选择对话框打开 THEN THE Window_Selector SHALL 显示一个"🔄 刷新"按钮
2. WHEN 用户点击"刷新"按钮 THEN THE Window_Selector SHALL 重新获取所有窗口列表
3. WHEN 刷新完成 THEN THE Window_Selector SHALL 保持当前的搜索过滤条件
