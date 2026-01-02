# 需求文档

## 简介

本文档定义了MMORPG游戏AI助手的三个增强功能：智能录制优化、多游戏配置管理、以及自动调参系统。这些功能将提升数据收集质量、支持多游戏适配、并实现AI参数的自动优化。

## 术语表

- **Smart_Recorder**: 智能录制模块，负责识别和筛选高价值训练数据
- **Recording_Segment**: 录制片段，一段连续的游戏操作记录
- **Value_Score**: 价值评分，衡量训练片段对模型学习的价值
- **Config_Manager**: 配置管理器，管理多游戏配置方案
- **Game_Profile**: 游戏配置档案，包含特定游戏的所有配置参数
- **Auto_Tuner**: 自动调参器，根据运行效果优化决策引擎参数
- **Performance_Metric**: 性能指标，衡量AI运行效果的量化数据
- **Parameter_Space**: 参数空间，可调整参数的取值范围定义

## 需求

### 需求 1: 智能录制 - 高价值片段识别

**用户故事:** 作为用户，我希望AI能自动识别有价值的训练片段，以便收集更高质量的训练数据。

#### 验收标准

1. THE Smart_Recorder SHALL 实时分析录制中的游戏画面和操作序列
2. WHEN 检测到成功击杀怪物 THEN THE Smart_Recorder SHALL 标记该片段为高价值并提高Value_Score
3. WHEN 检测到完成任务对话 THEN THE Smart_Recorder SHALL 标记该片段为高价值
4. WHEN 检测到成功拾取物品 THEN THE Smart_Recorder SHALL 标记该片段为中等价值
5. WHEN 检测到技能连招组合 THEN THE Smart_Recorder SHALL 标记该片段为高价值
6. THE Smart_Recorder SHALL 为每个Recording_Segment计算Value_Score（0-100分）

### 需求 2: 智能录制 - 无效数据过滤

**用户故事:** 作为用户，我希望AI能自动过滤无效的训练数据，以避免低质量数据影响模型训练。

#### 验收标准

1. WHEN 检测到连续5秒无操作 THEN THE Smart_Recorder SHALL 标记该片段为低价值
2. WHEN 检测到重复相同操作超过10次 THEN THE Smart_Recorder SHALL 标记为重复数据
3. WHEN 检测到角色卡住不动超过3秒 THEN THE Smart_Recorder SHALL 标记为异常数据
4. WHEN 检测到游戏加载画面 THEN THE Smart_Recorder SHALL 暂停录制直到加载完成
5. WHEN 检测到游戏菜单界面 THEN THE Smart_Recorder SHALL 根据配置决定是否录制
6. THE Smart_Recorder SHALL 在保存时提供选项：保留全部/仅保留高价值/自动过滤低价值

### 需求 3: 智能录制 - 数据统计与反馈

**用户故事:** 作为用户，我希望能看到录制数据的质量统计，以便了解数据收集效果。

#### 验收标准

1. THE Smart_Recorder SHALL 实时显示当前片段的Value_Score
2. THE Smart_Recorder SHALL 显示本次录制的高/中/低价值片段数量统计
3. THE Smart_Recorder SHALL 显示各动作类别的样本分布情况
4. WHEN 录制结束 THEN THE Smart_Recorder SHALL 生成数据质量报告
5. THE Smart_Recorder SHALL 提供建议：哪些动作类别需要更多样本

### 需求 4: 多游戏配置 - 配置档案管理

**用户故事:** 作为用户，我希望能为不同游戏保存独立的配置方案，以便快速切换使用。

#### 验收标准

1. THE Config_Manager SHALL 支持创建新的Game_Profile
2. THE Config_Manager SHALL 支持保存当前配置为新档案或覆盖现有档案
3. THE Config_Manager SHALL 支持删除不需要的Game_Profile
4. THE Config_Manager SHALL 支持导出Game_Profile为JSON文件
5. THE Config_Manager SHALL 支持从JSON文件导入Game_Profile
6. WHEN 用户选择一个Game_Profile THEN THE Config_Manager SHALL 加载该档案的所有配置

### 需求 5: 多游戏配置 - 配置项分类

**用户故事:** 作为用户，我希望配置项按游戏相关性分类，以便清楚哪些需要针对不同游戏调整。

