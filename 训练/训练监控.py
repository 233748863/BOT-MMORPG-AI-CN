"""
训练监控模块

提供训练过程中的指标收集、实时可视化和健康状态监控功能。

主要组件:
- 指标记录器: 记录训练过程中的各项指标
- 实时图表: 动态更新的训练曲线图
- 训练监控器: 监控训练健康状况
- 终端输出器: 优化的终端训练输出
- 可视化回调: 训练可视化回调函数
- 历史数据管理器: 管理和比较多个训练历史
"""

import os
import json
import time
import glob
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from datetime import datetime


@dataclass
class 批次指标:
    """批次级别的训练指标"""
    批次: int
    loss: float
    时间戳: float = field(default_factory=time.time)
    其他指标: Dict[str, float] = field(default_factory=dict)


@dataclass
class 轮次指标:
    """轮次级别的训练指标"""
    轮次: int
    训练loss: float
    验证loss: Optional[float] = None
    训练准确率: Optional[float] = None
    验证准确率: Optional[float] = None
    学习率: Optional[float] = None
    耗时: float = 0.0
    时间戳: float = field(default_factory=time.time)


class 指标记录器:
    """
    记录训练过程中的各项指标
    
    功能:
    - 记录每个批次的 loss 值 (需求 1.1)
    - 记录每个轮次的准确率 (需求 1.2)
    - 记录验证 loss 和准确率 (需求 1.3)
    - 记录学习率变化 (需求 1.4)
    - 保存指标到日志文件 (需求 1.5)
    """
    
    def __init__(self, 日志目录: str = "日志/训练"):
        """
        初始化记录器
        
        参数:
            日志目录: 日志文件保存目录
        """
        self.日志目录 = 日志目录
        self._批次历史: List[批次指标] = []
        self._轮次历史: List[轮次指标] = []
        self._当前轮次: int = 0
        self._训练开始时间: Optional[float] = None
        self._轮次开始时间: Optional[float] = None
        
        # 确保日志目录存在
        if 日志目录:
            os.makedirs(日志目录, exist_ok=True)
    
    def 记录批次(self, 批次: int, loss: float, **其他指标) -> None:
        """
        记录每个批次的指标 (需求 1.1)
        
        参数:
            批次: 当前批次号
            loss: 损失值
            其他指标: 其他需要记录的指标
        """
        指标 = 批次指标(
            批次=批次,
            loss=loss,
            时间戳=time.time(),
            其他指标=其他指标
        )
        self._批次历史.append(指标)
    
    def 记录轮次(self, 轮次: int, 训练loss: float, 
                 验证loss: Optional[float] = None,
                 训练准确率: Optional[float] = None, 
                 验证准确率: Optional[float] = None,
                 学习率: Optional[float] = None) -> None:
        """
        记录每个轮次的指标 (需求 1.2, 1.3, 1.4)
        
        参数:
            轮次: 当前轮次号
            训练loss: 训练损失
            验证loss: 验证损失
            训练准确率: 训练准确率
            验证准确率: 验证准确率
            学习率: 当前学习率
        """
        # 计算轮次耗时
        耗时 = 0.0
        if self._轮次开始时间 is not None:
            耗时 = time.time() - self._轮次开始时间
        
        指标 = 轮次指标(
            轮次=轮次,
            训练loss=训练loss,
            验证loss=验证loss,
            训练准确率=训练准确率,
            验证准确率=验证准确率,
            学习率=学习率,
            耗时=耗时,
            时间戳=time.time()
        )
        self._轮次历史.append(指标)
        self._当前轮次 = 轮次
    
    def 开始轮次(self) -> None:
        """标记轮次开始，用于计算耗时"""
        self._轮次开始时间 = time.time()
    
    def 开始训练(self) -> None:
        """标记训练开始"""
        self._训练开始时间 = time.time()
    
    def 获取历史(self, 指标名: str) -> List[float]:
        """
        获取指定指标的历史记录
        
        参数:
            指标名: 指标名称，支持 'loss', '训练loss', '验证loss', 
                   '训练准确率', '验证准确率', '学习率'
        
        返回:
            指标值列表
        """
        if 指标名 == 'loss' or 指标名 == '批次loss':
            return [m.loss for m in self._批次历史]
        elif 指标名 == '训练loss':
            return [m.训练loss for m in self._轮次历史]
        elif 指标名 == '验证loss':
            return [m.验证loss for m in self._轮次历史 if m.验证loss is not None]
        elif 指标名 == '训练准确率':
            return [m.训练准确率 for m in self._轮次历史 if m.训练准确率 is not None]
        elif 指标名 == '验证准确率':
            return [m.验证准确率 for m in self._轮次历史 if m.验证准确率 is not None]
        elif 指标名 == '学习率':
            return [m.学习率 for m in self._轮次历史 if m.学习率 is not None]
        else:
            return []
    
    def 获取批次历史(self) -> List[批次指标]:
        """获取所有批次指标"""
        return self._批次历史.copy()
    
    def 获取轮次历史(self) -> List[轮次指标]:
        """获取所有轮次指标"""
        return self._轮次历史.copy()
    
    def 获取最新批次指标(self) -> Optional[批次指标]:
        """获取最新的批次指标"""
        if self._批次历史:
            return self._批次历史[-1]
        return None
    
    def 获取最新轮次指标(self) -> Optional[轮次指标]:
        """获取最新的轮次指标"""
        if self._轮次历史:
            return self._轮次历史[-1]
        return None
    
    def 获取训练时长(self) -> float:
        """获取训练总时长（秒）"""
        if self._训练开始时间 is None:
            return 0.0
        return time.time() - self._训练开始时间
    
    def 清空(self) -> None:
        """清空所有历史记录"""
        self._批次历史.clear()
        self._轮次历史.clear()
        self._当前轮次 = 0
        self._训练开始时间 = None
        self._轮次开始时间 = None
    
    def _生成日志文件名(self) -> str:
        """生成带时间戳的日志文件名"""
        时间戳 = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"训练日志_{时间戳}.json"
    
    def 保存(self, 文件路径: Optional[str] = None) -> str:
        """
        保存指标到文件 (需求 1.5)
        
        参数:
            文件路径: 可选的文件路径，如果不指定则自动生成
        
        返回:
            保存的文件路径
        """
        if 文件路径 is None:
            文件路径 = os.path.join(self.日志目录, self._生成日志文件名())
        
        # 确保目录存在
        目录 = os.path.dirname(文件路径)
        if 目录:
            os.makedirs(目录, exist_ok=True)
        
        # 构建保存数据
        数据 = {
            "元信息": {
                "保存时间": datetime.now().isoformat(),
                "训练时长": self.获取训练时长(),
                "总批次数": len(self._批次历史),
                "总轮次数": len(self._轮次历史)
            },
            "批次历史": [asdict(m) for m in self._批次历史],
            "轮次历史": [asdict(m) for m in self._轮次历史]
        }
        
        with open(文件路径, 'w', encoding='utf-8') as f:
            json.dump(数据, f, ensure_ascii=False, indent=2)
        
        return 文件路径
    
    def 加载(self, 日志路径: str) -> bool:
        """
        从文件加载历史指标 (需求 1.5)
        
        参数:
            日志路径: 日志文件路径
        
        返回:
            是否加载成功
        """
        if not os.path.exists(日志路径):
            return False
        
        try:
            with open(日志路径, 'r', encoding='utf-8') as f:
                数据 = json.load(f)
            
            # 清空现有数据
            self.清空()
            
            # 加载批次历史
            for 项 in 数据.get("批次历史", []):
                指标 = 批次指标(
                    批次=项["批次"],
                    loss=项["loss"],
                    时间戳=项.get("时间戳", 0.0),
                    其他指标=项.get("其他指标", {})
                )
                self._批次历史.append(指标)
            
            # 加载轮次历史
            for 项 in 数据.get("轮次历史", []):
                指标 = 轮次指标(
                    轮次=项["轮次"],
                    训练loss=项["训练loss"],
                    验证loss=项.get("验证loss"),
                    训练准确率=项.get("训练准确率"),
                    验证准确率=项.get("验证准确率"),
                    学习率=项.get("学习率"),
                    耗时=项.get("耗时", 0.0),
                    时间戳=项.get("时间戳", 0.0)
                )
                self._轮次历史.append(指标)
            
            # 更新当前轮次
            if self._轮次历史:
                self._当前轮次 = self._轮次历史[-1].轮次
            
            return True
            
        except (json.JSONDecodeError, KeyError, TypeError, UnicodeDecodeError) as e:
            print(f"⚠️ 加载日志文件失败: {e}")
            return False
    
    def __len__(self) -> int:
        """返回记录的批次数量"""
        return len(self._批次历史)
    
    def __repr__(self) -> str:
        return f"指标记录器(批次数={len(self._批次历史)}, 轮次数={len(self._轮次历史)})"


