"""
全局配置设置
"""

import logging
import os

# 配置日志
logger = logging.getLogger(__name__)

# ==================== 自动窗口检测设置 ====================
# 是否启用自动窗口检测
# 启用后，系统会自动检测游戏窗口位置，无需手动配置坐标
# 需求: 4.1 - 窗口标识配置
启用自动窗口检测 = True

# 窗口标识配置
# 用于自动查找游戏窗口
# 标识类型: "process" (进程名) 或 "title" (窗口标题)
# 需求: 4.1 - 窗口标识配置
窗口标识类型 = "process"  # "process" 或 "title"
窗口标识值 = ""  # 进程名如 "game.exe" 或窗口标题关键字

# 是否启用窗口跟踪
# 启用后，当窗口移动时会自动更新截取区域
# 需求: 3.2 - 窗口移动时自动更新截取区域
启用窗口跟踪 = True

# 窗口配置文件路径
窗口配置路径 = "配置/窗口配置.json"

# ==================== 游戏窗口设置 ====================
# 游戏窗口区域 (左, 上, 右, 下)
# 当启用自动窗口检测时，此配置会被自动检测的值覆盖
游戏窗口区域 = (0, 40, 1920, 1120)

# 游戏分辨率 (根据窗口区域自动计算)
游戏宽度 = 游戏窗口区域[2] - 游戏窗口区域[0]
游戏高度 = 游戏窗口区域[3] - 游戏窗口区域[1]

# ==================== 模型设置 ====================
# 模型输入缩放比例 (游戏画面缩小的倍数)
# 比例越大，模型输入越小，速度越快但精度可能降低
模型缩放比例 = 4

# 输入图像尺寸 (根据游戏分辨率和缩放比例自动计算)
模型输入宽度 = 游戏宽度 // 模型缩放比例
模型输入高度 = 游戏高度 // 模型缩放比例

# 学习率
学习率 = 0.001

# 训练轮数
训练轮数 = 10

# ==================== 推理后端设置 ====================
# 需求: 4.4 - 提供配置选项来选择首选的推理后端

# ==================== 屏幕截取设置 ====================
# 需求: 2.4 - 记录正在使用的截取后端

# 首选截取后端
# 可选值: "auto"(自动检测), "dxgi"(DXGI Desktop Duplication), "mss"(MSS), "gdi"(GDI), "pil"(PIL)
# auto: 根据系统能力自动选择最佳后端
# dxgi: 使用 DXGI Desktop Duplication API（Windows 8+，最快）
# mss: 使用 MSS 库（跨平台，较快）
# gdi: 使用 GDI（Windows 原生，兼容性好）
# pil: 使用 PIL/Pillow（通用回退方案）
首选截取后端 = "auto"

# 是否启用截取回退机制
# 启用后，当首选后端失败时会自动尝试其他后端
启用截取回退 = True

# 是否启用截取性能监控
# 启用后，会记录截取时间等性能指标
启用截取性能监控 = True

# 截取显示器索引
# 0 表示主显示器，1 表示第二显示器，以此类推
截取显示器索引 = 0

# 截取配置文件路径
截取配置路径 = "配置/截取配置.json"

# 首选推理后端
# 可选值: "auto"(自动检测), "onnx"(ONNX Runtime), "tflearn"(TFLearn)
# auto: 根据模型文件格式自动选择后端
# onnx: 优先使用 ONNX Runtime（推荐，速度更快）
# tflearn: 使用原始 TFLearn 后端
首选推理后端 = "auto"

# 是否使用 GPU 加速
# 需要安装 onnxruntime-gpu 才能使用 GPU
# 如果 GPU 不可用，会自动回退到 CPU
推理使用GPU = True

# 是否启用统一推理引擎
# 启用后，决策引擎会使用统一推理引擎进行模型推理
# 需求: 4.2, 4.3 - 支持 TFLearn 和 ONNX 后端
启用推理引擎 = True

# 最大推理延迟阈值（毫秒）
# 超过此值会记录警告
# 需求: 2.2 - 50ms 内返回动作预测
最大推理延迟 = 50

