"""
类别权重平衡模块
解决训练数据中类别不平衡问题

功能:
- 类别分布分析
- 权重计算（多种策略）
- 数据采样（过采样/欠采样）
- 加权损失函数
"""

import os
import sys
import json
import numpy as np
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import Counter
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
日志 = logging.getLogger(__name__)

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from 配置.设置 import 总动作数, 动作定义, 数据保存路径
except ImportError:
    总动作数 = 9
    动作定义 = {}
    数据保存路径 = "数据"


# 动作映射字典
动作映射 = {i: 动作定义.get(i, {}).get("名称", f"动作{i}") for i in range(总动作数)}


@dataclass
class 类别统计信息:
    """单个类别的统计信息"""
    类别名称: str
    类别索引: int
    样本数量: int
    占比: float
    是否欠代表: bool = False


@dataclass
class 分析报告:
    """类别分布分析报告"""
    总样本数: int
    类别数量: int
    不平衡比率: float
    最大类别: str
    最小类别: str
    欠代表类别: List[str]
    建议: List[str]
    类别详情: List[类别统计信息] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            '总样本数': self.总样本数,
            '类别数量': self.类别数量,
            '不平衡比率': round(self.不平衡比率, 2),
            '最大类别': self.最大类别,
            '最小类别': self.最小类别,
            '欠代表类别': self.欠代表类别,
            '建议': self.建议
        }


class 权重策略(Enum):
    """权重计算策略"""
    逆频率 = "inverse_frequency"
    平方根逆频率 = "sqrt_inverse_frequency"
    有效样本数 = "effective_samples"


