"""
模型转换模块
将 TensorFlow/TFLearn 模型转换为 ONNX 格式

功能:
- TensorFlow 模型转 ONNX
- 模型验证
- 输出一致性检查
- 错误处理和描述性信息

需求: 1.1, 1.2, 1.3, 1.4
"""

import os
import logging
from typing import Tuple, Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum

import numpy as np

# 配置日志
logging.basicConfig(level=logging.INFO)
日志 = logging.getLogger(__name__)


class 转换错误类型(Enum):
    """转换错误类型枚举"""
    依赖缺失 = "dependency_missing"
    文件不存在 = "file_not_found"
    格式不支持 = "format_not_supported"
    转换失败 = "conversion_failed"
    验证失败 = "validation_failed"
    输入输出不匹配 = "io_mismatch"
    未知错误 = "unknown_error"


@dataclass
class 转换错误:
    """转换错误信息"""
    类型: 转换错误类型
    消息: str
    详情: Optional[str] = None
    建议: Optional[str] = None
    
    def __str__(self) -> str:
        结果 = f"[{self.类型.value}] {self.消息}"
        if self.详情:
            结果 += f"\n详情: {self.详情}"
        if self.建议:
            结果 += f"\n建议: {self.建议}"
        return 结果


@dataclass
class 转换结果:
    """转换操作结果"""
    成功: bool
    输出路径: Optional[str] = None
    错误: Optional[转换错误] = None
    警告: List[str] = field(default_factory=list)
    
    def __bool__(self) -> bool:
        return self.成功


@dataclass
class 验证结果:
    """模型验证结果"""
    有效: bool
    输入信息: List[Dict[str, Any]] = field(default_factory=list)
    输出信息: List[Dict[str, Any]] = field(default_factory=list)
    错误: Optional[转换错误] = None
    模型信息: Dict[str, Any] = field(default_factory=dict)
    
    def __bool__(self) -> bool:
        return self.有效


@dataclass
class 转换配置:
    """模型转换配置"""
    输入形状: Tuple[int, ...] = (1, 480, 270, 3)  # (batch, width, height, channels)
    输入名称: str = "input"
    输出名称: str = "output"
    opset版本: int = 13
    优化级别: int = 1  # 0: 无优化, 1: 基本优化, 2: 扩展优化