# 推理配置文件路径
推理配置路径 = "配置/推理配置.json"

# ==================== 类别权重平衡设置 ====================
# 需求 2.4: 将计算的权重保存到配置文件

# 是否启用类别权重平衡
启用类别权重平衡 = True

# 权重计算策略
# 可选值: "inverse_frequency", "sqrt_inverse_frequency", "effective_samples"
权重计算策略 = "inverse_frequency"

# 类别权重配置文件路径
类别权重配置路径 = "配置/类别权重.json"

# ==================== 数据增强设置 ====================
# 需求 3.4: 增强管道应可通过配置文件或字典进行配置

# 是否启用数据增强
启用数据增强 = True

# 数据增强配置文件路径
数据增强配置路径 = "配置/数据增强.json"

# 是否使用语义安全增强
# 启用后，会自动限制变换强度以保护动作语义
使用语义安全增强 = True

# 默认增强配置
# 当配置文件不存在时使用此默认配置
默认增强配置 = {
    "亮度调整": {
        "启用": True,
        "概率": 0.5,
        "范围": [-0.2, 0.2],
        "强度": 1.0
    },
    "对比度调整": {
        "启用": True,
        "概率": 0.5,
        "范围": [0.8, 1.2],
        "强度": 1.0
    },
    "水平翻转": {
        "启用": True,
        "概率": 0.5,
        "强度": 1.0
    },
    "高斯噪声": {
        "启用": True,
        "概率": 0.3,
        "标准差": 0.02,
        "强度": 1.0
    },
    "颜色抖动": {
        "启用": True,
        "概率": 0.3,
        "色调范围": 0.1,
        "饱和度范围": 0.2,
        "强度": 1.0
    },
    "旋转": {
        "启用": False,
        "概率": 0.3,
        "角度范围": [-10, 10],
        "强度": 1.0
    },
    "缩放裁剪": {
        "启用": False,
        "概率": 0.3,
        "缩放范围": [0.9, 1.1],
        "强度": 1.0
    },
    "高斯模糊": {
        "启用": False,
        "概率": 0.2,
        "核大小范围": [3, 7],
        "强度": 1.0
    },
    "光照模拟": {
        "启用": False,
        "概率": 0.3,
        "强度范围": [0.7, 1.3],
        "强度": 1.0
    },
    "透视变换": {
        "启用": False,
        "概率": 0.2,
        "最大偏移": 0.05,
        "强度": 1.0
    }
}

# ==================== 采样策略设置 ====================
# 是否启用数据采样
启用数据采样 = False

# 采样方法
# 可选值: "oversample" (过采样), "undersample" (欠采样), "mixed" (混合采样)
采样方法 = "oversample"

# 过采样目标比率 (1.0 表示完全平衡)
过采样目标比率 = 1.0

# 欠采样每类最大样本数 (None 表示使用最小类别数量)
欠采样最大样本数 = None

# 采样随机种子 (用于可重复性，None 表示随机)
采样随机种子 = 42

# 是否打乱采样后的数据
采样后打乱数据 = True

# ==================== 训练可视化设置 ====================
# 需求 2.4: 按可配置的间隔更新图表

# 是否启用训练可视化
启用训练可视化 = True

# 是否启用实时图表
# 启用后会显示实时更新的 loss 曲线
启用实时图表 = True

# 是否启用终端输出
# 启用后会在终端显示进度条和训练信息
启用终端输出 = True

# 是否启用健康监控
# 启用后会检测训练异常（平台期、发散、尖峰）
启用健康监控 = True

# 图表更新间隔（批次数）
# 每隔多少个批次更新一次图表
图表更新间隔 = 10

# 健康检查间隔（轮次数）
# 每隔多少个轮次进行一次健康检查
健康检查间隔 = 1

# 是否自动保存训练日志
自动保存训练日志 = True

# 训练日志保存目录
训练日志目录 = "日志/训练"

# 是否启用静默模式
# 启用后终端输出会最小化
训练静默模式 = False

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
    21: {"名称": "交互", "按键": "G", "类型": "特殊"},  # 修复: 从 "F" 改为 "G"，避免与技能F冲突
    
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