class 类别分析器:
    """分析训练数据中的类别分布"""
    
    def __init__(self, 数据路径: str = None):
        """
        初始化分析器
        
        参数:
            数据路径: 训练数据目录路径
        """
        self.数据路径 = 数据路径 or 数据保存路径
        self._类别统计: Dict[int, int] = {}
        self._总样本数: int = 0
        self._已分析: bool = False
    
    def 统计分布(self) -> Dict[int, int]:
        """
        统计各类别样本数量
        
        返回:
            {类别索引: 样本数} 字典
        """
        if self._已分析:
            return self._类别统计.copy()
        
        self._类别统计 = Counter()
        self._总样本数 = 0
        
        if not os.path.exists(self.数据路径):
            日志.warning(f"数据路径不存在: {self.数据路径}")
            return {}
        
        # 遍历数据文件
        for 文件名 in os.listdir(self.数据路径):
            if 文件名.endswith('.npy'):
                try:
                    文件路径 = os.path.join(self.数据路径, 文件名)
                    数据 = np.load(文件路径, allow_pickle=True)
                    
                    for _, 动作 in 数据:
                        if isinstance(动作, (list, np.ndarray)):
                            类别 = int(np.argmax(动作))
                        else:
                            类别 = int(动作)
                        
                        self._类别统计[类别] += 1
                        self._总样本数 += 1
                        
                except Exception as e:
                    日志.warning(f"加载 {文件名} 失败: {e}")
        
        self._已分析 = True
        日志.info(f"分析完成: {self._总样本数} 个样本, {len(self._类别统计)} 个类别")
        
        return self._类别统计.copy()

    def 计算不平衡比率(self) -> float:
        """
        计算不平衡比率
        
        返回:
            最大类别数量 / 最小类别数量
        """
        if not self._已分析:
            self.统计分布()
        
        if not self._类别统计:
            return 1.0
        
        数量列表 = list(self._类别统计.values())
        最大值 = max(数量列表)
        最小值 = min(数量列表) if min(数量列表) > 0 else 1
        
        return 最大值 / 最小值
    
    def 识别欠代表类别(self, 阈值: float = 0.05) -> List[str]:
        """
        识别严重欠代表的类别
        
        参数:
            阈值: 相对于最大类别的比例阈值
            
        返回:
            欠代表类别名称列表
        """
        if not self._已分析:
            self.统计分布()
        
        if not self._类别统计:
            return []
        
        最大数量 = max(self._类别统计.values())
        欠代表类别 = []
        
        for 类别, 数量 in self._类别统计.items():
            if 数量 / 最大数量 < 阈值:
                类别名 = 动作映射.get(类别, f"动作{类别}")
                欠代表类别.append(类别名)
        
        return 欠代表类别
    
    def 生成报告(self) -> 分析报告:
        """生成类别分布分析报告"""
        if not self._已分析:
            self.统计分布()
        
        if not self._类别统计:
            return 分析报告(
                总样本数=0, 类别数量=0, 不平衡比率=1.0,
                最大类别="", 最小类别="",
                欠代表类别=[], 建议=["数据目录为空，请先收集训练数据"]
            )
        
        # 找出最大和最小类别
        最大类别索引 = max(self._类别统计, key=self._类别统计.get)
        最小类别索引 = min(self._类别统计, key=self._类别统计.get)
        
        最大类别名 = 动作映射.get(最大类别索引, f"动作{最大类别索引}")
        最小类别名 = 动作映射.get(最小类别索引, f"动作{最小类别索引}")
        
        # 计算不平衡比率
        不平衡比率 = self.计算不平衡比率()
        
        # 识别欠代表类别
        欠代表类别 = self.识别欠代表类别()
        
        # 生成建议
        建议 = self._生成建议(不平衡比率, 欠代表类别)
        
        # 生成类别详情
        类别详情 = []
        for 类别, 数量 in sorted(self._类别统计.items()):
            类别名 = 动作映射.get(类别, f"动作{类别}")
            占比 = 数量 / self._总样本数 if self._总样本数 > 0 else 0
            是否欠代表 = 类别名 in 欠代表类别
            类别详情.append(类别统计信息(
                类别名称=类别名, 类别索引=类别,
                样本数量=数量, 占比=占比, 是否欠代表=是否欠代表
            ))
        
        return 分析报告(
            总样本数=self._总样本数,
            类别数量=len(self._类别统计),
            不平衡比率=不平衡比率,
            最大类别=最大类别名,
            最小类别=最小类别名,
            欠代表类别=欠代表类别,
            建议=建议,
            类别详情=类别详情
        )

    def _生成建议(self, 不平衡比率: float, 欠代表类别: List[str]) -> List[str]:
        """生成优化建议"""
        建议 = []
        
        if 不平衡比率 > 10:
            建议.append("数据严重不平衡，建议使用过采样或类别权重")
        elif 不平衡比率 > 5:
            建议.append("数据中度不平衡，建议使用类别权重")
        elif 不平衡比率 > 2:
            建议.append("数据轻度不平衡，可考虑使用类别权重")
        else:
            建议.append("数据分布较为均衡")
        
        if 欠代表类别:
            建议.append(f"欠代表类别: {', '.join(欠代表类别)}，建议增加这些类别的样本")
        
        return 建议
    
    def 可视化(self, 保存路径: str = None):
        """生成类别分布柱状图"""
        if not self._已分析:
            self.统计分布()
        
        try:
            import matplotlib.pyplot as plt
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
            plt.rcParams['axes.unicode_minus'] = False
            
            类别名列表 = [动作映射.get(i, f"动作{i}") for i in sorted(self._类别统计.keys())]
            数量列表 = [self._类别统计[i] for i in sorted(self._类别统计.keys())]
            
            plt.figure(figsize=(12, 6))
            bars = plt.bar(类别名列表, 数量列表, color='steelblue')
            
            # 标注数量
            for bar, 数量 in zip(bars, 数量列表):
                plt.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                        f'{数量}', ha='center', va='bottom')
            
            plt.xlabel('类别')
            plt.ylabel('样本数量')
            plt.title('训练数据类别分布')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            if 保存路径:
                plt.savefig(保存路径, dpi=150)
                日志.info(f"分布图已保存: {保存路径}")
            else:
                plt.show()
            
            plt.close()
            
        except ImportError:
            日志.warning("matplotlib 未安装，无法生成可视化图表")
    
    def 打印分布(self):
        """打印类别分布"""
        if not self._已分析:
            self.统计分布()
        
        print("\n📊 训练数据类别分布:")
        print("-" * 50)
        
        for 类别 in sorted(self._类别统计.keys()):
            数量 = self._类别统计[类别]
            百分比 = 数量 / self._总样本数 * 100 if self._总样本数 > 0 else 0
            类别名 = 动作映射.get(类别, f"动作{类别}")
            条形 = "█" * int(百分比 / 2)
            print(f"  {类别名:12s}: {数量:6d} ({百分比:5.1f}%) {条形}")
        
        print("-" * 50)
        print(f"  总计: {self._总样本数}")
        print(f"  不平衡比率: {self.计算不平衡比率():.2f}")


