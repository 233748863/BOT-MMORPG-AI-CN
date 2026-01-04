"""
模型热切换管理模块
支持在运行时切换不同的 AI 模型，无需重启程序

功能:
- 多模型加载和管理
- 运行时模型切换（线程安全、原子性）
- 自动切换规则
- 快捷键集成
- 配置热重载
- 预加载优化（100ms 内完成切换）

需求: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4
"""

import os
import sys
import time
import json
import logging
import threading
from typing import List, Dict, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, Future

import numpy as np

# 配置日志
logging.basicConfig(level=logging.INFO)
日志 = logging.getLogger(__name__)


# ==================== 数据类定义 ====================

@dataclass
class 模型槽位:
    """
    模型槽位信息
    
    存储已加载模型实例和元数据
    需求: 1.4 - 报告每个已加载模型的内存使用情况
    需求: 2.2 - 支持预加载优化
    """
    名称: str
    路径: str
    描述: str = ""
    适用状态: List[str] = field(default_factory=list)
    快捷键: str = ""
    模型实例: Any = None
    已加载: bool = False
    内存占用: int = 0  # 字节
    加载时间: float = 0.0  # 加载耗时（秒）
    最后使用时间: float = 0.0
    # 预加载相关
    预加载状态: str = "未预加载"  # "未预加载", "预加载中", "已预加载", "预加载失败"
    预热完成: bool = False  # 模型是否已预热（执行过一次推理）

    def 获取内存占用MB(self) -> float:
        """获取内存占用（MB）"""
        return self.内存占用 / (1024 * 1024)


@dataclass
class 切换事件:
    """
    模型切换事件记录
    
    记录所有切换事件，包含触发方式和原因
    需求: 2.4 - 当模型切换发生时，记录切换事件
    """
    时间戳: float
    原模型: str
    新模型: str
    触发方式: str  # "manual", "auto", "hotkey"
    触发原因: str
    切换耗时: float = 0.0  # 毫秒
    切换成功: bool = True  # 切换是否成功
    额外信息: Dict[str, Any] = field(default_factory=dict)  # 额外的上下文信息
    
    def 转为字典(self) -> Dict[str, Any]:
        """转换为字典格式，用于序列化"""
        return {
            "时间戳": self.时间戳,
            "时间": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.时间戳)),
            "原模型": self.原模型,
            "新模型": self.新模型,
            "触发方式": self.触发方式,
            "触发原因": self.触发原因,
            "切换耗时": self.切换耗时,
            "切换成功": self.切换成功,
            "额外信息": self.额外信息
        }
    
    def 转为日志字符串(self) -> str:
        """转换为日志字符串格式"""
        时间字符串 = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.时间戳))
        状态 = "成功" if self.切换成功 else "失败"
        return (
            f"[{时间字符串}] [{self.触发方式}] {self.原模型} -> {self.新模型} "
            f"({状态}, {self.切换耗时:.2f}ms) - {self.触发原因}"
        )
    
    @classmethod
    def 从字典创建(cls, 数据: Dict[str, Any]) -> '切换事件':
        """从字典创建切换事件"""
        return cls(
            时间戳=数据.get("时间戳", time.time()),
            原模型=数据.get("原模型", ""),
            新模型=数据.get("新模型", ""),
            触发方式=数据.get("触发方式", "manual"),
            触发原因=数据.get("触发原因", ""),
            切换耗时=数据.get("切换耗时", 0.0),
            切换成功=数据.get("切换成功", True),
            额外信息=数据.get("额外信息", {})
        )


@dataclass
class 自动切换规则:
    """
    自动切换规则
    
    定义基于游戏状态的自动切换规则
    需求: 3.1, 3.2 - 支持定义基于游戏状态的自动切换规则
    """
    名称: str  # 规则名称
    触发状态: List[str]  # 触发切换的游戏状态列表
    目标模型: str  # 切换到的目标模型
    优先级: int = 0  # 优先级，数值越大优先级越高
    冷却时间: float = 5.0  # 该规则的冷却时间（秒）
    启用: bool = True  # 是否启用该规则
    
    def 匹配状态(self, 当前状态: str) -> bool:
        """
        检查当前状态是否匹配该规则
        
        参数:
            当前状态: 当前游戏状态
            
        返回:
            是否匹配
        """
        if not self.启用:
            return False
        return 当前状态 in self.触发状态
    
    @classmethod
    def 从字典创建(cls, 数据: dict) -> '自动切换规则':
        """从字典创建自动切换规则"""
        return cls(
            名称=数据.get("名称", ""),
            触发状态=数据.get("触发状态", []),
            目标模型=数据.get("目标模型", ""),
            优先级=数据.get("优先级", 0),
            冷却时间=数据.get("冷却时间", 5.0),
            启用=数据.get("启用", True)
        )


@dataclass
class 模型配置:
    """模型配置信息"""
    名称: str
    路径: str
    描述: str = ""
    适用状态: List[str] = field(default_factory=list)
    快捷键: str = ""
    
    @classmethod
    def 从字典创建(cls, 数据: dict) -> '模型配置':
        """从字典创建模型配置"""
        return cls(
            名称=数据.get("名称", ""),
            路径=数据.get("路径", ""),
            描述=数据.get("描述", ""),
            适用状态=数据.get("适用状态", []),
            快捷键=数据.get("快捷键", "")
        )


@dataclass
class 管理器配置:
    """模型管理器配置"""
    模型列表: List[模型配置] = field(default_factory=list)
    默认模型: str = ""
    自动切换启用: bool = True
    冷却时间: float = 5.0  # 秒
    
    @classmethod
    def 从字典创建(cls, 数据: dict) -> '管理器配置':
        """从字典创建管理器配置"""
        模型列表 = []
        for 模型数据 in 数据.get("模型列表", []):
            模型列表.append(模型配置.从字典创建(模型数据))
        
        自动切换配置 = 数据.get("自动切换", {})
        
        return cls(
            模型列表=模型列表,
            默认模型=数据.get("默认模型", ""),
            自动切换启用=自动切换配置.get("启用", True),
            冷却时间=自动切换配置.get("冷却时间", 5.0)
        )


# ==================== 模型管理器类 ====================

