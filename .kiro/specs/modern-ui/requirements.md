# 需求文档

## 简介

为MMORPG游戏AI助手项目设计一个现代化的图形用户界面(GUI)，替代当前的命令行界面。界面采用明亮、清新的设计风格（非暗黑主题），提供直观的操作体验，让用户能够轻松进行数据收集、模型训练、机器人运行等操作。

## 术语表

- **主界面 (Main_Window)**: 应用程序的主窗口，包含导航和功能区域
- **控制面板 (Control_Panel)**: 显示当前操作状态和控制按钮的区域
- **状态监控器 (Status_Monitor)**: 实时显示AI运行状态、帧率、检测结果的组件
- **配置编辑器 (Config_Editor)**: 用于修改各项配置参数的界面
- **日志查看器 (Log_Viewer)**: 显示运行日志和调试信息的组件
- **数据管理器 (Data_Manager)**: 管理训练数据文件的界面

## 需求

### 需求 1: 主界面框架

**用户故事:** 作为用户，我希望有一个美观的主界面，以便快速访问所有功能模块。

#### 验收标准

1. THE Main_Window SHALL 采用明亮的浅色主题配色方案（白色/浅灰背景，蓝色/绿色强调色）
2. THE Main_Window SHALL 包含左侧导航栏，显示所有功能模块图标和名称
3. THE Main_Window SHALL 包含顶部标题栏，显示应用名称和当前状态
4. THE Main_Window SHALL 包含主内容区域，根据选择的功能模块动态切换内容
5. THE Main_Window SHALL 使用固定窗口尺寸800x600像素，不支持调整大小
6. WHEN 用户点击导航栏中的功能模块 THEN Main_Window SHALL 平滑切换到对应的功能页面

### 需求 2: 数据收集界面

**用户故事:** 作为用户，我希望通过图形界面控制数据收集过程，以便更方便地录制游戏操作。

#### 验收标准

1. THE Control_Panel SHALL 显示开始/暂停/停止按钮，使用清晰的图标和文字标签
2. THE Status_Monitor SHALL 实时显示当前录制状态（录制中/已暂停/已停止）
3. THE Status_Monitor SHALL 显示已收集的样本数量和当前文件编号
4. THE Status_Monitor SHALL 显示实时游戏画面预览（缩略图形式）
5. WHEN 用户点击开始按钮 THEN Control_Panel SHALL 启动数据收集并显示倒计时
6. WHEN 用户按下快捷键T THEN Control_Panel SHALL 切换暂停/继续状态
7. WHEN 样本数量达到设定值 THEN Status_Monitor SHALL 显示文件保存通知

### 需求 3: 模型训练界面

**用户故事:** 作为用户，我希望能够可视化地监控模型训练进度，以便了解训练状态。

#### 验收标准

1. THE Control_Panel SHALL 显示训练模式选择（主线任务/自动战斗）
2. THE Control_Panel SHALL 显示开始训练和停止训练按钮
3. THE Status_Monitor SHALL 显示训练进度条和当前轮次/总轮次
4. THE Status_Monitor SHALL 显示实时损失值曲线图
5. THE Status_Monitor SHALL 显示预计剩余训练时间
6. THE Log_Viewer SHALL 显示训练日志信息
7. WHEN 训练完成 THEN Status_Monitor SHALL 显示训练完成通知和模型保存位置

### 需求 4: 机器人运行界面

**用户故事:** 作为用户，我希望能够直观地控制和监控AI机器人的运行状态。

#### 验收标准

1. THE Control_Panel SHALL 显示运行模式选择（基础模式/增强模式）
2. THE Control_Panel SHALL 显示子模式选择（主线任务/自动战斗）
3. THE Control_Panel SHALL 显示启动/暂停/停止按钮
4. THE Status_Monitor SHALL 实时显示当前执行的动作名称和来源
5. THE Status_Monitor SHALL 显示当前游戏状态（战斗/对话/移动等）
6. THE Status_Monitor SHALL 显示帧率和运动量指标
7. THE Status_Monitor SHALL 显示增强模块状态（YOLO/状态识别/决策引擎）
8. WHEN 检测到角色卡住 THEN Status_Monitor SHALL 显示脱困提示
9. IF 性能不足 THEN Status_Monitor SHALL 显示性能警告并标识当前性能模式