class 权重计算器:
    """
    计算类别权重
    
    支持三种权重计算策略:
    - 逆频率: w_i = N / (K * n_i)
    - 平方根逆频率: w_i = sqrt(N / (K * n_i))
    - 有效样本数: 基于 Class-Balanced Loss 论文
    """
    
    def __init__(self, 类别统计: Dict[int, int], 策略: 权重策略 = 权重策略.逆频率):
        """
        初始化权重计算器
        
        参数:
            类别统计: {类别索引: 样本数} 字典
            策略: 权重计算策略
        """
        self.类别统计 = 类别统计
        self.策略 = 策略
        self._权重: Dict[int, float] = {}
    
    def 计算权重(self) -> Dict[int, float]:
        """
        计算类别权重
        
        返回:
            {类别索引: 权重} 字典
        """
        if not self.类别统计:
            return {}
        
        总样本数 = sum(self.类别统计.values())
        类别数 = len(self.类别统计)
        
        if self.策略 == 权重策略.逆频率:
            self._权重 = self._计算逆频率权重(总样本数, 类别数)
        elif self.策略 == 权重策略.平方根逆频率:
            self._权重 = self._计算平方根逆频率权重(总样本数, 类别数)
        elif self.策略 == 权重策略.有效样本数:
            self._权重 = self._计算有效样本数权重(总样本数)
        
        return self._权重.copy()
    
    def _计算逆频率权重(self, 总样本数: int, 类别数: int) -> Dict[int, float]:
        """逆频率权重: w_i = N / (K * n_i)"""
        权重 = {}
        for 类别, 数量 in self.类别统计.items():
            if 数量 > 0:
                权重[类别] = 总样本数 / (类别数 * 数量)
            else:
                权重[类别] = 1.0
        return 权重
    
    def _计算平方根逆频率权重(self, 总样本数: int, 类别数: int) -> Dict[int, float]:
        """平方根逆频率权重: w_i = sqrt(N / (K * n_i))"""
        权重 = {}
        for 类别, 数量 in self.类别统计.items():
            if 数量 > 0:
                权重[类别] = np.sqrt(总样本数 / (类别数 * 数量))
            else:
                权重[类别] = 1.0
        return 权重
    
    def _计算有效样本数权重(self, 总样本数: int, beta: float = 0.9999) -> Dict[int, float]:
        """有效样本数权重 (Class-Balanced Loss)"""
        权重 = {}
        for 类别, 数量 in self.类别统计.items():
            if 数量 > 0:
                有效样本数 = (1 - beta ** 数量) / (1 - beta)
                权重[类别] = 1.0 / 有效样本数
            else:
                权重[类别] = 1.0
        return 权重
    
    def 归一化权重(self, 权重: Dict[int, float] = None) -> Dict[int, float]:
        """
        归一化权重使平均值为 1.0
        
        参数:
            权重: 原始权重字典，None 则使用已计算的权重
            
        返回:
            归一化后的权重字典
        """
        if 权重 is None:
            if not self._权重:
                self.计算权重()
            权重 = self._权重
        
        if not 权重:
            return {}
        
        平均值 = np.mean(list(权重.values()))
        
        if 平均值 == 0:
            return 权重.copy()
        
        归一化权重 = {类别: w / 平均值 for 类别, w in 权重.items()}
        return 归一化权重

    def 保存权重(self, 配置路径: str):
        """保存权重到配置文件"""
        if not self._权重:
            self.计算权重()
        
        归一化权重 = self.归一化权重()
        
        配置 = {
            "策略": self.策略.value,
            "类别权重": {str(k): round(v, 4) for k, v in 归一化权重.items()},
            "类别名称": {str(k): 动作映射.get(k, f"动作{k}") for k in 归一化权重.keys()}
        }
        
        with open(配置路径, 'w', encoding='utf-8') as f:
            json.dump(配置, f, ensure_ascii=False, indent=2)
        
        日志.info(f"权重已保存: {配置路径}")
    
    @staticmethod
    def 加载权重(配置路径: str) -> Dict[int, float]:
        """从配置文件加载权重"""
        if not os.path.exists(配置路径):
            日志.warning(f"配置文件不存在: {配置路径}")
            return {}
        
        with open(配置路径, 'r', encoding='utf-8') as f:
            配置 = json.load(f)
        
        权重 = {int(k): float(v) for k, v in 配置.get("类别权重", {}).items()}
        return 权重
    
    def 打印权重(self):
        """打印权重信息"""
        if not self._权重:
            self.计算权重()
        
        归一化权重 = self.归一化权重()
        
        print(f"\n⚖️  类别权重 (策略: {self.策略.value}):")
        print("-" * 40)
        
        for 类别 in sorted(归一化权重.keys()):
            权重值 = 归一化权重[类别]
            类别名 = 动作映射.get(类别, f"动作{类别}")
            条形 = "█" * int(权重值 * 5)
            print(f"  {类别名:12s}: {权重值:.4f} {条形}")


@dataclass
class 采样配置:
    """采样器配置"""
    目标比率: float = 1.0  # 目标平衡比率 (1.0 表示完全平衡)
    最大样本数: Optional[int] = None  # 每个类别的最大样本数
    打乱数据: bool = True  # 是否打乱采样后的数据
    随机种子: Optional[int] = None  # 随机种子，用于可重复性
    k_neighbors: int = 5  # SMOTE 算法的近邻数
    
    def to_dict(self) -> dict:
        return {
            '目标比率': self.目标比率,
            '最大样本数': self.最大样本数,
            '打乱数据': self.打乱数据,
            '随机种子': self.随机种子,
            'k_neighbors': self.k_neighbors
        }


