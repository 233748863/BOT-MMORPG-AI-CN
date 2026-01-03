"""
模型转换模块
将 TensorFlow/TFLearn 模型转换为 ONNX 格式

功能:
- TensorFlow 模型转 ONNX
- 模型验证
- 输出一致性检查
"""

import os
import logging
from typing import Tuple, Optional, Dict, Any
from dataclasses import dataclass

import numpy as np

# 配置日志
logging.basicConfig(level=logging.INFO)
日志 = logging.getLogger(__name__)


@dataclass
class 转换配置:
    """模型转换配置"""
    输入形状: Tuple[int, ...] = (1, 480, 270, 3)  # (batch, width, height, channels)
    输入名称: str = "input"
    输出名称: str = "output"
    opset版本: int = 13


class 模型转换器:
    """将 TensorFlow 模型转换为 ONNX 格式"""
    
    def __init__(self, 配置: 转换配置 = None):
        """
        初始化转换器
        
        参数:
            配置: 转换配置，None 则使用默认配置
        """
        self.配置 = 配置 or 转换配置()
        self._检查依赖()
    
    def _检查依赖(self):
        """检查必要的依赖库"""
        self.tf2onnx可用 = False
        self.onnx可用 = False
        
        try:
            import tf2onnx
            self.tf2onnx可用 = True
        except ImportError:
            日志.warning("tf2onnx 未安装，模型转换功能不可用")
            日志.info("安装命令: pip install tf2onnx")
        
        try:
            import onnx
            self.onnx可用 = True
        except ImportError:
            日志.warning("onnx 未安装，模型验证功能不可用")
            日志.info("安装命令: pip install onnx")
    
    def 转换(self, tf模型路径: str, onnx输出路径: str) -> bool:
        """
        执行模型转换
        
        参数:
            tf模型路径: TensorFlow 模型文件路径（不含扩展名）
            onnx输出路径: ONNX 模型输出路径
            
        返回:
            转换是否成功
        """
        if not self.tf2onnx可用:
            日志.error("tf2onnx 未安装，无法进行转换")
            return False
        
        try:
            import tensorflow as tf
            import tf2onnx
            
            日志.info(f"开始转换模型: {tf模型路径}")
            
            # 加载 TensorFlow 模型
            # TFLearn 模型通常保存为 checkpoint 格式
            模型目录 = os.path.dirname(tf模型路径)
            
            # 尝试加载 SavedModel 格式
            saved_model_路径 = tf模型路径 if os.path.isdir(tf模型路径) else 模型目录
            
            if os.path.exists(os.path.join(saved_model_路径, 'saved_model.pb')):
                # SavedModel 格式
                日志.info("检测到 SavedModel 格式")
                模型规格, 外部张量存储 = tf2onnx.convert.from_saved_model(
                    saved_model_路径,
                    opset=self.配置.opset版本
                )
            else:
                # 尝试从 checkpoint 加载
                日志.info("尝试从 checkpoint 加载模型")
                return self._从checkpoint转换(tf模型路径, onnx输出路径)
            
            # 保存 ONNX 模型
            确保目录存在(os.path.dirname(onnx输出路径))
            
            with open(onnx输出路径, 'wb') as f:
                f.write(模型规格.SerializeToString())
            
            日志.info(f"模型转换成功: {onnx输出路径}")
            return True
            
        except Exception as e:
            日志.error(f"模型转换失败: {e}")
            return False
    
    def _从checkpoint转换(self, checkpoint路径: str, onnx输出路径: str) -> bool:
        """从 TensorFlow checkpoint 转换"""
        try:
            import tensorflow as tf
            import tf2onnx
            from tf2onnx import tfonnx
            
            # 创建一个简单的转换脚本
            日志.warning("Checkpoint 格式转换需要模型定义，请使用 SavedModel 格式")
            日志.info("建议: 先将模型导出为 SavedModel 格式，再进行转换")
            
            # 提供转换指南
            print("\n" + "=" * 50)
            print("📋 模型转换指南")
            print("=" * 50)
            print("\n1. 在训练代码中添加 SavedModel 导出:")
            print("   tf.saved_model.save(模型, '导出路径')")
            print("\n2. 或使用命令行工具:")
            print(f"   python -m tf2onnx.convert --checkpoint {checkpoint路径} --output {onnx输出路径}")
            print("=" * 50)
            
            return False
            
        except Exception as e:
            日志.error(f"Checkpoint 转换失败: {e}")
            return False
    
    def 验证(self, onnx模型路径: str) -> Dict[str, Any]:
        """
        验证转换后的模型
        
        参数:
            onnx模型路径: ONNX 模型文件路径
            
        返回:
            验证结果字典
        """
        结果 = {
            '有效': False,
            '输入': [],
            '输出': [],
            '错误': None
        }
        
        if not self.onnx可用:
            结果['错误'] = "onnx 未安装"
            return 结果
        
        try:
            import onnx
            
            # 加载并检查模型
            模型 = onnx.load(onnx模型路径)
            onnx.checker.check_model(模型)
            
            # 获取输入输出信息
            for 输入 in 模型.graph.input:
                形状 = [d.dim_value for d in 输入.type.tensor_type.shape.dim]
                结果['输入'].append({
                    '名称': 输入.name,
                    '形状': 形状
                })
            
            for 输出 in 模型.graph.output:
                形状 = [d.dim_value for d in 输出.type.tensor_type.shape.dim]
                结果['输出'].append({
                    '名称': 输出.name,
                    '形状': 形状
                })
            
            结果['有效'] = True
            日志.info(f"模型验证通过: {onnx模型路径}")
            
        except Exception as e:
            结果['错误'] = str(e)
            日志.error(f"模型验证失败: {e}")
        
        return 结果
    
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


def 确保目录存在(目录路径: str):
    """确保目录存在"""
    if 目录路径:
        os.makedirs(目录路径, exist_ok=True)