class 模型管理器:
    """
    管理多个模型的加载和切换
    
    功能:
    - 模型槽位管理
    - 模型加载和卸载
    - 运行时切换（线程安全、原子性）
    - 配置文件加载
    - 预加载优化（100ms 内完成切换）
    
    需求: 1.1, 1.3, 1.5, 2.1, 2.2, 2.3, 2.4
    """
    
    def __init__(self, 配置路径: str = None):
        """
        初始化模型管理器
        
        参数:
            配置路径: 模型配置文件路径（JSON/YAML）
            
        需求: 1.2, 5.1
        """
        # 模型槽位字典 {名称: 模型槽位}
        self._槽位: Dict[str, 模型槽位] = {}
        
        # 当前活动模型名称
        self._活动模型: str = ""
        
        # 线程安全锁
        # 使用 RLock 支持同一线程重入
        self._锁 = threading.RLock()
        
        # 切换专用锁，确保切换操作的原子性
        # 需求: 2.1, 2.3 - 线程安全的模型切换
        self._切换锁 = threading.Lock()
        
        # 切换状态标志，用于原子性检查
        self._正在切换 = threading.Event()
        self._正在切换.clear()  # 初始状态：未在切换
        
        # 切换事件日志
        self._切换日志: List[切换事件] = []
        self._日志最大长度 = 100
        
        # 配置
        self._配置: Optional[管理器配置] = None
        self._配置路径 = 配置路径
        
        # 切换回调函数
        self._切换回调: List[Callable[[str, str], None]] = []
        
        # 预加载相关
        # 需求: 2.2 - 预加载模型到内存，100ms 内完成切换
        self._预加载线程池 = ThreadPoolExecutor(max_workers=2, thread_name_prefix="模型预加载")
        self._预加载任务: Dict[str, Future] = {}
        
        # 切换性能目标（毫秒）
        self._切换性能目标 = 100  # 100ms
        
        # 加载配置
        if 配置路径:
            self.加载配置(配置路径)
        
        日志.info("模型管理器初始化完成")

    # ==================== 配置加载方法 ====================
    
    def 加载配置(self, 配置路径: str) -> bool:
        """
        从配置文件加载模型配置
        
        参数:
            配置路径: JSON 或 YAML 配置文件路径
            
        返回:
            是否加载成功
            
        需求: 1.2, 5.1, 5.2, 5.4
        """
        if not os.path.exists(配置路径):
            日志.error(f"配置文件不存在: {配置路径}")
            return False
        
        try:
            # 根据文件扩展名选择解析方式
            扩展名 = os.path.splitext(配置路径)[1].lower()
            
            with open(配置路径, 'r', encoding='utf-8') as f:
                if 扩展名 in ['.yaml', '.yml']:
                    try:
                        import yaml
                        数据 = yaml.safe_load(f)
                    except ImportError:
                        日志.error("未安装 PyYAML，无法解析 YAML 文件")
                        return False
                else:  # 默认 JSON
                    数据 = json.load(f)
            
            # 验证配置
            if not self._验证配置(数据):
                return False
            
            # 解析配置
            self._配置 = 管理器配置.从字典创建(数据)
            self._配置路径 = 配置路径
            
            日志.info(f"配置加载成功: {配置路径}")
            日志.info(f"  模型数量: {len(self._配置.模型列表)}")
            日志.info(f"  默认模型: {self._配置.默认模型}")
            
            return True
            
        except json.JSONDecodeError as e:
            日志.error(f"配置文件 JSON 解析错误: {e}")
            return False
        except Exception as e:
            日志.error(f"加载配置失败: {e}")
            return False
    
    def _验证配置(self, 数据: dict) -> bool:
        """
        验证配置数据
        
        需求: 5.4 - 验证配置并报告错误
        """
        错误列表 = []
        
        # 检查模型列表
        模型列表 = 数据.get("模型列表", [])
        if not 模型列表:
            错误列表.append("模型列表为空")
        
        模型名称集合 = set()
        for i, 模型 in enumerate(模型列表):
            # 检查必需字段
            if not 模型.get("名称"):
                错误列表.append(f"模型 {i+1}: 缺少名称")
            else:
                名称 = 模型["名称"]
                if 名称 in 模型名称集合:
                    错误列表.append(f"模型名称重复: {名称}")
                模型名称集合.add(名称)
            
            if not 模型.get("路径"):
                错误列表.append(f"模型 {模型.get('名称', i+1)}: 缺少路径")
        
        # 检查默认模型
        默认模型 = 数据.get("默认模型", "")
        if 默认模型 and 默认模型 not in 模型名称集合:
            错误列表.append(f"默认模型不存在: {默认模型}")
        
        # 报告错误
        if 错误列表:
            for 错误 in 错误列表:
                日志.error(f"配置验证错误: {错误}")
            return False
        
        return True

    def 重新加载配置(self) -> bool:
        """
        重新加载配置文件
        
        需求: 5.3 - 支持在不重启的情况下重新加载配置
        """
        if not self._配置路径:
            日志.warning("没有配置文件路径，无法重新加载")
            return False
        
        return self.加载配置(self._配置路径)
    
    def 保存配置(self, 配置路径: str = None) -> bool:
        """
        保存当前配置到文件
        
        参数:
            配置路径: 保存路径，默认使用原配置路径
        """
        路径 = 配置路径 or self._配置路径
        if not 路径:
            日志.error("没有指定配置文件路径")
            return False
        
        try:
            # 构建配置数据
            数据 = {
                "模型列表": [],
                "默认模型": self._配置.默认模型 if self._配置 else "",
                "自动切换": {
                    "启用": self._配置.自动切换启用 if self._配置 else True,
                    "冷却时间": self._配置.冷却时间 if self._配置 else 5.0
                }
            }
            
            # 添加模型信息
            for 名称, 槽位 in self._槽位.items():
                数据["模型列表"].append({
                    "名称": 槽位.名称,
                    "路径": 槽位.路径,
                    "描述": 槽位.描述,
                    "适用状态": 槽位.适用状态,
                    "快捷键": 槽位.快捷键
                })
            
            # 保存文件
            扩展名 = os.path.splitext(路径)[1].lower()
            with open(路径, 'w', encoding='utf-8') as f:
                if 扩展名 in ['.yaml', '.yml']:
                    try:
                        import yaml
                        yaml.dump(数据, f, allow_unicode=True, default_flow_style=False)
                    except ImportError:
                        日志.error("未安装 PyYAML，无法保存 YAML 文件")
                        return False
                else:
                    json.dump(数据, f, ensure_ascii=False, indent=2)
            
            日志.info(f"配置已保存: {路径}")
            return True
            
        except Exception as e:
            日志.error(f"保存配置失败: {e}")
            return False

    # ==================== 模型加载和卸载方法 ====================
    
    def 加载模型(self, 名称: str, 路径: str, 描述: str = "",
                适用状态: List[str] = None, 快捷键: str = "") -> bool:
        """
        加载模型到指定槽位
        
        参数:
            名称: 模型名称（唯一标识）
            路径: 模型文件路径
            描述: 模型描述
            适用状态: 适用的游戏状态列表
            快捷键: 切换快捷键
            
        返回:
            是否加载成功
            
        需求: 1.1, 1.3
        """
        with self._锁:
            # 检查是否已存在
            if 名称 in self._槽位:
                日志.warning(f"模型槽位已存在: {名称}，将覆盖")
                self.卸载模型(名称)
            
            # 验证模型文件
            if not self._验证模型文件(路径):
                日志.error(f"模型文件验证失败: {路径}")
                return False
            
            # 创建槽位
            槽位 = 模型槽位(
                名称=名称,
                路径=路径,
                描述=描述,
                适用状态=适用状态 or [],
                快捷键=快捷键
            )
            
            # 加载模型实例
            开始时间 = time.perf_counter()
            模型实例 = self._加载模型实例(路径)
            加载耗时 = time.perf_counter() - 开始时间
            
            if 模型实例 is None:
                日志.error(f"模型加载失败: {名称}")
                return False
            
            # 更新槽位信息
            槽位.模型实例 = 模型实例
            槽位.已加载 = True
            槽位.加载时间 = 加载耗时
            槽位.内存占用 = self._估算内存占用(模型实例)
            槽位.最后使用时间 = time.time()
            
            # 添加到槽位字典
            self._槽位[名称] = 槽位
            
            日志.info(f"模型加载成功: {名称}")
            日志.info(f"  路径: {路径}")
            日志.info(f"  加载耗时: {加载耗时*1000:.1f}ms")
            日志.info(f"  内存占用: {槽位.获取内存占用MB():.2f}MB")
            
            # 如果是第一个模型，设为活动模型
            if not self._活动模型:
                self._活动模型 = 名称
            
            return True
    
    def _验证模型文件(self, 路径: str) -> bool:
        """
        验证模型文件存在且兼容
        
        需求: 1.3 - 验证模型文件存在且兼容
        """
        # 检查文件存在
        if not os.path.exists(路径):
            # 检查是否是目录（某些模型格式）
            if not os.path.isdir(路径):
                日志.error(f"模型文件不存在: {路径}")
                return False
        
        # 检查文件扩展名
        支持的格式 = ['.onnx', '.pt', '.pth', '.pb', '.h5', '.keras', '.index']
        扩展名 = os.path.splitext(路径)[1].lower()
        
        # 如果是目录或没有扩展名，假设是有效的
        if os.path.isdir(路径) or not 扩展名:
            return True
        
        if 扩展名 not in 支持的格式:
            日志.warning(f"未知的模型格式: {扩展名}，尝试加载")
        
        return True

    def _加载模型实例(self, 路径: str) -> Any:
        """
        加载模型实例
        
        支持多种模型格式：ONNX、PyTorch、TensorFlow 等
        """
        扩展名 = os.path.splitext(路径)[1].lower()
        
        try:
            # ONNX 模型
            if 扩展名 == '.onnx':
                return self._加载ONNX模型(路径)
            
            # PyTorch 模型
            elif 扩展名 in ['.pt', '.pth']:
                return self._加载PyTorch模型(路径)
            
            # TensorFlow/Keras 模型
            elif 扩展名 in ['.pb', '.h5', '.keras']:
                return self._加载TensorFlow模型(路径)
            
            # TFLearn 检查点
            elif 扩展名 == '.index' or os.path.exists(路径 + '.index'):
                return self._加载TFLearn模型(路径)
            
            # 目录（可能是 SavedModel）
            elif os.path.isdir(路径):
                return self._加载SavedModel(路径)
            
            else:
                # 尝试作为 ONNX 加载
                日志.warning(f"未知格式，尝试作为 ONNX 加载: {路径}")
                return self._加载ONNX模型(路径)
                
        except Exception as e:
            日志.error(f"加载模型实例失败: {e}")
            return None
    
    def _加载ONNX模型(self, 路径: str) -> Any:
        """加载 ONNX 模型"""
        try:
            import onnxruntime as ort
            
            # 配置执行提供者
            providers = []
            if 'CUDAExecutionProvider' in ort.get_available_providers():
                providers.append('CUDAExecutionProvider')
            elif 'DmlExecutionProvider' in ort.get_available_providers():
                providers.append('DmlExecutionProvider')
            providers.append('CPUExecutionProvider')
            
            # 创建会话
            会话选项 = ort.SessionOptions()
            会话选项.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            
            会话 = ort.InferenceSession(路径, sess_options=会话选项, providers=providers)
            
            日志.info(f"ONNX 模型加载成功，使用: {会话.get_providers()[0]}")
            return 会话
            
        except ImportError:
            日志.error("未安装 onnxruntime")
            return None
        except Exception as e:
            日志.error(f"ONNX 模型加载失败: {e}")
            return None
    
    def _加载PyTorch模型(self, 路径: str) -> Any:
        """加载 PyTorch 模型"""
        try:
            import torch
            模型 = torch.load(路径, map_location='cpu')
            if hasattr(模型, 'eval'):
                模型.eval()
            日志.info("PyTorch 模型加载成功")
            return 模型
        except ImportError:
            日志.error("未安装 PyTorch")
            return None
        except Exception as e:
            日志.error(f"PyTorch 模型加载失败: {e}")
            return None
    
    def _加载TensorFlow模型(self, 路径: str) -> Any:
        """加载 TensorFlow/Keras 模型"""
        try:
            import tensorflow as tf
            模型 = tf.keras.models.load_model(路径)
            日志.info("TensorFlow/Keras 模型加载成功")
            return 模型
        except ImportError:
            日志.error("未安装 TensorFlow")
            return None
        except Exception as e:
            日志.error(f"TensorFlow 模型加载失败: {e}")
            return None
    
    def _加载TFLearn模型(self, 路径: str) -> Any:
        """加载 TFLearn 检查点模型"""
        try:
            # 尝试使用项目中的模型定义
            from 核心.模型定义 import inception_v3
            from 配置.设置 import 模型输入宽度, 模型输入高度, 学习率, 总动作数
            
            模型 = inception_v3(
                模型输入宽度, 模型输入高度, 3, 学习率,
                输出类别=总动作数, 模型名称=路径
            )
            模型.load(路径)
            日志.info("TFLearn 模型加载成功")
            return 模型
        except Exception as e:
            日志.error(f"TFLearn 模型加载失败: {e}")
            return None
    
    def _加载SavedModel(self, 路径: str) -> Any:
        """加载 TensorFlow SavedModel"""
        try:
            import tensorflow as tf
            模型 = tf.saved_model.load(路径)
            日志.info("SavedModel 加载成功")
            return 模型
        except ImportError:
            日志.error("未安装 TensorFlow")
            return None
        except Exception as e:
            日志.error(f"SavedModel 加载失败: {e}")
            return None

    def _估算内存占用(self, 模型实例: Any) -> int:
        """
        估算模型内存占用
        
        需求: 1.4 - 报告每个已加载模型的内存使用情况
        """
        try:
            # 尝试使用 sys.getsizeof
            基础大小 = sys.getsizeof(模型实例)
            
            # ONNX Runtime 会话
            if hasattr(模型实例, 'get_inputs'):
                # 估算：输入输出张量大小
                输入信息 = 模型实例.get_inputs()
                if 输入信息:
                    形状 = 输入信息[0].shape
                    if all(isinstance(d, int) for d in 形状):
                        元素数 = 1
                        for d in 形状:
                            元素数 *= d
                        基础大小 += 元素数 * 4  # float32
            
            # PyTorch 模型
            elif hasattr(模型实例, 'parameters'):
                import torch
                参数数 = sum(p.numel() for p in 模型实例.parameters())
                基础大小 = 参数数 * 4  # float32
            
            # TensorFlow/Keras 模型
            elif hasattr(模型实例, 'count_params'):
                参数数 = 模型实例.count_params()
                基础大小 = 参数数 * 4
            
            return max(基础大小, 1024 * 1024)  # 至少 1MB
            
        except Exception as e:
            日志.warning(f"估算内存占用失败: {e}")
            return 10 * 1024 * 1024  # 默认 10MB
    
    def 卸载模型(self, 名称: str) -> bool:
        """
        卸载指定模型以释放内存
        
        参数:
            名称: 模型名称
            
        返回:
            是否卸载成功
            
        需求: 1.5 - 支持卸载模型以释放内存
        """
        with self._锁:
            if 名称 not in self._槽位:
                日志.warning(f"模型不存在: {名称}")
                return False
            
            # 不能卸载当前活动模型
            if 名称 == self._活动模型:
                日志.error(f"不能卸载当前活动模型: {名称}")
                return False
            
            槽位 = self._槽位[名称]
            内存占用 = 槽位.获取内存占用MB()
            
            # 清理模型实例
            槽位.模型实例 = None
            槽位.已加载 = False
            
            # 从槽位字典移除
            del self._槽位[名称]
            
            # 强制垃圾回收
            import gc
            gc.collect()
            
            日志.info(f"模型已卸载: {名称}，释放约 {内存占用:.2f}MB")
            return True
    
    def 卸载所有模型(self) -> None:
        """卸载所有模型"""
        with self._锁:
            模型列表 = list(self._槽位.keys())
            for 名称 in 模型列表:
                if 名称 != self._活动模型:
                    self.卸载模型(名称)
            
            # 最后卸载活动模型
            if self._活动模型 in self._槽位:
                self._槽位[self._活动模型].模型实例 = None
                self._槽位[self._活动模型].已加载 = False
                del self._槽位[self._活动模型]
            
            self._活动模型 = ""
            
            import gc
            gc.collect()
            
            日志.info("所有模型已卸载")

    # ==================== 模型切换方法 ====================
    
    def 切换模型(self, 名称: str, 触发方式: str = "manual", 
                触发原因: str = "") -> bool:
        """
        切换活动模型（线程安全、原子性）
        
        参数:
            名称: 目标模型名称
            触发方式: "manual", "auto", "hotkey"
            触发原因: 切换原因描述
            
        返回:
            是否切换成功
            
        需求: 2.1, 2.3 - 线程安全的模型切换，确保切换原子性
        需求: 2.2 - 100ms 内完成切换
        """
        开始时间 = time.perf_counter()
        
        # 使用切换锁确保原子性
        # 需求: 2.3 - 确保线程安全的模型切换
        if not self._切换锁.acquire(timeout=1.0):
            日志.warning(f"切换锁获取超时，可能有其他切换正在进行")
            return False
        
        try:
            # 设置切换状态标志
            self._正在切换.set()
            
            with self._锁:
                # 检查目标模型是否存在
                if 名称 not in self._槽位:
                    日志.error(f"目标模型不存在: {名称}")
                    return False
                
                # 检查目标模型是否已加载
                目标槽位 = self._槽位[名称]
                if not 目标槽位.已加载:
                    日志.error(f"目标模型未加载: {名称}")
                    return False
                
                # 如果已经是活动模型，无需切换
                if 名称 == self._活动模型:
                    日志.debug(f"模型已是活动状态: {名称}")
                    return True
                
                # 记录原模型
                原模型 = self._活动模型
                
                # 执行原子切换
                # 需求: 2.1 - 在不停止 AI 的情况下切换活动模型
                self._活动模型 = 名称
                目标槽位.最后使用时间 = time.time()
                
                # 计算切换耗时
                切换耗时 = (time.perf_counter() - 开始时间) * 1000  # 毫秒
                
                # 检查是否满足性能目标
                # 需求: 2.2 - 100ms 内完成切换
                if 切换耗时 > self._切换性能目标:
                    日志.warning(f"切换耗时 {切换耗时:.2f}ms 超过目标 {self._切换性能目标}ms")
                
                # 记录切换事件
                事件 = 切换事件(
                    时间戳=time.time(),
                    原模型=原模型,
                    新模型=名称,
                    触发方式=触发方式,
                    触发原因=触发原因 or f"切换到 {名称}",
                    切换耗时=切换耗时
                )
                self._记录切换事件(事件)
                
                # 调用回调函数（在锁外执行以避免死锁）
                回调列表 = list(self._切换回调)
            
            # 在锁外执行回调
            for 回调 in 回调列表:
                try:
                    回调(原模型, 名称)
                except Exception as e:
                    日志.warning(f"切换回调执行失败: {e}")
            
            日志.info(f"模型切换成功: {原模型} -> {名称}")
            日志.info(f"  切换耗时: {切换耗时:.2f}ms")
            
            return True
            
        finally:
            # 清除切换状态标志
            self._正在切换.clear()
            # 释放切换锁
            self._切换锁.release()
    
    def 正在切换(self) -> bool:
        """
        检查是否正在进行模型切换
        
        返回:
            True 表示正在切换，False 表示未在切换
            
        需求: 2.1, 2.3 - 用于确保切换原子性
        """
        return self._正在切换.is_set()
    
    def 等待切换完成(self, 超时: float = 1.0) -> bool:
        """
        等待当前切换操作完成
        
        参数:
            超时: 最大等待时间（秒）
            
        返回:
            True 表示切换已完成，False 表示超时
            
        需求: 2.1, 2.3 - 确保切换原子性
        """
        if not self._正在切换.is_set():
            return True
        
        # 等待切换完成
        开始时间 = time.time()
        while self._正在切换.is_set():
            if time.time() - 开始时间 > 超时:
                return False
            time.sleep(0.001)  # 1ms 轮询
        
        return True
    
    def _记录切换事件(self, 事件: 切换事件) -> None:
        """
        记录切换事件
        
        需求: 2.4 - 记录切换事件
        """
        self._切换日志.append(事件)
        
        # 限制日志长度
        while len(self._切换日志) > self._日志最大长度:
            self._切换日志.pop(0)
    
    def 获取活动模型(self) -> str:
        """获取当前活动模型名称"""
        return self._活动模型
    
    def 获取活动模型实例(self) -> Any:
        """获取当前活动模型实例"""
        with self._锁:
            if not self._活动模型:
                return None
            
            槽位 = self._槽位.get(self._活动模型)
            if 槽位 and 槽位.已加载:
                return 槽位.模型实例
            
            return None

    # ==================== 推理方法 ====================
    
    def 预测(self, 图像: np.ndarray) -> List[float]:
        """
        使用活动模型进行预测
        
        参数:
            图像: 输入图像
            
        返回:
            动作概率列表
            
        需求: 2.1 - 切换过程中不应返回无效预测结果
        需求: 2.3 - 确保线程安全
        """
        # 等待切换完成，确保不在切换过程中进行预测
        # 需求: 2.1 - 切换过程中不应返回无效预测结果
        if self._正在切换.is_set():
            if not self.等待切换完成(超时=0.5):
                日志.warning("等待切换完成超时，跳过本次预测")
                return []
        
        with self._锁:
            模型实例 = self.获取活动模型实例()
            
            if 模型实例 is None:
                日志.warning("没有可用的活动模型")
                return []
            
            # 再次检查切换状态（双重检查）
            if self._正在切换.is_set():
                日志.warning("检测到切换正在进行，跳过本次预测")
                return []
            
            try:
                return self._执行预测(模型实例, 图像)
            except Exception as e:
                日志.error(f"预测失败: {e}")
                return []
    
    def _执行预测(self, 模型实例: Any, 图像: np.ndarray) -> List[float]:
        """执行模型预测"""
        # 预处理图像
        if 图像.dtype != np.float32:
            图像 = 图像.astype(np.float32)
        if 图像.max() > 1.0:
            图像 = 图像 / 255.0
        if len(图像.shape) == 3:
            图像 = np.expand_dims(图像, axis=0)
        
        # ONNX Runtime 会话
        if hasattr(模型实例, 'run') and hasattr(模型实例, 'get_inputs'):
            输入名 = 模型实例.get_inputs()[0].name
            输出名 = 模型实例.get_outputs()[0].name
            结果 = 模型实例.run([输出名], {输入名: 图像})[0]
            return 结果[0].tolist() if len(结果.shape) > 1 else 结果.tolist()
        
        # PyTorch 模型
        elif hasattr(模型实例, 'forward'):
            import torch
            with torch.no_grad():
                张量 = torch.from_numpy(图像)
                结果 = 模型实例(张量)
                return 结果[0].cpu().numpy().tolist()
        
        # TensorFlow/Keras 模型
        elif hasattr(模型实例, 'predict'):
            结果 = 模型实例.predict(图像, verbose=0)
            return 结果[0].tolist()
        
        # TFLearn 模型
        elif hasattr(模型实例, 'predict'):
            结果 = 模型实例.predict(图像)
            return 结果[0].tolist()
        
        else:
            日志.error("不支持的模型类型")
            return []
    
    # ==================== 查询方法 ====================
    
    def 获取模型列表(self) -> List[str]:
        """获取所有已加载模型的名称列表"""
        return list(self._槽位.keys())
    
    def 获取模型信息(self, 名称: str) -> Optional[Dict]:
        """
        获取指定模型的详细信息
        
        需求: 1.4 - 报告每个已加载模型的内存使用情况
        """
        槽位 = self._槽位.get(名称)
        if not 槽位:
            return None
        
        return {
            "名称": 槽位.名称,
            "路径": 槽位.路径,
            "描述": 槽位.描述,
            "适用状态": 槽位.适用状态,
            "快捷键": 槽位.快捷键,
            "已加载": 槽位.已加载,
            "内存占用MB": 槽位.获取内存占用MB(),
            "加载耗时": 槽位.加载时间,
            "最后使用时间": 槽位.最后使用时间,
            "是活动模型": 名称 == self._活动模型
        }
    
    def 获取内存使用(self) -> Dict[str, float]:
        """
        获取各模型内存使用情况
        
        返回:
            {模型名称: 内存占用MB}
            
        需求: 1.4
        """
        return {
            名称: 槽位.获取内存占用MB()
            for 名称, 槽位 in self._槽位.items()
        }
    
    def 获取总内存使用(self) -> float:
        """获取所有模型的总内存使用（MB）"""
        return sum(self.获取内存使用().values())
    
    def 获取切换日志(self, 数量: int = 10) -> List[Dict]:
        """
        获取最近的切换日志
        
        需求: 2.4 - 记录切换事件
        """
        日志列表 = self._切换日志[-数量:] if len(self._切换日志) > 数量 else self._切换日志
        
        return [
            {
                "时间戳": 事件.时间戳,
                "原模型": 事件.原模型,
                "新模型": 事件.新模型,
                "触发方式": 事件.触发方式,
                "触发原因": 事件.触发原因,
                "切换耗时": 事件.切换耗时
            }
            for 事件 in 日志列表
        ]

    # ==================== 回调和事件方法 ====================
    
    def 注册切换回调(self, 回调: Callable[[str, str], None]) -> None:
        """
        注册模型切换回调函数
        
        参数:
            回调: 回调函数，接收 (原模型名称, 新模型名称)
        """
        self._切换回调.append(回调)
    
    def 移除切换回调(self, 回调: Callable[[str, str], None]) -> bool:
        """移除切换回调函数"""
        try:
            self._切换回调.remove(回调)
            return True
        except ValueError:
            return False
    
    # ==================== 从配置初始化方法 ====================
    
    def 从配置初始化(self) -> bool:
        """
        根据已加载的配置初始化所有模型
        
        返回:
            是否全部初始化成功
        """
        if not self._配置:
            日志.warning("没有加载配置，无法初始化")
            return False
        
        成功数 = 0
        失败数 = 0
        
        for 模型配置 in self._配置.模型列表:
            结果 = self.加载模型(
                名称=模型配置.名称,
                路径=模型配置.路径,
                描述=模型配置.描述,
                适用状态=模型配置.适用状态,
                快捷键=模型配置.快捷键
            )
            
            if 结果:
                成功数 += 1
            else:
                失败数 += 1
        
        # 设置默认模型
        if self._配置.默认模型 and self._配置.默认模型 in self._槽位:
            self.切换模型(self._配置.默认模型, "auto", "设置默认模型")
        
        日志.info(f"模型初始化完成: 成功 {成功数}, 失败 {失败数}")
        return 失败数 == 0
    
    # ==================== 状态和统计方法 ====================
    
    def 获取状态(self) -> Dict:
        """获取模型管理器状态"""
        return {
            "活动模型": self._活动模型,
            "已加载模型数": len(self._槽位),
            "总内存使用MB": self.获取总内存使用(),
            "模型列表": self.获取模型列表(),
            "配置路径": self._配置路径,
            "自动切换启用": self._配置.自动切换启用 if self._配置 else False,
            "冷却时间": self._配置.冷却时间 if self._配置 else 5.0
        }
    
    def 获取统计信息(self) -> Dict:
        """获取统计信息"""
        切换日志 = self._切换日志
        
        if not 切换日志:
            return {
                "总切换次数": 0,
                "手动切换次数": 0,
                "自动切换次数": 0,
                "快捷键切换次数": 0,
                "平均切换耗时": 0.0
            }
        
        手动次数 = sum(1 for e in 切换日志 if e.触发方式 == "manual")
        自动次数 = sum(1 for e in 切换日志 if e.触发方式 == "auto")
        快捷键次数 = sum(1 for e in 切换日志 if e.触发方式 == "hotkey")
        平均耗时 = sum(e.切换耗时 for e in 切换日志) / len(切换日志)
        
        return {
            "总切换次数": len(切换日志),
            "手动切换次数": 手动次数,
            "自动切换次数": 自动次数,
            "快捷键切换次数": 快捷键次数,
            "平均切换耗时": 平均耗时
        }

    # ==================== 预加载优化方法 ====================
    
    def 预加载模型(self, 名称: str) -> bool:
        """
        预加载指定模型到内存（异步）
        
        参数:
            名称: 模型名称
            
        返回:
            是否成功启动预加载
            
        需求: 2.2 - 预加载模型到内存，100ms 内完成切换
        """
        with self._锁:
            if 名称 not in self._槽位:
                日志.warning(f"模型不存在，无法预加载: {名称}")
                return False
            
            槽位 = self._槽位[名称]
            
            # 如果已加载，无需预加载
            if 槽位.已加载:
                日志.debug(f"模型已加载，无需预加载: {名称}")
                return True
            
            # 如果正在预加载，返回
            if 名称 in self._预加载任务:
                任务 = self._预加载任务[名称]
                if not 任务.done():
                    日志.debug(f"模型正在预加载中: {名称}")
                    return True
            
            # 更新预加载状态
            槽位.预加载状态 = "预加载中"
        
        # 提交预加载任务
        def 执行预加载():
            try:
                结果 = self.加载模型(
                    名称=槽位.名称,
                    路径=槽位.路径,
                    描述=槽位.描述,
                    适用状态=槽位.适用状态,
                    快捷键=槽位.快捷键
                )
                
                with self._锁:
                    if 名称 in self._槽位:
                        if 结果:
                            self._槽位[名称].预加载状态 = "已预加载"
                        else:
                            self._槽位[名称].预加载状态 = "预加载失败"
                
                return 结果
            except Exception as e:
                日志.error(f"预加载失败: {名称}, 错误: {e}")
                with self._锁:
                    if 名称 in self._槽位:
                        self._槽位[名称].预加载状态 = "预加载失败"
                return False
        
        任务 = self._预加载线程池.submit(执行预加载)
        self._预加载任务[名称] = 任务
        
        日志.info(f"已启动模型预加载: {名称}")
        return True
    
    def 预加载所有模型(self) -> int:
        """
        预加载所有配置的模型
        
        返回:
            启动预加载的模型数量
            
        需求: 2.2 - 预加载模型到内存
        """
        if not self._配置:
            日志.warning("没有配置，无法预加载")
            return 0
        
        启动数 = 0
        for 模型配置 in self._配置.模型列表:
            # 先创建槽位（如果不存在）
            if 模型配置.名称 not in self._槽位:
                self._槽位[模型配置.名称] = 模型槽位(
                    名称=模型配置.名称,
                    路径=模型配置.路径,
                    描述=模型配置.描述,
                    适用状态=模型配置.适用状态,
                    快捷键=模型配置.快捷键
                )
            
            if self.预加载模型(模型配置.名称):
                启动数 += 1
        
        日志.info(f"已启动 {启动数} 个模型的预加载")
        return 启动数
    
    def 等待预加载完成(self, 名称: str = None, 超时: float = 30.0) -> bool:
        """
        等待预加载完成
        
        参数:
            名称: 模型名称，None 表示等待所有
            超时: 最大等待时间（秒）
            
        返回:
            是否全部完成
            
        需求: 2.2 - 确保模型预加载完成
        """
        开始时间 = time.time()
        
        if 名称:
            # 等待指定模型
            if 名称 in self._预加载任务:
                任务 = self._预加载任务[名称]
                剩余时间 = 超时 - (time.time() - 开始时间)
                if 剩余时间 > 0:
                    try:
                        任务.result(timeout=剩余时间)
                        return True
                    except Exception:
                        return False
            return True
        else:
            # 等待所有模型
            for 模型名, 任务 in list(self._预加载任务.items()):
                剩余时间 = 超时 - (time.time() - 开始时间)
                if 剩余时间 <= 0:
                    日志.warning("等待预加载超时")
                    return False
                try:
                    任务.result(timeout=剩余时间)
                except Exception as e:
                    日志.warning(f"预加载任务异常: {模型名}, {e}")
            
            return True
    
    def 预热模型(self, 名称: str, 输入形状: Tuple[int, ...] = None) -> bool:
        """
        预热模型（执行一次推理以优化后续性能）
        
        参数:
            名称: 模型名称
            输入形状: 输入张量形状，默认自动检测
            
        返回:
            是否预热成功
            
        需求: 2.2 - 优化切换性能
        """
        with self._锁:
            if 名称 not in self._槽位:
                日志.warning(f"模型不存在: {名称}")
                return False
            
            槽位 = self._槽位[名称]
            
            if not 槽位.已加载:
                日志.warning(f"模型未加载，无法预热: {名称}")
                return False
            
            if 槽位.预热完成:
                日志.debug(f"模型已预热: {名称}")
                return True
            
            模型实例 = 槽位.模型实例
        
        try:
            # 确定输入形状
            if 输入形状 is None:
                输入形状 = self._获取模型输入形状(模型实例)
            
            if 输入形状 is None:
                输入形状 = (1, 224, 224, 3)  # 默认形状
            
            # 创建虚拟输入
            虚拟输入 = np.zeros(输入形状, dtype=np.float32)
            
            # 执行预热推理
            开始时间 = time.perf_counter()
            self._执行预测(模型实例, 虚拟输入)
            预热耗时 = (time.perf_counter() - 开始时间) * 1000
            
            # 更新预热状态
            with self._锁:
                if 名称 in self._槽位:
                    self._槽位[名称].预热完成 = True
            
            日志.info(f"模型预热完成: {名称}, 耗时: {预热耗时:.2f}ms")
            return True
            
        except Exception as e:
            日志.error(f"模型预热失败: {名称}, 错误: {e}")
            return False
    
    def _获取模型输入形状(self, 模型实例: Any) -> Optional[Tuple[int, ...]]:
        """获取模型输入形状"""
        try:
            # ONNX Runtime
            if hasattr(模型实例, 'get_inputs'):
                输入信息 = 模型实例.get_inputs()
                if 输入信息:
                    形状 = 输入信息[0].shape
                    # 替换动态维度
                    形状 = tuple(d if isinstance(d, int) else 1 for d in 形状)
                    return 形状
            
            # Keras/TensorFlow
            if hasattr(模型实例, 'input_shape'):
                形状 = 模型实例.input_shape
                if isinstance(形状, tuple):
                    形状 = tuple(d if d is not None else 1 for d in 形状)
                    return 形状
            
            return None
        except Exception:
            return None
    
    def 获取预加载状态(self) -> Dict[str, str]:
        """
        获取所有模型的预加载状态
        
        返回:
            {模型名称: 预加载状态}
        """
        with self._锁:
            return {
                名称: 槽位.预加载状态
                for 名称, 槽位 in self._槽位.items()
            }
    
    def 关闭(self) -> None:
        """
        关闭模型管理器，释放资源
        """
        # 关闭预加载线程池
        self._预加载线程池.shutdown(wait=False)
        
        # 卸载所有模型
        self.卸载所有模型()
        
        日志.info("模型管理器已关闭")


