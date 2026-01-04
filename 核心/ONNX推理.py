"""
ONNX 推理引擎模块
使用 ONNX Runtime 进行高性能模型推理

功能:
- ONNX 模型加载和推理
- GPU/CPU 自动选择（支持 CUDA、DirectML）
- 性能统计和延迟监控
- 与 TFLearn 后端的统一接口

需求: 2.1, 2.2, 2.3, 2.4, 2.5
"""

import os
import time
import logging
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field
from collections import deque
from enum import Enum

import numpy as np

# 配置日志
logging.basicConfig(level=logging.INFO)
日志 = logging.getLogger(__name__)


class 推理后端类型(Enum):
    """推理后端类型枚举"""
    CPU = "CPU"
    CUDA = "CUDA"
    DirectML = "DirectML"
    TensorRT = "TensorRT"
    OpenVINO = "OpenVINO"
    UNKNOWN = "unknown"


@dataclass
class 推理配置:
    """推理配置
    
    需求: 2.1 - 推理引擎配置
    """
    模型路径: str
    使用GPU: bool = True
    输入宽度: int = 480
    输入高度: int = 270
    预热次数: int = 10
    统计窗口: int = 100  # 统计最近N次推理的延迟
    最大延迟阈值: float = 50.0  # 最大允许延迟（毫秒），需求 2.2


@dataclass
class 性能指标:
    """性能指标
    
    需求: 3.1, 3.2 - 性能基准测试
    """
    平均延迟: float = 0.0  # 毫秒
    最小延迟: float = 0.0
    最大延迟: float = 0.0
    推理次数: int = 0
    后端类型: str = ""
    P95延迟: float = 0.0  # 95分位延迟
    P99延迟: float = 0.0  # 99分位延迟
    满足延迟要求: bool = True  # 是否满足 50ms 延迟要求