### 需求 5: 配置管理界面

**用户故事:** 作为用户，我希望能够通过图形界面修改配置参数，而不需要直接编辑代码文件。

#### 验收标准

1. THE Config_Editor SHALL 分类显示所有配置项（游戏窗口/模型/训练/增强模块）
2. THE Config_Editor SHALL 为每个配置项提供合适的输入控件（滑块/输入框/下拉框/开关）
3. THE Config_Editor SHALL 显示每个配置项的说明文字
4. THE Config_Editor SHALL 提供保存和重置按钮
5. WHEN 用户修改配置值 THEN Config_Editor SHALL 实时验证输入有效性
6. WHEN 用户点击保存 THEN Config_Editor SHALL 将配置写入对应的配置文件
7. IF 配置值无效 THEN Config_Editor SHALL 显示错误提示并阻止保存

### 需求 6: 数据管理界面

**用户故事:** 作为用户，我希望能够方便地管理训练数据文件，包括查看、删除和统计。

#### 验收标准

1. THE Data_Manager SHALL 以列表形式显示所有训练数据文件
2. THE Data_Manager SHALL 显示每个文件的大小、创建时间和样本数量
3. THE Data_Manager SHALL 显示数据分布统计图表（各动作类别的样本数量）
4. THE Data_Manager SHALL 提供数据预处理和数据清洗的快捷操作按钮
5. WHEN 用户选择文件并点击删除 THEN Data_Manager SHALL 显示确认对话框
6. WHEN 用户点击预处理按钮 THEN Data_Manager SHALL 启动数据预处理流程并显示进度

### 需求 7: 日志和通知系统

**用户故事:** 作为用户，我希望能够查看运行日志和接收重要通知，以便了解系统状态。

#### 验收标准

1. THE Log_Viewer SHALL 显示带时间戳的日志消息
2. THE Log_Viewer SHALL 支持按日志级别（信息/警告/错误）过滤
3. THE Log_Viewer SHALL 支持搜索日志内容
4. THE Log_Viewer SHALL 支持导出日志到文件
5. WHEN 发生重要事件 THEN Main_Window SHALL 在右下角显示弹出通知
6. WHEN 发生错误 THEN Main_Window SHALL 显示错误通知并提供查看详情选项

### 需求 8: 快捷键支持

**用户故事:** 作为用户，我希望能够使用快捷键快速操作，以提高使用效率。

#### 验收标准

1. THE Main_Window SHALL 支持全局快捷键T切换暂停/继续
2. THE Main_Window SHALL 支持全局快捷键ESC停止当前操作
3. THE Main_Window SHALL 支持Ctrl+S保存当前配置
4. THE Main_Window SHALL 在设置中显示所有可用快捷键列表
5. WHEN 用户按下快捷键 THEN Main_Window SHALL 执行对应操作并显示视觉反馈

### 需求 9: 界面响应性

**用户故事:** 作为用户，我希望界面在执行耗时操作时保持响应，不会卡顿。

#### 验收标准

1. WHEN 执行数据收集操作 THEN Main_Window SHALL 在后台线程运行，界面保持响应
2. WHEN 执行模型训练操作 THEN Main_Window SHALL 在后台线程运行，界面保持响应
3. WHEN 执行机器人运行操作 THEN Main_Window SHALL 在后台线程运行，界面保持响应
4. THE Status_Monitor SHALL 以不超过100ms的延迟更新状态显示
5. IF 后台操作发生错误 THEN Main_Window SHALL 安全地显示错误信息而不崩溃

### 需求 10: 视觉设计规范

**用户故事:** 作为用户，我希望界面美观、现代，给人专业可靠的感觉。

#### 验收标准

1. THE Main_Window SHALL 使用圆角卡片式布局组织内容区域
2. THE Main_Window SHALL 使用一致的间距和对齐方式
3. THE Main_Window SHALL 使用清晰易读的字体（推荐微软雅黑或思源黑体）
4. THE Main_Window SHALL 为按钮和交互元素提供悬停和点击状态反馈
5. THE Main_Window SHALL 使用图标配合文字标签提高可识别性
6. THE Status_Monitor SHALL 使用颜色编码区分不同状态（绿色=正常，黄色=警告，红色=错误）