# ==================== 自动切换器类 ====================

class 自动切换器:
    """
    根据游戏状态自动切换模型
    
    功能:
    - 规则定义和匹配
    - 优先级处理
    - 冷却时间机制
    - 可配置启用/禁用
    
    需求: 3.1, 3.2, 3.3, 3.4
    """
    
    def __init__(self, 模型管理器实例: 模型管理器):
        """
        初始化自动切换器
        
        参数:
            模型管理器实例: 模型管理器实例
        """
        self._模型管理器 = 模型管理器实例
        
        # 规则列表
        self._规则列表: List[自动切换规则] = []
        
        # 冷却时间相关
        # 需求: 3.3 - 支持自动切换之间的冷却时间
        self._上次切换时间: float = 0.0  # 全局上次切换时间
        self._规则上次触发时间: Dict[str, float] = {}  # 每个规则的上次触发时间
        self._全局冷却时间: float = 5.0  # 全局冷却时间（秒）
        
        # 启用状态
        # 需求: 3.4 - 支持通过配置禁用自动切换
        self._启用: bool = True
        
        # 线程安全锁
        self._锁 = threading.Lock()
        
        日志.info("自动切换器初始化完成")
    
    # ==================== 规则管理方法 ====================
    
    def 添加规则(self, 规则: 自动切换规则) -> bool:
        """
        添加自动切换规则
        
        参数:
            规则: 自动切换规则实例
            
        返回:
            是否添加成功
            
        需求: 3.1 - 支持定义基于游戏状态的自动切换规则
        """
        with self._锁:
            # 检查规则名称是否重复
            for 已有规则 in self._规则列表:
                if 已有规则.名称 == 规则.名称:
                    日志.warning(f"规则名称已存在，将覆盖: {规则.名称}")
                    self._规则列表.remove(已有规则)
                    break
            
            self._规则列表.append(规则)
            
            # 按优先级排序（高优先级在前）
            self._规则列表.sort(key=lambda r: r.优先级, reverse=True)
            
            日志.info(f"添加自动切换规则: {规则.名称}")
            日志.info(f"  触发状态: {规则.触发状态}")
            日志.info(f"  目标模型: {规则.目标模型}")
            日志.info(f"  优先级: {规则.优先级}")
            日志.info(f"  冷却时间: {规则.冷却时间}秒")
            
            return True
    
    def 移除规则(self, 规则名称: str) -> bool:
        """
        移除指定规则
        
        参数:
            规则名称: 规则名称
            
        返回:
            是否移除成功
        """
        with self._锁:
            for 规则 in self._规则列表:
                if 规则.名称 == 规则名称:
                    self._规则列表.remove(规则)
                    # 清理该规则的触发时间记录
                    if 规则名称 in self._规则上次触发时间:
                        del self._规则上次触发时间[规则名称]
                    日志.info(f"移除自动切换规则: {规则名称}")
                    return True
            
            日志.warning(f"规则不存在: {规则名称}")
            return False
    
    def 清空规则(self) -> None:
        """清空所有规则"""
        with self._锁:
            self._规则列表.clear()
            self._规则上次触发时间.clear()
            日志.info("已清空所有自动切换规则")
    
    def 获取规则列表(self) -> List[Dict]:
        """
        获取所有规则的信息
        
        返回:
            规则信息列表
        """
        with self._锁:
            return [
                {
                    "名称": 规则.名称,
                    "触发状态": 规则.触发状态,
                    "目标模型": 规则.目标模型,
                    "优先级": 规则.优先级,
                    "冷却时间": 规则.冷却时间,
                    "启用": 规则.启用
                }
                for 规则 in self._规则列表
            ]
    
    def 获取规则(self, 规则名称: str) -> Optional[自动切换规则]:
        """
        获取指定规则
        
        参数:
            规则名称: 规则名称
            
        返回:
            规则实例，不存在返回 None
        """
        with self._锁:
            for 规则 in self._规则列表:
                if 规则.名称 == 规则名称:
                    return 规则
            return None
    
    def 设置规则启用状态(self, 规则名称: str, 启用: bool) -> bool:
        """
        设置规则的启用状态
        
        参数:
            规则名称: 规则名称
            启用: 是否启用
            
        返回:
            是否设置成功
        """
        with self._锁:
            for 规则 in self._规则列表:
                if 规则.名称 == 规则名称:
                    规则.启用 = 启用
                    日志.info(f"规则 {规则名称} 已{'启用' if 启用 else '禁用'}")
                    return True
            
            日志.warning(f"规则不存在: {规则名称}")
            return False
    
    # ==================== 冷却时间方法 ====================
    
    def 设置全局冷却时间(self, 冷却时间: float) -> None:
        """
        设置全局冷却时间
        
        参数:
            冷却时间: 冷却时间（秒）
            
        需求: 3.3 - 支持自动切换之间的冷却时间
        """
        with self._锁:
            self._全局冷却时间 = max(0.0, 冷却时间)
            日志.info(f"全局冷却时间设置为: {self._全局冷却时间}秒")
    
    def 获取全局冷却时间(self) -> float:
        """获取全局冷却时间"""
        return self._全局冷却时间
    
    def _检查全局冷却(self) -> bool:
        """
        检查全局冷却时间是否已过
        
        返回:
            True 表示冷却已过，可以切换
            
        需求: 3.3 - 支持自动切换之间的冷却时间
        """
        当前时间 = time.time()
        return (当前时间 - self._上次切换时间) >= self._全局冷却时间
    
    def _检查规则冷却(self, 规则: 自动切换规则) -> bool:
        """
        检查指定规则的冷却时间是否已过
        
        参数:
            规则: 自动切换规则
            
        返回:
            True 表示冷却已过，可以触发
            
        需求: 3.3 - 支持自动切换之间的冷却时间
        """
        当前时间 = time.time()
        上次触发时间 = self._规则上次触发时间.get(规则.名称, 0.0)
        return (当前时间 - 上次触发时间) >= 规则.冷却时间
    
    def 获取冷却剩余时间(self) -> float:
        """
        获取全局冷却剩余时间
        
        返回:
            剩余冷却时间（秒），0 表示冷却已过
        """
        当前时间 = time.time()
        已过时间 = 当前时间 - self._上次切换时间
        剩余时间 = self._全局冷却时间 - 已过时间
        return max(0.0, 剩余时间)
    
    def 获取规则冷却剩余时间(self, 规则名称: str) -> float:
        """
        获取指定规则的冷却剩余时间
        
        参数:
            规则名称: 规则名称
            
        返回:
            剩余冷却时间（秒），0 表示冷却已过，-1 表示规则不存在
        """
        with self._锁:
            规则 = self.获取规则(规则名称)
            if 规则 is None:
                return -1.0
            
            当前时间 = time.time()
            上次触发时间 = self._规则上次触发时间.get(规则名称, 0.0)
            已过时间 = 当前时间 - 上次触发时间
            剩余时间 = 规则.冷却时间 - 已过时间
            return max(0.0, 剩余时间)
    
    def _更新切换时间(self, 规则: 自动切换规则) -> None:
        """
        更新切换时间记录
        
        参数:
            规则: 触发的规则
        """
        当前时间 = time.time()
        self._上次切换时间 = 当前时间
        self._规则上次触发时间[规则.名称] = 当前时间
    
    # ==================== 启用/禁用方法 ====================
    
    def 启用自动切换(self) -> None:
        """
        启用自动切换
        
        需求: 3.4 - 支持通过配置禁用自动切换
        """
        with self._锁:
            self._启用 = True
            日志.info("自动切换已启用")
    
    def 禁用自动切换(self) -> None:
        """
        禁用自动切换
        
        需求: 3.4 - 支持通过配置禁用自动切换
        """
        with self._锁:
            self._启用 = False
            日志.info("自动切换已禁用")
    
    def 是否启用(self) -> bool:
        """检查自动切换是否启用"""
        return self._启用
    
    def 设置启用状态(self, 启用: bool) -> None:
        """
        设置自动切换启用状态
        
        参数:
            启用: 是否启用
            
        需求: 3.4 - 支持通过配置禁用自动切换
        """
        with self._锁:
            self._启用 = 启用
            日志.info(f"自动切换已{'启用' if 启用 else '禁用'}")
    
    # ==================== 核心切换检查方法 ====================
    
    def 检查切换(self, 当前状态: str) -> Optional[str]:
        """
        检查是否需要切换模型
        
        根据当前游戏状态检查所有规则，返回需要切换到的目标模型
        
        参数:
            当前状态: 当前游戏状态
            
        返回:
            目标模型名称，None 表示不需要切换
            
        需求: 3.2 - 当游戏状态匹配规则时，切换到指定模型
        需求: 3.3 - 支持自动切换之间的冷却时间
        """
        with self._锁:
            # 检查是否启用
            if not self._启用:
                return None
            
            # 检查全局冷却时间
            if not self._检查全局冷却():
                return None
            
            # 获取当前活动模型
            当前模型 = self._模型管理器.获取活动模型()
            
            # 按优先级顺序检查规则（已排序）
            for 规则 in self._规则列表:
                # 检查规则是否启用
                if not 规则.启用:
                    continue
                
                # 检查状态是否匹配
                if not 规则.匹配状态(当前状态):
                    continue
                
                # 检查目标模型是否与当前模型相同
                if 规则.目标模型 == 当前模型:
                    continue
                
                # 检查规则冷却时间
                if not self._检查规则冷却(规则):
                    continue
                
                # 找到匹配的规则
                日志.debug(f"规则匹配: {规则.名称}, 状态: {当前状态}, 目标: {规则.目标模型}")
                return 规则.目标模型
            
            return None
    
    def 执行自动切换(self, 当前状态: str) -> bool:
        """
        执行自动切换
        
        检查并执行模型切换
        
        参数:
            当前状态: 当前游戏状态
            
        返回:
            是否执行了切换
            
        需求: 3.2 - 当游戏状态匹配规则时，切换到指定模型
        """
        目标模型 = self.检查切换(当前状态)
        
        if 目标模型 is None:
            return False
        
        # 查找匹配的规则（用于更新冷却时间）
        匹配规则 = None
        with self._锁:
            for 规则 in self._规则列表:
                if 规则.目标模型 == 目标模型 and 规则.匹配状态(当前状态):
                    匹配规则 = 规则
                    break
        
        # 执行切换
        结果 = self._模型管理器.切换模型(
            目标模型,
            触发方式="auto",
            触发原因=f"状态 '{当前状态}' 触发自动切换"
        )
        
        if 结果 and 匹配规则:
            with self._锁:
                self._更新切换时间(匹配规则)
            日志.info(f"自动切换成功: {当前状态} -> {目标模型}")
        
        return 结果
    
    # ==================== 配置加载方法 ====================
    
    def 从配置加载规则(self, 配置数据: dict) -> int:
        """
        从配置数据加载规则
        
        参数:
            配置数据: 配置字典，包含 "自动切换规则" 列表
            
        返回:
            加载的规则数量
        """
        规则列表 = 配置数据.get("自动切换规则", [])
        
        加载数 = 0
        for 规则数据 in 规则列表:
            try:
                规则 = 自动切换规则.从字典创建(规则数据)
                if self.添加规则(规则):
                    加载数 += 1
            except Exception as e:
                日志.warning(f"加载规则失败: {e}")
        
        # 加载全局设置
        自动切换配置 = 配置数据.get("自动切换", {})
        if "启用" in 自动切换配置:
            self.设置启用状态(自动切换配置["启用"])
        if "冷却时间" in 自动切换配置:
            self.设置全局冷却时间(自动切换配置["冷却时间"])
        
        日志.info(f"从配置加载了 {加载数} 条自动切换规则")
        return 加载数
    
    def 从模型配置生成规则(self) -> int:
        """
        从模型管理器的配置自动生成规则
        
        根据每个模型的适用状态自动创建切换规则
        
        返回:
            生成的规则数量
        """
        生成数 = 0
        
        for 模型名称 in self._模型管理器.获取模型列表():
            模型信息 = self._模型管理器.获取模型信息(模型名称)
            if 模型信息 is None:
                continue
            
            适用状态 = 模型信息.get("适用状态", [])
            if not 适用状态:
                continue
            
            # 创建规则
            规则 = 自动切换规则(
                名称=f"自动_{模型名称}",
                触发状态=适用状态,
                目标模型=模型名称,
                优先级=0,
                冷却时间=self._全局冷却时间
            )
            
            if self.添加规则(规则):
                生成数 += 1
        
        日志.info(f"从模型配置生成了 {生成数} 条自动切换规则")
        return 生成数
    
    # ==================== 状态和统计方法 ====================
    
    def 获取状态(self) -> Dict:
        """获取自动切换器状态"""
        with self._锁:
            return {
                "启用": self._启用,
                "规则数量": len(self._规则列表),
                "全局冷却时间": self._全局冷却时间,
                "冷却剩余时间": self.获取冷却剩余时间(),
                "上次切换时间": self._上次切换时间
            }
    
    def 获取统计信息(self) -> Dict:
        """获取统计信息"""
        with self._锁:
            return {
                "规则数量": len(self._规则列表),
                "启用规则数量": sum(1 for r in self._规则列表 if r.启用),
                "规则列表": [r.名称 for r in self._规则列表]
            }