class ONNX推理引擎:
    """使用 ONNX Runtime 进行模型推理
    
    需求: 2.1 - 加载 ONNX 模型并初始化推理会话
    需求: 2.3 - CUDA 可用时支持 GPU 加速
    需求: 2.4 - GPU 不可用时回退到 CPU 推理
    """
    
    def __init__(self, 模型路径: str, 使用GPU: bool = True, 预热: bool = True,
                 输入宽度: int = None, 输入高度: int = None):
        """
        初始化推理引擎
        
        参数:
            模型路径: ONNX 模型文件路径
            使用GPU: 是否使用 GPU 加速
            预热: 是否进行预热推理
            输入宽度: 输入图像宽度（可选，从模型自动获取）
            输入高度: 输入图像高度（可选，从模型自动获取）
            
        需求: 2.1 - 加载 ONNX 模型并初始化推理会话
        """
        self.模型路径 = 模型路径
        self.使用GPU = 使用GPU
        self.会话: Optional[Any] = None
        self.输入名称: str = ""
        self.输出名称: str = ""
        self.输入形状: Tuple = ()
        self.后端类型: str = "CPU"
        self._可用提供者: List[str] = []
        
        # 输入尺寸配置
        self._配置输入宽度 = 输入宽度
        self._配置输入高度 = 输入高度
        
        # 性能统计
        self._延迟记录: deque = deque(maxlen=100)
        self._推理次数: int = 0
        self._最大延迟阈值: float = 50.0  # 需求 2.2: 50ms 内返回
        
        # 初始化状态
        self._已初始化: bool = False
        self._初始化错误: Optional[str] = None
        
        # 初始化
        self._初始化引擎()
        
        if 预热 and self._已初始化:
            self._预热()
    
    def _初始化引擎(self):
        """初始化 ONNX Runtime 会话
        
        需求: 2.1 - 加载 ONNX 模型并初始化推理会话
        需求: 2.3 - CUDA 可用时支持 GPU 加速
        需求: 2.4 - GPU 不可用时回退到 CPU 推理
        """
        try:
            import onnxruntime as ort
            
            # 获取可用的执行提供者
            self._可用提供者 = ort.get_available_providers()
            日志.info(f"可用的执行提供者: {self._可用提供者}")
            
            # 配置执行提供者（按优先级排序）
            providers = []
            
            if self.使用GPU:
                # 需求 2.3: CUDA 可用时支持 GPU 加速
                if 'CUDAExecutionProvider' in self._可用提供者:
                    providers.append(('CUDAExecutionProvider', {
                        'device_id': 0,
                        'arena_extend_strategy': 'kNextPowerOfTwo',
                        'gpu_mem_limit': 2 * 1024 * 1024 * 1024,  # 2GB
                        'cudnn_conv_algo_search': 'EXHAUSTIVE',
                    }))
                    self.后端类型 = "CUDA"
                    日志.info("使用 CUDA GPU 加速")
                
                # 尝试使用 TensorRT（如果可用）
                elif 'TensorrtExecutionProvider' in self._可用提供者:
                    providers.append('TensorrtExecutionProvider')
                    self.后端类型 = "TensorRT"
                    日志.info("使用 TensorRT GPU 加速")
                
                # 尝试使用 DirectML (Windows)
                elif 'DmlExecutionProvider' in self._可用提供者:
                    providers.append('DmlExecutionProvider')
                    self.后端类型 = "DirectML"
                    日志.info("使用 DirectML GPU 加速")
                
                # 尝试使用 OpenVINO
                elif 'OpenVINOExecutionProvider' in self._可用提供者:
                    providers.append('OpenVINOExecutionProvider')
                    self.后端类型 = "OpenVINO"
                    日志.info("使用 OpenVINO 加速")
                
                else:
                    # 需求 2.4: GPU 不可用时回退到 CPU 推理
                    日志.warning("GPU 不可用，回退到 CPU 推理")
                    self.后端类型 = "CPU"
            
            # 添加 CPU 作为后备
            providers.append('CPUExecutionProvider')
            if self.后端类型 == "CPU":
                日志.info("使用 CPU 推理")
            
            # 创建会话选项
            会话选项 = ort.SessionOptions()
            会话选项.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            会话选项.intra_op_num_threads = 0  # 自动选择线程数
            会话选项.inter_op_num_threads = 0
            
            # 启用内存优化
            会话选项.enable_mem_pattern = True
            会话选项.enable_cpu_mem_arena = True
            
            # 创建推理会话
            self.会话 = ort.InferenceSession(
                self.模型路径,
                sess_options=会话选项,
                providers=providers
            )
            
            # 获取输入输出信息
            输入信息 = self.会话.get_inputs()[0]
            self.输入名称 = 输入信息.name
            self.输入形状 = tuple(输入信息.shape)
            
            输出信息 = self.会话.get_outputs()[0]
            self.输出名称 = 输出信息.name
            
            # 验证实际使用的提供者
            实际提供者 = self.会话.get_providers()
            日志.info(f"实际使用的提供者: {实际提供者}")
            
            self._已初始化 = True
            日志.info(f"ONNX 模型加载成功: {self.模型路径}")
            日志.info(f"输入形状: {self.输入形状}, 输入名称: {self.输入名称}")
            
        except ImportError as e:
            self._初始化错误 = "onnxruntime 未安装"
            日志.error(self._初始化错误)
            日志.info("安装命令: pip install onnxruntime 或 pip install onnxruntime-gpu")
            raise ImportError(self._初始化错误) from e
        except FileNotFoundError as e:
            self._初始化错误 = f"模型文件不存在: {self.模型路径}"
            日志.error(self._初始化错误)
            raise FileNotFoundError(self._初始化错误) from e
        except Exception as e:
            self._初始化错误 = f"初始化 ONNX 引擎失败: {e}"
            日志.error(self._初始化错误)
            raise RuntimeError(self._初始化错误) from e
    
    def _预热(self, 次数: int = 10):
        """预热推理引擎
        
        预热可以让 GPU 内存分配和 JIT 编译提前完成，
        避免首次推理时的延迟波动。
        """
        日志.info(f"预热推理引擎 ({次数} 次)...")
        
        # 创建虚拟输入
        if len(self.输入形状) == 4:
            batch, w, h, c = self.输入形状
            # 处理动态维度
            batch = 1 if batch == -1 or isinstance(batch, str) else batch
            w = self._配置输入宽度 or (w if isinstance(w, int) and w > 0 else 480)
            h = self._配置输入高度 or (h if isinstance(h, int) and h > 0 else 270)
            c = c if isinstance(c, int) and c > 0 else 3
            虚拟输入 = np.random.rand(batch, w, h, c).astype(np.float32)
        else:
            # 处理其他形状
            形状 = []
            for dim in self.输入形状:
                if isinstance(dim, int) and dim > 0:
                    形状.append(dim)
                else:
                    形状.append(1)  # 动态维度使用 1
            虚拟输入 = np.random.rand(*形状).astype(np.float32)
        
        for _ in range(次数):
            self._执行推理(虚拟输入)
        
        # 清空预热期间的统计
        self._延迟记录.clear()
        self._推理次数 = 0
        
        日志.info("预热完成")
    
    def _执行推理(self, 输入数据: np.ndarray) -> np.ndarray:
        """执行推理并记录延迟"""
        开始时间 = time.perf_counter()
        
        结果 = self.会话.run(
            [self.输出名称],
            {self.输入名称: 输入数据}
        )[0]
        
        延迟 = (time.perf_counter() - 开始时间) * 1000  # 转换为毫秒
        self._延迟记录.append(延迟)
        self._推理次数 += 1
        
        return 结果
    
    def 预测(self, 图像: np.ndarray) -> List[float]:
        """
        执行推理预测
        
        参数:
            图像: 输入图像，形状为 (width, height, 3) 或 (batch, width, height, 3)
            
        返回:
            动作概率列表
            
        需求: 2.2 - 50ms 内返回动作预测
        需求: 2.5 - 提供与原始 TFLearn 模型相同的输出格式
        """
        if self.会话 is None:
            raise RuntimeError("推理引擎未初始化")
        
        if not self._已初始化:
            raise RuntimeError(f"推理引擎初始化失败: {self._初始化错误}")
        
        # 预处理输入
        输入数据 = self._预处理(图像)
        
        # 执行推理
        输出 = self._执行推理(输入数据)
        
        # 后处理输出（需求 2.5: 与 TFLearn 相同的输出格式）
        return self._后处理(输出)
    
    def _预处理(self, 图像: np.ndarray) -> np.ndarray:
        """预处理输入图像
        
        将输入图像转换为模型所需的格式：
        - 转换为 float32
        - 归一化到 0-1 范围
        - 添加 batch 维度
        
        需求: 2.2 - 图像预处理
        """
        # 确保是 float32
        if 图像.dtype != np.float32:
            图像 = 图像.astype(np.float32)
        
        # 归一化到 0-1（如果需要）
        if 图像.max() > 1.0:
            图像 = 图像 / 255.0
        
        # 添加 batch 维度
        if len(图像.shape) == 3:
            图像 = np.expand_dims(图像, axis=0)
        
        return 图像
    
    def _后处理(self, 输出: np.ndarray) -> List[float]:
        """后处理输出
        
        将模型输出转换为动作概率列表，
        与 TFLearn 模型的输出格式保持一致。
        
        需求: 2.5 - 提供与原始 TFLearn 模型相同的输出格式
        """
        # 移除 batch 维度
        if len(输出.shape) > 1:
            输出 = 输出[0]
        
        return 输出.tolist()
    
    def 获取延迟统计(self) -> 性能指标:
        """获取推理延迟统计信息
        
        需求: 3.1 - 测量推理延迟
        需求: 3.2 - 报告平均、最小和最大延迟
        """
        if not self._延迟记录:
            return 性能指标(后端类型=self.后端类型)
        
        延迟列表 = list(self._延迟记录)
        平均延迟 = float(np.mean(延迟列表))
        
        return 性能指标(
            平均延迟=平均延迟,
            最小延迟=float(np.min(延迟列表)),
            最大延迟=float(np.max(延迟列表)),
            推理次数=self._推理次数,
            后端类型=self.后端类型,
            P95延迟=float(np.percentile(延迟列表, 95)) if len(延迟列表) >= 20 else 0.0,
            P99延迟=float(np.percentile(延迟列表, 99)) if len(延迟列表) >= 100 else 0.0,
            满足延迟要求=平均延迟 < self._最大延迟阈值
        )
    
    def 检查延迟要求(self) -> bool:
        """检查是否满足延迟要求（50ms）
        
        需求: 2.2 - 50ms 内返回动作预测
        """
        统计 = self.获取延迟统计()
        return 统计.满足延迟要求
    
    def 获取可用提供者(self) -> List[str]:
        """获取可用的执行提供者列表"""
        return self._可用提供者.copy()
    
    def 是否已初始化(self) -> bool:
        """检查引擎是否已成功初始化"""
        return self._已初始化
    
    def 打印统计(self):
        """打印性能统计"""
        统计 = self.获取延迟统计()
        print(f"\n推理性能统计 ({统计.后端类型}):")
        print(f"  推理次数: {统计.推理次数}")
        print(f"  平均延迟: {统计.平均延迟:.2f} ms")
        print(f"  最小延迟: {统计.最小延迟:.2f} ms")
        print(f"  最大延迟: {统计.最大延迟:.2f} ms")
        if 统计.P95延迟 > 0:
            print(f"  P95 延迟: {统计.P95延迟:.2f} ms")
        if 统计.P99延迟 > 0:
            print(f"  P99 延迟: {统计.P99延迟:.2f} ms")
        print(f"  满足延迟要求 (<50ms): {'是' if 统计.满足延迟要求 else '否'}")