#### 验收标准

1. THE Game_Profile SHALL 包含游戏窗口配置（窗口区域、分辨率）
2. THE Game_Profile SHALL 包含按键映射配置（技能键、移动键、交互键）
3. THE Game_Profile SHALL 包含UI区域配置（血条位置、技能栏位置、对话框区域）
4. THE Game_Profile SHALL 包含检测参数配置（YOLO模型路径、置信度阈值）
5. THE Game_Profile SHALL 包含决策规则配置（状态优先级、动作权重）
6. THE Config_Manager SHALL 显示每个配置项的游戏相关性说明

### 需求 6: 多游戏配置 - 快速切换

**用户故事:** 作为用户，我希望能快速切换不同游戏的配置，无需重启程序。

#### 验收标准

1. THE Config_Manager SHALL 在界面提供游戏配置下拉选择框
2. WHEN 用户切换Game_Profile THEN THE Config_Manager SHALL 热加载新配置
3. WHEN 切换配置时有未保存更改 THEN THE Config_Manager SHALL 提示用户保存或放弃
4. THE Config_Manager SHALL 记住上次使用的Game_Profile，下次启动自动加载
5. WHEN 配置切换完成 THEN THE Config_Manager SHALL 显示切换成功通知

### 需求 7: 自动调参 - 性能指标收集

**用户故事:** 作为用户，我希望系统能自动收集AI运行效果数据，为参数优化提供依据。

#### 验收标准

1. THE Auto_Tuner SHALL 收集以下Performance_Metric：动作执行成功率、状态识别准确率、卡住次数、任务完成效率
2. THE Auto_Tuner SHALL 按时间窗口（如每5分钟）汇总性能指标
3. THE Auto_Tuner SHALL 记录每次参数调整前后的性能变化
4. THE Auto_Tuner SHALL 将性能数据持久化存储，支持历史查询
5. WHEN 性能指标异常下降 THEN THE Auto_Tuner SHALL 发出警告通知

### 需求 8: 自动调参 - 参数优化策略

**用户故事:** 作为用户，我希望系统能根据运行效果自动调整参数，提升AI表现。

#### 验收标准

1. THE Auto_Tuner SHALL 定义可调参数的Parameter_Space（最小值、最大值、步长）
2. THE Auto_Tuner SHALL 支持以下可调参数：动作冷却时间、状态切换阈值、规则优先级权重、检测置信度阈值
3. WHEN 启用自动调参 THEN THE Auto_Tuner SHALL 在安全范围内小幅调整参数
4. WHEN 参数调整后性能提升 THEN THE Auto_Tuner SHALL 保留新参数值
5. WHEN 参数调整后性能下降 THEN THE Auto_Tuner SHALL 回滚到之前的参数值
6. THE Auto_Tuner SHALL 使用渐进式调整策略，避免参数剧烈变化

### 需求 9: 自动调参 - 用户控制

**用户故事:** 作为用户，我希望能控制自动调参的行为，避免意外的参数变化。

#### 验收标准

1. THE Auto_Tuner SHALL 提供启用/禁用自动调参的开关
2. THE Auto_Tuner SHALL 支持设置参数调整的激进程度（保守/平衡/激进）
3. THE Auto_Tuner SHALL 支持锁定特定参数不被自动调整
4. WHEN 自动调整参数 THEN THE Auto_Tuner SHALL 在日志中记录调整原因和幅度
5. THE Auto_Tuner SHALL 提供一键恢复默认参数的功能
6. THE Auto_Tuner SHALL 显示当前参数与默认值的差异对比

### 需求 10: 模块集成

**用户故事:** 作为用户，我希望这三个新功能能与现有系统无缝集成。

#### 验收标准

1. THE Smart_Recorder SHALL 集成到现有的数据收集流程中
2. THE Config_Manager SHALL 与现有配置系统兼容，支持读取旧配置文件
3. THE Auto_Tuner SHALL 与决策引擎集成，实时应用参数调整
4. WHEN 任一新模块出错 THEN 系统 SHALL 降级到基础功能继续运行
5. THE 三个模块 SHALL 在GUI界面中有独立的控制入口
6. THE 三个模块 SHALL 共享统一的日志系统