# ==================== 快捷键处理器类 ====================

class 快捷键处理器:
    """
    处理模型切换快捷键
    
    功能:
    - 快捷键注册和处理
    - 循环切换功能
    - 切换反馈（显示当前活动模型名称）
    - 状态输出集成
    
    需求: 4.1, 4.2, 4.3, 4.4
    """
    
    # 默认快捷键映射
    默认快捷键 = ["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8"]
    
    # 循环切换快捷键
    循环切换键 = "F9"
    
    def __init__(self, 模型管理器实例: 模型管理器):
        """
        初始化快捷键处理器
        
        参数:
            模型管理器实例: 模型管理器实例
            
        需求: 4.1 - 支持模型切换的快捷键
        """
        self._模型管理器 = 模型管理器实例
        
        # 快捷键映射 {按键: 模型名}
        self._快捷键映射: Dict[str, str] = {}
        
        # 模型到快捷键的反向映射 {模型名: 按键}
        self._模型快捷键映射: Dict[str, str] = {}
        
        # 循环切换索引
        self._循环索引: int = 0
        
        # 切换回调函数（用于显示反馈）
        # 需求: 4.2 - 显示新的活动模型名称
        self._切换回调: List[Callable[[str, str], None]] = []
        
        # 状态输出回调（用于状态输出集成）
        # 需求: 4.4 - 在状态输出中显示当前活动模型
        self._状态输出回调: Optional[Callable[[str], None]] = None
        
        # 启用状态
        self._启用: bool = True
        
        # 线程安全锁
        self._锁 = threading.Lock()
        
        # 从模型管理器配置自动注册快捷键
        self._从配置注册快捷键()
        
        日志.info("快捷键处理器初始化完成")
    
    # ==================== 快捷键注册方法 ====================
    
    def 注册快捷键(self, 按键: str, 模型名: str) -> bool:
        """
        注册快捷键
        
        参数:
            按键: 快捷键名称（如 "F1", "F2"）
            模型名: 对应的模型名称
            
        返回:
            是否注册成功
            
        需求: 4.1 - 支持模型切换的快捷键
        """
        with self._锁:
            # 标准化按键名称
            按键 = 按键.upper().strip()
            
            # 检查模型是否存在
            if 模型名 not in self._模型管理器.获取模型列表():
                # 模型可能还未加载，允许预注册
                日志.warning(f"模型 '{模型名}' 尚未加载，快捷键 '{按键}' 已预注册")
            
            # 检查按键是否已被使用
            if 按键 in self._快捷键映射:
                旧模型 = self._快捷键映射[按键]
                日志.warning(f"快捷键 '{按键}' 已绑定到 '{旧模型}'，将重新绑定到 '{模型名}'")
                # 移除旧的反向映射
                if 旧模型 in self._模型快捷键映射:
                    del self._模型快捷键映射[旧模型]
            
            # 检查模型是否已有快捷键
            if 模型名 in self._模型快捷键映射:
                旧按键 = self._模型快捷键映射[模型名]
                日志.warning(f"模型 '{模型名}' 已有快捷键 '{旧按键}'，将更新为 '{按键}'")
                # 移除旧的快捷键映射
                if 旧按键 in self._快捷键映射:
                    del self._快捷键映射[旧按键]
            
            # 注册快捷键
            self._快捷键映射[按键] = 模型名
            self._模型快捷键映射[模型名] = 按键
            
            日志.info(f"注册快捷键: {按键} -> {模型名}")
            return True
    
    def 注销快捷键(self, 按键: str) -> bool:
        """
        注销快捷键
        
        参数:
            按键: 快捷键名称
            
        返回:
            是否注销成功
        """
        with self._锁:
            按键 = 按键.upper().strip()
            
            if 按键 not in self._快捷键映射:
                日志.warning(f"快捷键 '{按键}' 未注册")
                return False
            
            模型名 = self._快捷键映射[按键]
            
            # 移除映射
            del self._快捷键映射[按键]
            if 模型名 in self._模型快捷键映射:
                del self._模型快捷键映射[模型名]
            
            日志.info(f"注销快捷键: {按键}")
            return True
    
    def 清空快捷键(self) -> None:
        """清空所有快捷键"""
        with self._锁:
            self._快捷键映射.clear()
            self._模型快捷键映射.clear()
            日志.info("已清空所有快捷键")
    
    def _从配置注册快捷键(self) -> None:
        """
        从模型管理器配置自动注册快捷键
        
        需求: 4.1 - 支持模型切换的快捷键（如 F1-F4）
        """
        模型列表 = self._模型管理器.获取模型列表()
        
        for 模型名 in 模型列表:
            模型信息 = self._模型管理器.获取模型信息(模型名)
            if 模型信息 and 模型信息.get("快捷键"):
                self.注册快捷键(模型信息["快捷键"], 模型名)
    
    def 刷新快捷键(self) -> None:
        """
        刷新快捷键映射（从模型管理器重新加载）
        """
        with self._锁:
            self._快捷键映射.clear()
            self._模型快捷键映射.clear()
        
        self._从配置注册快捷键()
        日志.info("快捷键映射已刷新")
    
    # ==================== 快捷键处理方法 ====================
    
    def 处理按键(self, 按键: str) -> bool:
        """
        处理按键事件
        
        参数:
            按键: 按键名称
            
        返回:
            是否触发了模型切换
            
        需求: 4.1 - 支持模型切换的快捷键
        需求: 4.2 - 显示新的活动模型名称
        """
        if not self._启用:
            return False
        
        按键 = 按键.upper().strip()
        
        # 检查是否是循环切换键
        if 按键 == self.循环切换键.upper():
            新模型 = self.循环切换()
            return 新模型 is not None
        
        with self._锁:
            # 检查按键是否已注册
            if 按键 not in self._快捷键映射:
                return False
            
            目标模型 = self._快捷键映射[按键]
        
        # 获取当前模型（用于反馈）
        原模型 = self._模型管理器.获取活动模型()
        
        # 执行切换
        结果 = self._模型管理器.切换模型(
            目标模型,
            触发方式="hotkey",
            触发原因=f"快捷键 {按键} 触发"
        )
        
        if 结果:
            # 触发切换反馈
            # 需求: 4.2 - 显示新的活动模型名称
            self._触发切换反馈(原模型, 目标模型)
            
            # 更新状态输出
            # 需求: 4.4 - 在状态输出中显示当前活动模型
            self._更新状态输出(目标模型)
            
            日志.info(f"快捷键切换成功: {按键} -> {目标模型}")
        
        return 结果
    
    def 循环切换(self) -> Optional[str]:
        """
        循环切换到下一个模型
        
        返回:
            新的活动模型名称，切换失败返回 None
            
        需求: 4.3 - 支持用单个按键循环切换可用模型
        """
        if not self._启用:
            return None
        
        模型列表 = self._模型管理器.获取模型列表()
        
        if not 模型列表:
            日志.warning("没有可用的模型进行循环切换")
            return None
        
        # 获取当前模型
        当前模型 = self._模型管理器.获取活动模型()
        原模型 = 当前模型
        
        with self._锁:
            # 找到当前模型的索引
            try:
                当前索引 = 模型列表.index(当前模型)
            except ValueError:
                当前索引 = -1
            
            # 计算下一个索引
            下一索引 = (当前索引 + 1) % len(模型列表)
            目标模型 = 模型列表[下一索引]
            
            # 更新循环索引
            self._循环索引 = 下一索引
        
        # 执行切换
        结果 = self._模型管理器.切换模型(
            目标模型,
            触发方式="hotkey",
            触发原因=f"循环切换 ({下一索引 + 1}/{len(模型列表)})"
        )
        
        if 结果:
            # 触发切换反馈
            self._触发切换反馈(原模型, 目标模型)
            
            # 更新状态输出
            self._更新状态输出(目标模型)
            
            日志.info(f"循环切换成功: {原模型} -> {目标模型} ({下一索引 + 1}/{len(模型列表)})")
            return 目标模型
        
        return None
    
    # ==================== 切换反馈方法 ====================
    
    def 注册切换回调(self, 回调: Callable[[str, str], None]) -> None:
        """
        注册切换反馈回调函数
        
        参数:
            回调: 回调函数，接收 (原模型名称, 新模型名称)
            
        需求: 4.2 - 显示新的活动模型名称
        """
        with self._锁:
            self._切换回调.append(回调)
    
    def 移除切换回调(self, 回调: Callable[[str, str], None]) -> bool:
        """移除切换反馈回调函数"""
        with self._锁:
            try:
                self._切换回调.remove(回调)
                return True
            except ValueError:
                return False
    
    def 设置状态输出回调(self, 回调: Callable[[str], None]) -> None:
        """
        设���状态输出回调函数
        
        参数:
            回调: 回调函数，接收当前活动模型名称
            
        需求: 4.4 - 在状态输出中显示当前活动模型
        """
        self._状态输出回调 = 回调
    
    def _触发切换反馈(self, 原模型: str, 新模型: str) -> None:
        """
        触发切换反馈
        
        需求: 4.2 - 显示新的活动模型名称
        """
        with self._锁:
            回调列表 = list(self._切换回调)
        
        for 回调 in 回调列表:
            try:
                回调(原模型, 新模型)
            except Exception as e:
                日志.warning(f"切换反馈回调执行失败: {e}")
    
    def _更新状态输出(self, 模型名: str) -> None:
        """
        更新状态输出
        
        需求: 4.4 - 在状态输出中显示当前活动模型
        """
        if self._状态输出回调:
            try:
                self._状态输出回调(模型名)
            except Exception as e:
                日志.warning(f"状态输出回调执行失败: {e}")
    
    def 获取切换反馈消息(self, 原模型: str, 新模型: str) -> str:
        """
        生成切换反馈消息
        
        参数:
            原模型: 原模型名称
            新模型: 新模型名称
            
        返回:
            反馈消息字符串
            
        需求: 4.2 - 显示新的活动模型名称
        """
        # 获取新模型的快捷键
        快捷键 = self._模型快捷键映射.get(新模型, "")
        快捷键信息 = f" [{快捷键}]" if 快捷键 else ""
        
        # 获取新模型的描述
        模型信息 = self._模型管理器.获取模型信息(新模型)
        描述 = 模型信息.get("描述", "") if 模型信息 else ""
        描述信息 = f" - {描述}" if 描述 else ""
        
        return f"模型已切换: {新模型}{快捷键信息}{描述信息}"
    
    # ==================== 启用/禁用方法 ====================
    
    def 启用(self) -> None:
        """启用快捷键处理"""
        self._启用 = True
        日志.info("快捷键处理已启用")
    
    def 禁用(self) -> None:
        """禁用快捷键处理"""
        self._启用 = False
        日志.info("快捷键处理已禁用")
    
    def 是否启用(self) -> bool:
        """检查快捷键处理是否启用"""
        return self._启用
    
    def 设置启用状态(self, 启用: bool) -> None:
        """设置快捷键处理启用状态"""
        self._启用 = 启用
        日志.info(f"快捷键处理已{'启用' if 启用 else '禁用'}")
    
    # ==================== 查询方法 ====================
    
    def 获取快捷键映射(self) -> Dict[str, str]:
        """
        获取快捷键映射
        
        返回:
            {按键: 模型名}
        """
        with self._锁:
            return dict(self._快捷键映射)
    
    def 获取模型快捷键(self, 模型名: str) -> Optional[str]:
        """
        获取指定模型的快捷键
        
        参数:
            模型名: 模型名称
            
        返回:
            快捷键名称，未注册返回 None
        """
        with self._锁:
            return self._模型快捷键映射.get(模型名)
    
    def 获取快捷键模型(self, 按键: str) -> Optional[str]:
        """
        获取指定快捷键对应的模型
        
        参数:
            按键: 快捷键名称
            
        返回:
            模型名称，未注册返回 None
        """
        with self._锁:
            return self._快捷键映射.get(按键.upper().strip())
    
    def 获取所有快捷键信息(self) -> List[Dict]:
        """
        获取所有快捷键的详细信息
        
        返回:
            快捷键信息列表
        """
        with self._锁:
            结果 = []
            for 按键, 模型名 in self._快捷键映射.items():
                模型信息 = self._模型管理器.获取模型信息(模型名)
                结果.append({
                    "按键": 按键,
                    "模型名": 模型名,
                    "描述": 模型信息.get("描述", "") if 模型信息 else "",
                    "是活动模型": 模型名 == self._模型管理器.获取活动模型()
                })
            return 结果
    
    def 获取状态(self) -> Dict:
        """获取快捷键处理器状态"""
        with self._锁:
            return {
                "启用": self._启用,
                "已注册快捷键数": len(self._快捷键映射),
                "快捷键映射": dict(self._快捷键映射),
                "循环切换键": self.循环切换键,
                "当前活动模型": self._模型管理器.获取活动模型()
            }
    
    def 获取当前模型状态字符串(self) -> str:
        """
        获取当前模型状态字符串（用于状态输出）
        
        返回:
            状态字符串
            
        需求: 4.4 - 在状态输出中显示当前活动模型
        """
        当前模型 = self._模型管理器.获取活动模型()
        快捷键 = self._模型快捷键映射.get(当前模型, "")
        
        if 快捷键:
            return f"当前模型: {当前模型} [{快捷键}]"
        else:
            return f"当前模型: {当前模型}"