class 实时图表:
    """
    实时更新的训练曲线图
    
    功能:
    - 显示实时更新的 loss 曲线 (需求 2.1)
    - 在同一图表上显示训练和验证指标 (需求 2.2)
    - 支持在不同子图中显示多个指标 (需求 2.3)
    - 按可配置的间隔更新 (需求 2.4)
    - 不阻塞训练过程 (需求 2.5)
    """
    
    # 默认图表配置
    默认配置 = {
        "图表宽度": 12,
        "图表高度": 8,
        "线条宽度": 1.5,
        "标记大小": 4,
        "网格透明度": 0.3,
        "训练颜色": "#2196F3",  # 蓝色
        "验证颜色": "#FF9800",  # 橙色
        "历史颜色": "#9E9E9E",  # 灰色
        "字体大小": 10,
        "标题字体大小": 12,
    }
    
    def __init__(self, 更新间隔: int = 10, 图表配置: Optional[Dict[str, Any]] = None):
        """
        初始化实时图表
        
        参数:
            更新间隔: 每隔多少批次更新一次
            图表配置: 图表显示配置
        """
        self.更新间隔 = 更新间隔
        self.配置 = {**self.默认配置, **(图表配置 or {})}
        
        # 图表状态
        self._已启动 = False
        self._图表 = None
        self._子图列表: List[Any] = []
        self._子图配置: Dict[str, Dict[str, Any]] = {}
        self._历史数据: List[Dict[str, Any]] = []
        self._上次更新批次 = 0
        
        # matplotlib 相关
        self._plt = None
        self._fig = None
        self._axes: Dict[str, Any] = {}
        self._lines: Dict[str, Any] = {}
        
    def _导入matplotlib(self) -> bool:
        """
        延迟导入 matplotlib，避免在不需要图表时加载
        
        返回:
            是否导入成功
        """
        if self._plt is not None:
            return True
            
        try:
            import matplotlib
            # 使用非阻塞后端
            matplotlib.use('TkAgg')
            import matplotlib.pyplot as plt
            self._plt = plt
            
            # 设置中文字体支持
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
            
            return True
        except ImportError as e:
            print(f"⚠️ 无法导入 matplotlib: {e}")
            return False
        except Exception as e:
            print(f"⚠️ matplotlib 初始化失败: {e}")
            return False
    
    def 添加子图(self, 名称: str, 指标列表: List[str], 
                 标题: Optional[str] = None,
                 y轴标签: Optional[str] = None) -> None:
        """
        添加子图配置 (需求 2.3)
        
        参数:
            名称: 子图名称（唯一标识）
            指标列表: 要显示的指标名称列表
            标题: 子图标题
            y轴标签: Y轴标签
        """
        self._子图配置[名称] = {
            "指标列表": 指标列表,
            "标题": 标题 or 名称,
            "y轴标签": y轴标签 or "值"
        }
    
    def 启动(self) -> bool:
        """
        启动图表窗口（非阻塞）(需求 2.5)
        
        返回:
            是否启动成功
        """
        if self._已启动:
            return True
            
        if not self._导入matplotlib():
            return False
        
        try:
            # 启用交互模式（非阻塞）
            self._plt.ion()
            
            # 如果没有配置子图，使用默认配置
            if not self._子图配置:
                self.添加子图("loss", ["批次loss"], 标题="Loss 曲线", y轴标签="Loss")
            
            # 创建图表
            子图数量 = len(self._子图配置)
            self._fig, axes = self._plt.subplots(
                子图数量, 1,
                figsize=(self.配置["图表宽度"], self.配置["图表高度"]),
                squeeze=False
            )
            
            # 设置窗口标题
            self._fig.canvas.manager.set_window_title("训练监控 - 实时图表")
            
            # 初始化每个子图
            for idx, (名称, 配置) in enumerate(self._子图配置.items()):
                ax = axes[idx, 0]
                self._axes[名称] = ax
                
                ax.set_title(配置["标题"], fontsize=self.配置["标题字体大小"])
                ax.set_xlabel("批次/轮次", fontsize=self.配置["字体大小"])
                ax.set_ylabel(配置["y轴标签"], fontsize=self.配置["字体大小"])
                ax.grid(True, alpha=self.配置["网格透明度"])
                
                # 为每个指标创建空线条
                self._lines[名称] = {}
                for 指标名 in 配置["指标列表"]:
                    颜色 = self._获取指标颜色(指标名)
                    line, = ax.plot([], [], 
                                   label=指标名,
                                   color=颜色,
                                   linewidth=self.配置["线条宽度"])
                    self._lines[名称][指标名] = line
                
                ax.legend(loc='upper right', fontsize=self.配置["字体大小"])
            
            self._plt.tight_layout()
            self._fig.canvas.draw()
            self._fig.canvas.flush_events()
            
            self._已启动 = True
            return True
            
        except Exception as e:
            print(f"⚠️ 启动图表失败: {e}")
            self._已启动 = False
            return False
    
    def _获取指标颜色(self, 指标名: str) -> str:
        """根据指标名称返回对应颜色"""
        if "验证" in 指标名:
            return self.配置["验证颜色"]
        elif "历史" in 指标名:
            return self.配置["历史颜色"]
        else:
            return self.配置["训练颜色"]
    
    def 更新(self, 指标记录器实例: '指标记录器', 强制更新: bool = False) -> bool:
        """
        更新图表数据 (需求 2.1, 2.4)
        
        参数:
            指标记录器实例: 包含最新数据的记录器
            强制更新: 是否强制更新（忽略更新间隔）
        
        返回:
            是否更新成功
        """
        if not self._已启动:
            return False
        
        # 检查是否需要更新
        当前批次 = len(指标记录器实例)
        if not 强制更新 and (当前批次 - self._上次更新批次) < self.更新间隔:
            return True
        
        try:
            # 检查窗口是否仍然打开
            if not self._plt.fignum_exists(self._fig.number):
                self._已启动 = False
                return False
            
            # 更新每个子图
            for 名称, 配置 in self._子图配置.items():
                ax = self._axes[名称]
                
                for 指标名 in 配置["指标列表"]:
                    # 获取数据
                    数据 = 指标记录器实例.获取历史(指标名)
                    if not 数据:
                        continue
                    
                    # 更新线条数据
                    line = self._lines[名称].get(指标名)
                    if line:
                        x数据 = list(range(len(数据)))
                        line.set_data(x数据, 数据)
                
                # 自动调整坐标轴范围
                ax.relim()
                ax.autoscale_view()
            
            # 刷新图表
            self._fig.canvas.draw_idle()
            self._fig.canvas.flush_events()
            
            self._上次更新批次 = 当前批次
            return True
            
        except Exception as e:
            print(f"⚠️ 更新图表失败: {e}")
            return False
    
    def 叠加历史(self, 历史数据: Dict[str, List[float]], 标签: str) -> bool:
        """
        叠加历史训练数据 (需求 5.1, 5.2)
        
        参数:
            历史数据: 历史指标数据，格式为 {指标名: [值列表]}
            标签: 历史数据标签
        
        返回:
            是否叠加成功
        """
        if not self._已启动:
            return False
        
        try:
            # 保存历史数据引用
            self._历史数据.append({
                "数据": 历史数据,
                "标签": 标签
            })
            
            # 在每个相关子图上添加历史曲线
            for 名称, 配置 in self._子图配置.items():
                ax = self._axes[名称]
                
                for 指标名 in 配置["指标列表"]:
                    if 指标名 in 历史数据:
                        数据 = 历史数据[指标名]
                        x数据 = list(range(len(数据)))
                        
                        # 添加历史曲线（使用虚线和较低透明度）
                        ax.plot(x数据, 数据,
                               label=f"{标签} - {指标名}",
                               color=self.配置["历史颜色"],
                               linewidth=self.配置["线条宽度"] * 0.8,
                               linestyle='--',
                               alpha=0.6)
                
                # 更新图例
                ax.legend(loc='upper right', fontsize=self.配置["字体大小"])
            
            # 刷新图表
            self._fig.canvas.draw_idle()
            self._fig.canvas.flush_events()
            
            return True
            
        except Exception as e:
            print(f"⚠️ 叠加历史数据失败: {e}")
            return False
    
    def 加载并叠加历史(self, 日志路径: str, 标签: Optional[str] = None) -> bool:
        """
        从日志文件加载历史数据并叠加到图表 (需求 5.1, 5.2)
        
        参数:
            日志路径: 历史日志文件路径
            标签: 历史数据标签，如果不指定则使用文件名
        
        返回:
            是否加载成功
        """
        if not os.path.exists(日志路径):
            print(f"⚠️ 历史日志文件不存在: {日志路径}")
            return False
        
        try:
            with open(日志路径, 'r', encoding='utf-8') as f:
                数据 = json.load(f)
            
            # 提取历史指标
            历史数据 = {}
            
            # 从批次历史提取 loss
            批次历史 = 数据.get("批次历史", [])
            if 批次历史:
                历史数据["批次loss"] = [项["loss"] for 项 in 批次历史]
            
            # 从轮次历史提取各项指标
            轮次历史 = 数据.get("轮次历史", [])
            if 轮次历史:
                历史数据["训练loss"] = [项["训练loss"] for 项 in 轮次历史]
                
                验证loss = [项.get("验证loss") for 项 in 轮次历史]
                if any(v is not None for v in 验证loss):
                    历史数据["验证loss"] = [v for v in 验证loss if v is not None]
                
                训练准确率 = [项.get("训练准确率") for 项 in 轮次历史]
                if any(v is not None for v in 训练准确率):
                    历史数据["训练准确率"] = [v for v in 训练准确率 if v is not None]
                
                验证准确率 = [项.get("验证准确率") for 项 in 轮次历史]
                if any(v is not None for v in 验证准确率):
                    历史数据["验证准确率"] = [v for v in 验证准确率 if v is not None]
            
            # 使用文件名作为默认标签
            if 标签 is None:
                标签 = os.path.splitext(os.path.basename(日志路径))[0]
            
            return self.叠加历史(历史数据, 标签)
            
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"⚠️ 加载历史日志失败: {e}")
            return False
    
    def 关闭(self) -> None:
        """关闭图表窗口"""
        if self._已启动 and self._plt is not None:
            try:
                self._plt.close(self._fig)
            except Exception:
                pass
            finally:
                self._已启动 = False
                self._fig = None
                self._axes.clear()
                self._lines.clear()
    
    def 是否已启动(self) -> bool:
        """检查图表是否已启动"""
        return self._已启动
    
    def 获取更新间隔(self) -> int:
        """获取更新间隔"""
        return self.更新间隔
    
    def 设置更新间隔(self, 间隔: int) -> None:
        """设置更新间隔"""
        self.更新间隔 = max(1, 间隔)
    
    def __del__(self):
        """析构时关闭图表"""
        self.关闭()
    
    def 配置标准训练图表(self) -> None:
        """
        配置标准的训练监控图表布局 (需求 2.2, 2.3)
        
        包含三个子图:
        - Loss 曲线: 显示训练和验证 loss
        - 准确率曲线: 显示训练和验证准确率
        - 学习率曲线: 显示学习率变化
        """
        self.添加子图(
            "loss", 
            ["训练loss", "验证loss"], 
            标题="Loss 曲线", 
            y轴标签="Loss"
        )
        self.添加子图(
            "accuracy", 
            ["训练准确率", "验证准确率"], 
            标题="准确率曲线", 
            y轴标签="准确率"
        )
        self.添加子图(
            "learning_rate", 
            ["学习率"], 
            标题="学习率曲线", 
            y轴标签="学习率"
        )
    
    def 配置简单图表(self) -> None:
        """
        配置简单的训练监控图表布局
        
        只包含一个子图显示批次 loss
        """
        self.添加子图(
            "loss", 
            ["批次loss"], 
            标题="Loss 曲线", 
            y轴标签="Loss"
        )
    
    def 配置双指标图表(self) -> None:
        """
        配置双指标训练监控图表布局 (需求 2.2)
        
        包含两个子图:
        - Loss 曲线: 同时显示训练和验证 loss
        - 准确率曲线: 同时显示训练和验证准确率
        """
        self.添加子图(
            "loss", 
            ["训练loss", "验证loss"], 
            标题="Loss 曲线 (训练 vs 验证)", 
            y轴标签="Loss"
        )
        self.添加子图(
            "accuracy", 
            ["训练准确率", "验证准确率"], 
            标题="准确率曲线 (训练 vs 验证)", 
            y轴标签="准确率"
        )
    
    def 获取子图配置(self) -> Dict[str, Dict[str, Any]]:
        """获取当前子图配置"""
        return self._子图配置.copy()
    
    def 清除子图配置(self) -> None:
        """清除所有子图配置（需要在启动前调用）"""
        if not self._已启动:
            self._子图配置.clear()
    
    def 获取已叠加历史(self) -> List[Dict[str, Any]]:
        """
        获取已叠加的历史数据列表 (需求 5.1)
        
        返回:
            历史数据列表，每项包含 "数据" 和 "标签"
        """
        return self._历史数据.copy()
    
    def 清除历史叠加(self) -> bool:
        """
        清除所有已叠加的历史数据
        
        注意: 需要重新启动图表才能完全清除显示
        
        返回:
            是否清除成功
        """
        self._历史数据.clear()
        return True
    
    def 批量加载历史(self, 日志路径列表: List[str]) -> int:
        """
        批量加载多个历史日志文件 (需求 5.1, 5.2)
        
        参数:
            日志路径列表: 历史日志文件路径列表
        
        返回:
            成功加载的文件数量
        """
        成功数量 = 0
        for 路径 in 日志路径列表:
            if self.加载并叠加历史(路径):
                成功数量 += 1
        return 成功数量
    
    def __repr__(self) -> str:
        状态 = "已启动" if self._已启动 else "未启动"
        return f"实时图表(状态={状态}, 更新间隔={self.更新间隔}, 子图数={len(self._子图配置)})"


