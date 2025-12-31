# Requirements Document

## Introduction

本文档定义了MMORPG游戏AI助手的三个核心增强功能：YOLO目标检测集成、游戏状态识别系统、以及智能决策引擎。这些功能将使AI助手从简单的模仿学习升级为具备场景理解和智能决策能力的系统。

## Glossary

- **Game_AI_System**: 游戏AI助手的核心系统，负责协调各模块工作
- **YOLO_Detector**: 基于YOLO的目标检测模块，用于识别游戏中的实体
- **State_Recognizer**: 游戏状态识别模块，判断当前游戏场景类型
- **Decision_Engine**: 智能决策引擎，结合规则和学习模型做出决策
- **Game_Entity**: 游戏中的可识别实体（怪物、NPC、玩家、物品等）
- **Game_State**: 游戏当前状态（战斗、对话、菜单、移动等）
- **Action_Priority**: 动作优先级，决定在特定状态下哪些动作更重要

## Requirements

### Requirement 1: YOLO目标检测集成

**User Story:** As a 游戏AI用户, I want AI能够识别游戏画面中的目标（怪物、NPC、物品等）, so that AI可以做出更精准的决策。

#### Acceptance Criteria

1. WHEN 游戏画面输入到检测器 THEN THE YOLO_Detector SHALL 返回检测到的实体列表，包含类型、位置和置信度
2. WHEN 检测到多个实体 THEN THE YOLO_Detector SHALL 按置信度降序排列结果
3. WHEN 检测置信度低于阈值 THEN THE YOLO_Detector SHALL 过滤掉该检测结果
4. THE YOLO_Detector SHALL 支持以下实体类型：怪物、NPC、玩家角色、可拾取物品、技能特效
5. WHEN 未加载模型文件 THEN THE YOLO_Detector SHALL 返回空列表并记录警告日志
6. THE YOLO_Detector SHALL 提供实体位置相对于屏幕中心的方向信息

### Requirement 2: 游戏状态识别

**User Story:** As a 游戏AI用户, I want AI能够识别当前游戏状态（战斗中、对话中、菜单界面等）, so that AI可以根据不同状态采取合适的行动。

#### Acceptance Criteria

1. THE State_Recognizer SHALL 识别以下游戏状态：战斗状态、对话状态、菜单状态、移动状态、拾取状态、采集状态、死亡状态、加载状态
2. WHEN 屏幕画面输入 THEN THE State_Recognizer SHALL 返回当前状态和置信度
3. WHEN 检测到UI元素（对话框、菜单） THEN THE State_Recognizer SHALL 优先判定为对应的UI状态
4. WHEN 检测到敌对实体且距离较近 THEN THE State_Recognizer SHALL 判定为战斗状态
5. WHEN 状态发生变化 THEN THE State_Recognizer SHALL 触发状态变更事件
6. THE State_Recognizer SHALL 维护状态历史记录，支持查询最近N次状态
7. WHEN 连续多帧状态相同 THEN THE State_Recognizer SHALL 提高该状态的置信度

### Requirement 3: 智能决策引擎

**User Story:** As a 游戏AI用户, I want AI能够结合规则和学习模型做出智能决策, so that AI的行为更加合理和高效。

#### Acceptance Criteria

1. THE Decision_Engine SHALL 根据当前游戏状态选择对应的决策策略
2. WHEN 处于战斗状态 THEN THE Decision_Engine SHALL 优先考虑技能释放和走位动作
3. WHEN 处于对话状态 THEN THE Decision_Engine SHALL 优先考虑交互和确认动作
4. WHEN 处于移动状态 THEN THE Decision_Engine SHALL 优先考虑移动和寻路动作
5. WHEN 处于采集状态 THEN THE Decision_Engine SHALL 等待采集完成，仅在被攻击时中断
6. THE Decision_Engine SHALL 支持规则优先级配置，高优先级规则可覆盖模型预测
6. WHEN 检测到紧急情况（血量低、被围攻） THEN THE Decision_Engine SHALL 触发紧急响应规则
7. THE Decision_Engine SHALL 记录决策日志，包含状态、候选动作、最终选择及原因
8. WHEN 模型预测与规则冲突 THEN THE Decision_Engine SHALL 根据配置的冲突解决策略处理
9. THE Decision_Engine SHALL 支持动作冷却机制，避免重复执行相同动作

### Requirement 4: 模块集成

**User Story:** As a 游戏AI用户, I want 三个新模块能够与现有系统无缝集成, so that 整体系统稳定运行。

#### Acceptance Criteria

1. THE Game_AI_System SHALL 在主循环中依次调用目标检测、状态识别、决策引擎
2. WHEN 任一模块出错 THEN THE Game_AI_System SHALL 降级到基础模仿学习模式
3. THE Game_AI_System SHALL 提供模块启用/禁用配置
4. WHEN 性能不足 THEN THE Game_AI_System SHALL 自动降低检测频率
5. THE Game_AI_System SHALL 在配置文件中暴露所有可调参数