class 采样器:
    """
    数据采样策略
    
    支持多种采样方法:
    - 随机过采样: 复制少数类别样本
    - 随机欠采样: 减少多数类别样本
    - 增强过采样: 类似 SMOTE，通过插值生成新样本
    - 知情欠采样: 保留多样化样本
    """
    
    def __init__(self, 数据集: List[Tuple[Any, Any]], 类别统计: Dict[int, int] = None,
                 配置: 采样配置 = None):
        """
        初始化采样器
        
        参数:
            数据集: [(图像, 标签), ...] 列表
            类别统计: {类别索引: 样本数} 字典，None 则自动统计
            配置: 采样配置对象
        """
        self.数据集 = 数据集
        self.配置 = 配置 or 采样配置()
        
        # 设置随机种子
        if self.配置.随机种子 is not None:
            np.random.seed(self.配置.随机种子)
        
        self._按类别分组()
        
        if 类别统计:
            self.类别统计 = 类别统计
        else:
            self.类别统计 = {类别: len(样本) for 类别, 样本 in self._类别数据.items()}
    
    def _按类别分组(self):
        """将数据按类别分组"""
        self._类别数据: Dict[int, List[Tuple[Any, Any]]] = {}
        
        for 样本 in self.数据集:
            图像, 标签 = 样本
            if isinstance(标签, (list, np.ndarray)):
                类别 = int(np.argmax(标签))
            else:
                类别 = int(标签)
            
            if 类别 not in self._类别数据:
                self._类别数据[类别] = []
            self._类别数据[类别].append(样本)
    
    def _获取标签(self, 标签) -> int:
        """获取类别索引"""
        if isinstance(标签, (list, np.ndarray)):
            return int(np.argmax(标签))
        return int(标签)
    
    def _打乱数据(self, 数据: List[Tuple[Any, Any]]) -> List[Tuple[Any, Any]]:
        """打乱数据顺序"""
        if self.配置.打乱数据:
            索引 = np.random.permutation(len(数据))
            return [数据[i] for i in 索引]
        return 数据
    
    def _获取最终数据集大小(self) -> int:
        """获取采样后的数据集大小"""
        return sum(len(样本) for 样本 in self._类别数据.values())

    def 随机过采样(self, 目标比率: float = None) -> List[Tuple[Any, Any]]:
        """
        对少数类别进行随机过采样
        
        参数:
            目标比率: 目标平衡比率 (1.0 表示完全平衡)，None 则使用配置值
            
        返回:
            平衡后的数据集
        """
        if not self._类别数据:
            return self.数据集.copy()
        
        目标比率 = 目标比率 if 目标比率 is not None else self.配置.目标比率
        
        最大数量 = max(len(样本) for 样本 in self._类别数据.values())
        目标数量 = int(最大数量 * 目标比率)
        
        平衡数据 = []
        
        for 类别, 样本列表 in self._类别数据.items():
            当前数量 = len(样本列表)
            
            if 当前数量 >= 目标数量:
                # 不需要过采样
                平衡数据.extend(样本列表)
            else:
                # 添加原始样本
                平衡数据.extend(样本列表)
                
                # 随机复制样本
                需要添加 = 目标数量 - 当前数量
                复制索引 = np.random.choice(当前数量, 需要添加, replace=True)
                for idx in 复制索引:
                    平衡数据.append(样本列表[idx])
        
        平衡数据 = self._打乱数据(平衡数据)
        日志.info(f"过采样完成: {len(self.数据集)} -> {len(平衡数据)} 样本")
        return 平衡数据
    
    def 随机欠采样(self, 最大样本数: int = None) -> List[Tuple[Any, Any]]:
        """
        对多数类别进行随机欠采样
        
        参数:
            最大样本数: 每个类别的最大样本数，None 则使用配置值或最小类别数量
            
        返回:
            平衡后的数据集
        """
        if not self._类别数据:
            return self.数据集.copy()
        
        if 最大样本数 is None:
            最大样本数 = self.配置.最大样本数
        
        if 最大样本数 is None:
            最大样本数 = min(len(样本) for 样本 in self._类别数据.values())
        
        平衡数据 = []
        
        for 类别, 样本列表 in self._类别数据.items():
            当前数量 = len(样本列表)
            
            if 当前数量 <= 最大样本数:
                平衡数据.extend(样本列表)
            else:
                # 随机选择样本
                选择索引 = np.random.choice(当前数量, 最大样本数, replace=False)
                for idx in 选择索引:
                    平衡数据.append(样本列表[idx])
        
        平衡数据 = self._打乱数据(平衡数据)
        日志.info(f"欠采样完成: {len(self.数据集)} -> {len(平衡数据)} 样本")
        return 平衡数据
    
    def 混合采样(self, 过采样比率: float = 0.5, 欠采样比率: float = 0.5) -> List[Tuple[Any, Any]]:
        """
        混合过采样和欠采样
        
        参数:
            过采样比率: 少数类别的目标比率
            欠采样比率: 多数类别的目标比率
            
        返回:
            平衡后的数据集
        """
        if not self._类别数据:
            return self.数据集.copy()
        
        数量列表 = [len(样本) for 样本 in self._类别数据.values()]
        中位数 = int(np.median(数量列表))
        
        过采样目标 = int(中位数 * 过采样比率)
        欠采样目标 = int(中位数 / 欠采样比率)
        
        平衡数据 = []
        
        for 类别, 样本列表 in self._类别数据.items():
            当前数量 = len(样本列表)
            
            if 当前数量 < 过采样目标:
                # 过采样
                平衡数据.extend(样本列表)
                需要添加 = 过采样目标 - 当前数量
                复制索引 = np.random.choice(当前数量, 需要添加, replace=True)
                for idx in 复制索引:
                    平衡数据.append(样本列表[idx])
            elif 当前数量 > 欠采样目标:
                # 欠采样
                选择索引 = np.random.choice(当前数量, 欠采样目标, replace=False)
                for idx in 选择索引:
                    平衡数据.append(样本列表[idx])
            else:
                平衡数据.extend(样本列表)
        
        平衡数据 = self._打乱数据(平衡数据)
        日志.info(f"混合采样完成: {len(self.数据集)} -> {len(平衡数据)} 样本")
        return 平衡数据
    
    def 增强过采样(self, 目标比率: float = None) -> List[Tuple[Any, Any]]:
        """
        对少数类别进行增强过采样（类似 SMOTE）
        
        通过在特征空间中对少数类别样本进行插值来生成新样本。
        对于图像数据，使用像素级插值。
        
        参数:
            目标比率: 目标平衡比率 (1.0 表示完全平衡)，None 则使用配置值
            
        返回:
            平衡后的数据集
        """
        if not self._类别数据:
            return self.数据集.copy()
        
        目标比率 = 目标比率 if 目标比率 is not None else self.配置.目标比率
        k_neighbors = self.配置.k_neighbors
        
        最大数量 = max(len(样本) for 样本 in self._类别数据.values())
        目标数量 = int(最大数量 * 目标比率)
        
        平衡数据 = []
        
        for 类别, 样本列表 in self._类别数据.items():
            当前数量 = len(样本列表)
            
            if 当前数量 >= 目标数量:
                # 不需要过采样
                平衡数据.extend(样本列表)
            else:
                # 添加原始样本
                平衡数据.extend(样本列表)
                
                # 生成合成样本
                需要添加 = 目标数量 - 当前数量
                
                # 提取特征（图像数据展平）
                特征列表 = []
                for 图像, _ in 样本列表:
                    if isinstance(图像, np.ndarray):
                        特征列表.append(图像.flatten().astype(np.float32))
                    else:
                        特征列表.append(np.array(图像).flatten().astype(np.float32))
                
                特征矩阵 = np.array(特征列表)
                
                # 生成合成样本
                for _ in range(需要添加):
                    # 随机选择一个样本
                    idx = np.random.randint(当前数量)
                    原始样本 = 样本列表[idx]
                    原始特征 = 特征矩阵[idx]
                    
                    # 找到 k 个最近邻
                    实际k = min(k_neighbors, 当前数量 - 1)
                    if 实际k < 1:
                        # 样本太少，直接复制
                        平衡数据.append(原始样本)
                        continue
                    
                    # 计算距离
                    距离 = np.linalg.norm(特征矩阵 - 原始特征, axis=1)
                    距离[idx] = np.inf  # 排除自身
                    近邻索引 = np.argsort(距离)[:实际k]
                    
                    # 随机选择一个近邻
                    近邻idx = np.random.choice(近邻索引)
                    近邻特征 = 特征矩阵[近邻idx]
                    
                    # 在两个样本之间插值
                    alpha = np.random.random()
                    合成特征 = 原始特征 + alpha * (近邻特征 - 原始特征)
                    
                    # 恢复图像形状
                    原始图像 = 原始样本[0]
                    if isinstance(原始图像, np.ndarray):
                        合成图像 = 合成特征.reshape(原始图像.shape).astype(原始图像.dtype)
                    else:
                        合成图像 = 合成特征.reshape(np.array(原始图像).shape)
                    
                    平衡数据.append((合成图像, 原始样本[1]))
        
        平衡数据 = self._打乱数据(平衡数据)
        日志.info(f"增强过采样完成: {len(self.数据集)} -> {len(平衡数据)} 样本")
        return 平衡数据
    
    def 知情欠采样(self, 最大样本数: int = None) -> List[Tuple[Any, Any]]:
        """
        对多数类别进行知情欠采样（保留多样化样本）
        
        使用聚类方法选择最具代表性的样本，而不是随机选择。
        这样可以保留数据的多样性。
        
        参数:
            最大样本数: 每个类别的最大样本数，None 则使用配置值或最小类别数量
            
        返回:
            平衡后的数据集
        """
        if not self._类别数据:
            return self.数据集.copy()
        
        if 最大样本数 is None:
            最大样本数 = self.配置.最大样本数
        
        if 最大样本数 is None:
            最大样本数 = min(len(样本) for 样本 in self._类别数据.values())
        
        平衡数据 = []
        
        for 类别, 样本列表 in self._类别数据.items():
            当前数量 = len(样本列表)
            
            if 当前数量 <= 最大样本数:
                平衡数据.extend(样本列表)
            else:
                # 提取特征
                特征列表 = []
                for 图像, _ in 样本列表:
                    if isinstance(图像, np.ndarray):
                        特征列表.append(图像.flatten().astype(np.float32))
                    else:
                        特征列表.append(np.array(图像).flatten().astype(np.float32))
                
                特征矩阵 = np.array(特征列表)
                
                # 使用 K-Means 聚类选择代表性样本
                选择索引 = self._kmeans_选择(特征矩阵, 最大样本数)
                
                for idx in 选择索引:
                    平衡数据.append(样本列表[idx])
        
        平衡数据 = self._打乱数据(平衡数据)
        日志.info(f"知情欠采样完成: {len(self.数据集)} -> {len(平衡数据)} 样本")
        return 平衡数据
    
    def _kmeans_选择(self, 特征矩阵: np.ndarray, k: int) -> List[int]:
        """
        使用简化的 K-Means++ 初始化选择 k 个代表性样本
        
        参数:
            特征矩阵: 样本特征矩阵
            k: 要选择的样本数
            
        返回:
            选择的样本索引列表
        """
        n_samples = len(特征矩阵)
        
        if k >= n_samples:
            return list(range(n_samples))
        
        # K-Means++ 初始化
        选择索引 = []
        
        # 随机选择第一个中心
        第一个 = np.random.randint(n_samples)
        选择索引.append(第一个)
        
        # 选择剩余的中心
        for _ in range(k - 1):
            # 计算每个点到最近中心的距离
            距离 = np.full(n_samples, np.inf)
            for idx in 选择索引:
                d = np.linalg.norm(特征矩阵 - 特征矩阵[idx], axis=1)
                距离 = np.minimum(距离, d)
            
            # 已选择的点距离设为 0
            for idx in 选择索引:
                距离[idx] = 0
            
            # 按距离的平方作为概率选择下一个中心
            概率 = 距离 ** 2
            概率总和 = 概率.sum()
            
            if 概率总和 > 0:
                概率 = 概率 / 概率总和
                下一个 = np.random.choice(n_samples, p=概率)
            else:
                # 所有点都已选择或距离为 0
                剩余 = [i for i in range(n_samples) if i not in 选择索引]
                if 剩余:
                    下一个 = np.random.choice(剩余)
                else:
                    break
            
            选择索引.append(下一个)
        
        return 选择索引
    
    def 获取采样统计(self) -> Dict[str, Any]:
        """
        获取采样统计信息
        
        返回:
            包含采样统计的字典
        """
        统计 = {
            '原始样本数': len(self.数据集),
            '类别数': len(self._类别数据),
            '各类别样本数': {类别: len(样本) for 类别, 样本 in self._类别数据.items()},
            '配置': self.配置.to_dict()
        }
        return 统计
    
    def 报告最终数据集大小(self, 平衡数据: List[Tuple[Any, Any]]) -> Dict[str, int]:
        """
        报告平衡后的数据集大小
        
        参数:
            平衡数据: 平衡后的数据集
            
        返回:
            各类别样本数统计
        """
        统计 = {}
        for 样本 in 平衡数据:
            _, 标签 = 样本
            类别 = self._获取标签(标签)
            统计[类别] = 统计.get(类别, 0) + 1
        
        日志.info(f"最终数据集大小: {len(平衡数据)} 样本")
        for 类别, 数量 in sorted(统计.items()):
            类别名 = 动作映射.get(类别, f"动作{类别}")
            日志.info(f"  {类别名}: {数量}")
        
        return 统计