def 检测按键冲突() -> list:
    """
    检测动作定义中的按键冲突
    
    检查所有动作定义，找出映射到相同按键的不同动作索引。
    
    需求: 4.4 - 如果在配置加载时检测到按键冲突，配置模块应记录警告信息
    
    返回:
        list: 冲突列表，每个元素为 (按键, [(索引1, 名称1), (索引2, 名称2), ...])
    """
    按键映射 = {}
    
    for 索引, 动作信息 in 动作定义.items():
        按键 = 动作信息.get("按键", "")
        名称 = 动作信息.get("名称", "")
        
        # 跳过特殊按键（无操作、鼠标等）
        if 按键 in ["无", "鼠标左", "鼠标右", "鼠标中"]:
            continue
        
        if 按键 not in 按键映射:
            按键映射[按键] = []
        按键映射[按键].append((索引, 名称))
    
    # 找出有冲突的按键（映射到多个动作）
    冲突列表 = []
    for 按键, 动作列表 in 按键映射.items():
        if len(动作列表) > 1:
            冲突列表.append((按键, 动作列表))
            logger.warning(f"按键冲突检测: 按键 '{按键}' 被多个动作使用: {动作列表}")
    
    return 冲突列表


# 在模块加载时检测按键冲突
_按键冲突 = 检测按键冲突()
if _按键冲突:
    logger.warning(f"检测到 {len(_按键冲突)} 个按键冲突，请检查动作定义")

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
    "Q": 0x10, "E": 0x12, "R": 0x13, "F": 0x21, "G": 0x22,
    "1": 0x02, "2": 0x03, "3": 0x04, "4": 0x05,
    "5": 0x06, "6": 0x07, "7": 0x08, "8": 0x09,
    "9": 0x0A, "0": 0x0B,
    "空格": 0x39, "Tab": 0x0F,
    "Shift": 0x2A, "Ctrl": 0x1D, "Alt": 0x38,
}


# ==================== 配置管理模块 ====================
# 尝试导入配置管理模块
try:
    from 核心.配置管理 import 配置管理器
    配置管理可用 = True
except ImportError:
    配置管理可用 = False

# 全局配置管理器实例
_配置管理器实例 = None


def 获取配置管理器():
    """获取或创建配置管理器实例"""
    global _配置管理器实例
    
    if not 配置管理可用:
        return None
    
    if _配置管理器实例 is None:
        try:
            _配置管理器实例 = 配置管理器()
        except Exception as e:
            logger.error(f"创建配置管理器失败: {e}")
            return None
    
    return _配置管理器实例


# ==================== 窗口检测辅助函数 ====================
def 更新窗口区域(新区域: tuple):
    """
    更新游戏窗口区域配置
    
    当自动窗口检测获取到新的窗口位置时调用此函数更新全局配置
    
    参数:
        新区域: (x, y, width, height) 格式的窗口区域
        
    需求: 5.1, 5.2, 5.3 - 模型输入尺寸同步
    """
    global 游戏窗口区域, 游戏宽度, 游戏高度, 模型输入宽度, 模型输入高度
    
    if 新区域 and len(新区域) == 4:
        x, y, width, height = 新区域
        游戏窗口区域 = (x, y, x + width, y + height)
        游戏宽度 = width
        游戏高度 = height
        
        # 同步更新模型输入尺寸
        # 需求 5.2: 模型输入宽度 = 游戏宽度 // 模型缩放比例
        # 需求 5.3: 模型输入高度 = 游戏高度 // 模型缩放比例
        模型输入宽度 = 游戏宽度 // 模型缩放比例
        模型输入高度 = 游戏高度 // 模型缩放比例
        
        logger.info(f"游戏窗口区域已更新: {游戏窗口区域}")
        logger.info(f"模型输入尺寸已同步: {模型输入宽度}x{模型输入高度}")


