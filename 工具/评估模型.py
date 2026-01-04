#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
模型评估脚本

命令行工具，用于评估训练模型的性能。
支持指定模型和测试数据，自动生成评估报告。

用法:
    python 工具/评估模型.py --model 模型路径 --data 数据路径 [选项]

示例:
    # 评估模型并生成报告
    python 工具/评估模型.py --model 模型/best_model.h5 --data 数据/test.npy
    
    # 指定输出目录和报告格式
    python 工具/评估模型.py --model 模型/model.h5 --data 数据/ --output 评估结果 --format markdown html
    
    # 使用 ONNX 模型
    python 工具/评估模型.py --model 模型/model.onnx --data 数据/test.npz --onnx

需求: 3.1, 4.1 - 评估报告生成和批量评估
"""

import os
import sys
import argparse
import json
import time
import logging
from typing import Dict, List, Optional, Any

import numpy as np

# 添加项目根目录到路径
项目根目录 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if 项目根目录 not in sys.path:
    sys.path.insert(0, 项目根目录)

# 导入评估模块
from 工具.模型评估 import (
    模型评估器,
    批量评估器,
    报告生成器,
    可视化器,
    测试数据加载器,
    动作类别分析器,
    评估结果,
    默认动作分组
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
日志 = logging.getLogger(__name__)


# 默认动作定义（可通过配置文件覆盖）
默认动作定义 = {
    0: "前进", 1: "后退", 2: "左移", 3: "右移",
    4: "左前", 5: "右前", 6: "左后", 7: "右后", 8: "静止",
    9: "技能1", 10: "技能2", 11: "技能3", 12: "技能4",
    13: "技能5", 14: "技能6", 15: "技能7", 16: "技能8",
    17: "技能9", 18: "技能10",
    19: "闪避", 20: "跳跃", 21: "交互",
    22: "左键", 23: "右键", 24: "中键",
    25: "前进+技能1", 26: "后退+技能1", 27: "左移+技能1", 28: "右移+技能1",
    29: "前进+闪避", 30: "后退+闪避", 31: "跳跃+技能1"
}


class 模型加载器:
    """模型加载器，支持多种模型格式"""
    
    @staticmethod
    def 加载模型(模型路径: str, 使用ONNX: bool = False):
        """
        加载模型
        
        参数:
            模型路径: 模型文件路径
            使用ONNX: 是否使用 ONNX 推理
            
        返回:
            加载的模型对象
        """
        if not os.path.exists(模型路径):
            raise FileNotFoundError(f"模型文件不存在: {模型路径}")
        
        扩展名 = os.path.splitext(模型路径)[1].lower()
        
        if 使用ONNX or 扩展名 == '.onnx':
            return 模型加载器._加载ONNX模型(模型路径)
        elif 扩展名 in ['.h5', '.keras']:
            return 模型加载器._加载Keras模型(模型路径)
        elif 扩展名 == '.pt' or 扩展名 == '.pth':
            return 模型加载器._加载PyTorch模型(模型路径)
        elif 扩展名 == '.pkl':
            return 模型加载器._加载Pickle模型(模型路径)
        else:
            # 尝试作为 TensorFlow SavedModel 加载
            return 模型加载器._加载SavedModel(模型路径)
    
    @staticmethod
    def _加载ONNX模型(模型路径: str):
        """加载 ONNX 模型"""
        try:
            import onnxruntime as ort
            
            class ONNX模型包装器:
                def __init__(self, 会话):
                    self.会话 = 会话
                    self.输入名 = 会话.get_inputs()[0].name
                    self.输出名 = 会话.get_outputs()[0].name
                
                def predict(self, x):
                    # 确保输入是 float32
                    if x.dtype != np.float32:
                        x = x.astype(np.float32)
                    结果 = self.会话.run([self.输出名], {self.输入名: x})
                    return 结果[0]
            
            会话 = ort.InferenceSession(模型路径)
            日志.info(f"已加载 ONNX 模型: {模型路径}")
            return ONNX模型包装器(会话)
            
        except ImportError:
            raise ImportError("需要安装 onnxruntime: pip install onnxruntime")
    
    @staticmethod
    def _加载Keras模型(模型路径: str):
        """加载 Keras/TensorFlow 模型"""
        try:
            import tensorflow as tf
            模型 = tf.keras.models.load_model(模型路径)
            日志.info(f"已加载 Keras 模型: {模型路径}")
            return 模型
        except ImportError:
            raise ImportError("需要安装 tensorflow: pip install tensorflow")
    
    @staticmethod
    def _加载PyTorch模型(模型路径: str):
        """加载 PyTorch 模型"""
        try:
            import torch
            
            class PyTorch模型包装器:
                def __init__(self, 模型):
                    self.模型 = 模型
                    self.模型.eval()
                    self.设备 = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
                    self.模型.to(self.设备)
                
                def predict(self, x):
                    with torch.no_grad():
                        张量 = torch.from_numpy(x).float().to(self.设备)
                        输出 = self.模型(张量)
                        return 输出.cpu().numpy()
            
            模型 = torch.load(模型路径, map_location='cpu')
            日志.info(f"已加载 PyTorch 模型: {模型路径}")
            return PyTorch模型包装器(模型)
            
        except ImportError:
            raise ImportError("需要安装 pytorch: pip install torch")
    
    @staticmethod
    def _加载Pickle模型(模型路径: str):
        """加载 Pickle 格式模型"""
        import pickle
        with open(模型路径, 'rb') as f:
            模型 = pickle.load(f)
        日志.info(f"已加载 Pickle 模型: {模型路径}")
        return 模型
    
    @staticmethod
    def _加载SavedModel(模型路径: str):
        """加载 TensorFlow SavedModel"""
        try:
            import tensorflow as tf
            模型 = tf.saved_model.load(模型路径)
            日志.info(f"已加载 SavedModel: {模型路径}")
            return 模型
        except Exception as e:
            raise ValueError(f"无法加载模型 {模型路径}: {e}")


def 加载动作定义(配置路径: str = None) -> Dict[int, str]:
    """
    加载动作定义配置
    
    参数:
        配置路径: 配置文件路径（JSON 格式）
        
    返回:
        动作定义字典
    """
    if 配置路径 and os.path.exists(配置路径):
        try:
            with open(配置路径, 'r', encoding='utf-8') as f:
                配置 = json.load(f)
            
            # 支持两种格式：直接字典或嵌套在 'actions' 键下
            if 'actions' in 配置:
                动作定义 = 配置['actions']
            else:
                动作定义 = 配置
            
            # 确保键是整数
            return {int(k): v for k, v in 动作定义.items()}
            
        except Exception as e:
            日志.warning(f"加载动作定义配置失败: {e}，使用默认配置")
    
    return 默认动作定义.copy()


def 加载动作分组(配置路径: str = None) -> Dict[str, List[int]]:
    """
    加载动作分组配置
    
    参数:
        配置路径: 配置文件路径（JSON 格式）
        
    返回:
        动作分组字典
    """
    if 配置路径 and os.path.exists(配置路径):
        try:
            with open(配置路径, 'r', encoding='utf-8') as f:
                配置 = json.load(f)
            
            if 'groups' in 配置:
                return 配置['groups']
            
        except Exception as e:
            日志.warning(f"加载动作分组配置失败: {e}，使用默认配置")
    
    return 默认动作分组.copy()


def 执行评估(参数: argparse.Namespace) -> Dict[str, Any]:
    """
    执行模型评估
    
    参数:
        参数: 命令行参数
        
    返回:
        评估结果字典
    """
    结果 = {
        '成功': False,
        '评估结果': None,
        '生成文件': {},
        '错误信息': None
    }
    
    try:
        # 1. 加载动作定义
        日志.info("正在加载配置...")
        动作定义 = 加载动作定义(参数.actions_config)
        动作分组 = 加载动作分组(参数.actions_config)
        日志.info(f"已加载 {len(动作定义)} 个动作定义")
        
        # 2. 加载模型
        日志.info(f"正在加载模型: {参数.model}")
        模型 = 模型加载器.加载模型(参数.model, 参数.onnx)
        
        # 3. 创建批量评估器
        评估器 = 批量评估器(模型, 动作定义)
        
        # 4. 执行评估
        日志.info(f"正在评估模型，数据路径: {参数.data}")
        评估结果对象 = 评估器.批量评估(
            数据路径=参数.data,
            测试比例=参数.test_ratio,
            显示进度=not 参数.quiet,
            最大样本数=参数.max_samples
        )
        
        if 评估结果对象.样本数量 == 0:
            结果['错误信息'] = "没有加载到测试数据"
            return 结果
        
        结果['评估结果'] = 评估结果对象
        
        # 5. 创建输出目录
        输出目录 = 参数.output
        os.makedirs(输出目录, exist_ok=True)
        时间戳 = time.strftime("%Y%m%d_%H%M%S")
        
        # 6. 生成报告
        报告格式列表 = 参数.format if 参数.format else ['text', 'markdown']
        报告生成 = 报告生成器(评估结果对象, 动作定义)
        
        for 格式 in 报告格式列表:
            try:
                if 格式 == 'text':
                    路径 = os.path.join(输出目录, f"评估报告_{时间戳}.txt")
                    with open(路径, 'w', encoding='utf-8') as f:
                        f.write(报告生成.生成文本报告())
                    结果['生成文件']['text'] = 路径
                    日志.info(f"已生成文本报告: {路径}")
                    
                elif 格式 == 'markdown':
                    路径 = os.path.join(输出目录, f"评估报告_{时间戳}.md")
                    报告生成.生成Markdown报告(路径)
                    结果['生成文件']['markdown'] = 路径
                    
                elif 格式 == 'html':
                    路径 = os.path.join(输出目录, f"评估报告_{时间戳}.html")
                    报告生成.生成HTML报告(路径)
                    结果['生成文件']['html'] = 路径
                    
                elif 格式 == 'json':
                    路径 = os.path.join(输出目录, f"评估报告_{时间戳}.json")
                    报告生成.生成JSON报告(路径)
                    结果['生成文件']['json'] = 路径
                    
            except Exception as e:
                日志.warning(f"生成 {格式} 格式报告失败: {e}")
        
        # 7. 生成可视化（如果启用）
        if not 参数.no_visualize:
            try:
                可视化 = 可视化器(动作定义)
                可视化文件 = 可视化.生成完整可视化报告(
                    评估结果对象, 输出目录, f"eval_{时间戳}"
                )
                结果['生成文件'].update(可视化文件)
            except Exception as e:
                日志.warning(f"生成可视化报告失败: {e}")
        
        # 8. 动作类别分析（如果启用）
        if 参数.analyze:
            try:
                分析器 = 动作类别分析器(动作定义, 动作分组)
                分析结果 = 分析器.完整分析(评估结果对象, F1阈值=参数.f1_threshold)
                
                # 保存分析报告
                分析报告路径 = os.path.join(输出目录, f"类别分析_{时间戳}.md")
                分析报告内容 = 分析器.生成分析报告(分析结果, 格式="markdown")
                with open(分析报告路径, 'w', encoding='utf-8') as f:
                    f.write(分析报告内容)
                结果['生成文件']['类别分析'] = 分析报告路径
                日志.info(f"已生成类别分析报告: {分析报告路径}")
                
                # 打印弱势类别摘要
                if 分析结果.弱势类别列表 and not 参数.quiet:
                    print("\n" + "=" * 50)
                    print("弱势类别摘要:")
                    print("=" * 50)
                    for 弱势 in 分析结果.弱势类别列表[:5]:
                        print(f"  • {弱势.类别名称}: F1={弱势.F1分数:.4f}, {弱势.问题类型}")
                    if len(分析结果.弱势类别列表) > 5:
                        print(f"  ... 还有 {len(分析结果.弱势类别列表) - 5} 个弱势类别")
                    print()
                    
            except Exception as e:
                日志.warning(f"动作类别分析失败: {e}")
        
        # 9. 打印评估摘要
        if not 参数.quiet:
            print("\n" + "=" * 50)
            print("评估完成!")
            print("=" * 50)
            print(f"  样本数量: {评估结果对象.样本数量}")
            print(f"  评估时间: {评估结果对象.评估时间:.2f} 秒")
            print(f"  吞吐量: {评估结果对象.样本数量 / 评估结果对象.评估时间:.1f} 样本/秒")
            print(f"  总体准确率: {评估结果对象.总体准确率:.4f}")
            if 评估结果对象.宏平均:
                print(f"  宏平均 F1: {评估结果对象.宏平均.get('F1分数', 0):.4f}")
            print(f"\n生成的文件:")
            for 类型, 路径 in 结果['生成文件'].items():
                print(f"  • {类型}: {路径}")
            print()
        
        结果['成功'] = True
        
    except FileNotFoundError as e:
        结果['错误信息'] = str(e)
        日志.error(f"文件未找到: {e}")
    except ImportError as e:
        结果['错误信息'] = str(e)
        日志.error(f"缺少依赖: {e}")
    except Exception as e:
        结果['错误信息'] = str(e)
        日志.error(f"评估失败: {e}")
        import traceback
        traceback.print_exc()
    
    return 结果


def 创建参数解析器() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    解析器 = argparse.ArgumentParser(
        description='模型评估工具 - 评估训练模型的性能并生成报告',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本评估
  python 工具/评估模型.py --model 模型/best_model.h5 --data 数据/test.npy
  
  # 指定输出目录和多种报告格式
  python 工具/评估模型.py --model 模型/model.h5 --data 数据/ \\
      --output 评估结果 --format text markdown html json
  
  # 使用 ONNX 模型并进行类别分析
  python 工具/评估模型.py --model 模型/model.onnx --data 数据/test.npz \\
      --onnx --analyze --f1-threshold 0.8
  
  # 限制评估样本数
  python 工具/评估模型.py --model 模型/model.h5 --data 数据/ \\
      --max-samples 1000 --quiet
"""
    )
    
    # 必需参数
    解析器.add_argument(
        '--model', '-m',
        required=True,
        help='模型文件路径 (支持 .h5, .keras, .onnx, .pt, .pth, .pkl 格式)'
    )
    
    解析器.add_argument(
        '--data', '-d',
        required=True,
        help='测试数据路径 (文件或目录，支持 .npy, .npz, .json, .pkl 格式)'
    )
    
    # 可选参数
    解析器.add_argument(
        '--output', '-o',
        default='评估报告',
        help='输出目录 (默认: 评估报告)'
    )
    
    解析器.add_argument(
        '--format', '-f',
        nargs='+',
        choices=['text', 'markdown', 'html', 'json'],
        default=['text', 'markdown'],
        help='报告格式 (默认: text markdown)'
    )
    
    解析器.add_argument(
        '--onnx',
        action='store_true',
        help='使用 ONNX Runtime 进行推理'
    )
    
    解析器.add_argument(
        '--actions-config', '-a',
        help='动作定义配置文件路径 (JSON 格式)'
    )
    
    解析器.add_argument(
        '--test-ratio', '-r',
        type=float,
        default=1.0,
        help='测试数据比例，1.0 表示使用全部数据 (默认: 1.0)'
    )
    
    解析器.add_argument(
        '--max-samples', '-n',
        type=int,
        default=None,
        help='最大评估样本数 (默认: 无限制)'
    )
    
    解析器.add_argument(
        '--analyze',
        action='store_true',
        help='执行动作类别分析'
    )
    
    解析器.add_argument(
        '--f1-threshold',
        type=float,
        default=0.7,
        help='F1 分数阈值，低于此值视为弱势类别 (默认: 0.7)'
    )
    
    解析器.add_argument(
        '--no-visualize',
        action='store_true',
        help='禁用可视化报告生成'
    )
    
    解析器.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='安静模式，减少输出'
    )
    
    解析器.add_argument(
        '--version', '-v',
        action='version',
        version='模型评估工具 v1.0.0'
    )
    
    return 解析器


def main():
    """主函数"""
    解析器 = 创建参数解析器()
    参数 = 解析器.parse_args()
    
    # 执行评估
    结果 = 执行评估(参数)
    
    # 返回退出码
    if 结果['成功']:
        return 0
    else:
        if 结果['错误信息']:
            print(f"\n错误: {结果['错误信息']}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