class 训练状态(Enum):
    """训练健康状态枚举"""
    正常 = "normal"      # 绿色 - 训练正常进行
    警告 = "warning"     # 黄色 - 可能存在问题
    异常 = "abnormal"    # 红色 - 检测到严重问题


@dataclass
class 监控结果:
    """监控检查结果"""
    状态: 训练状态
    问题列表: List[str] = field(default_factory=list)
    详细信息: Dict[str, Any] = field(default_factory=dict)


class 训练监控器:
    """
    监控训练健康状况
    
    功能:
    - 检测 loss 是否不再下降（可能的平台期）(需求 3.1)
    - 检测 loss 是否在上升（可能的发散）(需求 3.2)
    - 检测大的 loss 尖峰（可能的数据问题）(需求 3.3)
    - 显示警告信息 (需求 3.4)
    - 使用颜色编码指示训练健康状况 (需求 3.5)
    """
    
    # 默认监控配置
    默认配置 = {
        "平台期检测": {
            "窗口": 10,           # 检测窗口大小
            "阈值": 0.001,        # loss 变化小于此值视为停滞
            "最小数据量": 10      # 最少需要的数据点数量
        },
        "发散检测": {
            "窗口": 5,            # 检测窗口大小
            "阈值": 0.1,          # loss 连续上升超过此值视为发散
            "连续上升次数": 5     # 连续上升的次数阈值
        },
        "尖峰检测": {
            "阈值": 3.0,          # 标准差倍数阈值
            "最小数据量": 10      # 最少需要的数据点数量
        }
    }
    
    def __init__(self, 配置: Optional[Dict[str, Any]] = None):
        """
        初始化监控器
        
        参数:
            配置: 监控配置（阈值等），会与默认配置合并
        """
        # 深度合并配置
        self.配置 = self._合并配置(self.默认配置, 配置 or {})
        
        # 监控状态
        self._上次检查结果: Optional[监控结果] = None
        self._问题历史: List[Dict[str, Any]] = []
    
    def _合并配置(self, 默认: Dict, 自定义: Dict) -> Dict:
        """深度合并配置字典"""
        结果 = 默认.copy()
        for 键, 值 in 自定义.items():
            if 键 in 结果 and isinstance(结果[键], dict) and isinstance(值, dict):
                结果[键] = self._合并配置(结果[键], 值)
            else:
                结果[键] = 值
        return 结果
    
    def 检查(self, 指标记录器实例: '指标记录器') -> 监控结果:
        """
        检查训练健康状况 (需求 3.1, 3.2, 3.3)
        
        参数:
            指标记录器实例: 包含训练指标的记录器
        
        返回:
            监控结果，包含状态和问题列表
        """
        问题列表 = []
        详细信息 = {}
        
        # 获取 loss 历史
        loss历史 = 指标记录器实例.获取历史('loss')
        
        # 检测平台期
        平台期结果 = self.检测平台期(loss历史)
        详细信息["平台期"] = 平台期结果
        if 平台期结果:
            问题列表.append("⚠️ 检测到训练平台期：Loss 在最近的训练中几乎没有下降")
        
        # 检测发散
        发散结果 = self.检测发散(loss历史)
        详细信息["发散"] = 发散结果
        if 发散结果:
            问题列表.append("🔴 检测到训练发散：Loss 持续上升，建议降低学习率或检查数据")
        
        # 检测尖峰
        尖峰结果 = self.检测尖峰(loss历史)
        详细信息["尖峰"] = 尖峰结果
        if 尖峰结果:
            问题列表.append("⚡ 检测到 Loss 尖峰：可能存在异常数据或梯度爆炸")
        
        # 确定整体状态
        if 发散结果:
            状态 = 训练状态.异常
        elif 平台期结果 or 尖峰结果:
            状态 = 训练状态.警告
        else:
            状态 = 训练状态.正常
        
        # 创建结果
        结果 = 监控结果(
            状态=状态,
            问题列表=问题列表,
            详细信息=详细信息
        )
        
        # 保存检查结果
        self._上次检查结果 = 结果
        
        # 如果有问题，记录到历史
        if 问题列表:
            self._问题历史.append({
                "时间戳": time.time(),
                "状态": 状态.value,
                "问题": 问题列表.copy()
            })
        
        return 结果
    
    def 检测平台期(self, loss历史: List[float], 
                   窗口: Optional[int] = None) -> bool:
        """
        检测 loss 是否停滞（平台期）(需求 3.1)
        
        参数:
            loss历史: loss 历史记录
            窗口: 检测窗口大小，如果不指定则使用配置值
        
        返回:
            是否处于平台期
        """
        配置 = self.配置["平台期检测"]
        窗口 = 窗口 or 配置["窗口"]
        阈值 = 配置["阈值"]
        最小数据量 = 配置["最小数据量"]
        
        # 数据不足时无法判断
        if len(loss历史) < 最小数据量:
            return False
        
        # 取最近窗口内的数据
        窗口数据 = loss历史[-窗口:] if len(loss历史) >= 窗口 else loss历史
        
        if len(窗口数据) < 2:
            return False
        
        # 计算窗口内的变化范围
        最大值 = max(窗口数据)
        最小值 = min(窗口数据)
        变化范围 = 最大值 - 最小值
        
        # 如果变化范围小于阈值，认为处于平台期
        return 变化范围 < 阈值
    
    def 检测发散(self, loss历史: List[float], 
                 窗口: Optional[int] = None) -> bool:
        """
        检测 loss 是否发散（持续上升）(需求 3.2)
        
        参数:
            loss历史: loss 历史记录
            窗口: 检测窗口大小，如果不指定则使用配置值
        
        返回:
            是否发散
        """
        配置 = self.配置["发散检测"]
        窗口 = 窗口 or 配置["窗口"]
        连续上升次数 = 配置["连续上升次数"]
        
        # 数据不足时无法判断
        if len(loss历史) < 窗口:
            return False
        
        # 取最近窗口内的数据
        窗口数据 = loss历史[-窗口:]
        
        # 检查是否连续上升
        上升次数 = 0
        for i in range(1, len(窗口数据)):
            if 窗口数据[i] > 窗口数据[i - 1]:
                上升次数 += 1
            else:
                上升次数 = 0  # 重置计数
        
        # 如果连续上升次数达到阈值，认为发散
        # 对于窗口大小为 N 的数据，最多有 N-1 次比较
        # 如果所有比较都是上升的，则认为发散
        return 上升次数 >= (窗口 - 1) and 上升次数 >= 连续上升次数 - 1
    
    def 检测尖峰(self, loss历史: List[float], 
                 阈值: Optional[float] = None) -> bool:
        """
        检测 loss 尖峰（异常值）(需求 3.3)
        
        参数:
            loss历史: loss 历史记录
            阈值: 标准差倍数阈值，如果不指定则使用配置值
        
        返回:
            是否有尖峰
        """
        配置 = self.配置["尖峰检测"]
        阈值 = 阈值 or 配置["阈值"]
        最小数据量 = 配置["最小数据量"]
        
        # 数据不足时无法判断
        if len(loss历史) < 最小数据量:
            return False
        
        # 计算均值和标准差
        均值 = sum(loss历史) / len(loss历史)
        方差 = sum((x - 均值) ** 2 for x in loss历史) / len(loss历史)
        标准差 = 方差 ** 0.5
        
        # 标准差为0时无法检测尖峰
        if 标准差 == 0:
            return False
        
        # 检查最新值是否为尖峰
        最新值 = loss历史[-1]
        偏离程度 = abs(最新值 - 均值) / 标准差
        
        return 偏离程度 > 阈值
    
    def 获取上次检查结果(self) -> Optional[监控结果]:
        """获取上次检查的结果"""
        return self._上次检查结果
    
    def 获取问题历史(self) -> List[Dict[str, Any]]:
        """获取问题历史记录"""
        return self._问题历史.copy()
    
    def 清空问题历史(self) -> None:
        """清空问题历史记录"""
        self._问题历史.clear()
    
    def 获取状态颜色(self, 状态: Optional[训练状态] = None) -> str:
        """
        获取状态对应的颜色代码 (需求 3.5)
        
        参数:
            状态: 训练状态，如果不指定则使用上次检查结果的状态
        
        返回:
            颜色代码（用于终端或 GUI）
        """
        if 状态 is None:
            if self._上次检查结果 is None:
                状态 = 训练状态.正常
            else:
                状态 = self._上次检查结果.状态
        
        颜色映射 = {
            训练状态.正常: "\033[92m",   # 绿色
            训练状态.警告: "\033[93m",   # 黄色
            训练状态.异常: "\033[91m",   # 红色
        }
        return 颜色映射.get(状态, "\033[0m")
    
    def 获取状态图标(self, 状态: Optional[训练状态] = None) -> str:
        """
        获取状态对应的图标
        
        参数:
            状态: 训练状态，如果不指定则使用上次检查结果的状态
        
        返回:
            状态图标
        """
        if 状态 is None:
            if self._上次检查结果 is None:
                状态 = 训练状态.正常
            else:
                状态 = self._上次检查结果.状态
        
        图标映射 = {
            训练状态.正常: "✅",
            训练状态.警告: "⚠️",
            训练状态.异常: "🔴",
        }
        return 图标映射.get(状态, "❓")
    
    def 获取状态文本(self, 状态: Optional[训练状态] = None) -> str:
        """
        获取状态对应的文本描述
        
        参数:
            状态: 训练状态，如果不指定则使用上次检查结果的状态
        
        返回:
            状态文本
        """
        if 状态 is None:
            if self._上次检查结果 is None:
                状态 = 训练状态.正常
            else:
                状态 = self._上次检查结果.状态
        
        文本映射 = {
            训练状态.正常: "训练正常",
            训练状态.警告: "存在警告",
            训练状态.异常: "检测到异常",
        }
        return 文本映射.get(状态, "未知状态")
    
    def 更新配置(self, 新配置: Dict[str, Any]) -> None:
        """
        更新监控配置
        
        参数:
            新配置: 新的配置项
        """
        self.配置 = self._合并配置(self.配置, 新配置)
    
    def 获取配置(self) -> Dict[str, Any]:
        """获取当前配置"""
        return self.配置.copy()
    
    def __repr__(self) -> str:
        状态文本 = "未检查"
        if self._上次检查结果:
            状态文本 = self._上次检查结果.状态.value
        return f"训练监控器(状态={状态文本}, 问题历史数={len(self._问题历史)})"
    
    def 显示警告(self, 结果: Optional[监控结果] = None, 
                 使用颜色: bool = True) -> str:
        """
        生成格式化的警告信息 (需求 3.4, 3.5)
        
        参数:
            结果: 监控结果，如果不指定则使用上次检查结果
            使用颜色: 是否使用终端颜色代码
        
        返回:
            格式化的警告信息字符串
        """
        if 结果 is None:
            结果 = self._上次检查结果
        
        if 结果 is None:
            return ""
        
        # 颜色代码
        重置 = "\033[0m" if 使用颜色 else ""
        颜色 = self.获取状态颜色(结果.状态) if 使用颜色 else ""
        
        # 构建输出
        输出行 = []
        
        # 状态行
        图标 = self.获取状态图标(结果.状态)
        状态文本 = self.获取状态文本(结果.状态)
        输出行.append(f"{颜色}{图标} 训练状态: {状态文本}{重置}")
        
        # 问题列表
        if 结果.问题列表:
            输出行.append(f"{颜色}检测到以下问题:{重置}")
            for 问题 in 结果.问题列表:
                输出行.append(f"  {问题}")
        
        return "\n".join(输出行)
    
    def 打印警告(self, 结果: Optional[监控结果] = None) -> None:
        """
        打印警告信息到终端 (需求 3.4)
        
        参数:
            结果: 监控结果，如果不指定则使用上次检查结果
        """
        警告文本 = self.显示警告(结果, 使用颜色=True)
        if 警告文本:
            print(警告文本)
    
    def 获取状态摘要(self, 结果: Optional[监控结果] = None) -> Dict[str, Any]:
        """
        获取状态摘要信息（用于 GUI 显示）(需求 3.5)
        
        参数:
            结果: 监控结果，如果不指定则使用上次检查结果
        
        返回:
            包含状态信息的字典
        """
        if 结果 is None:
            结果 = self._上次检查结果
        
        if 结果 is None:
            return {
                "状态": 训练状态.正常.value,
                "状态文本": "未检查",
                "图标": "❓",
                "颜色": "#808080",  # 灰色
                "问题数量": 0,
                "问题列表": []
            }
        
        # GUI 颜色映射
        GUI颜色映射 = {
            训练状态.正常: "#4CAF50",   # 绿色
            训练状态.警告: "#FF9800",   # 橙色
            训练状态.异常: "#F44336",   # 红色
        }
        
        return {
            "状态": 结果.状态.value,
            "状态文本": self.获取状态文本(结果.状态),
            "图标": self.获取状态图标(结果.状态),
            "颜色": GUI颜色映射.get(结果.状态, "#808080"),
            "问题数量": len(结果.问题列表),
            "问题列表": 结果.问题列表.copy(),
            "详细信息": 结果.详细信息.copy()
        }
    
    def 生成状态条(self, 宽度: int = 40, 结果: Optional[监控结果] = None,
                   使用颜色: bool = True) -> str:
        """
        生成状态指示条（用于终端显示）(需求 3.5)
        
        参数:
            宽度: 状态条宽度
            结果: 监控结果，如果不指定则使用上次检查结果
            使用颜色: 是否使用终端颜色代码
        
        返回:
            格式化的状态条字符串
        """
        if 结果 is None:
            结果 = self._上次检查结果
        
        状态 = 结果.状态 if 结果 else 训练状态.正常
        
        # 颜色代码
        重置 = "\033[0m" if 使用颜色 else ""
        颜色 = self.获取状态颜色(状态) if 使用颜色 else ""
        
        # 状态字符
        字符映射 = {
            训练状态.正常: "█",
            训练状态.警告: "▓",
            训练状态.异常: "░",
        }
        字符 = 字符映射.get(状态, "█")
        
        # 生成状态条
        图标 = self.获取状态图标(状态)
        状态文本 = self.获取状态文本(状态)
        条 = 字符 * 宽度
        
        return f"{颜色}[{条}] {图标} {状态文本}{重置}"


