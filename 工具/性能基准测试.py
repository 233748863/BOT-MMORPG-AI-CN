"""
性能基准测试模块
用于测量和比较推理引擎的性能

功能:
- 延迟测量和统计
- TFLearn 和 ONNX 后端性能对比
- 性能报告生成

需求: 3.1, 3.2, 3.3
"""

import os
import time
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from collections import deque
from datetime import datetime

import numpy as np

# 配置日志
logging.basicConfig(level=logging.INFO)
日志 = logging.getLogger(__name__)


@dataclass
class 延迟统计:
    """延迟统计数据
    
    需求: 3.1 - 测量推理延迟
    需求: 3.2 - 报告平均、最小和最大延迟
    """
    平均延迟: float = 0.0  # 毫秒
    最小延迟: float = 0.0
    最大延迟: float = 0.0
    标准差: float = 0.0
    P50延迟: float = 0.0  # 中位数
    P95延迟: float = 0.0
    P99延迟: float = 0.0
    推理次数: int = 0
    总耗时: float = 0.0  # 秒
    理论FPS: float = 0.0
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            '平均延迟_ms': round(self.平均延迟, 3),
            '最小延迟_ms': round(self.最小延迟, 3),
            '最大延迟_ms': round(self.最大延迟, 3),
            '标准差_ms': round(self.标准差, 3),
            'P50延迟_ms': round(self.P50延迟, 3),
            'P95延迟_ms': round(self.P95延迟, 3),
            'P99延迟_ms': round(self.P99延迟, 3),
            '推理次数': self.推理次数,
            '总耗时_s': round(self.总耗时, 3),
            '理论FPS': round(self.理论FPS, 1)
        }


@dataclass
class 基准测试结果:
    """基准测试结果
    
    需求: 3.3 - 记录性能指标以便比较
    """
    后端名称: str = ""
    延迟统计: 延迟统计 = field(default_factory=延迟统计)
    测试时间: str = ""
    输入形状: Tuple = ()
    使用GPU: bool = False
    满足延迟要求: bool = True  # 是否满足 50ms 延迟要求
    原始延迟数据: List[float] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            '后端名称': self.后端名称,
            '延迟统计': self.延迟统计.to_dict(),
            '测试时间': self.测试时间,
            '输入形状': list(self.输入形状),
            '使用GPU': self.使用GPU,
            '满足延迟要求': self.满足延迟要求
        }


@dataclass
class 对比报告:
    """性能对比报告
    
    需求: 3.3 - 记录性能指标以便与原始模型进行比较
    """
    测试时间: str = ""
    测试次数: int = 0
    输入形状: Tuple = ()
    结果列表: List[基准测试结果] = field(default_factory=list)
    加速比: float = 0.0  # ONNX 相对于 TFLearn 的加速比
    推荐后端: str = ""
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            '测试时间': self.测试时间,
            '测试次数': self.测试次数,
            '输入形状': list(self.输入形状),
            '结果列表': [r.to_dict() for r in self.结果列表],
            '加速比': round(self.加速比, 2),
            '推荐后端': self.推荐后端
        }