class 统一推理引擎:
    """统一的推理接口，自动选择后端
    
    需求: 4.1 - 自动检测模型格式（TFLearn 或 ONNX）
    需求: 4.2 - 加载旧格式模型时使用原始 TFLearn 推理
    需求: 4.3 - 加载新格式模型时使用 ONNX Runtime 推理
    需求: 4.4 - 提供配置选项来选择首选的推理后端
    """
    
    # 支持的后端类型
    后端_自动 = "auto"
    后端_ONNX = "onnx"
    后端_TFLearn = "tflearn"
    
    # 支持的模型格式
    格式_ONNX = "onnx"
    格式_TFLearn = "tflearn"
    格式_TensorFlow = "tensorflow"
    格式_SavedModel = "savedmodel"
    格式_未知 = "unknown"
    
    def __init__(self, 模型路径: str = None, 首选后端: str = "auto", 
                 使用GPU: bool = True, 配置: Dict[str, Any] = None):
        """
        初始化统一推理引擎
        
        参数:
            模型路径: 模型文件路径，如果为 None 则从配置加载
            首选后端: "auto"（自动检测）, "onnx", "tflearn"
            使用GPU: 是否使用 GPU 加速
            配置: 可选的配置字典，用于覆盖默认设置
            
        需求: 4.1 - 自动检测模型格式
        需求: 4.4 - 提供配置选项来选择首选的推理后端
        """
        # 加载配置
        self._配置 = self._加载配置(配置)
        
        # 设置模型路径
        if 模型路径 is None:
            模型路径 = self._配置.get("模型路径", "")
        self.模型路径 = 模型路径
        
        # 设置首选后端（配置优先）
        配置后端 = self._配置.get("首选后端", 首选后端)
        self.首选后端 = 配置后端 if 配置后端 else 首选后端
        
        # GPU 设置
        self.使用GPU = self._配置.get("使用GPU", 使用GPU)
        
        # 状态变量
        self.当前后端: str = ""
        self.检测到的格式: str = ""
        self._引擎: Any = None
        self._已初始化: bool = False
        self._初始化错误: Optional[str] = None
        
        # 如果提供了模型路径，则初始化
        if self.模型路径:
            self._初始化()
    
    def _加载配置(self, 配置: Dict[str, Any] = None) -> Dict[str, Any]:
        """加载推理配置
        
        从配置文件或传入的配置字典加载设置。
        
        需求: 4.4 - 支持配置文件设置
        """
        默认配置 = {
            "模型路径": "",
            "首选后端": "auto",
            "使用GPU": True,
            "输入宽度": 480,
            "输入高度": 270,
            "预热次数": 10,
        }
        
        # 尝试从配置文件加载
        配置文件路径 = "配置/推理配置.json"
        if os.path.exists(配置文件路径):
            try:
                import json
                with open(配置文件路径, 'r', encoding='utf-8') as f:
                    文件配置 = json.load(f)
                    默认配置.update(文件配置)
                日志.info(f"已从配置文件加载推理配置: {配置文件路径}")
            except Exception as e:
                日志.warning(f"加载推理配置文件失败: {e}")
        
        # 传入的配置覆盖文件配置
        if 配置:
            默认配置.update(配置)
        
        return 默认配置
    
    def 保存配置(self, 配置文件路径: str = None) -> bool:
        """保存当前配置到文件
        
        需求: 4.4 - 支持配置文件设置
        """
        if 配置文件路径 is None:
            配置文件路径 = "配置/推理配置.json"
        
        try:
            import json
            
            # 确保目录存在
            目录 = os.path.dirname(配置文件路径)
            if 目录 and not os.path.exists(目录):
                os.makedirs(目录)
            
            配置数据 = {
                "模型路径": self.模型路径,
                "首选后端": self.首选后端,
                "使用GPU": self.使用GPU,
                "输入宽度": self._配置.get("输入宽度", 480),
                "输入高度": self._配置.get("输入高度", 270),
                "预热次数": self._配置.get("预热次数", 10),
            }
            
            with open(配置文件路径, 'w', encoding='utf-8') as f:
                json.dump(配置数据, f, ensure_ascii=False, indent=2)
            
            日志.info(f"推理配置已保存到: {配置文件路径}")
            return True
        except Exception as e:
            日志.error(f"保存推理配置失败: {e}")
            return False
    
    def 检测模型格式(self, 模型路径: str = None) -> str:
        """检测模型文件格式
        
        需求: 4.1 - 自动检测模型格式（TFLearn 或 ONNX）
        
        参数:
            模型路径: 模型文件路径，如果为 None 则使用实例的模型路径
            
        返回:
            模型格式字符串: "onnx", "tflearn", "tensorflow", "savedmodel", "unknown"
        """
        路径 = 模型路径 or self.模型路径
        
        if not 路径:
            return self.格式_未知
        
        # 检查 ONNX 格式
        if 路径.endswith('.onnx'):
            if os.path.exists(路径):
                return self.格式_ONNX
            return self.格式_未知
        
        # 检查 TensorFlow frozen graph
        if 路径.endswith('.pb'):
            if os.path.exists(路径):
                return self.格式_TensorFlow
            return self.格式_未知
        
        # 检查 TFLearn checkpoint 格式
        # TFLearn 模型通常有 .index, .data-00000-of-00001, .meta 文件
        if os.path.exists(路径 + '.index'):
            return self.格式_TFLearn
        
        # 检查是否是目录（可能是 SavedModel）
        if os.path.isdir(路径):
            if os.path.exists(os.path.join(路径, 'saved_model.pb')):
                return self.格式_SavedModel
        
        # 尝试查找对应的 ONNX 文件
        可能的onnx路径 = 路径.rsplit('.', 1)[0] + '.onnx' if '.' in 路径 else 路径 + '.onnx'
        if os.path.exists(可能的onnx路径):
            return self.格式_ONNX
        
        return self.格式_未知
    
    def _初始化(self):
        """初始化推理引擎
        
        需求: 4.1 - 自动检测模型格式
        需求: 4.2 - 加载旧格式模型时使用原始 TFLearn 推理
        需求: 4.3 - 加载新格式模型时使用 ONNX Runtime 推理
        """
        # 检测模型格式
        self.检测到的格式 = self.检测模型格式()
        日志.info(f"检测到模型格式: {self.检测到的格式}")
        
        # 根据首选后端和模型格式选择引擎
        初始化成功 = False
        
        if self.首选后端 == self.后端_ONNX:
            # 用户明确指定 ONNX
            初始化成功 = self._尝试初始化ONNX()
            if not 初始化成功:
                日志.warning("ONNX 后端初始化失败，尝试 TFLearn 后端")
                初始化成功 = self._尝试初始化TFLearn()
        
        elif self.首选后端 == self.后端_TFLearn:
            # 用户明确指定 TFLearn
            初始化成功 = self._尝试初始化TFLearn()
            if not 初始化成功:
                日志.warning("TFLearn 后端初始化失败，尝试 ONNX 后端")
                初始化成功 = self._尝试初始化ONNX()
        
        else:  # auto 模式
            # 需求: 4.1, 4.2, 4.3 - 根据格式自动选择
            if self.检测到的格式 == self.格式_ONNX:
                # 需求: 4.3 - 加载新格式模型时使用 ONNX Runtime 推理
                初始化成功 = self._尝试初始化ONNX()
                if not 初始化成功:
                    初始化成功 = self._尝试初始化TFLearn()
            elif self.检测到的格式 == self.格式_TFLearn:
                # 需求: 4.2 - 加载旧格式模型时使用原始 TFLearn 推理
                初始化成功 = self._尝试初始化TFLearn()
                if not 初始化成功:
                    初始化成功 = self._尝试初始化ONNX()
            else:
                # 未知格式，尝试两种后端
                初始化成功 = self._尝试初始化ONNX() or self._尝试初始化TFLearn()
        
        if not 初始化成功:
            self._初始化错误 = f"无法初始化推理引擎，模型路径: {self.模型路径}"
            日志.error(self._初始化错误)
            raise RuntimeError(self._初始化错误)
        
        self._已初始化 = True
        日志.info(f"统一推理引擎初始化成功，使用后端: {self.当前后端}")
    
    def _尝试初始化ONNX(self) -> bool:
        """尝试初始化 ONNX 引擎
        
        需求: 4.3 - 加载新格式模型时使用 ONNX Runtime 推理
        
        返回:
            是否初始化成功
        """
        onnx路径 = self.模型路径
        
        # 如果不是 .onnx 文件，尝试查找对应的 ONNX 文件
        if not onnx路径.endswith('.onnx'):
            可能路径 = onnx路径.rsplit('.', 1)[0] + '.onnx' if '.' in onnx路径 else onnx路径 + '.onnx'
            if os.path.exists(可能路径):
                onnx路径 = 可能路径
            else:
                日志.info("未找到 ONNX 模型文件")
                return False
        
        if not os.path.exists(onnx路径):
            日志.info(f"ONNX 模型文件不存在: {onnx路径}")
            return False
        
        try:
            self._引擎 = ONNX推理引擎(
                onnx路径, 
                使用GPU=self.使用GPU,
                输入宽度=self._配置.get("输入宽度"),
                输入高度=self._配置.get("输入高度")
            )
            self.当前后端 = self.后端_ONNX
            日志.info(f"已初始化 ONNX 推理引擎: {onnx路径}")
            return True
        except Exception as e:
            日志.warning(f"ONNX 引擎初始化失败: {e}")
            return False
    
    def _尝试初始化TFLearn(self) -> bool:
        """尝试初始化 TFLearn 引擎
        
        需求: 4.2 - 加载旧格式模型时使用原始 TFLearn 推理
        
        返回:
            是否初始化成功
        """
        try:
            from 核心.模型定义 import inception_v3
            from 配置.设置 import 模型输入宽度, 模型输入高度, 学习率, 总动作数
            
            # 使用配置中的尺寸或默认值
            输入宽度 = self._配置.get("输入宽度") or 模型输入宽度
            输入高度 = self._配置.get("输入高度") or 模型输入高度
            
            # 创建模型
            模型 = inception_v3(
                输入宽度,
                输入高度,
                3,
                学习率,
                输出类别=总动作数,
                模型名称=self.模型路径
            )
            
            # 加载权重
            模型.load(self.模型路径)
            
            self._引擎 = TFLearn推理包装器(模型)
            self.当前后端 = self.后端_TFLearn
            日志.info(f"已初始化 TFLearn 推理引擎: {self.模型路径}")
            return True
            
        except ImportError as e:
            日志.warning(f"TFLearn 模块导入失败: {e}")
            return False
        except Exception as e:
            日志.warning(f"TFLearn 引擎初始化失败: {e}")
            return False
    
    def 加载模型(self, 模型路径: str, 首选后端: str = None) -> bool:
        """加载新模型
        
        允许在运行时切换模型。
        
        参数:
            模型路径: 新模型的路径
            首选后端: 可选，指定首选后端
            
        返回:
            是否加载成功
        """
        self.模型路径 = 模型路径
        if 首选后端:
            self.首选后端 = 首选后端
        
        self._引擎 = None
        self._已初始化 = False
        self._初始化错误 = None
        
        try:
            self._初始化()
            return True
        except Exception as e:
            日志.error(f"加载模型失败: {e}")
            return False
    
    def 预测(self, 图像: np.ndarray) -> List[float]:
        """
        执行推理预测
        
        参数:
            图像: 输入图像
            
        返回:
            动作概率列表
            
        需求: 2.5 - 提供与原始 TFLearn 模型相同的输出格式
        """
        if self._引擎 is None:
            raise RuntimeError("推理引擎未初始化")
        
        if not self._已初始化:
            raise RuntimeError(f"推理引擎初始化失败: {self._初始化错误}")
        
        return self._引擎.预测(图像)
    
    def 获取当前后端(self) -> str:
        """获取当前使用的推理后端
        
        返回:
            当前后端名称: "onnx", "tflearn", 或空字符串
        """
        return self.当前后端
    
    def 获取检测到的格式(self) -> str:
        """获取检测到的模型格式
        
        返回:
            模型格式: "onnx", "tflearn", "tensorflow", "savedmodel", "unknown"
        """
        return self.检测到的格式
    
    def 获取延迟统计(self) -> 性能指标:
        """获取推理延迟统计
        
        需求: 3.1 - 测量推理延迟
        """
        if hasattr(self._引擎, '获取延迟统计'):
            return self._引擎.获取延迟统计()
        return 性能指标(后端类型=self.当前后端)
    
    def 是否已初始化(self) -> bool:
        """检查引擎是否已成功初始化"""
        return self._已初始化
    
    def 获取状态信息(self) -> Dict[str, Any]:
        """获取引擎状态信息
        
        返回:
            包含引擎状态的字典
        """
        return {
            "已初始化": self._已初始化,
            "模型路径": self.模型路径,
            "检测到的格式": self.检测到的格式,
            "当前后端": self.当前后端,
            "首选后端": self.首选后端,
            "使用GPU": self.使用GPU,
            "初始化错误": self._初始化错误,
        }
    
    def 设置首选后端(self, 后端: str) -> None:
        """设置首选后端
        
        需求: 4.4 - 提供配置选项来选择首选的推理后端
        
        参数:
            后端: "auto", "onnx", "tflearn"
        """
        if 后端 not in [self.后端_自动, self.后端_ONNX, self.后端_TFLearn]:
            raise ValueError(f"无效的后端类型: {后端}，支持: auto, onnx, tflearn")
        
        self.首选后端 = 后端
        日志.info(f"首选后端已设置为: {后端}")
    
    def 打印状态(self):
        """打印引擎状态信息"""
        状态 = self.获取状态信息()
        print(f"\n统一推理引擎状态:")
        print(f"  已初始化: {'是' if 状态['已初始化'] else '否'}")
        print(f"  模型路径: {状态['模型路径']}")
        print(f"  检测到的格式: {状态['检测到的格式']}")
        print(f"  当前后端: {状态['当前后端']}")
        print(f"  首选后端: {状态['首选后端']}")
        print(f"  使用GPU: {'是' if 状态['使用GPU'] else '否'}")
        if 状态['初始化错误']:
            print(f"  初始化错误: {状态['初始化错误']}")