class 模型转换器:
    """
    将 TensorFlow 模型转换为 ONNX 格式
    
    支持的输入格式:
    - TensorFlow SavedModel
    - TensorFlow Checkpoint (需要模型定义)
    - Keras H5 模型
    
    需求: 1.1 - TensorFlow → ONNX 转换
    """
    
    def __init__(self, 配置: 转换配置 = None):
        """
        初始化转换器
        
        参数:
            配置: 转换配置，None 则使用默认配置
        """
        self.配置 = 配置 or 转换配置()
        self._tf2onnx可用 = False
        self._onnx可用 = False
        self._tensorflow可用 = False
        self._onnxruntime可用 = False
        self._检查依赖()
    
    @property
    def tf2onnx可用(self) -> bool:
        """tf2onnx 是否可用"""
        return self._tf2onnx可用
    
    @property
    def onnx可用(self) -> bool:
        """onnx 是否可用"""
        return self._onnx可用
    
    @property
    def tensorflow可用(self) -> bool:
        """tensorflow 是否可用"""
        return self._tensorflow可用
    
    @property
    def onnxruntime可用(self) -> bool:
        """onnxruntime 是否可用"""
        return self._onnxruntime可用
    
    def _检查依赖(self) -> Dict[str, bool]:
        """
        检查必要的依赖库
        
        返回:
            依赖可用性字典
        """
        依赖状态 = {}
        
        # 检查 TensorFlow
        try:
            import tensorflow as tf
            self._tensorflow可用 = True
            依赖状态['tensorflow'] = True
            日志.debug(f"TensorFlow 版本: {tf.__version__}")
        except ImportError:
            依赖状态['tensorflow'] = False
            日志.warning("tensorflow 未安装")
        
        # 检查 tf2onnx
        try:
            import tf2onnx
            self._tf2onnx可用 = True
            依赖状态['tf2onnx'] = True
            日志.debug(f"tf2onnx 版本: {tf2onnx.__version__}")
        except ImportError:
            依赖状态['tf2onnx'] = False
            日志.warning("tf2onnx 未安装，模型转换功能不可用")
            日志.info("安装命令: pip install tf2onnx")
        
        # 检查 onnx
        try:
            import onnx
            self._onnx可用 = True
            依赖状态['onnx'] = True
            日志.debug(f"onnx 版本: {onnx.__version__}")
        except (ImportError, AttributeError) as e:
            依赖状态['onnx'] = False
            日志.warning(f"onnx 不可用: {e}")
            日志.info("安装命令: pip install onnx")
        
        # 检查 onnxruntime
        try:
            import onnxruntime as ort
            self._onnxruntime可用 = True
            依赖状态['onnxruntime'] = True
            日志.debug(f"onnxruntime 版本: {ort.__version__}")
        except (ImportError, AttributeError) as e:
            依赖状态['onnxruntime'] = False
            日志.info(f"onnxruntime 不可用: {e}")
        
        return 依赖状态
    
    def 转换(self, tf模型路径: str, onnx输出路径: str) -> 转换结果:
        """
        执行模型转换
        
        参数:
            tf模型路径: TensorFlow 模型文件路径
            onnx输出路径: ONNX 模型输出路径
            
        返回:
            转换结果对象，包含成功状态和错误信息
            
        需求: 1.1 - TensorFlow → ONNX 转换
        需求: 1.3 - 错误处理
        """
        # 检查依赖
        if not self._tf2onnx可用:
            return 转换结果(
                成功=False,
                错误=转换错误(
                    类型=转换错误类型.依赖缺失,
                    消息="tf2onnx 未安装，无法进行转换",
                    建议="请运行: pip install tf2onnx"
                )
            )
        
        if not self._tensorflow可用:
            return 转换结果(
                成功=False,
                错误=转换错误(
                    类型=转换错误类型.依赖缺失,
                    消息="tensorflow 未安装，无法进行转换",
                    建议="请运行: pip install tensorflow"
                )
            )
        
        # 检查输入文件
        if not os.path.exists(tf模型路径):
            return 转换结果(
                成功=False,
                错误=转换错误(
                    类型=转换错误类型.文件不存在,
                    消息=f"模型文件不存在: {tf模型路径}",
                    建议="请检查文件路径是否正确"
                )
            )
        
        警告列表 = []
        
        try:
            import tensorflow as tf
            import tf2onnx
            
            日志.info(f"开始转换模型: {tf模型路径}")
            
            # 确保输出目录存在
            输出目录 = os.path.dirname(onnx输出路径)
            if 输出目录:
                os.makedirs(输出目录, exist_ok=True)
            
            # 检测模型格式并转换
            转换成功 = False
            
            # 1. 尝试 SavedModel 格式
            if os.path.isdir(tf模型路径):
                saved_model_pb = os.path.join(tf模型路径, 'saved_model.pb')
                if os.path.exists(saved_model_pb):
                    日志.info("检测到 SavedModel 格式")
                    转换成功 = self._转换SavedModel(tf模型路径, onnx输出路径)
            
            # 2. 尝试 Keras H5 格式
            if not 转换成功 and tf模型路径.endswith('.h5'):
                日志.info("检测到 Keras H5 格式")
                转换成功 = self._转换KerasH5(tf模型路径, onnx输出路径)
            
            # 3. 尝试 Keras 目录格式
            if not 转换成功 and os.path.isdir(tf模型路径):
                keras_metadata = os.path.join(tf模型路径, 'keras_metadata.pb')
                if os.path.exists(keras_metadata):
                    日志.info("检测到 Keras 目录格式")
                    转换成功 = self._转换KerasDir(tf模型路径, onnx输出路径)
            
            # 4. 尝试 Checkpoint 格式
            if not 转换成功:
                # 检查是否是 checkpoint 格式
                模型目录 = os.path.dirname(tf模型路径) if os.path.isfile(tf模型路径) else tf模型路径
                checkpoint_文件 = os.path.join(模型目录, 'checkpoint')
                if os.path.exists(checkpoint_文件):
                    日志.info("检测到 Checkpoint 格式")
                    警告列表.append("Checkpoint 格式需要模型定义，建议先导出为 SavedModel")
                    return 转换结果(
                        成功=False,
                        错误=转换错误(
                            类型=转换错误类型.格式不支持,
                            消息="Checkpoint 格式需要模型定义才能转换",
                            详情="TFLearn 的 checkpoint 格式不包含完整的图定义",
                            建议="请先将模型导出为 SavedModel 格式: tf.saved_model.save(model, 'path')"
                        ),
                        警告=警告列表
                    )
            
            if not 转换成功:
                return 转换结果(
                    成功=False,
                    错误=转换错误(
                        类型=转换错误类型.格式不支持,
                        消息=f"无法识别模型格式: {tf模型路径}",
                        建议="支持的格式: SavedModel, Keras H5 (.h5), Keras 目录"
                    ),
                    警告=警告列表
                )
            
            # 验证输出文件
            if not os.path.exists(onnx输出路径):
                return 转换结果(
                    成功=False,
                    错误=转换错误(
                        类型=转换错误类型.转换失败,
                        消息="转换完成但输出文件未生成",
                        建议="请检查磁盘空间和写入权限"
                    ),
                    警告=警告列表
                )
            
            日志.info(f"模型转换成功: {onnx输出路径}")
            return 转换结果(
                成功=True,
                输出路径=onnx输出路径,
                警告=警告列表
            )
            
        except ImportError as e:
            return 转换结果(
                成功=False,
                错误=转换错误(
                    类型=转换错误类型.依赖缺失,
                    消息=f"缺少必要的依赖: {e}",
                    建议="请安装所需依赖: pip install tensorflow tf2onnx"
                ),
                警告=警告列表
            )
        except Exception as e:
            return 转换结果(
                成功=False,
                错误=转换错误(
                    类型=转换错误类型.转换失败,
                    消息=f"模型转换失败: {str(e)}",
                    详情=str(type(e).__name__),
                    建议="请检查模型文件是否完整，或尝试其他格式"
                ),
                警告=警告列表
            )
    
    def _转换SavedModel(self, 模型路径: str, 输出路径: str) -> bool:
        """转换 SavedModel 格式"""
        try:
            import tf2onnx
            
            模型规格, _ = tf2onnx.convert.from_saved_model(
                模型路径,
                opset=self.配置.opset版本
            )
            
            with open(输出路径, 'wb') as f:
                f.write(模型规格.SerializeToString())
            
            return True
        except Exception as e:
            日志.error(f"SavedModel 转换失败: {e}")
            return False
    
    def _转换KerasH5(self, 模型路径: str, 输出路径: str) -> bool:
        """转换 Keras H5 格式"""
        try:
            import tensorflow as tf
            import tf2onnx
            
            # 加载 Keras 模型
            模型 = tf.keras.models.load_model(模型路径)
            
            # 转换为 ONNX
            模型规格, _ = tf2onnx.convert.from_keras(
                模型,
                opset=self.配置.opset版本
            )
            
            with open(输出路径, 'wb') as f:
                f.write(模型规格.SerializeToString())
            
            return True
        except Exception as e:
            日志.error(f"Keras H5 转换失败: {e}")
            return False
    
    def _转换KerasDir(self, 模型路径: str, 输出路径: str) -> bool:
        """转换 Keras 目录格式"""
        try:
            import tensorflow as tf
            import tf2onnx
            
            # 加载 Keras 模型
            模型 = tf.keras.models.load_model(模型路径)
            
            # 转换为 ONNX
            模型规格, _ = tf2onnx.convert.from_keras(
                模型,
                opset=self.配置.opset版本
            )
            
            with open(输出路径, 'wb') as f:
                f.write(模型规格.SerializeToString())
            
            return True
        except Exception as e:
            日志.error(f"Keras 目录转换失败: {e}")
            return False
    
    def 验证(self, onnx模型路径: str) -> 验证结果:
        """
        验证转换后的模型
        
        参数:
            onnx模型路径: ONNX 模型文件路径
            
        返回:
            验证结果对象，包含输入输出信息
            
        需求: 1.2 - 验证输出模型结构
        需求: 1.4 - 保持输入/输出维度
        """
        # 检查依赖
        if not self._onnx可用:
            return 验证结果(
                有效=False,
                错误=转换错误(
                    类型=转换错误类型.依赖缺失,
                    消息="onnx 未安装，无法验证模型",
                    建议="请运行: pip install onnx"
                )
            )
        
        # 检查文件存在
        if not os.path.exists(onnx模型路径):
            return 验证结果(
                有效=False,
                错误=转换错误(
                    类型=转换错误类型.文件不存在,
                    消息=f"ONNX 模型文件不存在: {onnx模型路径}"
                )
            )
        
        try:
            import onnx
            
            # 加载模型
            模型 = onnx.load(onnx模型路径)
            
            # 检查模型结构
            try:
                onnx.checker.check_model(模型)
            except onnx.checker.ValidationError as e:
                return 验证结果(
                    有效=False,
                    错误=转换错误(
                        类型=转换错误类型.验证失败,
                        消息="模型结构验证失败",
                        详情=str(e),
                        建议="模型可能已损坏，请重新转换"
                    )
                )
            
            # 获取输入信息
            输入信息列表 = []
            for 输入 in 模型.graph.input:
                形状 = []
                for d in 输入.type.tensor_type.shape.dim:
                    if d.dim_value > 0:
                        形状.append(d.dim_value)
                    elif d.dim_param:
                        形状.append(d.dim_param)  # 动态维度
                    else:
                        形状.append(-1)  # 未知维度
                
                输入信息列表.append({
                    '名称': 输入.name,
                    '形状': 形状,
                    '数据类型': self._获取数据类型名称(输入.type.tensor_type.elem_type)
                })
            
            # 获取输出信息
            输出信息列表 = []
            for 输出 in 模型.graph.output:
                形状 = []
                for d in 输出.type.tensor_type.shape.dim:
                    if d.dim_value > 0:
                        形状.append(d.dim_value)
                    elif d.dim_param:
                        形状.append(d.dim_param)
                    else:
                        形状.append(-1)
                
                输出信息列表.append({
                    '名称': 输出.name,
                    '形状': 形状,
                    '数据类型': self._获取数据类型名称(输出.type.tensor_type.elem_type)
                })
            
            # 获取模型元信息
            模型信息 = {
                'ir版本': 模型.ir_version,
                'opset版本': [opset.version for opset in 模型.opset_import],
                '生产者': 模型.producer_name,
                '生产者版本': 模型.producer_version,
                '节点数量': len(模型.graph.node),
                '文件大小': os.path.getsize(onnx模型路径)
            }
            
            日志.info(f"模型验证通过: {onnx模型路径}")
            日志.info(f"输入: {输入信息列表}")
            日志.info(f"输出: {输出信息列表}")
            
            return 验证结果(
                有效=True,
                输入信息=输入信息列表,
                输出信息=输出信息列表,
                模型信息=模型信息
            )
            
        except Exception as e:
            return 验证结果(
                有效=False,
                错误=转换错误(
                    类型=转换错误类型.验证失败,
                    消息=f"模型验证失败: {str(e)}",
                    详情=str(type(e).__name__)
                )
            )
    
    def _获取数据类型名称(self, 类型代码: int) -> str:
        """将 ONNX 数据类型代码转换为名称"""
        类型映射 = {
            1: 'float32',
            2: 'uint8',
            3: 'int8',
            4: 'uint16',
            5: 'int16',
            6: 'int32',
            7: 'int64',
            8: 'string',
            9: 'bool',
            10: 'float16',
            11: 'float64',
            12: 'uint32',
            13: 'uint64',
        }
        return 类型映射.get(类型代码, f'unknown({类型代码})')
    
    def 验证输入输出维度(self, onnx模型路径: str, 
                        期望输入形状: Tuple[int, ...] = None,
                        期望输出形状: Tuple[int, ...] = None) -> 验证结果:
        """
        验证模型的输入输出维度是否符合预期
        
        参数:
            onnx模型路径: ONNX 模型文件路径
            期望输入形状: 期望的输入形状
            期望输出形状: 期望的输出形状
            
        返回:
            验证结果
            
        需求: 1.4 - 保持输入/输出维度
        """
        # 先进行基本验证
        基本验证 = self.验证(onnx模型路径)
        if not 基本验证.有效:
            return 基本验证
        
        # 使用配置中的默认形状
        if 期望输入形状 is None:
            期望输入形状 = self.配置.输入形状
        
        # 检查输入维度
        if 基本验证.输入信息:
            实际输入形状 = tuple(基本验证.输入信息[0]['形状'])
            
            # 比较形状（忽略动态维度）
            if not self._形状匹配(实际输入形状, 期望输入形状):
                return 验证结果(
                    有效=False,
                    输入信息=基本验证.输入信息,
                    输出信息=基本验证.输出信息,
                    模型信息=基本验证.模型信息,
                    错误=转换错误(
                        类型=转换错误类型.输入输出不匹配,
                        消息=f"输入维度不匹配",
                        详情=f"期望: {期望输入形状}, 实际: {实际输入形状}",
                        建议="请检查转换配置中的输入形状设置"
                    )
                )
        
        # 检查输出维度（如果指定）
        if 期望输出形状 and 基本验证.输出信息:
            实际输出形状 = tuple(基本验证.输出信息[0]['形状'])
            
            if not self._形状匹配(实际输出形状, 期望输出形状):
                return 验证结果(
                    有效=False,
                    输入信息=基本验证.输入信息,
                    输出信息=基本验证.输出信息,
                    模型信息=基本验证.模型信息,
                    错误=转换错误(
                        类型=转换错误类型.输入输出不匹配,
                        消息=f"输出维度不匹配",
                        详情=f"期望: {期望输出形状}, 实际: {实际输出形状}"
                    )
                )
        
        return 基本验证
    
    def _形状匹配(self, 实际形状: Tuple, 期望形状: Tuple) -> bool:
        """
        比较两个形状是否匹配（忽略动态维度）
        
        动态维度（-1 或字符串）可以匹配任何值
        """
        if len(实际形状) != len(期望形状):
            return False
        
        for 实际, 期望 in zip(实际形状, 期望形状):
            # 动态维度可以匹配任何值
            if isinstance(实际, str) or isinstance(期望, str):
                continue
            if 实际 == -1 or 期望 == -1:
                continue
            if 实际 != 期望:
                return False
        
        return True
    
    def 比较输出(self, tf模型, onnx模型路径: str, 
                 测试输入: np.ndarray, 容差: float = 0.01) -> Dict[str, Any]:
        """
        比较 TensorFlow 和 ONNX 模型的输出
        
        参数:
            tf模型: TensorFlow/TFLearn 模型
            onnx模型路径: ONNX 模型路径
            测试输入: 测试输入数据
            容差: 允许的最大差异
            
        返回:
            比较结果字典
        """
        结果 = {
            '一致': False,
            '最大差异': None,
            '平均差异': None,
            '错误': None
        }
        
        if not self._onnxruntime可用:
            结果['错误'] = "onnxruntime 未安装"
            return 结果
        
        try:
            import onnxruntime as ort
            
            # TensorFlow 预测
            tf输出 = tf模型.predict(测试输入)
            
            # ONNX 预测
            会话 = ort.InferenceSession(onnx模型路径)
            输入名称 = 会话.get_inputs()[0].name
            onnx输出 = 会话.run(None, {输入名称: 测试输入.astype(np.float32)})[0]
            
            # 计算差异
            差异 = np.abs(np.array(tf输出) - np.array(onnx输出))
            结果['最大差异'] = float(np.max(差异))
            结果['平均差异'] = float(np.mean(差异))
            结果['一致'] = 结果['最大差异'] < 容差
            
            if 结果['一致']:
                日志.info(f"输出一致性验证通过，最大差异: {结果['最大差异']:.6f}")
            else:
                日志.warning(f"输出差异超过容差，最大差异: {结果['最大差异']:.6f}")
            
        except Exception as e:
            结果['错误'] = str(e)
            日志.error(f"输出比较失败: {e}")
        
        return 结果
    
    def 获取依赖状态(self) -> Dict[str, bool]:
        """
        获取所有依赖的可用状态
        
        返回:
            依赖名称到可用状态的映射
        """
        return {
            'tensorflow': self._tensorflow可用,
            'tf2onnx': self._tf2onnx可用,
            'onnx': self._onnx可用,
            'onnxruntime': self._onnxruntime可用
        }
    
    def 打印转换指南(self):
        """打印模型转换指南"""
        print("\n" + "=" * 60)
        print("📋 模型转换指南")
        print("=" * 60)
        print("\n支持的输入格式:")
        print("  1. TensorFlow SavedModel (推荐)")
        print("  2. Keras H5 模型 (.h5)")
        print("  3. Keras 目录格式")
        print("\n转换步骤:")
        print("  1. 确保安装依赖: pip install tensorflow tf2onnx onnx")
        print("  2. 准备模型文件")
        print("  3. 调用 转换器.转换(输入路径, 输出路径)")
        print("  4. 调用 转换器.验证(输出路径) 验证结果")
        print("\n如果使用 TFLearn checkpoint 格式:")
        print("  需要先导出为 SavedModel:")
        print("  tf.saved_model.save(model, 'saved_model_path')")
        print("=" * 60)