# ==================== 便捷函数 ====================

def 创建模型管理器(配置路径: str = None) -> 模型管理器:
    """
    创建模型管理器实例
    
    参数:
        配置路径: 配置文件路径
        
    返回:
        模型管理器实例
    """
    管理器 = 模型管理器(配置路径)
    
    if 配置路径:
        管理器.从配置初始化()
    
    return 管理器


def 创建快捷键处理器(模型管理器实例: 模型管理器) -> 快捷键处理器:
    """
    创建快捷键处理器实例
    
    参数:
        模型管理器实例: 模型管理器实例
        
    返回:
        快捷键处理器实例
        
    需求: 4.1 - 支持模型切换的快捷键
    """
    return 快捷键处理器(模型管理器实例)


# ==================== 切换反馈管理器类 ====================

class 切换反馈管理器:
    """
    模型切换反馈管理器
    
    功能:
    - 显示当前活动模型名称
    - 状态输出集成
    - 通知服务集成
    - 控制台输出
    
    需求: 4.2, 4.4
    """
    
    def __init__(self, 模型管理器实例: 模型管理器, 快捷键处理器实例: 快捷键处理器 = None):
        """
        初始化切换反馈管理器
        
        参数:
            模型管理器实例: 模型管理器实例
            快捷键处理器实例: 快捷键处理器实例（可选）
            
        需求: 4.2 - 显示新的活动模型名称
        需求: 4.4 - 在状态输出中显示当前活动模型
        """
        self._模型管理器 = 模型管理器实例
        self._快捷键处理器 = 快捷键处理器实例
        
        # 通知服务引用（需要外部设置）
        self._通知服务 = None
        
        # 状态输出回调
        self._状态输出回调: Optional[Callable[[str], None]] = None
        
        # 控制台输出启用
        self._控制台输出启用: bool = True
        
        # 通知启用
        self._通知启用: bool = True
        
        # 注册模型管理器的切换回调
        self._模型管理器.注册切换回调(self._处理切换事件)
        
        # 如果有快捷键处理器，也注册回调
        if self._快捷键处理器:
            self._快捷键处理器.注册切换回调(self._处理快捷键切换)
        
        日志.info("切换反馈管理器初始化完成")
    
    def 设置通知服务(self, 通知服务) -> None:
        """
        设置通知服务
        
        参数:
            通知服务: 通知服务实例
            
        需求: 4.2 - 显示新的活动模型名称
        """
        self._通知服务 = 通知服务
    
    def 设置状态输出回调(self, 回调: Callable[[str], None]) -> None:
        """
        设置状态输出回调
        
        参数:
            回调: 回调函数，接收状态字符串
            
        需求: 4.4 - 在状态输出中显示当前活动模型
        """
        self._状态输出回调 = 回调
    
    def 设置控制台输出(self, 启用: bool) -> None:
        """设置是否启用控制台输出"""
        self._控制台输出启用 = 启用
    
    def 设置通知输出(self, 启用: bool) -> None:
        """设置是否启用通知输出"""
        self._通知启用 = 启用
    
    def _处理切换事件(self, 原模型: str, 新模型: str) -> None:
        """
        处理模型切换事件
        
        参数:
            原模型: 原模型名称
            新模型: 新模型名称
            
        需求: 4.2 - 显示新的活动模型名称
        """
        # 生成反馈消息
        消息 = self._生成切换消息(原模型, 新模型)
        
        # 控制台输出
        if self._控制台输出启用:
            print(f"[模型切换] {消息}")
        
        # 通知服务输出
        if self._通知启用 and self._通知服务:
            try:
                self._通知服务.显示成功("模型切换", 消息)
            except Exception as e:
                日志.warning(f"通知服务调用失败: {e}")
        
        # 状态输出
        self._更新状态输出()
    
    def _处理快捷键切换(self, 原模型: str, 新模型: str) -> None:
        """
        处理快捷键触发的切换事件
        
        参数:
            原模型: 原模型名称
            新模型: 新模型名称
        """
        # 快捷键切换已经在模型管理器中记录，这里可以添加额外的快捷键特定反馈
        快捷键 = ""
        if self._快捷键处理器:
            快捷键 = self._快捷键处理器.获取模型快捷键(新模型) or ""
        
        if 快捷键:
            日志.debug(f"快捷键 [{快捷键}] 触发切换: {原模型} -> {新模型}")
    
    def _生成切换消息(self, 原模型: str, 新模型: str) -> str:
        """
        生成切换反馈消息
        
        参数:
            原模型: 原模型名称
            新模型: 新模型名称
            
        返回:
            反馈消息字符串
            
        需求: 4.2 - 显示新的活动模型名称
        """
        # 获取新模型信息
        模型信息 = self._模型管理器.获取模型信息(新模型)
        描述 = 模型信息.get("描述", "") if 模型信息 else ""
        
        # 获取快捷键
        快捷键 = ""
        if self._快捷键处理器:
            快捷键 = self._快捷键处理器.获取模型快捷键(新模型) or ""
        
        # 构建消息
        消息部分 = [f"{原模型} → {新模型}"]
        
        if 快捷键:
            消息部分.append(f"[{快捷键}]")
        
        if 描述:
            消息部分.append(f"({描述})")
        
        return " ".join(消息部分)
    
    def _更新状态输出(self) -> None:
        """
        更新状态输出
        
        需求: 4.4 - 在状态输出中显示当前活动模型
        """
        if self._状态输出回调:
            状态字符串 = self.获取当前状态字符串()
            try:
                self._状态输出回调(状态字符串)
            except Exception as e:
                日志.warning(f"状态输出回调失败: {e}")
    
    def 获取当前状态字符串(self) -> str:
        """
        获取当前模型状态字符串
        
        返回:
            状态字符串
            
        需求: 4.4 - 在状态输出中显示当前活动模型
        """
        当前模型 = self._模型管理器.获取活动模型()
        
        if not 当前模型:
            return "当前模型: 无"
        
        # 获取快捷键
        快捷键 = ""
        if self._快捷键处理器:
            快捷键 = self._快捷键处理器.获取模型快捷键(当前模型) or ""
        
        # 获取模型信息
        模型信息 = self._模型管理器.获取模型信息(当前模型)
        描述 = 模型信息.get("描述", "") if 模型信息 else ""
        
        # 构建状态字符串
        if 快捷键 and 描述:
            return f"当前模型: {当前模型} [{快捷键}] - {描述}"
        elif 快捷键:
            return f"当前模型: {当前模型} [{快捷键}]"
        elif 描述:
            return f"当前模型: {当前模型} - {描述}"
        else:
            return f"当前模型: {当前模型}"
    
    def 显示当前模型信息(self) -> None:
        """
        显示当前模型的详细信息
        
        需求: 4.2 - 显示新的活动模型名称
        """
        当前模型 = self._模型管理器.获取活动模型()
        
        if not 当前模型:
            print("当前没有活动模型")
            return
        
        模型信息 = self._模型管理器.获取模型信息(当前模型)
        
        print(f"\n{'='*40}")
        print(f"当前活动模型: {当前模型}")
        print(f"{'='*40}")
        
        if 模型信息:
            print(f"  路径: {模型信息.get('路径', '未知')}")
            print(f"  描述: {模型信息.get('描述', '无')}")
            print(f"  适用状态: {', '.join(模型信息.get('适用状态', [])) or '无'}")
            print(f"  快捷键: {模型信息.get('快捷键', '无')}")
            print(f"  内存占用: {模型信息.get('内存占用MB', 0):.2f} MB")
            print(f"  已加载: {'是' if 模型信息.get('已加载', False) else '否'}")
        
        print(f"{'='*40}\n")
    
    def 显示所有模型状态(self) -> None:
        """
        显示所有模型的状态
        
        需求: 4.4 - 在状态输出中显示当前活动模型
        """
        模型列表 = self._模型管理器.获取模型列表()
        当前模型 = self._模型管理器.获取活动模型()
        
        print(f"\n{'='*50}")
        print("模型状态列表")
        print(f"{'='*50}")
        
        for 模型名 in 模型列表:
            模型信息 = self._模型管理器.获取模型信息(模型名)
            是活动 = "★" if 模型名 == 当前模型 else " "
            快捷键 = 模型信息.get("快捷键", "") if 模型信息 else ""
            快捷键显示 = f"[{快捷键}]" if 快捷键 else "    "
            描述 = 模型信息.get("描述", "") if 模型信息 else ""
            
            print(f"  {是活动} {快捷键显示} {模型名}: {描述}")
        
        print(f"{'='*50}")
        print(f"  ★ = 当前活动模型")
        print(f"{'='*50}\n")