class 延迟测量器:
    """延迟测量器
    
    记录每次推理的延迟，计算统计数据。
    
    需求: 3.1 - 提供测量推理延迟的方法
    需求: 3.2 - 报告 100 次迭代的平均、最小和最大延迟
    """
    
    def __init__(self, 窗口大小: int = 1000, 最大延迟阈值: float = 50.0):
        """
        初始化延迟测量器
        
        参数:
            窗口大小: 保留的最近延迟记录数量
            最大延迟阈值: 最大允许延迟（毫秒），用于判断是否满足要求
        """
        self._延迟记录: deque = deque(maxlen=窗口大小)
        self._所有延迟: List[float] = []  # 保存所有延迟用于完整统计
        self._推理次数: int = 0
        self._总耗时: float = 0.0
        self._最大延迟阈值 = 最大延迟阈值
        self._开始时间: Optional[float] = None
    
    def 开始测量(self):
        """开始一次延迟测量"""
        self._开始时间 = time.perf_counter()
    
    def 结束测量(self) -> float:
        """
        结束一次延迟测量
        
        返回:
            本次推理延迟（毫秒）
        """
        if self._开始时间 is None:
            raise RuntimeError("未调用 开始测量()")
        
        延迟 = (time.perf_counter() - self._开始时间) * 1000  # 转换为毫秒
        self._记录延迟(延迟)
        self._开始时间 = None
        return 延迟
    
    def 记录延迟(self, 延迟_ms: float):
        """
        直接记录一次延迟
        
        参数:
            延迟_ms: 延迟时间（毫秒）
        """
        self._记录延迟(延迟_ms)
    
    def _记录延迟(self, 延迟: float):
        """内部方法：记录延迟"""
        self._延迟记录.append(延迟)
        self._所有延迟.append(延迟)
        self._推理次数 += 1
        self._总耗时 += 延迟 / 1000  # 转换为秒
    
    def 测量(self, 函数, *args, **kwargs) -> Tuple[Any, float]:
        """
        测量函数执行延迟
        
        参数:
            函数: 要测量的函数
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        返回:
            (函数返回值, 延迟毫秒)
        """
        self.开始测量()
        结果 = 函数(*args, **kwargs)
        延迟 = self.结束测量()
        return 结果, 延迟
    
    def 获取统计(self, 使用全部数据: bool = False) -> 延迟统计:
        """
        获取延迟统计信息
        
        参数:
            使用全部数据: 是否使用所有历史数据，否则只使用窗口内数据
            
        返回:
            延迟统计对象
            
        需求: 3.1 - 测量推理延迟
        需求: 3.2 - 报告平均、最小和最大延迟
        """
        延迟列表 = self._所有延迟 if 使用全部数据 else list(self._延迟记录)
        
        if not 延迟列表:
            return 延迟统计()
        
        平均延迟 = float(np.mean(延迟列表))
        
        return 延迟统计(
            平均延迟=平均延迟,
            最小延迟=float(np.min(延迟列表)),
            最大延迟=float(np.max(延迟列表)),
            标准差=float(np.std(延迟列表)),
            P50延迟=float(np.percentile(延迟列表, 50)),
            P95延迟=float(np.percentile(延迟列表, 95)) if len(延迟列表) >= 20 else 0.0,
            P99延迟=float(np.percentile(延迟列表, 99)) if len(延迟列表) >= 100 else 0.0,
            推理次数=len(延迟列表),
            总耗时=sum(延迟列表) / 1000,
            理论FPS=1000 / 平均延迟 if 平均延迟 > 0 else 0.0
        )
    
    def 检查延迟要求(self) -> bool:
        """
        检查是否满足延迟要求
        
        返回:
            是否满足 50ms 延迟要求
        """
        统计 = self.获取统计()
        return 统计.平均延迟 < self._最大延迟阈值
    
    def 获取原始数据(self) -> List[float]:
        """获取所有原始延迟数据"""
        return self._所有延迟.copy()
    
    def 重置(self):
        """重置所有统计数据"""
        self._延迟记录.clear()
        self._所有延迟.clear()
        self._推理次数 = 0
        self._总耗时 = 0.0
        self._开始时间 = None
    
    def 打印统计(self, 标题: str = "延迟统计"):
        """打印统计信息"""
        统计 = self.获取统计(使用全部数据=True)
        print(f"\n{标题}:")
        print(f"  推理次数: {统计.推理次数}")
        print(f"  平均延迟: {统计.平均延迟:.3f} ms")
        print(f"  最小延迟: {统计.最小延迟:.3f} ms")
        print(f"  最大延迟: {统计.最大延迟:.3f} ms")
        print(f"  标准差: {统计.标准差:.3f} ms")
        print(f"  P50 延迟: {统计.P50延迟:.3f} ms")
        if 统计.P95延迟 > 0:
            print(f"  P95 延迟: {统计.P95延迟:.3f} ms")
        if 统计.P99延迟 > 0:
            print(f"  P99 延迟: {统计.P99延迟:.3f} ms")
        print(f"  理论 FPS: {统计.理论FPS:.1f}")
        print(f"  满足延迟要求 (<{self._最大延迟阈值}ms): {'是' if self.检查延迟要求() else '否'}")