class 加权交叉熵损失:
    """
    带类别权重的交叉熵损失函数
    
    支持两种使用方式:
    1. NumPy 模式: 直接调用计算损失值（用于评估）
    2. TensorFlow 模式: 返回 TensorFlow 损失函数（用于训练）
    
    使用示例:
        # NumPy 模式
        损失函数 = 加权交叉熵损失({0: 0.5, 1: 2.0, 2: 1.5})
        损失值 = 损失函数(预测, 标签)
        
        # TensorFlow 模式 (用于 TFLearn)
        tf_损失 = 损失函数.获取tensorflow损失函数()
    """
    
    def __init__(self, 类别权重: Dict[int, float], 类别数: int = None, 设备: str = "cpu"):
        """
        初始化加权损失函数
        
        参数:
            类别权重: {类别索引: 权重} 字典
            类别数: 总类别数，None 则从权重推断
            设备: 计算设备 ("cpu" 或 "cuda"/"gpu")，用于 TensorFlow 设备放置
        """
        self.类别权重 = 类别权重
        self.类别数 = 类别数 or (max(类别权重.keys()) + 1 if 类别权重 else 1)
        self.设备 = 设备
        
        # 转换为权重数组
        self._权重数组 = np.ones(self.类别数, dtype=np.float32)
        for 类别, 权重 in 类别权重.items():
            if 0 <= 类别 < self.类别数:
                self._权重数组[类别] = float(权重)
        
        # TensorFlow 相关变量（延迟初始化）
        self._tf_权重张量 = None
        self._tf_损失函数 = None
    
    def __call__(self, 预测: np.ndarray, 标签: np.ndarray) -> float:
        """
        计算加权交叉熵损失 (NumPy 模式)
        
        参数:
            预测: 模型预测输出 (softmax 后的概率)，形状 [batch_size, num_classes]
            标签: 真实标签 (one-hot 或类别索引)
            
        返回:
            加权损失值 (标量)
        """
        # 确保预测值在有效范围内，避免 log(0)
        预测 = np.clip(预测, 1e-7, 1 - 1e-7)
        
        # 处理标签格式
        if 标签.ndim == 1 or (标签.ndim == 2 and 标签.shape[1] == 1):
            # 类别索引格式
            if 标签.ndim == 2:
                标签 = 标签.flatten()
            批量大小 = len(标签)
            损失 = 0.0
            for i in range(批量大小):
                类别 = int(标签[i])
                if 0 <= 类别 < self.类别数:
                    权重 = self._权重数组[类别]
                    损失 -= 权重 * np.log(预测[i, 类别])
            return 损失 / 批量大小 if 批量大小 > 0 else 0.0
        else:
            # one-hot 格式
            批量大小 = 标签.shape[0]
            损失 = 0.0
            for i in range(批量大小):
                类别 = int(np.argmax(标签[i]))
                if 0 <= 类别 < self.类别数:
                    权重 = self._权重数组[类别]
                    损失 -= 权重 * np.log(预测[i, 类别])
            return 损失 / 批量大小 if 批量大小 > 0 else 0.0
    
    def 计算批次损失(self, 预测: np.ndarray, 标签: np.ndarray) -> np.ndarray:
        """
        计算每个样本的加权损失 (NumPy 模式)
        
        参数:
            预测: 模型预测输出，形状 [batch_size, num_classes]
            标签: 真实标签 (one-hot 或类别索引)
            
        返回:
            每个样本的损失值，形状 [batch_size]
        """
        预测 = np.clip(预测, 1e-7, 1 - 1e-7)
        批量大小 = 预测.shape[0]
        损失数组 = np.zeros(批量大小)
        
        # 处理标签格式
        if 标签.ndim == 1 or (标签.ndim == 2 and 标签.shape[1] == 1):
            if 标签.ndim == 2:
                标签 = 标签.flatten()
            for i in range(批量大小):
                类别 = int(标签[i])
                if 0 <= 类别 < self.类别数:
                    权重 = self._权重数组[类别]
                    损失数组[i] = -权重 * np.log(预测[i, 类别])
        else:
            for i in range(批量大小):
                类别 = int(np.argmax(标签[i]))
                if 0 <= 类别 < self.类别数:
                    权重 = self._权重数组[类别]
                    损失数组[i] = -权重 * np.log(预测[i, 类别])
        
        return 损失数组
    
    def 获取权重数组(self) -> np.ndarray:
        """
        获取权重数组（用于框架集成）
        
        返回:
            权重数组，形状 [num_classes]
        """
        return self._权重数组.copy()
    
    def 获取tensorflow损失函数(self):
        """
        获取 TensorFlow 兼容的损失函数
        
        返回:
            可用于 TFLearn regression 层的损失函数
            
        使用示例:
            损失函数 = 加权交叉熵损失({0: 0.5, 1: 2.0})
            tf_loss = 损失函数.获取tensorflow损失函数()
            
            # 在 TFLearn 中使用
            network = regression(network, optimizer='adam',
                               loss=tf_loss,
                               learning_rate=0.001)
        """
        try:
            import tensorflow as tf
            
            # 创建权重张量
            权重张量 = tf.constant(self._权重数组, dtype=tf.float32, name='class_weights')
            
            def 加权损失(y_pred, y_true):
                """
                TensorFlow 加权交叉熵损失函数
                
                参数:
                    y_pred: 预测值张量，形状 [batch_size, num_classes]
                    y_true: 真实标签张量，形状 [batch_size, num_classes] (one-hot)
                    
                返回:
                    损失张量 (标量)
                """
                # 裁剪预测值，避免 log(0)
                y_pred = tf.clip_by_value(y_pred, 1e-7, 1 - 1e-7)
                
                # 获取每个样本的真实类别索引
                类别索引 = tf.argmax(y_true, axis=1)
                
                # 获取每个样本对应的权重
                样本权重 = tf.gather(权重张量, 类别索引)
                
                # 计算交叉熵损失
                交叉熵 = -tf.reduce_sum(y_true * tf.math.log(y_pred), axis=1)
                
                # 应用权重
                加权损失值 = 样本权重 * 交叉熵
                
                # 返回平均损失
                return tf.reduce_mean(加权损失值)
            
            self._tf_损失函数 = 加权损失
            return 加权损失
            
        except ImportError:
            日志.error("TensorFlow 未安装，无法创建 TensorFlow 损失函数")
            raise ImportError("需要安装 TensorFlow 才能使用此功能")
    
    def 获取tflearn损失函数(self):
        """
        获取 TFLearn 兼容的损失函数（别名）
        
        返回:
            可用于 TFLearn regression 层的损失函数
        """
        return self.获取tensorflow损失函数()
    
    def 打印权重信息(self):
        """打印权重信息"""
        print(f"\n⚖️  加权交叉熵损失函数")
        print(f"   类别数: {self.类别数}")
        print(f"   设备: {self.设备}")
        print("-" * 40)
        for i, 权重 in enumerate(self._权重数组):
            类别名 = 动作映射.get(i, f"动作{i}")
            条形 = "█" * int(权重 * 5)
            print(f"   {类别名:12s}: {权重:.4f} {条形}")
    
    @classmethod
    def 从配置创建(cls, 配置路径: str, 类别数: int = None, 设备: str = "cpu"):
        """
        从配置文件创建加权损失函数
        
        参数:
            配置路径: 权重配置文件路径
            类别数: 总类别数
            设备: 计算设备
            
        返回:
            加权交叉熵损失实例
        """
        权重 = 权重计算器.加载权重(配置路径)
        return cls(权重, 类别数, 设备)
    
    @classmethod
    def 从数据创建(cls, 数据路径: str = None, 策略: 权重策略 = 权重策略.逆频率, 
                  类别数: int = None, 设备: str = "cpu"):
        """
        从训练数据自动创建加权损失函数
        
        参数:
            数据路径: 训练数据目录路径
            策略: 权重计算策略
            类别数: 总类别数
            设备: 计算设备
            
        返回:
            加权交叉熵损失实例
        """
        分析器 = 类别分析器(数据路径)
        统计 = 分析器.统计分布()
        
        if not 统计:
            日志.warning("未找到训练数据，使用默认权重 (1.0)")
            return cls({}, 类别数 or 总动作数, 设备)
        
        计算器 = 权重计算器(统计, 策略)
        归一化权重 = 计算器.归一化权重(计算器.计算权重())
        
        return cls(归一化权重, 类别数 or len(归一化权重), 设备)