def 确保目录存在(目录路径: str):
    """确保目录存在"""
    if 目录路径:
        os.makedirs(目录路径, exist_ok=True)


# 便捷函数
def 快速转换(tf模型路径: str, onnx输出路径: str, 
             输入形状: Tuple[int, ...] = None) -> 转换结果:
    """
    快速转换模型的便捷函数
    
    参数:
        tf模型路径: TensorFlow 模型路径
        onnx输出路径: ONNX 输出路径
        输入形状: 可选的输入形状
        
    返回:
        转换结果
    """
    配置 = 转换配置()
    if 输入形状:
        配置.输入形状 = 输入形状
    
    转换器 = 模型转换器(配置)
    return 转换器.转换(tf模型路径, onnx输出路径)


def 快速验证(onnx模型路径: str) -> 验证结果:
    """
    快速验证模型的便捷函数
    
    参数:
        onnx模型路径: ONNX 模型路径
        
    返回:
        验证结果
    """
    转换器 = 模型转换器()
    return 转换器.验证(onnx模型路径)


@dataclass
class 输出比较结果:
    """输出比较结果
    
    需求: 2.5 - 提供与原始 TFLearn 模型相同的输出格式
    """
    一致: bool = False
    最大差异: float = 0.0
    平均差异: float = 0.0
    标准差: float = 0.0
    差异百分位: Dict[str, float] = field(default_factory=dict)  # P50, P95, P99
    测试样本数: int = 0
    容差: float = 0.01
    错误: Optional[str] = None
    详细差异: List[float] = field(default_factory=list)  # 每个样本的最大差异
    
    def __bool__(self) -> bool:
        return self.一致
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            '一致': self.一致,
            '最大差异': round(self.最大差异, 6),
            '平均差异': round(self.平均差异, 6),
            '标准差': round(self.标准差, 6),
            '差异百分位': {k: round(v, 6) for k, v in self.差异百分位.items()},
            '测试样本数': self.测试样本数,
            '容差': self.容差,
            '错误': self.错误
        }