class 性能基准测试器:
    """性能基准测试器
    
    对比 TFLearn 和 ONNX 后端性能，生成性能报告。
    
    需求: 3.3 - 记录性能指标以便与原始模型进行比较
    """
    
    def __init__(self, 测试次数: int = 100, 预热次数: int = 10,
                 输入形状: Tuple = (480, 270, 3)):
        """
        初始化基准测试器
        
        参数:
            测试次数: 基准测试迭代次数
            预热次数: 预热迭代次数
            输入形状: 输入图像形状 (width, height, channels)
        """
        self.测试次数 = 测试次数
        self.预热次数 = 预热次数
        self.输入形状 = 输入形状
        self._结果列表: List[基准测试结果] = []
    
    def 测试引擎(self, 引擎, 后端名称: str, 使用GPU: bool = False) -> 基准测试结果:
        """
        测试单个推理引擎的性能
        
        参数:
            引擎: 推理引擎实例（需要有 预测 方法）
            后端名称: 后端名称标识
            使用GPU: 是否使用 GPU
            
        返回:
            基准测试结果
        """
        日志.info(f"开始测试 {后端名称} 后端...")
        
        # 生成测试数据
        测试数据 = np.random.rand(*self.输入形状).astype(np.float32)
        
        # 预热
        日志.info(f"  预热 ({self.预热次数} 次)...")
        for _ in range(self.预热次数):
            try:
                引擎.预测(测试数据)
            except Exception as e:
                日志.warning(f"  预热失败: {e}")
                break
        
        # 正式测试
        日志.info(f"  正式测试 ({self.测试次数} 次)...")
        测量器 = 延迟测量器()
        
        for i in range(self.测试次数):
            try:
                测量器.测量(引擎.预测, 测试数据)
                
                if (i + 1) % 20 == 0:
                    日志.info(f"    进度: {i + 1}/{self.测试次数}")
            except Exception as e:
                日志.error(f"  测试失败 (第 {i + 1} 次): {e}")
                break
        
        # 获取统计
        统计 = 测量器.获取统计(使用全部数据=True)
        
        结果 = 基准测试结果(
            后端名称=后端名称,
            延迟统计=统计,
            测试时间=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            输入形状=self.输入形状,
            使用GPU=使用GPU,
            满足延迟要求=统计.平均延迟 < 50.0,
            原始延迟数据=测量器.获取原始数据()
        )
        
        self._结果列表.append(结果)
        
        日志.info(f"  {后端名称} 测试完成: 平均延迟 {统计.平均延迟:.3f} ms")
        
        return 结果
    
    def 测试ONNX引擎(self, 模型路径: str, 使用GPU: bool = True) -> Optional[基准测试结果]:
        """
        测试 ONNX 推理引擎
        
        参数:
            模型路径: ONNX 模型文件路径
            使用GPU: 是否使用 GPU
            
        返回:
            基准测试结果，失败返回 None
        """
        try:
            from 核心.ONNX推理 import ONNX推理引擎
            
            引擎 = ONNX推理引擎(
                模型路径, 
                使用GPU=使用GPU, 
                预热=False,
                输入宽度=self.输入形状[0],
                输入高度=self.输入形状[1]
            )
            
            后端名称 = f"ONNX ({'GPU' if 使用GPU else 'CPU'})"
            return self.测试引擎(引擎, 后端名称, 使用GPU)
            
        except Exception as e:
            日志.error(f"ONNX 引擎测试失败: {e}")
            return None
    
    def 测试TFLearn引擎(self, 模型路径: str) -> Optional[基准测试结果]:
        """
        测试 TFLearn 推理引擎
        
        参数:
            模型路径: TFLearn 模型文件路径
            
        返回:
            基准测试结果，失败返回 None
        """
        try:
            from 核心.模型定义 import inception_v3
            from 配置.设置 import 学习率, 总动作数
            
            # 创建模型
            模型 = inception_v3(
                self.输入形状[0],
                self.输入形状[1],
                3,
                学习率,
                输出类别=总动作数,
                模型名称=模型路径
            )
            
            # 加载权重
            模型.load(模型路径)
            
            # 创建包装器
            from 核心.ONNX推理 import TFLearn推理包装器
            引擎 = TFLearn推理包装器(模型)
            
            return self.测试引擎(引擎, "TFLearn", False)
            
        except Exception as e:
            日志.error(f"TFLearn 引擎测试失败: {e}")
            return None
    
    def 对比测试(self, onnx模型路径: str = None, tflearn模型路径: str = None,
                 使用GPU: bool = True) -> 对比报告:
        """
        对比 ONNX 和 TFLearn 后端性能
        
        参数:
            onnx模型路径: ONNX 模型路径
            tflearn模型路径: TFLearn 模型路径
            使用GPU: ONNX 是否使用 GPU
            
        返回:
            对比报告
            
        需求: 3.3 - 记录性能指标以便与原始模型进行比较
        """
        日志.info("=" * 60)
        日志.info("开始性能对比测试")
        日志.info("=" * 60)
        
        self._结果列表.clear()
        
        # 测试 ONNX
        onnx结果 = None
        if onnx模型路径 and os.path.exists(onnx模型路径):
            onnx结果 = self.测试ONNX引擎(onnx模型路径, 使用GPU)
        
        # 测试 TFLearn
        tflearn结果 = None
        if tflearn模型路径:
            tflearn结果 = self.测试TFLearn引擎(tflearn模型路径)
        
        # 生成对比报告
        报告 = 对比报告(
            测试时间=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            测试次数=self.测试次数,
            输入形状=self.输入形状,
            结果列表=self._结果列表.copy()
        )
        
        # 计算加速比
        if onnx结果 and tflearn结果:
            tflearn延迟 = tflearn结果.延迟统计.平均延迟
            onnx延迟 = onnx结果.延迟统计.平均延迟
            if onnx延迟 > 0:
                报告.加速比 = tflearn延迟 / onnx延迟
        
        # 推荐后端
        if onnx结果 and tflearn结果:
            if onnx结果.延迟统计.平均延迟 < tflearn结果.延迟统计.平均延迟:
                报告.推荐后端 = "ONNX"
            else:
                报告.推荐后端 = "TFLearn"
        elif onnx结果:
            报告.推荐后端 = "ONNX"
        elif tflearn结果:
            报告.推荐后端 = "TFLearn"
        
        return 报告
    
    def 生成报告(self, 报告: 对比报告, 输出路径: str = None) -> str:
        """
        生成性能报告
        
        参数:
            报告: 对比报告对象
            输出路径: 输出文件路径（可选）
            
        返回:
            报告文本内容
        """
        行列表 = []
        行列表.append("=" * 70)
        行列表.append("推理性能基准测试报告")
        行列表.append("=" * 70)
        行列表.append("")
        行列表.append(f"测试时间: {报告.测试时间}")
        行列表.append(f"测试次数: {报告.测试次数}")
        行列表.append(f"输入形状: {报告.输入形状}")
        行列表.append("")
        
        # 各后端结果
        for 结果 in 报告.结果列表:
            行列表.append("-" * 70)
            行列表.append(f"后端: {结果.后端名称}")
            行列表.append("-" * 70)
            统计 = 结果.延迟统计
            行列表.append(f"  平均延迟: {统计.平均延迟:.3f} ms")
            行列表.append(f"  最小延迟: {统计.最小延迟:.3f} ms")
            行列表.append(f"  最大延迟: {统计.最大延迟:.3f} ms")
            行列表.append(f"  标准差: {统计.标准差:.3f} ms")
            行列表.append(f"  P50 延迟: {统计.P50延迟:.3f} ms")
            if 统计.P95延迟 > 0:
                行列表.append(f"  P95 延迟: {统计.P95延迟:.3f} ms")
            if 统计.P99延迟 > 0:
                行列表.append(f"  P99 延迟: {统计.P99延迟:.3f} ms")
            行列表.append(f"  理论 FPS: {统计.理论FPS:.1f}")
            行列表.append(f"  满足延迟要求 (<50ms): {'是' if 结果.满足延迟要求 else '否'}")
            行列表.append("")
        
        # 对比结论
        if len(报告.结果列表) >= 2:
            行列表.append("=" * 70)
            行列表.append("对比结论")
            行列表.append("=" * 70)
            行列表.append(f"  加速比: {报告.加速比:.2f}x")
            行列表.append(f"  推荐后端: {报告.推荐后端}")
            行列表.append("")
        
        行列表.append("=" * 70)
        
        内容 = "\n".join(行列表)
        
        # 保存到文件
        if 输出路径:
            目录 = os.path.dirname(输出路径)
            if 目录:
                os.makedirs(目录, exist_ok=True)
            with open(输出路径, 'w', encoding='utf-8') as f:
                f.write(内容)
            日志.info(f"报告已保存: {输出路径}")
        
        return 内容
    
    def 保存JSON报告(self, 报告: 对比报告, 输出路径: str) -> bool:
        """
        保存 JSON 格式报告
        
        参数:
            报告: 对比报告对象
            输出路径: 输出文件路径
            
        返回:
            是否保存成功
        """
        try:
            目录 = os.path.dirname(输出路径)
            if 目录:
                os.makedirs(目录, exist_ok=True)
            
            with open(输出路径, 'w', encoding='utf-8') as f:
                json.dump(报告.to_dict(), f, ensure_ascii=False, indent=2)
            
            日志.info(f"JSON 报告已保存: {输出路径}")
            return True
        except Exception as e:
            日志.error(f"保存 JSON 报告失败: {e}")
            return False
    
    def 打印报告(self, 报告: 对比报告):
        """打印报告到控制台"""
        print(self.生成报告(报告))


