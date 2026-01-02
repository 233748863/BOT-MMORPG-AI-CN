"""
全局配置设置
"""

# ==================== 游戏窗口设置 ====================
# 游戏窗口区域 (左, 上, 右, 下)
游戏窗口区域 = (0, 40, 1920, 1120)

# 游戏分辨率
游戏宽度 = 1920
游戏高度 = 1080

# ==================== 模型设置 ====================
# 输入图像尺寸 (缩放后)
模型输入宽度 = 480
模型输入高度 = 270

# 学习率
学习率 = 0.001

# 训练轮数
训练轮数 = 10

# 模型保存路径
模型保存路径 = "模型/游戏AI"

# 预训练模型路径 (原项目的模型)
预训练模型路径 = "模型/预训练模型/test"

# ==================== 数据收集设置 ====================
# 每个文件保存的样本数
每文件样本数 = 500

# 数据保存路径
数据保存路径 = "数据/"

# ==================== 运动检测设置 ====================
# 运动检测阈值 (低于此值认为卡住)
运动检测阈值 = 800

# 运动检测日志长度
运动日志长度 = 25

# ==================== 动作定义 ====================
# 完整动作列表 (32个动作)
动作定义 = {
    # 移动动作 (0-8)
    0: {"名称": "前进", "按键": "W", "类型": "移动"},
    1: {"名称": "后退", "按键": "S", "类型": "移动"},
    2: {"名称": "左移", "按键": "A", "类型": "移动"},
    3: {"名称": "右移", "按键": "D", "类型": "移动"},
    4: {"名称": "前进+左移", "按键": "W+A", "类型": "移动"},
    5: {"名称": "前进+右移", "按键": "W+D", "类型": "移动"},
    6: {"名称": "后退+左移", "按键": "S+A", "类型": "移动"},
    7: {"名称": "后退+右移", "按键": "S+D", "类型": "移动"},
    8: {"名称": "无操作", "按键": "无", "类型": "移动"},
    
    # 技能动作 (9-18)
    9: {"名称": "技能1", "按键": "1", "类型": "技能"},
    10: {"名称": "技能2", "按键": "2", "类型": "技能"},
    11: {"名称": "技能3", "按键": "3", "类型": "技能"},
    12: {"名称": "技能4", "按键": "4", "类型": "技能"},
    13: {"名称": "技能5", "按键": "5", "类型": "技能"},
    14: {"名称": "技能6", "按键": "6", "类型": "技能"},
    15: {"名称": "技能Q", "按键": "Q", "类型": "技能"},
    16: {"名称": "技能E", "按键": "E", "类型": "技能"},
    17: {"名称": "技能R", "按键": "R", "类型": "技能"},
    18: {"名称": "技能F", "按键": "F", "类型": "技能"},
    
    # 特殊动作 (19-23)
    19: {"名称": "跳跃/闪避", "按键": "空格", "类型": "特殊"},
    20: {"名称": "切换目标", "按键": "Tab", "类型": "特殊"},
    21: {"名称": "交互", "按键": "F", "类型": "特殊"},
    
    # 鼠标动作 (22-24)
    22: {"名称": "鼠标左键", "按键": "鼠标左", "类型": "鼠标"},
    23: {"名称": "鼠标右键", "按键": "鼠标右", "类型": "鼠标"},
    24: {"名称": "鼠标中键", "按键": "鼠标中", "类型": "鼠标"},
    
    # Shift组合技能 (25-28)
    25: {"名称": "Shift+1", "按键": "Shift+1", "类型": "组合"},
    26: {"名称": "Shift+2", "按键": "Shift+2", "类型": "组合"},
    27: {"名称": "Shift+Q", "按键": "Shift+Q", "类型": "组合"},
    28: {"名称": "Shift+E", "按键": "Shift+E", "类型": "组合"},
    
    # Ctrl组合技能 (29-31)
    29: {"名称": "Ctrl+1", "按键": "Ctrl+1", "类型": "组合"},
    30: {"名称": "Ctrl+2", "按键": "Ctrl+2", "类型": "组合"},
    31: {"名称": "Ctrl+Q", "按键": "Ctrl+Q", "类型": "组合"},
}

# 总动作数
总动作数 = len(动作定义)

# ==================== 训练模式设置 ====================
class 训练模式:
    """训练模式配置"""
    
    # 主线任务模式 - 侧重移动和交互
    主线任务 = {
        "名称": "主线任务练级",
        "描述": "学习做主线任务的操作习惯",
        "启用动作": list(range(9)) + [21, 22, 23],  # 移动 + 交互 + 鼠标
        "动作权重": [
            # 移动 (高权重)
            4.0, 0.5, 0.5, 0.5, 2.0, 2.0, 0.5, 0.5, 0.2,
            # 技能 (低权重)
            0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1,
            # 特殊
            0.5, 0.3, 1.0,
            # 鼠标 (中等权重)
            1.5, 1.5, 0.1,
            # 组合键 (低权重)
            0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1,
        ],
    }
    
    # 自动战斗模式 - 侧重技能和走位
    自动战斗 = {
        "名称": "自动战斗",
        "描述": "学习战斗技能释放和走位",
        "启用动作": list(range(32)),  # 全部动作
        "动作权重": [
            # 移动 (中等权重)
            2.0, 0.5, 1.0, 1.0, 1.5, 1.5, 0.5, 0.5, 0.1,
            # 技能 (高权重)
            2.0, 2.0, 2.0, 2.0, 1.5, 1.5, 2.0, 2.0, 1.5, 1.5,
            # 特殊 (高权重)
            2.0, 1.5, 1.0,
            # 鼠标 (高权重)
            2.5, 2.0, 0.5,
            # 组合键 (中等权重)
            1.5, 1.5, 1.5, 1.5, 1.0, 1.0, 1.0,
        ],
    }