class TFLearn推理包装器:
    """TFLearn 模型的推理包装器"""
    
    def __init__(self, 模型):
        self.模型 = 模型
        self._延迟记录: deque = deque(maxlen=100)
        self._推理次数: int = 0
    
    def 预测(self, 图像: np.ndarray) -> List[float]:
        """执行预测"""
        开始时间 = time.perf_counter()
        
        # 预处理
        if len(图像.shape) == 3:
            图像 = np.expand_dims(图像, axis=0)
        
        结果 = self.模型.predict(图像)
        
        延迟 = (time.perf_counter() - 开始时间) * 1000
        self._延迟记录.append(延迟)
        self._推理次数 += 1
        
        return 结果[0].tolist() if len(结果.shape) > 1 else 结果.tolist()
    
    def 获取延迟统计(self) -> 性能指标:
        """获取延迟统计"""
        if not self._延迟记录:
            return 性能指标(后端类型="TFLearn")
        
        延迟列表 = list(self._延迟记录)
        return 性能指标(
            平均延迟=np.mean(延迟列表),
            最小延迟=np.min(延迟列表),
            最大延迟=np.max(延迟列表),
            推理次数=self._推理次数,
            后端类型="TFLearn"
        )


def 基准测试(引擎, 测试次数: int = 100, 输入形状: Tuple = (480, 270, 3)):
    """
    运行推理基准测试
    
    参数:
        引擎: 推理引擎实例
        测试次数: 测试次数
        输入形状: 输入图像形状
    """
    print(f"\n运行基准测试 ({测试次数} 次)...")
    
    # 生成随机测试数据
    测试数据 = np.random.rand(*输入形状).astype(np.float32)
    
    延迟列表 = []
    
    for i in range(测试次数):
        开始 = time.perf_counter()
        引擎.预测(测试数据)
        延迟 = (time.perf_counter() - 开始) * 1000
        延迟列表.append(延迟)
        
        if (i + 1) % 20 == 0:
            print(f"  进度: {i + 1}/{测试次数}")
    
    # 统计结果
    print(f"\n基准测试结果:")
    print(f"  测试次数: {测试次数}")
    print(f"  平均延迟: {np.mean(延迟列表):.2f} ms")
    print(f"  最小延迟: {np.min(延迟列表):.2f} ms")
    print(f"  最大延迟: {np.max(延迟列表):.2f} ms")
    print(f"  标准差: {np.std(延迟列表):.2f} ms")
    print(f"  P95 延迟: {np.percentile(延迟列表, 95):.2f} ms")
    print(f"  P99 延迟: {np.percentile(延迟列表, 99):.2f} ms")
    print(f"  理论 FPS: {1000 / np.mean(延迟列表):.1f}")