def 创建切换反馈管理器(
    模型管理器实例: 模型管理器,
    快捷键处理器实例: 快捷键处理器 = None
) -> 切换反馈管理器:
    """
    创建切换反馈管理器实例
    
    参数:
        模型管理器实例: 模型管理器实例
        快捷键处理器实例: 快捷键处理器实例（可选）
        
    返回:
        切换反馈管理器实例
        
    需求: 4.2, 4.4
    """
    return 切换反馈管理器(模型管理器实例, 快捷键处理器实例)


# ==================== 切换事件日志管理器类 ====================

class 切换事件日志管理器:
    """
    切换事件日志管理器
    
    功能:
    - 记录所有切换事件到内存和文件
    - 包含触发方式和原因
    - 支持日志查询和导出
    - 支持日志持久化
    
    需求: 2.4 - 当模型切换发生时，记录切换事件
    """
    
    # 默认日志目录
    默认日志目录 = "日志"
    
    # 默认日志文件前缀
    默认日志文件前缀 = "模型切换日志"
    
    def __init__(self, 
                 模型管理器实例: 模型管理器,
                 日志目录: str = None,
                 启用文件日志: bool = True,
                 最大内存日志数: int = 1000):
        """
        初始化切换事件日志管理器
        
        参数:
            模型管理器实例: 模型管理器实例
            日志目录: 日志文件保存目录
            启用文件日志: 是否启用文件日志
            最大内存日志数: 内存中保存的最大日志数量
            
        需求: 2.4 - 记录切换事件
        """
        self._模型管理器 = 模型管理器实例
        self._日志目录 = 日志目录 or self.默认日志目录
        self._启用文件日志 = 启用文件日志
        self._最大内存日志数 = 最大内存日志数
        
        # 内存中的日志列表
        self._日志列表: List[切换事件] = []
        
        # 线程安全锁
        self._锁 = threading.Lock()
        
        # 当前日志文件路径
        self._当前日志文件: Optional[str] = None
        
        # 确保日志目录存在
        if self._启用文件日志:
            self._确保日志目录存在()
        
        # 注册模型管理器的切换回调
        self._模型管理器.注册切换回调(self._处理切换事件)
        
        日志.info(f"切换事件日志管理器初始化完成，日志目录: {self._日志目录}")
    
    def _确保日志目录存在(self) -> None:
        """确保日志目录存在"""
        if not os.path.exists(self._日志目录):
            os.makedirs(self._日志目录)
            日志.info(f"创建日志目录: {self._日志目录}")
    
    def _获取当前日志文件路径(self) -> str:
        """
        获取当前日期的日志文件路径
        
        返回:
            日志文件路径
        """
        日期字符串 = time.strftime("%Y%m%d")
        文件名 = f"{self.默认日志文件前缀}_{日期字符串}.log"
        return os.path.join(self._日志目录, 文件名)
    
    def _处理切换事件(self, 原模型: str, 新模型: str) -> None:
        """
        处理模型切换事件（回调函数）
        
        参数:
            原模型: 原模型名称
            新模型: 新模型名称
            
        需求: 2.4 - 记录切换事件
        """
        # 从模型管理器获取最新的切换日志
        最新日志 = self._模型管理器.获取切换日志(数量=1)
        
        if 最新日志:
            最新事件数据 = 最新日志[0]
            事件 = 切换事件(
                时间戳=最新事件数据.get("时间戳", time.time()),
                原模型=最新事件数据.get("原模型", 原模型),
                新模型=最新事件数据.get("新模型", 新模型),
                触发方式=最新事件数据.get("触发方式", "manual"),
                触发原因=最新事件数据.get("触发原因", ""),
                切换耗时=最新事件数据.get("切换耗时", 0.0),
                切换成功=True
            )
        else:
            # 如果没有获取到日志，创建一个基本事件
            事件 = 切换事件(
                时间戳=time.time(),
                原模型=原模型,
                新模型=新模型,
                触发方式="manual",
                触发原因=f"切换到 {新模型}",
                切换耗时=0.0,
                切换成功=True
            )
        
        # 记录事件
        self.记录事件(事件)
    
    def 记录事件(self, 事件: 切换事件) -> None:
        """
        记录切换事件
        
        参数:
            事件: 切换事件实例
            
        需求: 2.4 - 记录切换事件
        """
        with self._锁:
            # 添加到内存日志
            self._日志列表.append(事件)
            
            # 限制内存日志数量
            while len(self._日志列表) > self._最大内存日志数:
                self._日志列表.pop(0)
            
            # 写入文件日志
            if self._启用文件日志:
                self._写入文件日志(事件)
        
        日志.debug(f"记录切换事件: {事件.转为日志字符串()}")
    
    def _写入文件日志(self, 事件: 切换事件) -> None:
        """
        写入文件日志
        
        参数:
            事件: 切换事件实例
            
        需求: 2.4 - 记录切换事件
        """
        try:
            日志文件路径 = self._获取当前日志文件路径()
            
            # 确保日志目录存在
            self._确保日志目录存在()
            
            # 追加写入日志
            with open(日志文件路径, 'a', encoding='utf-8') as f:
                f.write(事件.转为日志字符串() + "\n")
            
            self._当前日志文件 = 日志文件路径
            
        except Exception as e:
            日志.error(f"写入切换事件日志失败: {e}")
    
    def 获取日志(self, 
                数量: int = 100,
                触发方式: str = None,
                开始时间: float = None,
                结束时间: float = None) -> List[Dict[str, Any]]:
        """
        获取切换事件日志
        
        参数:
            数量: 返回的最大日志数量
            触发方式: 过滤触发方式（"manual", "auto", "hotkey"）
            开始时间: 开始时间戳
            结束时间: 结束时间戳
            
        返回:
            日志列表（字典格式）
            
        需求: 2.4 - 记录切换事件
        """
        with self._锁:
            结果 = []
            
            for 事件 in reversed(self._日志列表):
                # 过滤触发方式
                if 触发方式 and 事件.触发方式 != 触发方式:
                    continue
                
                # 过滤时间范围
                if 开始时间 and 事件.时间戳 < 开始时间:
                    continue
                if 结束时间 and 事件.时间戳 > 结束时间:
                    continue
                
                结果.append(事件.转为字典())
                
                if len(结果) >= 数量:
                    break
            
            return 结果
    
    def _计算统计信息_无锁(self) -> Dict[str, Any]:
        """
        计算统计信息（内部方法，不加锁）
        
        注意：调用此方法前必须已持有 self._锁
        """
        if not self._日志列表:
            return {
                "总切换次数": 0,
                "手动切换次数": 0,
                "自动切换次数": 0,
                "快捷键切换次数": 0,
                "成功次数": 0,
                "失败次数": 0,
                "平均切换耗时": 0.0,
                "最近切换时间": None
            }
        
        手动次数 = sum(1 for e in self._日志列表 if e.触发方式 == "manual")
        自动次数 = sum(1 for e in self._日志列表 if e.触发方式 == "auto")
        快捷键次数 = sum(1 for e in self._日志列表 if e.触发方式 == "hotkey")
        成功次数 = sum(1 for e in self._日志列表 if e.切换成功)
        失败次数 = len(self._日志列表) - 成功次数
        平均耗时 = sum(e.切换耗时 for e in self._日志列表) / len(self._日志列表)
        最近时间 = self._日志列表[-1].时间戳 if self._日志列表 else None
        
        return {
            "总切换次数": len(self._日志列表),
            "手动切换次数": 手动次数,
            "自动切换次数": 自动次数,
            "快捷键切换次数": 快捷键次数,
            "成功次数": 成功次数,
            "失败次数": 失败次数,
            "平均切换耗时": 平均耗时,
            "最近切换时间": 最近时间
        }
    
    def 获取统计信息(self) -> Dict[str, Any]:
        """
        获取日志统计信息
        
        返回:
            统计信息字典
            
        需求: 2.4 - 记录切换事件
        """
        with self._锁:
            return self._计算统计信息_无锁()
    
    def 导出日志(self, 
                文件路径: str,
                格式: str = "json",
                触发方式: str = None,
                开始时间: float = None,
                结束时间: float = None) -> bool:
        """
        导出日志到文件
        
        参数:
            文件路径: 导出文件路径
            格式: 导出格式（"json", "csv", "txt"）
            触发方式: 过滤触发方式
            开始时间: 开始时间戳
            结束时间: 结束时间戳
            
        返回:
            是否导出成功
            
        需求: 2.4 - 记录切换事件
        """
        try:
            # 获取过滤后的日志
            日志数据 = self.获取日志(
                数量=self._最大内存日志数,
                触发方式=触发方式,
                开始时间=开始时间,
                结束时间=结束时间
            )
            
            # 反转顺序（按时间正序）
            日志数据 = list(reversed(日志数据))
            
            if 格式.lower() == "json":
                return self._导出为JSON(文件路径, 日志数据)
            elif 格式.lower() == "csv":
                return self._导出为CSV(文件路径, 日志数据)
            elif 格式.lower() == "txt":
                return self._导出为TXT(文件路径, 日志数据)
            else:
                日志.error(f"不支持的导出格式: {格式}")
                return False
                
        except Exception as e:
            日志.error(f"导出日志失败: {e}")
            return False
    
    def _导出为JSON(self, 文件路径: str, 日志数据: List[Dict]) -> bool:
        """导出为 JSON 格式"""
        try:
            with open(文件路径, 'w', encoding='utf-8') as f:
                json.dump({
                    "导出时间": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "日志数量": len(日志数据),
                    "日志列表": 日志数据
                }, f, ensure_ascii=False, indent=2)
            日志.info(f"日志已导出为 JSON: {文件路径}")
            return True
        except Exception as e:
            日志.error(f"导出 JSON 失败: {e}")
            return False
    
    def _导出为CSV(self, 文件路径: str, 日志数据: List[Dict]) -> bool:
        """导出为 CSV 格式"""
        try:
            import csv
            
            if not 日志数据:
                日志.warning("没有日志数据可导出")
                return False
            
            字段名 = ["时间", "原模型", "新模型", "触发方式", "触发原因", "切换耗时", "切换成功"]
            
            with open(文件路径, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=字段名, extrasaction='ignore')
                writer.writeheader()
                for 记录 in 日志数据:
                    writer.writerow(记录)
            
            日志.info(f"日志已导出为 CSV: {文件路径}")
            return True
        except Exception as e:
            日志.error(f"导出 CSV 失败: {e}")
            return False
    
    def _导出为TXT(self, 文件路径: str, 日志数据: List[Dict]) -> bool:
        """导出为 TXT 格式"""
        try:
            with open(文件路径, 'w', encoding='utf-8') as f:
                f.write(f"模型切换日志导出\n")
                f.write(f"导出时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"日志数量: {len(日志数据)}\n")
                f.write("=" * 80 + "\n\n")
                
                for 记录 in 日志数据:
                    状态 = "成功" if 记录.get("切换成功", True) else "失败"
                    f.write(
                        f"[{记录.get('时间', '')}] [{记录.get('触发方式', '')}] "
                        f"{记录.get('原模型', '')} -> {记录.get('新模型', '')} "
                        f"({状态}, {记录.get('切换耗时', 0):.2f}ms)\n"
                        f"  原因: {记录.get('触发原因', '')}\n\n"
                    )
            
            日志.info(f"日志已导出为 TXT: {文件路径}")
            return True
        except Exception as e:
            日志.error(f"导出 TXT 失败: {e}")
            return False
    
    def 清空日志(self) -> None:
        """清空内存中的日志"""
        with self._锁:
            self._日志列表.clear()
            日志.info("切换事件日志已清空")
    
    def 从文件加载日志(self, 文件路径: str = None) -> int:
        """
        从文件加载日志到内存
        
        参数:
            文件路径: 日志文件路径，默认使用当前日期的日志文件
            
        返回:
            加载的日志数量
        """
        if 文件路径 is None:
            文件路径 = self._获取当前日志文件路径()
        
        if not os.path.exists(文件路径):
            日志.warning(f"日志文件不存在: {文件路径}")
            return 0
        
        加载数 = 0
        
        try:
            with open(文件路径, 'r', encoding='utf-8') as f:
                for 行 in f:
                    行 = 行.strip()
                    if not 行:
                        continue
                    
                    # 解析日志行
                    事件 = self._解析日志行(行)
                    if 事件:
                        with self._锁:
                            self._日志列表.append(事件)
                            加载数 += 1
            
            日志.info(f"从文件加载了 {加载数} 条日志: {文件路径}")
            return 加载数
            
        except Exception as e:
            日志.error(f"加载日志文件失败: {e}")
            return 0
    
    def _解析日志行(self, 行: str) -> Optional[切换事件]:
        """
        解析日志行
        
        参数:
            行: 日志行字符串
            
        返回:
            切换事件实例，解析失败返回 None
        """
        try:
            # 格式: [时间] [触发方式] 原模型 -> 新模型 (状态, 耗时ms) - 原因
            import re
            
            模式 = r'\[(.+?)\] \[(.+?)\] (.+?) -> (.+?) \((.+?), ([\d.]+)ms\) - (.+)'
            匹配 = re.match(模式, 行)
            
            if not 匹配:
                return None
            
            时间字符串, 触发方式, 原模型, 新模型, 状态, 耗时, 原因 = 匹配.groups()
            
            # 解析时间
            try:
                时间戳 = time.mktime(time.strptime(时间字符串, "%Y-%m-%d %H:%M:%S"))
            except:
                时间戳 = time.time()
            
            return 切换事件(
                时间戳=时间戳,
                原模型=原模型,
                新模型=新模型,
                触发方式=触发方式,
                触发原因=原因,
                切换耗时=float(耗时),
                切换成功=(状态 == "成功")
            )
            
        except Exception as e:
            日志.debug(f"解析日志行失败: {e}")
            return None
    
    def 获取日志文件列表(self) -> List[str]:
        """
        获取所有日志文件列表
        
        返回:
            日志文件路径列表
        """
        if not os.path.exists(self._日志目录):
            return []
        
        文件列表 = []
        for 文件名 in os.listdir(self._日志目录):
            if 文件名.startswith(self.默认日志文件前缀) and 文件名.endswith(".log"):
                文件列表.append(os.path.join(self._日志目录, 文件名))
        
        return sorted(文件列表)
    
    def 设置启用文件日志(self, 启用: bool) -> None:
        """设置是否启用文件日志"""
        self._启用文件日志 = 启用
        日志.info(f"文件日志已{'启用' if 启用 else '禁用'}")
    
    def 获取状态(self) -> Dict[str, Any]:
        """获取日志管理器状态"""
        with self._锁:
            内存日志数量 = len(self._日志列表)
            统计 = self._计算统计信息_无锁()
        
        return {
            "内存日志数量": 内存日志数量,
            "最大内存日志数": self._最大内存日志数,
            "启用文件日志": self._启用文件日志,
            "日志目录": self._日志目录,
            "当前日志文件": self._当前日志文件,
            "统计信息": 统计
        }


def 创建切换事件日志管理器(
    模型管理器实例: 模型管理器,
    日志目录: str = None,
    启用文件日志: bool = True
) -> 切换事件日志管理器:
    """
    创建切换事件日志管理器实例
    
    参数:
        模型管理器实例: 模型管理器实例
        日志目录: 日志文件保存目录
        启用文件日志: 是否启用文件日志
        
    返回:
        切换事件日志管理器实例
        
    需求: 2.4 - 记录切换事件
    """
    return 切换事件日志管理器(模型管理器实例, 日志目录, 启用文件日志)