def 运行基准测试(onnx模型路径: str = None, tflearn模型路径: str = None,
                 测试次数: int = 100, 使用GPU: bool = True,
                 输入形状: Tuple = (480, 270, 3),
                 输出目录: str = "日志/基准测试") -> 对比报告:
    """
    运行基准测试的便捷函数
    
    参数:
        onnx模型路径: ONNX 模型路径
        tflearn模型路径: TFLearn 模型路径
        测试次数: 测试迭代次数
        使用GPU: 是否使用 GPU
        输入形状: 输入图像形状
        输出目录: 报告输出目录
        
    返回:
        对比报告
    """
    测试器 = 性能基准测试器(
        测试次数=测试次数,
        输入形状=输入形状
    )
    
    报告 = 测试器.对比测试(
        onnx模型路径=onnx模型路径,
        tflearn模型路径=tflearn模型路径,
        使用GPU=使用GPU
    )
    
    # 生成报告
    时间戳 = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if 输出目录:
        文本报告路径 = os.path.join(输出目录, f"基准测试报告_{时间戳}.txt")
        json报告路径 = os.path.join(输出目录, f"基准测试报告_{时间戳}.json")
        
        测试器.生成报告(报告, 文本报告路径)
        测试器.保存JSON报告(报告, json报告路径)
    
    # 打印报告
    测试器.打印报告(报告)
    
    return 报告