# ============== 兼容旧版本的函数 ==============

def 从数据计算初始权重(数据路径: str = None) -> List[float]:
    """
    根据训练数据计算初始权重 (反比于类别频率)
    
    参数:
        数据路径: 数据目录路径
    
    返回:
        初始权重列表
    """
    分析器 = 类别分析器(数据路径)
    统计 = 分析器.统计分布()
    
    if not 统计:
        return [1.0] * 总动作数
    
    计算器 = 权重计算器(统计, 权重策略.逆频率)
    权重字典 = 计算器.归一化权重(计算器.计算权重())
    
    # 转换为列表
    权重列表 = [权重字典.get(i, 1.0) for i in range(总动作数)]
    return 权重列表


def 显示数据分布(数据路径: str = None):
    """显示训练数据的类别分布"""
    分析器 = 类别分析器(数据路径)
    分析器.打印分布()


def 主程序():
    """主程序入口"""
    print("\n" + "=" * 50)
    print("⚖️  类别权重平衡工具")
    print("=" * 50)
    
    print("\n请选择功能:")
    print("  1. 显示数据分布")
    print("  2. 计算类别权重")
    print("  3. 生成分析报告")
    print("  4. 可视化分布")
    
    选择 = input("\n请输入选项 (1/2/3/4): ").strip()
    
    if 选择 == '1':
        显示数据分布()
    
    elif 选择 == '2':
        print("\n选择权重计算策略:")
        print("  1. 逆频率 (inverse_frequency)")
        print("  2. 平方根逆频率 (sqrt_inverse_frequency)")
        print("  3. 有效样本数 (effective_samples)")
        
        策略选择 = input("\n请输入选项 (1/2/3): ").strip()
        策略映射 = {'1': 权重策略.逆频率, '2': 权重策略.平方根逆频率, '3': 权重策略.有效样本数}
        策略 = 策略映射.get(策略选择, 权重策略.逆频率)
        
        分析器 = 类别分析器()
        统计 = 分析器.统计分布()
        
        if 统计:
            计算器 = 权重计算器(统计, 策略)
            计算器.计算权重()
            计算器.打印权重()
            
            保存 = input("\n是否保存权重配置? (y/n): ").strip().lower()
            if 保存 == 'y':
                计算器.保存权重("配置/类别权重.json")
        else:
            print("❌ 未找到训练数据")
    
    elif 选择 == '3':
        分析器 = 类别分析器()
        报告 = 分析器.生成报告()
        
        print("\n📋 分析报告:")
        print("-" * 50)
        print(f"  总样本数: {报告.总样本数}")
        print(f"  类别数量: {报告.类别数量}")
        print(f"  不平衡比率: {报告.不平衡比率:.2f}")
        print(f"  最大类别: {报告.最大类别}")
        print(f"  最小类别: {报告.最小类别}")
        print(f"  欠代表类别: {', '.join(报告.欠代表类别) or '无'}")
        print("\n建议:")
        for 建议 in 报告.建议:
            print(f"  • {建议}")
    
    elif 选择 == '4':
        分析器 = 类别分析器()
        分析器.统计分布()
        
        保存路径 = input("\n输入保存路径 (留空则显示): ").strip()
        分析器.可视化(保存路径 if 保存路径 else None)


# ============== 类别别名（向后兼容） ==============
# 为了兼容旧代码中使用的 "类别权重计算器" 名称
类别权重计算器 = 权重计算器


if __name__ == "__main__":
    主程序()