class 输出一致性验证器:
    """输出一致性验证器
    
    比较两个推理后端的输出差异，验证差异在可接受范围内。
    
    需求: 2.5 - 提供与原始 TFLearn 模型相同的输出格式
    需求: 1.4 - 保持模型的输入/输出维度
    """
    
    def __init__(self, 容差: float = 0.01, 输入形状: Tuple[int, ...] = (480, 270, 3)):
        """
        初始化验证器
        
        参数:
            容差: 允许的最大差异，默认 0.01
            输入形状: 输入图像形状 (width, height, channels)
        """
        self.容差 = 容差
        self.输入形状 = 输入形状
        self._onnxruntime可用 = False
        self._检查依赖()
    
    def _检查依赖(self):
        """检查必要的依赖"""
        try:
            import onnxruntime
            self._onnxruntime可用 = True
        except ImportError:
            日志.warning("onnxruntime 未安装，输出比较功能不可用")
    
    def 比较输出(self, 后端A, 后端B, 测试输入: np.ndarray = None,
                 后端A名称: str = "后端A", 后端B名称: str = "后端B") -> 输出比较结果:
        """
        比较两个推理后端的输出
        
        参数:
            后端A: 第一个推理后端（需要有 预测 方法）
            后端B: 第二个推理后端（需要有 预测 方法）
            测试输入: 测试输入数据，如果为 None 则生成随机数据
            后端A名称: 后端A的名称标识
            后端B名称: 后端B的名称标识
            
        返回:
            输出比较结果
            
        需求: 2.5 - 验证输出一致性
        """
        if 测试输入 is None:
            测试输入 = np.random.rand(*self.输入形状).astype(np.float32)
        
        try:
            # 获取两个后端的输出
            输出A = np.array(后端A.预测(测试输入))
            输出B = np.array(后端B.预测(测试输入))
            
            # 计算差异
            差异 = np.abs(输出A - 输出B)
            最大差异 = float(np.max(差异))
            平均差异 = float(np.mean(差异))
            标准差 = float(np.std(差异))
            
            # 判断是否一致
            一致 = 最大差异 < self.容差
            
            结果 = 输出比较结果(
                一致=一致,
                最大差异=最大差异,
                平均差异=平均差异,
                标准差=标准差,
                测试样本数=1,
                容差=self.容差,
                详细差异=[最大差异]
            )
            
            if 一致:
                日志.info(f"输出一致性验证通过: {后端A名称} vs {后端B名称}, 最大差异: {最大差异:.6f}")
            else:
                日志.warning(f"输出差异超过容差: {后端A名称} vs {后端B名称}, 最大差异: {最大差异:.6f} > {self.容差}")
            
            return 结果
            
        except Exception as e:
            日志.error(f"输出比较失败: {e}")
            return 输出比较结果(
                一致=False,
                错误=str(e),
                容差=self.容差
            )
    
    def 批量比较输出(self, 后端A, 后端B, 测试样本数: int = 100,
                     后端A名称: str = "后端A", 后端B名称: str = "后端B",
                     随机种子: int = None) -> 输出比较结果:
        """
        使用多个随机样本批量比较两个后端的输出
        
        参数:
            后端A: 第一个推理后端
            后端B: 第二个推理后端
            测试样本数: 测试样本数量
            后端A名称: 后端A的名称标识
            后端B名称: 后端B的名称标识
            随机种子: 随机种子，用于可重复性
            
        返回:
            输出比较结果
            
        需求: 2.5 - 验证输出一致性
        """
        if 随机种子 is not None:
            np.random.seed(随机种子)
        
        日志.info(f"开始批量输出比较: {后端A名称} vs {后端B名称}, 样本数: {测试样本数}")
        
        所有差异 = []
        详细差异 = []
        
        try:
            for i in range(测试样本数):
                # 生成随机测试输入
                测试输入 = np.random.rand(*self.输入形状).astype(np.float32)
                
                # 获取两个后端的输出
                输出A = np.array(后端A.预测(测试输入))
                输出B = np.array(后端B.预测(测试输入))
                
                # 计算差异
                差异 = np.abs(输出A - 输出B)
                所有差异.extend(差异.flatten().tolist())
                详细差异.append(float(np.max(差异)))
                
                if (i + 1) % 20 == 0:
                    日志.info(f"  进度: {i + 1}/{测试样本数}")
            
            # 计算统计数据
            所有差异数组 = np.array(所有差异)
            详细差异数组 = np.array(详细差异)
            
            最大差异 = float(np.max(详细差异数组))
            平均差异 = float(np.mean(所有差异数组))
            标准差 = float(np.std(所有差异数组))
            
            # 计算百分位数
            差异百分位 = {}
            if len(所有差异数组) >= 2:
                差异百分位['P50'] = float(np.percentile(所有差异数组, 50))
            if len(所有差异数组) >= 20:
                差异百分位['P95'] = float(np.percentile(所有差异数组, 95))
            if len(所有差异数组) >= 100:
                差异百分位['P99'] = float(np.percentile(所有差异数组, 99))
            
            # 判断是否一致（所有样本的最大差异都小于容差）
            一致 = 最大差异 < self.容差
            
            结果 = 输出比较结果(
                一致=一致,
                最大差异=最大差异,
                平均差异=平均差异,
                标准差=标准差,
                差异百分位=差异百分位,
                测试样本数=测试样本数,
                容差=self.容差,
                详细差异=详细差异
            )
            
            if 一致:
                日志.info(f"批量输出一致性验证通过: 最大差异 {最大差异:.6f} < 容差 {self.容差}")
            else:
                日志.warning(f"批量输出差异超过容差: 最大差异 {最大差异:.6f} >= 容差 {self.容差}")
            
            return 结果
            
        except Exception as e:
            日志.error(f"批量输出比较失败: {e}")
            return 输出比较结果(
                一致=False,
                错误=str(e),
                容差=self.容差
            )
    
    def 比较ONNX与TFLearn(self, onnx模型路径: str, tflearn模型,
                          测试样本数: int = 100, 随机种子: int = None) -> 输出比较结果:
        """
        比较 ONNX 模型和 TFLearn 模型的输出
        
        参数:
            onnx模型路径: ONNX 模型文件路径
            tflearn模型: TFLearn 模型实例
            测试样本数: 测试样本数量
            随机种子: 随机种子
            
        返回:
            输出比较结果
            
        需求: 2.5 - 提供与原始 TFLearn 模型相同的输出格式
        """
        if not self._onnxruntime可用:
            return 输出比较结果(
                一致=False,
                错误="onnxruntime 未安装",
                容差=self.容差
            )
        
        if not os.path.exists(onnx模型路径):
            return 输出比较结果(
                一致=False,
                错误=f"ONNX 模型文件不存在: {onnx模型路径}",
                容差=self.容差
            )
        
        try:
            # 创建 ONNX 推理包装器
            onnx后端 = _ONNX推理包装器(onnx模型路径)
            
            # 创建 TFLearn 推理包装器
            tflearn后端 = _TFLearn推理包装器(tflearn模型)
            
            return self.批量比较输出(
                onnx后端, tflearn后端,
                测试样本数=测试样本数,
                后端A名称="ONNX",
                后端B名称="TFLearn",
                随机种子=随机种子
            )
            
        except Exception as e:
            日志.error(f"ONNX 与 TFLearn 比较失败: {e}")
            return 输出比较结果(
                一致=False,
                错误=str(e),
                容差=self.容差
            )
    
    def 比较两个ONNX模型(self, onnx模型路径A: str, onnx模型路径B: str,
                         测试样本数: int = 100, 随机种子: int = None) -> 输出比较结果:
        """
        比较两个 ONNX 模型的输出
        
        参数:
            onnx模型路径A: 第一个 ONNX 模型路径
            onnx模型路径B: 第二个 ONNX 模型路径
            测试样本数: 测试样本数量
            随机种子: 随机种子
            
        返回:
            输出比较结果
        """
        if not self._onnxruntime可用:
            return 输出比较结果(
                一致=False,
                错误="onnxruntime 未安装",
                容差=self.容差
            )
        
        for 路径, 名称 in [(onnx模型路径A, "A"), (onnx模型路径B, "B")]:
            if not os.path.exists(路径):
                return 输出比较结果(
                    一致=False,
                    错误=f"ONNX 模型 {名称} 不存在: {路径}",
                    容差=self.容差
                )
        
        try:
            后端A = _ONNX推理包装器(onnx模型路径A)
            后端B = _ONNX推理包装器(onnx模型路径B)
            
            return self.批量比较输出(
                后端A, 后端B,
                测试样本数=测试样本数,
                后端A名称=f"ONNX({os.path.basename(onnx模型路径A)})",
                后端B名称=f"ONNX({os.path.basename(onnx模型路径B)})",
                随机种子=随机种子
            )
            
        except Exception as e:
            日志.error(f"两个 ONNX 模型比较失败: {e}")
            return 输出比较结果(
                一致=False,
                错误=str(e),
                容差=self.容差
            )
    
    def 打印比较结果(self, 结果: 输出比较结果, 标题: str = "输出一致性验证结果"):
        """打印比较结果"""
        print(f"\n{标题}")
        print("=" * 50)
        print(f"  一致性: {'通过 ✓' if 结果.一致 else '失败 ✗'}")
        print(f"  容差阈值: {结果.容差}")
        print(f"  测试样本数: {结果.测试样本数}")
        print(f"  最大差异: {结果.最大差异:.6f}")
        print(f"  平均差异: {结果.平均差异:.6f}")
        print(f"  标准差: {结果.标准差:.6f}")
        
        if 结果.差异百分位:
            print("  差异百分位:")
            for k, v in 结果.差异百分位.items():
                print(f"    {k}: {v:.6f}")
        
        if 结果.错误:
            print(f"  错误: {结果.错误}")
        
        print("=" * 50)