class 终端输出器:
    """
    优化的终端训练输出
    
    功能:
    - 为每个 epoch 显示进度条 (需求 4.1)
    - 显示当前 loss、准确率和预计剩余时间 (需求 4.2)
    - 在每个 epoch 结束时显示摘要 (需求 4.3)
    - 支持最小输出的静默模式 (需求 4.4)
    """
    
    # 默认配置
    默认配置 = {
        "进度条宽度": 40,
        "刷新间隔": 0.1,  # 秒
        "显示速度": True,
        "显示预计时间": True,
        "使用颜色": True,
    }
    
    def __init__(self, 静默模式: bool = False, 配置: Optional[Dict[str, Any]] = None):
        """
        初始化输出器 (需求 4.4)
        
        参数:
            静默模式: 是否最小化输出
            配置: 输出配置
        """
        self.静默模式 = 静默模式
        self.配置 = {**self.默认配置, **(配置 or {})}
        
        # 状态跟踪
        self._当前轮次: int = 0
        self._总轮次: int = 0
        self._当前批次: int = 0
        self._总批次: int = 0
        self._轮次开始时间: Optional[float] = None
        self._训练开始时间: Optional[float] = None
        self._上次刷新时间: float = 0
        self._上次批次: int = 0
        
        # 颜色代码
        self._颜色 = {
            "重置": "\033[0m",
            "粗体": "\033[1m",
            "绿色": "\033[92m",
            "黄色": "\033[93m",
            "红色": "\033[91m",
            "蓝色": "\033[94m",
            "青色": "\033[96m",
            "灰色": "\033[90m",
        }
    
    def _获取颜色(self, 颜色名: str) -> str:
        """获取颜色代码，如果禁用颜色则返回空字符串"""
        if not self.配置["使用颜色"]:
            return ""
        return self._颜色.get(颜色名, "")
    
    def 开始训练(self, 总轮次: int, 每轮批次: int) -> None:
        """
        标记训练开始
        
        参数:
            总轮次: 总训练轮次数
            每轮批次: 每轮的批次数
        """
        self._总轮次 = 总轮次
        self._总批次 = 每轮批次
        self._训练开始时间 = time.time()
        
        if not self.静默模式:
            重置 = self._获取颜色("重置")
            粗体 = self._获取颜色("粗体")
            蓝色 = self._获取颜色("蓝色")
            
            print(f"\n{粗体}{蓝色}{'='*60}{重置}")
            print(f"{粗体}{蓝色}🚀 开始训练{重置}")
            print(f"{蓝色}   总轮次: {总轮次}, 每轮批次: {每轮批次}{重置}")
            print(f"{粗体}{蓝色}{'='*60}{重置}\n")
    
    def 开始轮次(self, 轮次: int) -> None:
        """
        标记轮次开始
        
        参数:
            轮次: 当前轮次号
        """
        self._当前轮次 = 轮次
        self._当前批次 = 0
        self._轮次开始时间 = time.time()
        self._上次刷新时间 = 0
        self._上次批次 = 0
        
        if not self.静默模式:
            重置 = self._获取颜色("重置")
            粗体 = self._获取颜色("粗体")
            青色 = self._获取颜色("青色")
            
            print(f"\n{粗体}{青色}📊 轮次 {轮次}/{self._总轮次}{重置}")
    
    def 显示进度条(self, 当前: int, 总数: int, 前缀: str = "", 
                   后缀: str = "") -> str:
        """
        生成进度条字符串 (需求 4.1)
        
        参数:
            当前: 当前进度
            总数: 总数
            前缀: 进度条前缀
            后缀: 进度条后缀
        
        返回:
            进度条字符串
        """
        if 总数 <= 0:
            return ""
        
        宽度 = self.配置["进度条宽度"]
        进度 = 当前 / 总数
        已完成 = int(宽度 * 进度)
        未完成 = 宽度 - 已完成
        
        # 进度条字符
        已完成字符 = "█" * 已完成
        未完成字符 = "░" * 未完成
        
        # 百分比
        百分比 = f"{进度 * 100:5.1f}%"
        
        # 颜色
        绿色 = self._获取颜色("绿色")
        灰色 = self._获取颜色("灰色")
        重置 = self._获取颜色("重置")
        
        进度条 = f"{前缀}|{绿色}{已完成字符}{灰色}{未完成字符}{重置}| {百分比}"
        
        if 后缀:
            进度条 += f" {后缀}"
        
        return 进度条
    
    def 显示批次信息(self, 批次: int, loss: float, 
                     速度: Optional[float] = None,
                     其他指标: Optional[Dict[str, float]] = None) -> None:
        """
        显示批次信息 (需求 4.1, 4.2)
        
        参数:
            批次: 当前批次
            loss: 当前 loss
            速度: 每秒处理样本数（可选）
            其他指标: 其他需要显示的指标
        """
        self._当前批次 = 批次
        
        # 静默模式下不显示批次信息
        if self.静默模式:
            return
        
        # 检查是否需要刷新（避免过于频繁的输出）
        当前时间 = time.time()
        if 当前时间 - self._上次刷新时间 < self.配置["刷新间隔"]:
            return
        self._上次刷新时间 = 当前时间
        
        # 计算速度
        if 速度 is None and self._轮次开始时间 is not None:
            已用时间 = 当前时间 - self._轮次开始时间
            if 已用时间 > 0:
                速度 = 批次 / 已用时间
        
        # 构建后缀信息
        后缀部分 = []
        
        # Loss
        黄色 = self._获取颜色("黄色")
        重置 = self._获取颜色("重置")
        后缀部分.append(f"loss: {黄色}{loss:.4f}{重置}")
        
        # 其他指标
        if 其他指标:
            for 名称, 值 in 其他指标.items():
                后缀部分.append(f"{名称}: {值:.4f}")
        
        # 速度
        if 速度 is not None and self.配置["显示速度"]:
            后缀部分.append(f"速度: {速度:.1f} batch/s")
        
        # 预计剩余时间
        if self.配置["显示预计时间"] and self._轮次开始时间 is not None:
            预计时间 = self._计算预计剩余时间(批次, self._总批次, self._轮次开始时间)
            if 预计时间:
                后缀部分.append(f"剩余: {预计时间}")
        
        后缀 = " | ".join(后缀部分)
        
        # 生成进度条
        进度条 = self.显示进度条(批次, self._总批次, 前缀="  ", 后缀=后缀)
        
        # 使用回车符覆盖当前行
        print(f"\r{进度条}", end="", flush=True)
    
    def _计算预计剩余时间(self, 当前: int, 总数: int, 
                         开始时间: float) -> str:
        """
        计算预计剩余时间
        
        参数:
            当前: 当前进度
            总数: 总数
            开始时间: 开始时间戳
        
        返回:
            格式化的剩余时间字符串
        """
        if 当前 <= 0:
            return ""
        
        已用时间 = time.time() - 开始时间
        平均时间 = 已用时间 / 当前
        剩余数量 = 总数 - 当前
        剩余秒数 = 平均时间 * 剩余数量
        
        return self._格式化时间(剩余秒数)
    
    def _格式化时间(self, 秒数: float) -> str:
        """
        格式化时间显示
        
        参数:
            秒数: 秒数
        
        返回:
            格式化的时间字符串
        """
        if 秒数 < 0:
            return "0s"
        
        if 秒数 < 60:
            return f"{秒数:.0f}s"
        elif 秒数 < 3600:
            分钟 = int(秒数 // 60)
            秒 = int(秒数 % 60)
            return f"{分钟}m {秒}s"
        else:
            小时 = int(秒数 // 3600)
            分钟 = int((秒数 % 3600) // 60)
            return f"{小时}h {分钟}m"

    
    def 显示轮次摘要(self, 轮次: int, 训练loss: float, 
                     验证loss: Optional[float] = None,
                     训练准确率: Optional[float] = None, 
                     验证准确率: Optional[float] = None,
                     耗时: Optional[float] = None) -> None:
        """
        显示轮次结束摘要 (需求 4.3)
        
        参数:
            轮次: 当前轮次
            训练loss: 训练损失
            验证loss: 验证损失
            训练准确率: 训练准确率
            验证准确率: 验证准确率
            耗时: 轮次耗时（秒）
        """
        # 静默模式下只显示简要信息
        if self.静默模式:
            简要信息 = f"轮次 {轮次}: loss={训练loss:.4f}"
            if 验证loss is not None:
                简要信息 += f", val_loss={验证loss:.4f}"
            print(简要信息)
            return
        
        # 清除进度条行
        print()
        
        # 颜色
        重置 = self._获取颜色("重置")
        粗体 = self._获取颜色("粗体")
        绿色 = self._获取颜色("绿色")
        黄色 = self._获取颜色("黄色")
        青色 = self._获取颜色("青色")
        
        # 计算耗时
        if 耗时 is None and self._轮次开始时间 is not None:
            耗时 = time.time() - self._轮次开始时间
        
        # 构建摘要
        print(f"  {粗体}{'─'*56}{重置}")
        print(f"  {粗体}📈 轮次 {轮次} 摘要{重置}")
        print(f"  {粗体}{'─'*56}{重置}")
        
        # 训练指标
        print(f"  {青色}训练:{重置}")
        print(f"    • Loss: {黄色}{训练loss:.6f}{重置}")
        if 训练准确率 is not None:
            print(f"    • 准确率: {绿色}{训练准确率*100:.2f}%{重置}")
        
        # 验证指标
        if 验证loss is not None or 验证准确率 is not None:
            print(f"  {青色}验证:{重置}")
            if 验证loss is not None:
                print(f"    • Loss: {黄色}{验证loss:.6f}{重置}")
            if 验证准确率 is not None:
                print(f"    • 准确率: {绿色}{验证准确率*100:.2f}%{重置}")
        
        # 耗时
        if 耗时 is not None:
            print(f"  {青色}耗时:{重置} {self._格式化时间(耗时)}")
        
        # 预计总剩余时间
        if self._训练开始时间 is not None and self._总轮次 > 0:
            剩余轮次 = self._总轮次 - 轮次
            if 剩余轮次 > 0 and 耗时 is not None:
                预计剩余 = 耗时 * 剩余轮次
                print(f"  {青色}预计剩余:{重置} {self._格式化时间(预计剩余)} ({剩余轮次} 轮)")
        
        print(f"  {粗体}{'─'*56}{重置}")
    
    def 显示预计时间(self, 已完成: int, 总数: int, 
                     已用时间: Optional[float] = None) -> str:
        """
        显示预计剩余时间 (需求 4.2)
        
        参数:
            已完成: 已完成数量
            总数: 总数量
            已用时间: 已用时间（秒），如果不指定则自动计算
        
        返回:
            格式化的预计时间字符串
        """
        if 已完成 <= 0 or 总数 <= 0:
            return "计算中..."
        
        if 已用时间 is None:
            if self._训练开始时间 is not None:
                已用时间 = time.time() - self._训练开始时间
            else:
                return "计算中..."
        
        # 计算预计剩余时间
        平均时间 = 已用时间 / 已完成
        剩余数量 = 总数 - 已完成
        剩余秒数 = 平均时间 * 剩余数量
        
        # 计算预计完成时间
        预计完成时间戳 = time.time() + 剩余秒数
        预计完成时间 = datetime.fromtimestamp(预计完成时间戳)
        
        剩余时间文本 = self._格式化时间(剩余秒数)
        完成时间文本 = 预计完成时间.strftime("%H:%M:%S")
        
        return f"剩余 {剩余时间文本}，预计 {完成时间文本} 完成"
    
    def 结束训练(self, 总耗时: Optional[float] = None,
                 最终指标: Optional[Dict[str, float]] = None) -> None:
        """
        显示训练结束信息
        
        参数:
            总耗时: 总训练耗时（秒）
            最终指标: 最终训练指标
        """
        if 总耗时 is None and self._训练开始时间 is not None:
            总耗时 = time.time() - self._训练开始时间
        
        if self.静默模式:
            print(f"训练完成，耗时: {self._格式化时间(总耗时 or 0)}")
            return
        
        # 颜色
        重置 = self._获取颜色("重置")
        粗体 = self._获取颜色("粗体")
        绿色 = self._获取颜色("绿色")
        蓝色 = self._获取颜色("蓝色")
        
        print(f"\n{粗体}{绿色}{'='*60}{重置}")
        print(f"{粗体}{绿色}✅ 训练完成!{重置}")
        print(f"{粗体}{绿色}{'='*60}{重置}")
        
        if 总耗时 is not None:
            print(f"{蓝色}总耗时: {self._格式化时间(总耗时)}{重置}")
        
        if 最终指标:
            print(f"{蓝色}最终指标:{重置}")
            for 名称, 值 in 最终指标.items():
                if isinstance(值, float):
                    print(f"  • {名称}: {值:.6f}")
                else:
                    print(f"  • {名称}: {值}")
        
        print(f"{粗体}{绿色}{'='*60}{重置}\n")

    
    def 显示警告(self, 消息: str, 状态: 训练状态 = 训练状态.警告) -> None:
        """
        显示带颜色的警告信息 (需求 3.4, 3.5)
        
        参数:
            消息: 警告消息
            状态: 训练状态（决定颜色）
        """
        # 静默模式下只显示异常级别的警告
        if self.静默模式 and 状态 != 训练状态.异常:
            return
        
        # 颜色映射
        重置 = self._获取颜色("重置")
        颜色映射 = {
            训练状态.正常: self._获取颜色("绿色"),
            训练状态.警告: self._获取颜色("黄色"),
            训练状态.异常: self._获取颜色("红色"),
        }
        颜色 = 颜色映射.get(状态, "")
        
        # 图标映射
        图标映射 = {
            训练状态.正常: "✅",
            训练状态.警告: "⚠️",
            训练状态.异常: "🔴",
        }
        图标 = 图标映射.get(状态, "❓")
        
        print(f"\n{颜色}{图标} {消息}{重置}")
    
    def 设置静默模式(self, 静默: bool) -> None:
        """
        设置静默模式 (需求 4.4)
        
        参数:
            静默: 是否启用静默模式
        """
        self.静默模式 = 静默
    
    def 是否静默模式(self) -> bool:
        """
        检查是否处于静默模式 (需求 4.4)
        
        返回:
            是否静默模式
        """
        return self.静默模式
    
    def 更新配置(self, 新配置: Dict[str, Any]) -> None:
        """
        更新输出配置
        
        参数:
            新配置: 新的配置项
        """
        self.配置.update(新配置)
    
    def 获取配置(self) -> Dict[str, Any]:
        """获取当前配置"""
        return self.配置.copy()
    
    def 打印分隔线(self, 字符: str = "─", 长度: int = 60) -> None:
        """
        打印分隔线
        
        参数:
            字符: 分隔线字符
            长度: 分隔线长度
        """
        if not self.静默模式:
            print(字符 * 长度)
    
    def 打印标题(self, 标题: str, 图标: str = "📌") -> None:
        """
        打印带图标的标题
        
        参数:
            标题: 标题文本
            图标: 标题图标
        """
        if not self.静默模式:
            粗体 = self._获取颜色("粗体")
            重置 = self._获取颜色("重置")
            print(f"\n{粗体}{图标} {标题}{重置}")
    
    def 打印信息(self, 消息: str, 缩进: int = 0) -> None:
        """
        打印普通信息
        
        参数:
            消息: 消息文本
            缩进: 缩进空格数
        """
        if not self.静默模式:
            前缀 = " " * 缩进
            print(f"{前缀}{消息}")
    
    def 打印成功(self, 消息: str) -> None:
        """
        打印成功信息
        
        参数:
            消息: 消息文本
        """
        if not self.静默模式:
            绿色 = self._获取颜色("绿色")
            重置 = self._获取颜色("重置")
            print(f"{绿色}✅ {消息}{重置}")
    
    def 打印错误(self, 消息: str) -> None:
        """
        打印错误信息（即使在静默模式下也显示）
        
        参数:
            消息: 消息文本
        """
        红色 = self._获取颜色("红色")
        重置 = self._获取颜色("重置")
        print(f"{红色}❌ {消息}{重置}")
    
    def __repr__(self) -> str:
        模式 = "静默" if self.静默模式 else "正常"
        return f"终端输出器(模式={模式}, 进度条宽度={self.配置['进度条宽度']})"


class 可视化回调:
    """
    训练可视化回调函数
    
    集成所有可视化组件，提供训练生命周期钩子。
    
    功能:
    - 训练开始时初始化所有组件 (on_train_begin)
    - 每个批次结束时记录指标并更新图表 (on_batch_end)
    - 每个轮次结束时显示摘要并检查健康状况 (on_epoch_end)
    - 训练结束时保存日志并关闭图表 (on_train_end)
    
    需求: 2.4 - 按可配置的间隔更新图表
    """
    
    # 默认配置
    默认配置 = {
        "更新间隔": 10,           # 图表更新间隔（批次数）
        "启用图表": True,         # 是否启用实时图表
        "启用终端": True,         # 是否启用终端输出
        "启用监控": True,         # 是否启用健康监控
        "自动保存": True,         # 是否自动保存日志
        "静默模式": False,        # 终端静默模式
        "检查间隔": 1,            # 健康检查间隔（轮次数）
        "日志目录": "日志/训练",  # 日志保存目录
    }
    
    def __init__(self, 
                 启用图表: bool = True, 
                 启用终端: bool = True,
                 更新间隔: int = 10,
                 配置: Optional[Dict[str, Any]] = None):
        """
        初始化回调
        
        参数:
            启用图表: 是否启用实时图表
            启用终端: 是否启用终端输出
            更新间隔: 图表更新间隔（批次数）
            配置: 额外配置选项
        """
        # 合并配置
        self.配置 = {**self.默认配置, **(配置 or {})}
        self.配置["启用图表"] = 启用图表
        self.配置["启用终端"] = 启用终端
        self.配置["更新间隔"] = 更新间隔
        
        # 初始化组件
        self._指标记录器: Optional[指标记录器] = None
        self._实时图表: Optional[实时图表] = None
        self._训练监控器: Optional[训练监控器] = None
        self._终端输出器: Optional[终端输出器] = None
        
        # 训练状态
        self._总轮次: int = 0
        self._每轮批次: int = 0
        self._当前轮次: int = 0
        self._当前批次: int = 0
        self._已初始化: bool = False
        self._训练开始时间: Optional[float] = None
        self._轮次开始时间: Optional[float] = None
    
    def _初始化组件(self) -> None:
        """初始化所有可视化组件"""
        if self._已初始化:
            return
        
        # 初始化指标记录器
        self._指标记录器 = 指标记录器(日志目录=self.配置["日志目录"])
        
        # 初始化实时图表
        if self.配置["启用图表"]:
            self._实时图表 = 实时图表(更新间隔=self.配置["更新间隔"])
            self._实时图表.配置双指标图表()
        
        # 初始化训练监控器
        if self.配置["启用监控"]:
            self._训练监控器 = 训练监控器()
        
        # 初始化终端输出器
        if self.配置["启用终端"]:
            self._终端输出器 = 终端输出器(静默模式=self.配置["静默模式"])
        
        self._已初始化 = True
    
    def on_train_begin(self, 总轮次: int, 每轮批次: int) -> None:
        """
        训练开始时调用
        
        参数:
            总轮次: 总训练轮次数
            每轮批次: 每轮的批次数
        """
        self._总轮次 = 总轮次
        self._每轮批次 = 每轮批次
        self._当前轮次 = 0
        self._当前批次 = 0
        self._训练开始时间 = time.time()
        
        # 初始化组件
        self._初始化组件()
        
        # 启动指标记录器
        if self._指标记录器 is not None:
            self._指标记录器.开始训练()
        
        # 启动实时图表
        if self._实时图表 is not None and self.配置["启用图表"]:
            try:
                self._实时图表.启动()
            except Exception as e:
                print(f"⚠️ 启动实时图表失败: {e}")
                self._实时图表 = None
        
        # 显示训练开始信息
        if self._终端输出器 is not None:
            self._终端输出器.开始训练(总轮次, 每轮批次)
    
    def on_epoch_begin(self, 轮次: int) -> None:
        """
        轮次开始时调用
        
        参数:
            轮次: 当前轮次号（从1开始）
        """
        self._当前轮次 = 轮次
        self._当前批次 = 0
        self._轮次开始时间 = time.time()
        
        # 标记轮次开始
        if self._指标记录器 is not None:
            self._指标记录器.开始轮次()
        
        # 显示轮次开始信息
        if self._终端输出器 is not None:
            self._终端输出器.开始轮次(轮次)
    
    def on_batch_end(self, 批次: int, loss: float, **指标) -> None:
        """
        每个批次结束时调用
        
        参数:
            批次: 当前批次号
            loss: 当前批次的损失值
            指标: 其他需要记录的指标
        """
        self._当前批次 = 批次
        
        # 记录批次指标
        if self._指标记录器 is not None:
            self._指标记录器.记录批次(批次, loss, **指标)
        
        # 更新实时图表（按配置的间隔更新）
        if self._实时图表 is not None and self._指标记录器 is not None:
            try:
                self._实时图表.更新(self._指标记录器)
            except Exception as e:
                # 图表更新失败不应影响训练
                pass
        
        # 显示批次信息
        if self._终端输出器 is not None:
            self._终端输出器.显示批次信息(
                批次=批次,
                loss=loss,
                其他指标=指标 if 指标 else None
            )
    
    def on_epoch_end(self, 轮次: int, **指标) -> None:
        """
        每个轮次结束时调用
        
        参数:
            轮次: 当前轮次号
            指标: 轮次指标，可包含:
                - 训练loss: 训练损失
                - 验证loss: 验证损失
                - 训练准确率: 训练准确率
                - 验证准确率: 验证准确率
                - 学习率: 当前学习率
        """
        self._当前轮次 = 轮次
        
        # 提取指标
        训练loss = 指标.get('训练loss', 指标.get('loss', 0.0))
        验证loss = 指标.get('验证loss', 指标.get('val_loss'))
        训练准确率 = 指标.get('训练准确率', 指标.get('accuracy'))
        验证准确率 = 指标.get('验证准确率', 指标.get('val_accuracy'))
        学习率 = 指标.get('学习率', 指标.get('lr'))
        
        # 记录轮次指标
        if self._指标记录器 is not None:
            self._指标记录器.记录轮次(
                轮次=轮次,
                训练loss=训练loss,
                验证loss=验证loss,
                训练准确率=训练准确率,
                验证准确率=验证准确率,
                学习率=学习率
            )
        
        # 强制更新图表
        if self._实时图表 is not None and self._指标记录器 is not None:
            try:
                self._实时图表.更新(self._指标记录器, 强制更新=True)
            except Exception:
                pass
        
        # 计算轮次耗时
        耗时 = None
        if self._轮次开始时间 is not None:
            耗时 = time.time() - self._轮次开始时间
        
        # 显示轮次摘要
        if self._终端输出器 is not None:
            self._终端输出器.显示轮次摘要(
                轮次=轮次,
                训练loss=训练loss,
                验证loss=验证loss,
                训练准确率=训练准确率,
                验证准确率=验证准确率,
                耗时=耗时
            )
        
        # 健康检查
        if self._训练监控器 is not None and self._指标记录器 is not None:
            if 轮次 % self.配置["检查间隔"] == 0:
                结果 = self._训练监控器.检查(self._指标记录器)
                
                # 显示警告
                if 结果.问题列表 and self._终端输出器 is not None:
                    for 问题 in 结果.问题列表:
                        self._终端输出器.显示警告(问题, 结果.状态)
    
    def on_train_end(self) -> Optional[str]:
        """
        训练结束时调用
        
        返回:
            保存的日志文件路径（如果启用自动保存）
        """
        日志路径 = None
        
        # 计算总耗时
        总耗时 = None
        if self._训练开始时间 is not None:
            总耗时 = time.time() - self._训练开始时间
        
        # 获取最终指标
        最终指标 = {}
        if self._指标记录器 is not None:
            最新轮次 = self._指标记录器.获取最新轮次指标()
            if 最新轮次:
                最终指标["最终训练Loss"] = 最新轮次.训练loss
                if 最新轮次.验证loss is not None:
                    最终指标["最终验证Loss"] = 最新轮次.验证loss
                if 最新轮次.训练准确率 is not None:
                    最终指标["最终训练准确率"] = 最新轮次.训练准确率
                if 最新轮次.验证准确率 is not None:
                    最终指标["最终验证准确率"] = 最新轮次.验证准确率
        
        # 显示训练结束信息
        if self._终端输出器 is not None:
            self._终端输出器.结束训练(总耗时=总耗时, 最终指标=最终指标)
        
        # 自动保存日志
        if self.配置["自动保存"] and self._指标记录器 is not None:
            try:
                日志路径 = self._指标记录器.保存()
                if self._终端输出器 is not None and not self.配置["静默模式"]:
                    self._终端输出器.打印成功(f"训练日志已保存: {日志路径}")
            except Exception as e:
                if self._终端输出器 is not None:
                    self._终端输出器.打印错误(f"保存日志失败: {e}")
        
        # 关闭图表
        if self._实时图表 is not None:
            try:
                self._实时图表.关闭()
            except Exception:
                pass
        
        return 日志路径
    
    # ==================== 便捷方法 ====================
    
    def 获取指标记录器(self) -> Optional[指标记录器]:
        """获取指标记录器实例"""
        return self._指标记录器
    
    def 获取实时图表(self) -> Optional[实时图表]:
        """获取实时图表实例"""
        return self._实时图表
    
    def 获取训练监控器(self) -> Optional[训练监控器]:
        """获取训练监控器实例"""
        return self._训练监控器
    
    def 获取终端输出器(self) -> Optional[终端输出器]:
        """获取终端输出器实例"""
        return self._终端输出器
    
    def 加载历史对比(self, 日志路径: str, 标签: Optional[str] = None) -> bool:
        """
        加载历史训练数据进行对比
        
        参数:
            日志路径: 历史日志文件路径
            标签: 历史数据标签
        
        返回:
            是否加载成功
        """
        if self._实时图表 is not None:
            return self._实时图表.加载并叠加历史(日志路径, 标签)
        return False
    
    def 设置静默模式(self, 静默: bool) -> None:
        """
        设置静默模式
        
        参数:
            静默: 是否启用静默模式
        """
        self.配置["静默模式"] = 静默
        if self._终端输出器 is not None:
            self._终端输出器.设置静默模式(静默)
    
    def 获取当前状态(self) -> Dict[str, Any]:
        """
        获取当前训练状态
        
        返回:
            包含当前状态信息的字典
        """
        状态 = {
            "当前轮次": self._当前轮次,
            "总轮次": self._总轮次,
            "当前批次": self._当前批次,
            "每轮批次": self._每轮批次,
            "已初始化": self._已初始化,
        }
        
        # 添加训练时长
        if self._训练开始时间 is not None:
            状态["训练时长"] = time.time() - self._训练开始时间
        
        # 添加健康状态
        if self._训练监控器 is not None:
            结果 = self._训练监控器.获取上次检查结果()
            if 结果:
                状态["健康状态"] = 结果.状态.value
                状态["问题数量"] = len(结果.问题列表)
        
        return 状态
    
    def 手动保存日志(self, 文件路径: Optional[str] = None) -> Optional[str]:
        """
        手动保存训练日志
        
        参数:
            文件路径: 可选的文件路径
        
        返回:
            保存的文件路径，失败返回 None
        """
        if self._指标记录器 is not None:
            try:
                return self._指标记录器.保存(文件路径)
            except Exception as e:
                print(f"⚠️ 保存日志失败: {e}")
        return None
    
    def 更新配置(self, 新配置: Dict[str, Any]) -> None:
        """
        更新回调配置
        
        参数:
            新配置: 新的配置项
        """
        self.配置.update(新配置)
        
        # 同步更新子组件配置
        if "静默模式" in 新配置 and self._终端输出器 is not None:
            self._终端输出器.设置静默模式(新配置["静默模式"])
        
        if "更新间隔" in 新配置 and self._实时图表 is not None:
            self._实时图表.设置更新间隔(新配置["更新间隔"])
    
    def 获取配置(self) -> Dict[str, Any]:
        """获取当前配置"""
        return self.配置.copy()
    
    def 重置(self) -> None:
        """重置回调状态（用于新的训练）"""
        # 关闭现有图表
        if self._实时图表 is not None:
            self._实时图表.关闭()
        
        # 重置状态
        self._指标记录器 = None
        self._实时图表 = None
        self._训练监控器 = None
        self._终端输出器 = None
        self._总轮次 = 0
        self._每轮批次 = 0
        self._当前轮次 = 0
        self._当前批次 = 0
        self._已初始化 = False
        self._训练开始时间 = None
        self._轮次开始时间 = None
    
    def __repr__(self) -> str:
        组件状态 = []
        if self.配置["启用图表"]:
            组件状态.append("图表")
        if self.配置["启用终端"]:
            组件状态.append("终端")
        if self.配置["启用监控"]:
            组件状态.append("监控")
        
        组件文本 = ", ".join(组件状态) if 组件状态 else "无"
        return f"可视化回调(组件=[{组件文本}], 更新间隔={self.配置['更新间隔']})"
    
    def __enter__(self) -> '可视化回调':
        """支持上下文管理器"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """退出上下文时清理资源"""
        if self._实时图表 is not None:
            self._实时图表.关闭()
        return None



@dataclass
class 训练运行摘要:
    """训练运行的摘要信息"""
    文件路径: str
    运行名称: str
    保存时间: str
    训练时长: float
    总批次数: int
    总轮次数: int
    最终训练loss: Optional[float] = None
    最终验证loss: Optional[float] = None
    最终训练准确率: Optional[float] = None
    最终验证准确率: Optional[float] = None
    
    def 转为字典(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)


@dataclass
class 差异结果:
    """两个训练运行之间的差异结果"""
    运行A名称: str
    运行B名称: str
    指标差异: Dict[str, Dict[str, float]]  # {指标名: {差值, 百分比变化}}
    改进指标: List[str]  # 改进的指标列表
    退步指标: List[str]  # 退步的指标列表
    
    def 转为字典(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)


class 历史数据管理器:
    """
    管理和比较多个训练历史
    
    功能:
    - 扫描和列出所有训练历史 (需求 5.1)
    - 加载历史数据进行对比 (需求 5.2)
    - 高亮运行差异 (需求 5.3)
    - 保存训练历史以便将来比较 (需求 5.4)
    """
    
    def __init__(self, 日志目录: str = "日志/训练"):
        """
        初始化历史数据管理器
        
        参数:
            日志目录: 训练日志保存目录
        """
        self.日志目录 = 日志目录
        self._历史缓存: Dict[str, Dict[str, Any]] = {}  # 缓存已加载的历史数据
        
        # 确保日志目录存在
        if 日志目录:
            os.makedirs(日志目录, exist_ok=True)
    
    def 扫描历史文件(self) -> List[str]:
        """
        扫描日志目录中的所有训练历史文件 (需求 5.1)
        
        返回:
            历史文件路径列表，按时间倒序排列
        """
        if not os.path.exists(self.日志目录):
            return []
        
        # 查找所有 JSON 文件
        模式 = os.path.join(self.日志目录, "*.json")
        文件列表 = glob.glob(模式)
        
        # 按修改时间倒序排列
        文件列表.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        
        return 文件列表
    
    def 获取历史摘要列表(self) -> List[训练运行摘要]:
        """
        获取所有训练历史的摘要信息 (需求 5.1)
        
        返回:
            训练运行摘要列表
        """
        摘要列表 = []
        
        for 文件路径 in self.扫描历史文件():
            摘要 = self._提取运行摘要(文件路径)
            if 摘要:
                摘要列表.append(摘要)
        
        return 摘要列表
    
    def _提取运行摘要(self, 文件路径: str) -> Optional[训练运行摘要]:
        """
        从历史文件中提取运行摘要
        
        参数:
            文件路径: 历史文件路径
        
        返回:
            训练运行摘要，失败返回 None
        """
        try:
            with open(文件路径, 'r', encoding='utf-8') as f:
                数据 = json.load(f)
            
            元信息 = 数据.get("元信息", {})
            轮次历史 = 数据.get("轮次历史", [])
            
            # 提取最终指标
            最终训练loss = None
            最终验证loss = None
            最终训练准确率 = None
            最终验证准确率 = None
            
            if 轮次历史:
                最后一轮 = 轮次历史[-1]
                最终训练loss = 最后一轮.get("训练loss")
                最终验证loss = 最后一轮.get("验证loss")
                最终训练准确率 = 最后一轮.get("训练准确率")
                最终验证准确率 = 最后一轮.get("验证准确率")
            
            # 生成运行名称（使用文件名）
            运行名称 = os.path.splitext(os.path.basename(文件路径))[0]
            
            return 训练运行摘要(
                文件路径=文件路径,
                运行名称=运行名称,
                保存时间=元信息.get("保存时间", "未知"),
                训练时长=元信息.get("训练时长", 0.0),
                总批次数=元信息.get("总批次数", 0),
                总轮次数=元信息.get("总轮次数", 0),
                最终训练loss=最终训练loss,
                最终验证loss=最终验证loss,
                最终训练准确率=最终训练准确率,
                最终验证准确率=最终验证准确率
            )
            
        except (json.JSONDecodeError, KeyError, TypeError, IOError) as e:
            print(f"⚠️ 读取历史文件失败 {文件路径}: {e}")
            return None
    
    def 加载历史数据(self, 文件路径: str, 使用缓存: bool = True) -> Optional[Dict[str, Any]]:
        """
        加载历史训练数据 (需求 5.1)
        
        参数:
            文件路径: 历史文件路径
            使用缓存: 是否使用缓存
        
        返回:
            历史数据字典，失败返回 None
        """
        # 检查缓存
        if 使用缓存 and 文件路径 in self._历史缓存:
            return self._历史缓存[文件路径]
        
        if not os.path.exists(文件路径):
            print(f"⚠️ 历史文件不存在: {文件路径}")
            return None
        
        try:
            with open(文件路径, 'r', encoding='utf-8') as f:
                数据 = json.load(f)
            
            # 缓存数据
            if 使用缓存:
                self._历史缓存[文件路径] = 数据
            
            return 数据
            
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️ 加载历史数据失败: {e}")
            return None
    
    def 提取指标数据(self, 历史数据: Dict[str, Any]) -> Dict[str, List[float]]:
        """
        从历史数据中提取指标序列 (需求 5.2)
        
        参数:
            历史数据: 历史数据字典
        
        返回:
            指标数据字典，格式为 {指标名: [值列表]}
        """
        指标数据 = {}
        
        # 从批次历史提取 loss
        批次历史 = 历史数据.get("批次历史", [])
        if 批次历史:
            指标数据["批次loss"] = [项["loss"] for 项 in 批次历史]
        
        # 从轮次历史提取各项指标
        轮次历史 = 历史数据.get("轮次历史", [])
        if 轮次历史:
            指标数据["训练loss"] = [项["训练loss"] for 项 in 轮次历史]
            
            验证loss = [项.get("验证loss") for 项 in 轮次历史]
            if any(v is not None for v in 验证loss):
                指标数据["验证loss"] = [v for v in 验证loss if v is not None]
            
            训练准确率 = [项.get("训练准确率") for 项 in 轮次历史]
            if any(v is not None for v in 训练准确率):
                指标数据["训练准确率"] = [v for v in 训练准确率 if v is not None]
            
            验证准确率 = [项.get("验证准确率") for 项 in 轮次历史]
            if any(v is not None for v in 验证准确率):
                指标数据["验证准确率"] = [v for v in 验证准确率 if v is not None]
            
            学习率 = [项.get("学习率") for 项 in 轮次历史]
            if any(v is not None for v in 学习率):
                指标数据["学习率"] = [v for v in 学习率 if v is not None]
        
        return 指标数据
    
    def 比较运行(self, 文件路径A: str, 文件路径B: str) -> Optional[差异结果]:
        """
        比较两个训练运行的差异 (需求 5.3)
        
        参数:
            文件路径A: 第一个运行的文件路径（基准）
            文件路径B: 第二个运行的文件路径（对比）
        
        返回:
            差异结果，失败返回 None
        """
        # 加载两个运行的数据
        数据A = self.加载历史数据(文件路径A)
        数据B = self.加载历史数据(文件路径B)
        
        if 数据A is None or 数据B is None:
            return None
        
        # 提取摘要
        摘要A = self._提取运行摘要(文件路径A)
        摘要B = self._提取运行摘要(文件路径B)
        
        if 摘要A is None or 摘要B is None:
            return None
        
        # 计算指标差异
        指标差异 = {}
        改进指标 = []
        退步指标 = []
        
        # 比较最终训练 loss
        if 摘要A.最终训练loss is not None and 摘要B.最终训练loss is not None:
            差值 = 摘要B.最终训练loss - 摘要A.最终训练loss
            百分比 = (差值 / 摘要A.最终训练loss * 100) if 摘要A.最终训练loss != 0 else 0
            指标差异["最终训练loss"] = {"差值": 差值, "百分比变化": 百分比}
            # loss 降低是改进
            if 差值 < 0:
                改进指标.append("最终训练loss")
            elif 差值 > 0:
                退步指标.append("最终训练loss")
        
        # 比较最终验证 loss
        if 摘要A.最终验证loss is not None and 摘要B.最终验证loss is not None:
            差值 = 摘要B.最终验证loss - 摘要A.最终验证loss
            百分比 = (差值 / 摘要A.最终验证loss * 100) if 摘要A.最终验证loss != 0 else 0
            指标差异["最终验证loss"] = {"差值": 差值, "百分比变化": 百分比}
            # loss 降低是改进
            if 差值 < 0:
                改进指标.append("最终验证loss")
            elif 差值 > 0:
                退步指标.append("最终验证loss")
        
        # 比较最终训练准确率
        if 摘要A.最终训练准确率 is not None and 摘要B.最终训练准确率 is not None:
            差值 = 摘要B.最终训练准确率 - 摘要A.最终训练准确率
            百分比 = (差值 / 摘要A.最终训练准确率 * 100) if 摘要A.最终训练准确率 != 0 else 0
            指标差异["最终训练准确率"] = {"差值": 差值, "百分比变化": 百分比}
            # 准确率提高是改进
            if 差值 > 0:
                改进指标.append("最终训练准确率")
            elif 差值 < 0:
                退步指标.append("最终训练准确率")
        
        # 比较最终验证准确率
        if 摘要A.最终验证准确率 is not None and 摘要B.最终验证准确率 is not None:
            差值 = 摘要B.最终验证准确率 - 摘要A.最终验证准确率
            百分比 = (差值 / 摘要A.最终验证准确率 * 100) if 摘要A.最终验证准确率 != 0 else 0
            指标差异["最终验证准确率"] = {"差值": 差值, "百分比变化": 百分比}
            # 准确率提高是改进
            if 差值 > 0:
                改进指标.append("最终验证准确率")
            elif 差值 < 0:
                退步指标.append("最终验证准确率")
        
        # 比较训练时长
        if 摘要A.训练时长 > 0 and 摘要B.训练时长 > 0:
            差值 = 摘要B.训练时长 - 摘要A.训练时长
            百分比 = (差值 / 摘要A.训练时长 * 100)
            指标差异["训练时长"] = {"差值": 差值, "百分比变化": 百分比}
        
        return 差异结果(
            运行A名称=摘要A.运行名称,
            运行B名称=摘要B.运行名称,
            指标差异=指标差异,
            改进指标=改进指标,
            退步指标=退步指标
        )
    
    def 生成差异报告(self, 差异: 差异结果, 使用颜色: bool = True) -> str:
        """
        生成格式化的差异报告 (需求 5.3)
        
        参数:
            差异: 差异结果
            使用颜色: 是否使用终端颜色
        
        返回:
            格式化的差异报告字符串
        """
        # 颜色代码
        重置 = "\033[0m" if 使用颜色 else ""
        粗体 = "\033[1m" if 使用颜色 else ""
        绿色 = "\033[92m" if 使用颜色 else ""
        红色 = "\033[91m" if 使用颜色 else ""
        黄色 = "\033[93m" if 使用颜色 else ""
        青色 = "\033[96m" if 使用颜色 else ""
        
        行列表 = []
        
        # 标题
        行列表.append(f"\n{粗体}{青色}{'='*60}{重置}")
        行列表.append(f"{粗体}{青色}📊 训练运行对比报告{重置}")
        行列表.append(f"{粗体}{青色}{'='*60}{重置}")
        
        # 运行信息
        行列表.append(f"\n{粗体}基准运行:{重置} {差异.运行A名称}")
        行列表.append(f"{粗体}对比运行:{重置} {差异.运行B名称}")
        
        # 指标差异
        行列表.append(f"\n{粗体}{'─'*60}{重置}")
        行列表.append(f"{粗体}指标差异:{重置}")
        行列表.append(f"{粗体}{'─'*60}{重置}")
        
        for 指标名, 差异值 in 差异.指标差异.items():
            差值 = 差异值["差值"]
            百分比 = 差异值["百分比变化"]
            
            # 确定颜色和符号
            if 指标名 in 差异.改进指标:
                颜色 = 绿色
                符号 = "↑" if "准确率" in 指标名 else "↓"
                状态 = "改进"
            elif 指标名 in 差异.退步指标:
                颜色 = 红色
                符号 = "↓" if "准确率" in 指标名 else "↑"
                状态 = "退步"
            else:
                颜色 = 黄色
                符号 = "→"
                状态 = "持平"
            
            # 格式化差值
            if "时长" in 指标名:
                差值文本 = f"{差值:.2f}秒"
            elif "准确率" in 指标名:
                差值文本 = f"{差值*100:.2f}%"
            else:
                差值文本 = f"{差值:.6f}"
            
            行列表.append(
                f"  {颜色}{符号}{重置} {指标名}: "
                f"{颜色}{差值文本} ({百分比:+.2f}%){重置} [{状态}]"
            )
        
        # 总结
        行列表.append(f"\n{粗体}{'─'*60}{重置}")
        行列表.append(f"{粗体}总结:{重置}")
        
        if 差异.改进指标:
            行列表.append(f"  {绿色}✅ 改进指标: {', '.join(差异.改进指标)}{重置}")
        if 差异.退步指标:
            行列表.append(f"  {红色}❌ 退步指标: {', '.join(差异.退步指标)}{重置}")
        if not 差异.改进指标 and not 差异.退步指标:
            行列表.append(f"  {黄色}➡️ 无显著变化{重置}")
        
        行列表.append(f"{粗体}{青色}{'='*60}{重置}\n")
        
        return "\n".join(行列表)
    
    def 打印差异报告(self, 文件路径A: str, 文件路径B: str) -> bool:
        """
        比较两个运行并打印差异报告 (需求 5.3)
        
        参数:
            文件路径A: 第一个运行的文件路径（基准）
            文件路径B: 第二个运行的文件路径（对比）
        
        返回:
            是否成功
        """
        差异 = self.比较运行(文件路径A, 文件路径B)
        if 差异 is None:
            print("⚠️ 无法比较运行")
            return False
        
        报告 = self.生成差异报告(差异)
        print(报告)
        return True
    
    def 获取最近运行(self, 数量: int = 5) -> List[训练运行摘要]:
        """
        获取最近的训练运行 (需求 5.1)
        
        参数:
            数量: 返回的运行数量
        
        返回:
            最近的训练运行摘要列表
        """
        所有摘要 = self.获取历史摘要列表()
        return 所有摘要[:数量]
    
    def 查找最佳运行(self, 指标名: str = "最终验证loss", 
                     越小越好: bool = True) -> Optional[训练运行摘要]:
        """
        查找指定指标最佳的运行 (需求 5.3)
        
        参数:
            指标名: 要比较的指标名称
            越小越好: 是否越小越好（如 loss），否则越大越好（如准确率）
        
        返回:
            最佳运行的摘要，没有找到返回 None
        """
        所有摘要 = self.获取历史摘要列表()
        
        if not 所有摘要:
            return None
        
        # 过滤有效的摘要
        有效摘要 = []
        for 摘要 in 所有摘要:
            值 = getattr(摘要, 指标名.replace("最终", "最终"), None)
            if 值 is not None:
                有效摘要.append((摘要, 值))
        
        if not 有效摘要:
            return None
        
        # 排序并返回最佳
        有效摘要.sort(key=lambda x: x[1], reverse=not 越小越好)
        return 有效摘要[0][0]
    
    def 保存对比结果(self, 差异: 差异结果, 文件路径: Optional[str] = None) -> str:
        """
        保存对比结果到文件 (需求 5.4)
        
        参数:
            差异: 差异结果
            文件路径: 保存路径，如果不指定则自动生成
        
        返回:
            保存的文件路径
        """
        if 文件路径 is None:
            时间戳 = datetime.now().strftime("%Y%m%d_%H%M%S")
            文件路径 = os.path.join(self.日志目录, f"对比结果_{时间戳}.json")
        
        # 确保目录存在
        目录 = os.path.dirname(文件路径)
        if 目录:
            os.makedirs(目录, exist_ok=True)
        
        # 保存数据
        数据 = {
            "对比时间": datetime.now().isoformat(),
            "运行A": 差异.运行A名称,
            "运行B": 差异.运行B名称,
            "指标差异": 差异.指标差异,
            "改进指标": 差异.改进指标,
            "退步指标": 差异.退步指标
        }
        
        with open(文件路径, 'w', encoding='utf-8') as f:
            json.dump(数据, f, ensure_ascii=False, indent=2)
        
        return 文件路径
    
    def 清除缓存(self) -> None:
        """清除历史数据缓存"""
        self._历史缓存.clear()
    
    def 删除历史文件(self, 文件路径: str) -> bool:
        """
        删除历史文件
        
        参数:
            文件路径: 要删除的文件路径
        
        返回:
            是否删除成功
        """
        try:
            if os.path.exists(文件路径):
                os.remove(文件路径)
                # 从缓存中移除
                if 文件路径 in self._历史缓存:
                    del self._历史缓存[文件路径]
                return True
            return False
        except IOError as e:
            print(f"⚠️ 删除文件失败: {e}")
            return False
    
    def 清理旧历史(self, 保留数量: int = 10) -> int:
        """
        清理旧的历史文件，只保留最近的几个
        
        参数:
            保留数量: 要保留的文件数量
        
        返回:
            删除的文件数量
        """
        文件列表 = self.扫描历史文件()
        
        if len(文件列表) <= 保留数量:
            return 0
        
        # 删除旧文件
        要删除的文件 = 文件列表[保留数量:]
        删除数量 = 0
        
        for 文件路径 in 要删除的文件:
            if self.删除历史文件(文件路径):
                删除数量 += 1
        
        return 删除数量
    
    def __repr__(self) -> str:
        文件数量 = len(self.扫描历史文件())
        缓存数量 = len(self._历史缓存)
        return f"历史数据管理器(日志目录='{self.日志目录}', 文件数={文件数量}, 缓存数={缓存数量})"