def 获取窗口检测配置() -> dict:
    """
    获取窗口检测相关配置
    
    返回:
        包含窗口检测配置的字典
    """
    return {
        "启用自动检测": 启用自动窗口检测,
        "标识类型": 窗口标识类型,
        "标识值": 窗口标识值,
        "启用跟踪": 启用窗口跟踪,
        "配置路径": 窗口配置路径,
        "当前区域": 游戏窗口区域
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


# ==================== 推理配置辅助函数 ====================
# 需求: 4.4 - 提供配置选项来选择首选的推理后端

def 获取推理配置() -> dict:
    """获取推理相关配置
    
    从配置文件或全局变量获取推理配置。
    支持从配置文件加载完整的推理设置。
    
    需求: 4.4 - 提供配置选项来选择首选的推理后端
    
    Returns:
        包含推理配置的字典
    """
    import json
    
    配置 = {
        "首选后端": 首选推理后端,
        "使用GPU": 推理使用GPU,
        "模型路径": 预训练模型路径,
        "输入宽度": 模型输入宽度,
        "输入高度": 模型输入高度,
        "启用推理引擎": 启用推理引擎,
        "最大延迟阈值": 最大推理延迟,
        "预热次数": 10,
    }
    
    # 尝试从配置文件加载
    if os.path.exists(推理配置路径):
        try:
            with open(推理配置路径, 'r', encoding='utf-8') as f:
                文件配置 = json.load(f)
                # 移除说明字段
                文件配置.pop("说明", None)
                配置.update(文件配置)
        except Exception as e:
            logger.warning(f"加载推理配置文件失败: {e}")
    
    return 配置


def 设置推理后端(后端: str) -> bool:
    """设置首选推理后端
    
    Args:
        后端: "auto", "onnx", "tflearn"
        
    Returns:
        bool: 设置是否成功
    """
    global 首选推理后端
    
    有效后端 = ["auto", "onnx", "tflearn"]
    if 后端 not in 有效后端:
        logger.error(f"无效的推理后端: {后端}，有效值: {有效后端}")
        return False
    
    首选推理后端 = 后端
    logger.info(f"首选推理后端已设置为: {后端}")
    
    # 保存到配置文件
    return 保存推理配置()


def 设置推理GPU(使用GPU: bool) -> bool:
    """设置是否使用GPU进行推理
    
    Args:
        使用GPU: 是否使用GPU
        
    Returns:
        bool: 设置是否成功
    """
    global 推理使用GPU
    
    推理使用GPU = 使用GPU
    logger.info(f"推理GPU设置已更新: {'启用' if 使用GPU else '禁用'}")
    
    # 保存到配置文件
    return 保存推理配置()


def 保存推理配置() -> bool:
    """保存推理配置到文件
    
    将当前推理配置保存到 JSON 文件。
    
    需求: 4.4 - 提供配置选项来选择首选的推理后端
    
    Returns:
        bool: 保存是否成功
    """
    import json
    
    配置数据 = {
        "模型路径": 预训练模型路径,
        "首选后端": 首选推理后端,
        "使用GPU": 推理使用GPU,
        "输入宽度": 模型输入宽度,
        "输入高度": 模型输入高度,
        "预热次数": 10,
        "最大延迟阈值": 最大推理延迟,
        "启用推理引擎": 启用推理引擎,
        "GPU配置": {
            "设备ID": 0,
            "内存限制GB": 2,
            "优先使用CUDA": True,
            "允许DirectML": True
        },
        "说明": {
            "首选后端": "可选值: auto(自动检测), onnx(ONNX Runtime), tflearn(TFLearn)",
            "使用GPU": "是否使用GPU加速，需要安装onnxruntime-gpu",
            "预热次数": "推理引擎预热次数，用于稳定性能",
            "最大延迟阈值": "最大允许推理延迟(毫秒)，超过此值会记录警告",
            "启用推理引擎": "是否启用统一推理引擎",
            "GPU配置": {
                "设备ID": "GPU设备ID，默认为0",
                "内存限制GB": "GPU内存限制(GB)",
                "优先使用CUDA": "是否优先使用CUDA加速",
                "允许DirectML": "是否允许使用DirectML(Windows)"
            }
        }
    }
    
    try:
        # 确保目录存在
        目录 = os.path.dirname(推理配置路径)
        if 目录 and not os.path.exists(目录):
            os.makedirs(目录)
        
        with open(推理配置路径, 'w', encoding='utf-8') as f:
            json.dump(配置数据, f, ensure_ascii=False, indent=2)
        
        logger.info(f"推理配置已保存到: {推理配置路径}")
        return True
    except Exception as e:
        logger.error(f"保存推理配置失败: {e}")
        return False


def 创建统一推理引擎(模型路径: str = None):
    """创建统一推理引擎实例
    
    使用当前配置创建推理引擎。
    
    Args:
        模型路径: 可选，模型文件路径。如果不指定，使用配置中的路径。
        
    Returns:
        统一推理引擎实例，如果创建失败返回 None
    """
    try:
        from 核心.ONNX推理 import 统一推理引擎
        
        配置 = 获取推理配置()
        
        if 模型路径 is None:
            模型路径 = 配置.get("模型路径", 预训练模型路径)
        
        引擎 = 统一推理引擎(
            模型路径=模型路径,
            首选后端=配置.get("首选后端", "auto"),
            使用GPU=配置.get("使用GPU", True),
            配置=配置
        )
        
        return 引擎
    except Exception as e:
        logger.error(f"创建统一推理引擎失败: {e}")
        return None


def 设置启用推理引擎(启用: bool) -> bool:
    """设置是否启用推理引擎
    
    Args:
        启用: 是否启用推理引擎
        
    Returns:
        bool: 设置是否成功
        
    需求: 4.4 - 提供配置选项来选择首选的推理后端
    """
    global 启用推理引擎
    
    启用推理引擎 = 启用
    logger.info(f"推理引擎已{'启用' if 启用 else '禁用'}")
    
    # 保存到配置文件
    return 保存推理配置()


def 获取可用推理后端() -> list:
    """获取可用的推理后端列表
    
    检测系统中可用的推理后端。
    
    Returns:
        list: 可用后端列表，如 ["onnx", "tflearn"]
    """
    可用后端 = []
    
    # 检查 ONNX Runtime
    try:
        import onnxruntime
        可用后端.append("onnx")
        logger.debug(f"ONNX Runtime 可用，版本: {onnxruntime.__version__}")
    except ImportError:
        logger.debug("ONNX Runtime 不可用")
    
    # 检查 TFLearn
    try:
        import tflearn
        可用后端.append("tflearn")
        logger.debug("TFLearn 可用")
    except ImportError:
        logger.debug("TFLearn 不可用")
    
    return 可用后端


def 获取推理后端信息() -> dict:
    """获取推理后端详细信息
    
    返回所有推理后端的详细信息，包括版本、GPU支持等。
    
    Returns:
        dict: 后端信息字典
    """
    信息 = {
        "可用后端": 获取可用推理后端(),
        "当前配置": {
            "首选后端": 首选推理后端,
            "使用GPU": 推理使用GPU,
            "启用推理引擎": 启用推理引擎
        }
    }
    
    # ONNX Runtime 详细信息
    try:
        import onnxruntime as ort
        信息["onnx"] = {
            "版本": ort.__version__,
            "可用提供者": ort.get_available_providers(),
            "GPU支持": "CUDAExecutionProvider" in ort.get_available_providers() or 
                       "DmlExecutionProvider" in ort.get_available_providers()
        }
    except ImportError:
        信息["onnx"] = {"可用": False}
    
    # TFLearn 详细信息
    try:
        import tflearn
        import tensorflow as tf
        信息["tflearn"] = {
            "可用": True,
            "tensorflow版本": tf.__version__,
            "GPU支持": len(tf.config.list_physical_devices('GPU')) > 0
        }
    except ImportError:
        信息["tflearn"] = {"可用": False}
    
    return 信息


# ==================== 屏幕截取配置辅助函数 ====================
# 需求: 2.4 - 记录正在使用的截取后端

def 获取截取配置() -> dict:
    """获取屏幕截取相关配置
    
    从配置文件或全局变量获取截取配置。
    支持从配置文件加载完整的截取设置。
    
    需求: 2.4 - 记录正在使用的截取后端
    
    Returns:
        包含截取配置的字典
    """
    import json
    
    配置 = {
        "首选后端": 首选截取后端,
        "启用回退": 启用截取回退,
        "启用性能监控": 启用截取性能监控,
        "显示器索引": 截取显示器索引,
    }
    
    # 尝试从配置文件加载
    if os.path.exists(截取配置路径):
        try:
            with open(截取配置路径, 'r', encoding='utf-8') as f:
                文件配置 = json.load(f)
                # 移除说明字段
                文件配置.pop("说明", None)
                配置.update(文件配置)
        except Exception as e:
            logger.warning(f"加载截取配置文件失败: {e}")
    
    return 配置


def 设置截取后端(后端: str) -> bool:
    """设置首选截取后端
    
    需求: 2.4 - 记录正在使用的截取后端
    
    Args:
        后端: "auto", "dxgi", "mss", "gdi", "pil"
        
    Returns:
        bool: 设置是否成功
    """
    global 首选截取后端
    
    有效后端 = ["auto", "dxgi", "mss", "gdi", "pil"]
    if 后端 not in 有效后端:
        logger.error(f"无效的截取后端: {后端}，有效值: {有效后端}")
        return False
    
    首选截取后端 = 后端
    logger.info(f"首选截取后端已设置为: {后端}")
    
    # 保存到配置文件
    return 保存截取配置()


def 设置截取回退(启用: bool) -> bool:
    """设置是否启用截取回退机制
    
    Args:
        启用: 是否启用回退
        
    Returns:
        bool: 设置是否成功
    """
    global 启用截取回退
    
    启用截取回退 = 启用
    logger.info(f"截取回退机制已{'启用' if 启用 else '禁用'}")
    
    # 保存到配置文件
    return 保存截取配置()


def 设置截取性能监控(启用: bool) -> bool:
    """设置是否启用截取性能监控
    
    Args:
        启用: 是否启用性能监控
        
    Returns:
        bool: 设置是否成功
    """
    global 启用截取性能监控
    
    启用截取性能监控 = 启用
    logger.info(f"截取性能监控已{'启用' if 启用 else '禁用'}")
    
    # 保存到配置文件
    return 保存截取配置()


def 保存截取配置() -> bool:
    """保存截取配置到文件
    
    将当前截取配置保存到 JSON 文件。
    
    需求: 2.4 - 记录正在使用的截取后端
    
    Returns:
        bool: 保存是否成功
    """
    import json
    
    配置数据 = {
        "首选后端": 首选截取后端,
        "启用回退": 启用截取回退,
        "启用性能监控": 启用截取性能监控,
        "显示器索引": 截取显示器索引,
        "说明": {
            "首选后端": "可选值: auto(自动检测), dxgi(DXGI高性能), mss(跨平台), gdi(Windows原生), pil(通用回退)",
            "启用回退": "当首选后端失败时是否自动尝试其他后端",
            "启用性能监控": "是否记录截取时间等性能指标",
            "显示器索引": "要截取的显示器索引，0为主显示器"
        }
    }
    
    try:
        # 确保目录存在
        目录 = os.path.dirname(截取配置路径)
        if 目录 and not os.path.exists(目录):
            os.makedirs(目录)
        
        with open(截取配置路径, 'w', encoding='utf-8') as f:
            json.dump(配置数据, f, ensure_ascii=False, indent=2)
        
        logger.info(f"截取配置已保存到: {截取配置路径}")
        return True
    except Exception as e:
        logger.error(f"保存截取配置失败: {e}")
        return False


def 获取可用截取后端() -> list:
    """获取可用的截取后端列表
    
    检测系统中可用的截取后端。
    
    Returns:
        list: 可用后端列表，如 ["dxgi", "mss", "gdi", "pil"]
    """
    try:
        from 核心.屏幕截取 import 获取可用后端列表
        return 获取可用后端列表()
    except ImportError:
        # 如果无法导入，返回默认值
        return ["gdi"]


def 获取截取后端信息() -> dict:
    """获取截取后端详细信息
    
    返回所有截取后端的详细信息，包括可用性、性能等。
    
    Returns:
        dict: 后端信息字典
    """
    try:
        from 核心.屏幕截取 import 获取系统图形信息, 获取截取器状态
        
        信息 = {
            "系统图形信息": 获取系统图形信息(),
            "截取器状态": 获取截取器状态(),
            "当前配置": {
                "首选后端": 首选截取后端,
                "启用回退": 启用截取回退,
                "启用性能监控": 启用截取性能监控,
                "显示器索引": 截取显示器索引
            }
        }
        return 信息
    except ImportError as e:
        logger.warning(f"无法获取截取后端信息: {e}")
        return {
            "当前配置": {
                "首选后端": 首选截取后端,
                "启用回退": 启用截取回退,
                "启用性能监控": 启用截取性能监控,
                "显示器索引": 截取显示器索引
            }
        }


def 应用截取配置():
    """应用截取配置到截取模块
    
    将当前配置设置应用到屏幕截取模块。
    应在修改配置后调用此函数使配置生效。
    """
    try:
        from 核心.屏幕截取 import 设置截取配置 as 设置模块配置
        
        配置 = {
            "首选后端": 首选截取后端,
            "启用回退": 启用截取回退,
            "启用性能监控": 启用截取性能监控,
            "显示器索引": 截取显示器索引
        }
        
        设置模块配置(配置)
        logger.info("截取配置已应用到截取模块")
    except ImportError as e:
        logger.warning(f"无法应用截取配置: {e}")


# ==================== 数据增强配置辅助函数 ====================
# 需求 3.4: 增强管道应可通过配置文件或字典进行配置

def 获取数据增强配置() -> dict:
    """获取数据增强相关配置
    
    从配置文件或全局变量获取增强配置。
    支持从配置文件加载完整的增强设置。
    
    需求 3.4: 增强管道应可通过配置文件或字典进行配置
    
    Returns:
        包含增强配置的字典
    """
    import json
    
    配置 = 默认增强配置.copy()
    
    # 尝试从配置文件加载
    if os.path.exists(数据增强配置路径):
        try:
            with open(数据增强配置路径, 'r', encoding='utf-8') as f:
                文件配置 = json.load(f)
                # 移除说明字段
                文件配置.pop("说明", None)
                文件配置.pop("元数据", None)
                配置.update(文件配置)
        except Exception as e:
            logger.warning(f"加载数据增强配置文件失败: {e}")
    
    return 配置


def 保存数据增强配置(配置: dict = None) -> bool:
    """保存数据增强配置到文件
    
    将增强配置保存到 JSON 文件。
    
    需求 3.4: 增强管道应可通过配置文件或字典进行配置
    
    Args:
        配置: 要保存的配置字典，如果为 None 则使用默认配置
        
    Returns:
        bool: 保存是否成功
    """
    import json
    
    if 配置 is None:
        配置 = 默认增强配置.copy()
    
    配置数据 = 配置.copy()
    配置数据["元数据"] = {
        "启用数据增强": 启用数据增强,
        "使用语义安全增强": 使用语义安全增强
    }
    配置数据["说明"] = {
        "启用": "是否启用该变换",
        "概率": "应用变换的概率 (0.0-1.0)",
        "强度": "变换强度 (0.0-1.0)",
        "范围": "变换参数范围",
        "元数据": {
            "启用数据增强": "是否在训练时启用数据增强",
            "使用语义安全增强": "是否使用语义安全限制保护动作语义"
        }
    }
    
    try:
        # 确保目录存在
        目录 = os.path.dirname(数据增强配置路径)
        if 目录 and not os.path.exists(目录):
            os.makedirs(目录)
        
        with open(数据增强配置路径, 'w', encoding='utf-8') as f:
            json.dump(配置数据, f, ensure_ascii=False, indent=2)
        
        logger.info(f"数据增强配置已保存到: {数据增强配置路径}")
        return True
    except Exception as e:
        logger.error(f"保存数据增强配置失败: {e}")
        return False


def 设置启用数据增强(启用: bool) -> bool:
    """设置是否启用数据增强
    
    Args:
        启用: 是否启用数据增强
        
    Returns:
        bool: 设置是否成功
    """
    global 启用数据增强
    
    启用数据增强 = 启用
    logger.info(f"数据增强已{'启用' if 启用 else '禁用'}")
    
    return True


def 设置语义安全增强(启用: bool) -> bool:
    """设置是否使用语义安全增强
    
    启用后，会自动限制变换强度以保护动作语义。
    
    Args:
        启用: 是否启用语义安全增强
        
    Returns:
        bool: 设置是否成功
    """
    global 使用语义安全增强
    
    使用语义安全增强 = 启用
    logger.info(f"语义安全增强已{'启用' if 启用 else '禁用'}")
    
    return True


def 创建数据增强器(配置: dict = None, 随机种子: int = None):
    """创建数据增强器实例
    
    使用当前配置创建数据增强器。
    
    需求 3.4: 增强管道应可通过配置文件或字典进行配置
    需求 4.1, 4.2: 与训练数据加载器集成
    
    Args:
        配置: 可选，增强配置字典。如果不指定，使用配置文件或默认配置。
        随机种子: 可选，随机种子用于可重复性。
        
    Returns:
        数据增强器实例，如果创建失败返回 None
    """
    try:
        from 工具.数据增强 import 数据增强器, 创建语义安全增强器
        
        if 配置 is None:
            配置 = 获取数据增强配置()
        
        if 使用语义安全增强:
            增强器 = 创建语义安全增强器(配置=配置, 随机种子=随机种子)
        else:
            增强器 = 数据增强器(配置=配置, 随机种子=随机种子)
        
        logger.info("数据增强器已创建")
        return 增强器
    except ImportError as e:
        logger.error(f"无法导入数据增强模块: {e}")
        return None
    except Exception as e:
        logger.error(f"创建数据增强器失败: {e}")
        return None


def 获取数据增强信息() -> dict:
    """获取数据增强详细信息
    
    返回数据增强的配置和状态信息。
    
    Returns:
        dict: 增强信息字典
    """
    信息 = {
        "启用状态": 启用数据增强,
        "使用语义安全": 使用语义安全增强,
        "配置文件路径": 数据增强配置路径,
        "配置文件存在": os.path.exists(数据增强配置路径),
        "当前配置": 获取数据增强配置()
    }
    
    # 检查数据增强模块是否可用
    try:
        from 工具.数据增强 import 数据增强器, 变换类型映射
        信息["模块可用"] = True
        信息["可用变换类型"] = list(变换类型映射.keys())
    except ImportError:
        信息["模块可用"] = False
        信息["可用变换类型"] = []
    
    return 信息


def 更新增强变换配置(变换名称: str, 配置更新: dict) -> bool:
    """更新单个变换的配置
    
    Args:
        变换名称: 变换类型名称（如 "亮度调整"）
        配置更新: 要更新的配置项字典
        
    Returns:
        bool: 更新是否成功
    """
    try:
        配置 = 获取数据增强配置()
        
        if 变换名称 not in 配置:
            配置[变换名称] = {}
        
        配置[变换名称].update(配置更新)
        
        return 保存数据增强配置(配置)
    except Exception as e:
        logger.error(f"更新增强变换配置失败: {e}")
        return False


def 启用增强变换(变换名称: str) -> bool:
    """启用指定的增强变换
    
    Args:
        变换名称: 变换类型名称
        
    Returns:
        bool: 操作是否成功
    """
    return 更新增强变换配置(变换名称, {"启用": True})


def 禁用增强变换(变换名称: str) -> bool:
    """禁用指定的增强变换
    
    Args:
        变换名称: 变换类型名称
        
    Returns:
        bool: 操作是否成功
    """
    return 更新增强变换配置(变换名称, {"启用": False})