class _ONNX推理包装器:
    """ONNX 推理包装器（内部使用）"""
    
    def __init__(self, 模型路径: str):
        import onnxruntime as ort
        
        self.会话 = ort.InferenceSession(模型路径)
        self.输入名称 = self.会话.get_inputs()[0].name
    
    def 预测(self, 图像: np.ndarray) -> List[float]:
        """执行预测"""
        # 预处理
        if 图像.dtype != np.float32:
            图像 = 图像.astype(np.float32)
        if 图像.max() > 1.0:
            图像 = 图像 / 255.0
        if len(图像.shape) == 3:
            图像 = np.expand_dims(图像, axis=0)
        
        结果 = self.会话.run(None, {self.输入名称: 图像})[0]
        
        if len(结果.shape) > 1:
            结果 = 结果[0]
        
        return 结果.tolist()


class _TFLearn推理包装器:
    """TFLearn 推理包装器（内部使用）"""
    
    def __init__(self, 模型):
        self.模型 = 模型
    
    def 预测(self, 图像: np.ndarray) -> List[float]:
        """执行预测"""
        if len(图像.shape) == 3:
            图像 = np.expand_dims(图像, axis=0)
        
        结果 = self.模型.predict(图像)
        
        if len(结果.shape) > 1:
            结果 = 结果[0]
        
        return 结果.tolist()