def 快速测试ONNX(模型路径: str, 测试次数: int = 100, 使用GPU: bool = True) -> 延迟统计:
    """
    快速测试 ONNX 模型性能
    
    参数:
        模型路径: ONNX 模型路径
        测试次数: 测试次数
        使用GPU: 是否使用 GPU
        
    返回:
        延迟统计
    """
    try:
        from 核心.ONNX推理 import ONNX推理引擎
        
        引擎 = ONNX推理引擎(模型路径, 使用GPU=使用GPU)
        
        # 生成测试数据
        测试数据 = np.random.rand(480, 270, 3).astype(np.float32)
        
        # 预热
        for _ in range(10):
            引擎.预测(测试数据)
        
        # 测试
        测量器 = 延迟测量器()
        for _ in range(测试次数):
            测量器.测量(引擎.预测, 测试数据)
        
        测量器.打印统计("ONNX 推理延迟")
        return 测量器.获取统计(使用全部数据=True)
        
    except Exception as e:
        日志.error(f"快速测试失败: {e}")
        return 延迟统计()


# 命令行入口
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="推理性能基准测试")
    parser.add_argument("--onnx", type=str, help="ONNX 模型路径")
    parser.add_argument("--tflearn", type=str, help="TFLearn 模型路径")
    parser.add_argument("--iterations", type=int, default=100, help="测试迭代次数")
    parser.add_argument("--no-gpu", action="store_true", help="禁用 GPU")
    parser.add_argument("--output", type=str, default="日志/基准测试", help="输出目录")
    
    args = parser.parse_args()
    
    if not args.onnx and not args.tflearn:
        print("请指定至少一个模型路径 (--onnx 或 --tflearn)")
        exit(1)
    
    运行基准测试(
        onnx模型路径=args.onnx,
        tflearn模型路径=args.tflearn,
        测试次数=args.iterations,
        使用GPU=not args.no_gpu,
        输出目录=args.output
    )
