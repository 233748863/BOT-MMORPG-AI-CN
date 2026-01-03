"""
ONNX 推理引擎模块
使用 ONNX Runtime 进行高性能模型推理

功能:
- ONNX 模型加载和推理
- GPU/CPU 自动选择
- 性能统计
"""

import os
import time
import logging
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field
from collections import deque

import numpy as np

# 配置日志
logging.basicConfig(level=logging.INFO)
日志 = logging.getLogger(__name__)


@dataclass
class 推理配置:
    """推理配置"""
    模型路径: str
    使用GPU: bool = True
    输入宽度: int = 480
    输入高度: int = 270
    预热次数: int = 10
    统计窗口: int = 100  # 统计最近N次推理的延迟


@dataclass
class 性能指标:
    """性能指标"""
    平均延迟: float = 0.0  # 毫秒
    最小延迟: float = 0.0
    最大延迟: float = 0.0
    推理次数: int = 0
    后端类型: str = ""


class ONNX推理引擎:
    """使用 ONNX Runtime 进行模型推理"""
    
    def __init__(self, 模型路径: str, 使用GPU: bool = True, 预热: bool = True):
        """
        初始化推理引擎
        
        参数:
            模型路径: ONNX 模型文件路径
            使用GPU: 是否使用 GPU 加速
            预热: 是否进行预热推理
        """
        self.模型路径 = 模型路径
        self.使用GPU = 使用GPU
        self.会话: Optional[Any] = None
        self.输入名称: str = ""
        self.输出名称: str = ""
        self.输入形状: Tuple = ()
        self.后端类型: str = "CPU"
        
        # 性能统计
        self._延迟记录: deque = deque(maxlen=100)
        self._推理次数: int = 0
        
        # 初始化
        self._初始化引擎()
        
        if 预热:
            self._预热()
    
    def _初始化引擎(self):
        """初始化 ONNX Runtime 会话"""
        try:
            import onnxruntime as ort
            
            # 配置执行提供者
            providers = []
            
            if self.使用GPU:
                # 尝试使用 CUDA
                if 'CUDAExecutionProvider' in ort.get_available_providers():
                    providers.append('CUDAExecutionProvider')
                    self.后端类型 = "CUDA"
                    日志.info("使用 CUDA GPU 加速")
                # 尝试使用 DirectML (Windows)
                elif 'DmlExecutionProvider' in ort.get_available_providers():
                    providers.append('DmlExecutionProvider')
                    self.后端类型 = "DirectML"
                    日志.info("使用 DirectML GPU 加速")
                else:
                    日志.warning("GPU 不可用，回退到 CPU")
            
            # 添加 CPU 作为后备
            providers.append('CPUExecutionProvider')
            if self.后端类型 == "CPU":
                日志.info("使用 CPU 推理")
            
            # 创建会话
            会话选项 = ort.SessionOptions()
            会话选项.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            
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
            
            日志.info(f"ONNX 模型加载成功: {self.模型路径}")
            日志.info(f"输入形状: {self.输入形状}")
            
        except ImportError:
            日志.error("onnxruntime 未安装")
            日志.info("安装命令: pip install onnxruntime 或 pip install onnxruntime-gpu")
            raise
        except Exception as e:
            日志.error(f"初始化 ONNX 引擎失败: {e}")
            raise
    
    def _预热(self, 次数: int = 10):
        """预热推理引擎"""
        日志.info(f"预热推理引擎 ({次数} 次)...")
        
        # 创建虚拟输入
        if len(self.输入形状) == 4:
            batch, w, h, c = self.输入形状
            虚拟输入 = np.random.rand(1, w, h, c).astype(np.float32)
        else:
            虚拟输入 = np.random.rand(*self.输入形状).astype(np.float32)
        
        for _ in range(次数):
            self._执行推理(虚拟输入)
        
        # 清空预热期间的统计
        self._延迟记录.clear()
        self._推理次数 = 0
        
        日志.info("预热完成")
    
    def _执行推理(self, 输入数据: np.ndarray) -> np.ndarray:
        """执行推理"""
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
        """
        if self.会话 is None:
            raise RuntimeError("推理引擎未初始化")
        
        # 预处理输入
        输入数据 = self._预处理(图像)
        
        # 执行推理
        输出 = self._执行推理(输入数据)
        
        # 后处理输出
        return self._后处理(输出)
    
    def _预处理(self, 图像: np.ndarray) -> np.ndarray:
        """预处理输入图像"""
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
        """后处理输出"""
        # 移除 batch 维度
        if len(输出.shape) > 1:
            输出 = 输出[0]
        
        return 输出.tolist()
    
    def 获取延迟统计(self) -> 性能指标:
        """获取推理延迟统计信息"""
        if not self._延迟记录:
            return 性能指标(后端类型=self.后端类型)
        
        延迟列表 = list(self._延迟记录)
        
        return 性能指标(
            平均延迟=np.mean(延迟列表),
            最小延迟=np.min(延迟列表),
            最大延迟=np.max(延迟列表),
            推理次数=self._推理次数,
            后端类型=self.后端类型
        )
    
    def 打印统计(self):
        """打印性能统计"""
        统计 = self.获取延迟统计()
        print(f"\n推理性能统计 ({统计.后端类型}):")
        print(f"  推理次数: {统计.推理次数}")
        print(f"  平均延迟: {统计.平均延迟:.2f} ms")
        print(f"  最小延迟: {统计.最小延迟:.2f} ms")
        print(f"  最大延迟: {统计.最大延迟:.2f} ms")


class 统一推理引擎:
    """统一的推理接口，自动选择后端"""
    
    def __init__(self, 模型路径: str, 首选后端: str = "auto"):
        """
        初始化统一推理引擎
        
        参数:
            模型路径: 模型文件路径
            首选后端: "auto"（自动检测）, "onnx", "tflearn"
        """
        self.模型路径 = 模型路径
        self.首选后端 = 首选后端
        self.当前后端: str = ""
        self._引擎: Any = None
        
        self._初始化()
    
    def _检测模型格式(self) -> str:
        """检测模型文件格式"""
        if self.模型路径.endswith('.onnx'):
            return "onnx"
        elif self.模型路径.endswith('.pb'):
            return "tensorflow"
        elif os.path.exists(self.模型路径 + '.index'):
            return "tflearn"
        elif os.path.isdir(self.模型路径):
            # 检查是否是 SavedModel
            if os.path.exists(os.path.join(self.模型路径, 'saved_model.pb')):
                return "savedmodel"
        return "unknown"
    
    def _初始化(self):
        """初始化推理引擎"""
        格式 = self._检测模型格式()
        日志.info(f"检测到模型格式: {格式}")
        
        # 根据首选后端和模型格式选择引擎
        if self.首选后端 == "onnx" or (self.首选后端 == "auto" and 格式 == "onnx"):
            self._尝试初始化ONNX()
        
        if self._引擎 is None:
            self._尝试初始化TFLearn()
        
        if self._引擎 is None:
            raise RuntimeError(f"无法初始化推理引擎，模型路径: {self.模型路径}")
    
    def _尝试初始化ONNX(self):
        """尝试初始化 ONNX 引擎"""
        onnx路径 = self.模型路径
        if not onnx路径.endswith('.onnx'):
            # 尝试查找对应的 ONNX 文件
            可能路径 = self.模型路径.rsplit('.', 1)[0] + '.onnx'
            if os.path.exists(可能路径):
                onnx路径 = 可能路径
            else:
                日志.info("未找到 ONNX 模型文件")
                return
        
        if not os.path.exists(onnx路径):
            日志.info(f"ONNX 模型文件不存在: {onnx路径}")
            return
        
        try:
            self._引擎 = ONNX推理引擎(onnx路径)
            self.当前后端 = "onnx"
            日志.info("已初始化 ONNX 推理引擎")
        except Exception as e:
            日志.warning(f"ONNX 引擎初始化失败: {e}")
    
    def _尝试初始化TFLearn(self):
        """尝试初始化 TFLearn 引擎"""
        try:
            from 核心.模型定义 import inception_v3
            from 配置.设置 import 模型输入宽度, 模型输入高度, 学习率, 总动作数
            
            # 创建模型
            模型 = inception_v3(
                模型输入宽度,
                模型输入高度,
                3,
                学习率,
                输出类别=总动作数,
                模型名称=self.模型路径
            )
            
            # 加载权重
            模型.load(self.模型路径)
            
            self._引擎 = TFLearn推理包装器(模型)
            self.当前后端 = "tflearn"
            日志.info("已初始化 TFLearn 推理引擎")
            
        except Exception as e:
            日志.warning(f"TFLearn 引擎初始化失败: {e}")
    
    def 预测(self, 图像: np.ndarray) -> List[float]:
        """
        执行推理预测
        
        参数:
            图像: 输入图像
            
        返回:
            动作概率列表
        """
        if self._引擎 is None:
            raise RuntimeError("推理引擎未初始化")
        
        return self._引擎.预测(图像)
    
    def 获取当前后端(self) -> str:
        """获取当前使用的推理后端"""
        return self.当前后端
    
    def 获取延迟统计(self) -> 性能指标:
        """获取推理延迟统计"""
        if hasattr(self._引擎, '获取延迟统计'):
            return self._引擎.获取延迟统计()
        return 性能指标(后端类型=self.当前后端)


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