# 便捷函数
def 验证输出一致性(后端A, 后端B, 测试样本数: int = 100, 
                   容差: float = 0.01, 输入形状: Tuple[int, ...] = (480, 270, 3),
                   后端A名称: str = "后端A", 后端B名称: str = "后端B") -> 输出比较结果:
    """
    验证两个推理后端输出一致性的便捷函数
    
    参数:
        后端A: 第一个推理后端（需要有 预测 方法）
        后端B: 第二个推理后端（需要有 预测 方法）
        测试样本数: 测试样本数量
        容差: 允许的最大差异
        输入形状: 输入图像形状
        后端A名称: 后端A的名称标识
        后端B名称: 后端B的名称标识
        
    返回:
        输出比较结果
        
    需求: 2.5 - 验证输出一致性
    """
    验证器 = 输出一致性验证器(容差=容差, 输入形状=输入形状)
    return 验证器.批量比较输出(
        后端A, 后端B,
        测试样本数=测试样本数,
        后端A名称=后端A名称,
        后端B名称=后端B名称
    )


def 快速验证ONNX一致性(onnx模型路径: str, tflearn模型,
                        测试样本数: int = 100, 容差: float = 0.01,
                        输入形状: Tuple[int, ...] = (480, 270, 3)) -> 输出比较结果:
    """
    快速验证 ONNX 模型与 TFLearn 模型输出一致性的便捷函数
    
    参数:
        onnx模型路径: ONNX 模型文件路径
        tflearn模型: TFLearn 模型实例
        测试样本数: 测试样本数量
        容差: 允许的最大差异
        输入形状: 输入图像形状
        
    返回:
        输出比较结果
        
    需求: 2.5 - 提供与原始 TFLearn 模型相同的输出格式
    """
    验证器 = 输出一致性验证器(容差=容差, 输入形状=输入形状)
    return 验证器.比较ONNX与TFLearn(
        onnx模型路径, tflearn模型,
        测试样本数=测试样本数
    )