# ==================== 运动检测设置 ====================
# 运动检测阈值 (低于此值认为卡住)
运动检测阈值 = 800

# 运动检测日志长度
运动日志长度 = 25

# ==================== 按键扫描码 ====================
# DirectInput 扫描码 (供参考)
按键码 = {
    "W": 0x11, "A": 0x1E, "S": 0x1F, "D": 0x20,
    "Q": 0x10, "E": 0x12, "R": 0x13, "F": 0x21,
    "1": 0x02, "2": 0x03, "3": 0x04, "4": 0x05,
    "5": 0x06, "6": 0x07, "7": 0x08, "8": 0x09,
    "9": 0x0A, "0": 0x0B,
    "空格": 0x39, "Tab": 0x0F,
    "Shift": 0x2A, "Ctrl": 0x1D, "Alt": 0x38,
}


# ==================== 配置迁移功能 ====================
def 迁移旧配置到档案(档案名称: str = "default", 游戏名称: str = "默认游戏"):
    """将当前配置迁移到配置档案
    
    将现有的全局配置设置迁移到配置管理系统的档案中。
    这允许用户将旧配置转换为新的档案格式。
    
    需求: 10.2 - 实现配置迁移逻辑
    
    Args:
        档案名称: 新档案的名称
        游戏名称: 游戏名称
        
    Returns:
        bool: 迁移是否成功
    """
    if not 配置管理可用:
        logger.warning("配置管理模块不可用，无法迁移配置")
        return False
    
    try:
        from 核心.配置管理 import (
            GameProfile, WindowConfig, KeyMapping, 
            UIRegions, DetectionParams, DecisionRules
        )
        
        manager = 获取配置管理器()
        if manager is None:
            return False
        
        # 检查档案是否已存在
        if manager.profile_exists(档案名称):
            logger.warning(f"档案 '{档案名称}' 已存在，跳过迁移")
            return False
        
        # 从当前全局配置创建档案
        # 解析窗口区域
        x, y, x2, y2 = 游戏窗口区域
        width = x2 - x
        height = y2 - y
        
        window_config = WindowConfig(x=x, y=y, width=width, height=height)
        
        # 从动作定义创建按键映射
        move_keys = {}
        skill_keys = {}
        for action_id, action_info in 动作定义.items():
            按键 = action_info.get("按键", "")
            类型 = action_info.get("类型", "")
            if 类型 == "移动" and 按键 in ["W", "A", "S", "D"]:
                direction_map = {"W": "up", "S": "down", "A": "left", "D": "right"}
                if 按键 in direction_map:
                    move_keys[按键] = direction_map[按键]
            elif 类型 == "技能" and 按键.isdigit():
                skill_keys[按键] = f"skill{按键}"
        
        key_mapping = KeyMapping(
            move_keys=move_keys if move_keys else {"W": "up", "S": "down", "A": "left", "D": "right"},
            skill_keys=skill_keys if skill_keys else {"1": "skill1", "2": "skill2"},
            interact_key="F"
        )
        
        # 创建默认UI区域配置
        ui_regions = UIRegions()
        
        # 创建检测参数配置
        detection_params = DetectionParams(
            yolo_model_path=预训练模型路径,
            confidence_threshold=0.5
        )
        
        # 创建决策规则配置
        decision_rules = DecisionRules()
        
        # 创建配置档案
        profile = GameProfile(
            name=档案名称,
            game_name=游戏名称,
            window_config=window_config,
            key_mapping=key_mapping,
            ui_regions=ui_regions,
            detection_params=detection_params,
            decision_rules=decision_rules
        )
        
        # 保存档案
        manager.save_profile(profile)
        logger.info(f"配置已迁移到档案: {档案名称}")
        return True
        
    except Exception as e:
        logger.error(f"配置迁移失败: {e}")
        return False


def 切换配置档案(档案名称: str) -> bool:
    """切换到指定的配置档案
    
    切换配置档案后，全局配置变量会更新为新档案的值。
    
    Args:
        档案名称: 要切换到的档案名称
        
    Returns:
        bool: 切换是否成功
    """
    global 游戏窗口区域, 游戏宽度, 游戏高度
    
    if not 配置管理可用:
        logger.warning("配置管理模块不可用")
        return False
    
    try:
        manager = 获取配置管理器()
        if manager is None:
            return False
        
        # 切换档案
        manager.switch_profile(档案名称)
        
        # 重新加载配置
        profile = manager.get_current_profile()
        if profile:
            window = profile.window_config
            游戏窗口区域 = (window.x, window.y, 
                          window.x + window.width, 
                          window.y + window.height)
            游戏宽度 = window.width
            游戏高度 = window.height
            
            logger.info(f"已切换到配置档案: {档案名称}")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"切换配置档案失败: {e}")
        return False


def 获取所有配置档案() -> list:
    """获取所有可用的配置档案名称
    
    Returns:
        list: 档案名称列表
    """
    if not 配置管理可用:
        return []
    
    try:
        manager = 获取配置管理器()
        if manager:
            return manager.list_profiles()
    except Exception as e:
        logger.error(f"获取配置档案列表失败: {e}")
    
    return []


def 获取当前配置档案名称() -> str:
    """获取当前使用的配置档案名称
    
    Returns:
        str: 当前档案名称，如果没有则返回空字符串
    """
    if not 配置管理可用:
        return ""
    
    try:
        manager = 获取配置管理器()
        if manager:
            profile = manager.get_current_profile()
            if profile:
                return profile.name
    except Exception as e:
        logger.error(f"获取当前配置档案失败: {e}")
    
    return ""
