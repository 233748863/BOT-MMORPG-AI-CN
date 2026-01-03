"""
训练可视化模块
实时监控训练过程，可视化指标变化

功能:
- 指标记录和持久化
- 实时图表显示
- 训练健康监控
- 终端进度输出
"""

import os
import json
import time
import threading
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from collections import deque
import numpy as np
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
日志 = logging.getLogger(__name__)


@dataclass
class 批次指标:
    """单个批次的指标"""
    批次: int
    loss: float
    时间戳: float = field(default_factory=time.time)
    其他: Dict[str, float] = field(default_factory=dict)


@dataclass
class 轮次指标:
    """单个轮次的指标"""
    轮次: int
    训练loss: float
    验证loss: Optional[float] = None
    训练准确率: Optional[float] = None
    验证准确率: Optional[float] = None
    学习率: Optional[float] = None
    耗时: float = 0.0
    时间戳: float = field(default_factory=time.time)


class 指标记录器:
    """记录训练过程中的各项指标"""
    
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
        self._最大历史: int = 10000  # 防止内存溢出
        
        # 确保目录存在
        os.makedirs(日志目录, exist_ok=True)
    
    def 记录批次(self, 批次: int, loss: float, **其他指标):
        """
        记录每个批次的指标
        
        参数:
            批次: 当前批次号
            loss: 损失值
            其他指标: 其他需要记录的指标
        """
        指标 = 批次指标(批次=批次, loss=loss, 其他=其他指标)
        self._批次历史.append(指标)
        
        # 限制历史长度
        if len(self._批次历史) > self._最大历史:
            self._批次历史 = self._批次历史[-self._最大历史:]
    
    def 记录轮次(self, 轮次: int, 训练loss: float, 验证loss: float = None,
                 训练准确率: float = None, 验证准确率: float = None,
                 学习率: float = None, 耗时: float = 0.0):
        """
        记录每个轮次的指标
        
        参数:
            轮次: 当前轮次号
            训练loss: 训练损失
            验证loss: 验证损失
            训练准确率: 训练准确率
            验证准确率: 验证准确率
            学习率: 当前学习率
            耗时: 本轮耗时
        """
        指标 = 轮次指标(
            轮次=轮次, 训练loss=训练loss, 验证loss=验证loss,
            训练准确率=训练准确率, 验证准确率=验证准确率,
            学习率=学习率, 耗时=耗时
        )
        self._轮次历史.append(指标)
        self._当前轮次 = 轮次
    
    def 获取历史(self, 指标名: str) -> List[float]:
        """获取指定指标的历史记录"""
        if 指标名 == "loss" or 指标名 == "批次loss":
            return [m.loss for m in self._批次历史]
        elif 指标名 == "训练loss":
            return [m.训练loss for m in self._轮次历史]
        elif 指标名 == "验证loss":
            return [m.验证loss for m in self._轮次历史 if m.验证loss is not None]
        elif 指标名 == "训练准确率":
            return [m.训练准确率 for m in self._轮次历史 if m.训练准确率 is not None]
        elif 指标名 == "验证准确率":
            return [m.验证准确率 for m in self._轮次历史 if m.验证准确率 is not None]
        elif 指标名 == "学习率":
            return [m.学习率 for m in self._轮次历史 if m.学习率 is not None]
        return []
    
    def 获取最新批次(self, n: int = 100) -> List[批次指标]:
        """获取最近 n 个批次的指标"""
        return self._批次历史[-n:]
    
    def 获取轮次历史(self) -> List[轮次指标]:
        """获取所有轮次的指标"""
        return self._轮次历史.copy()

    def 保存(self, 文件名: str = None):
        """保存指标到文件"""
        if 文件名 is None:
            时间戳 = time.strftime("%Y%m%d_%H%M%S")
            文件名 = f"训练日志_{时间戳}.json"
        
        文件路径 = os.path.join(self.日志目录, 文件名)
        
        数据 = {
            "批次历史": [asdict(m) for m in self._批次历史],
            "轮次历史": [asdict(m) for m in self._轮次历史],
            "保存时间": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        try:
            with open(文件路径, 'w', encoding='utf-8') as f:
                json.dump(数据, f, ensure_ascii=False, indent=2)
            日志.info(f"训练日志已保存: {文件路径}")
        except Exception as e:
            日志.error(f"保存训练日志失败: {e}")
    
    def 加载(self, 日志路径: str) -> bool:
        """从文件加载历史指标"""
        if not os.path.exists(日志路径):
            日志.warning(f"日志文件不存在: {日志路径}")
            return False
        
        try:
            with open(日志路径, 'r', encoding='utf-8') as f:
                数据 = json.load(f)
            
            self._批次历史 = [批次指标(**m) for m in 数据.get("批次历史", [])]
            self._轮次历史 = [轮次指标(**m) for m in 数据.get("轮次历史", [])]
            
            日志.info(f"已加载训练日志: {len(self._轮次历史)} 轮次")
            return True
        except Exception as e:
            日志.error(f"加载训练日志失败: {e}")
            return False


class 训练状态(Enum):
    """训练健康状态"""
    正常 = "normal"
    警告 = "warning"
    异常 = "abnormal"


class 训练监控器:
    """监控训练健康状况"""
    
    def __init__(self, 配置: Dict = None):
        """
        初始化监控器
        
        参数:
            配置: 监控配置（阈值等）
        """
        默认配置 = {
            "平台期检测": {"窗口": 10, "阈值": 0.001},
            "发散检测": {"窗口": 5, "阈值": 0.1},
            "尖峰检测": {"阈值": 3.0}
        }
        self.配置 = {**默认配置, **(配置 or {})}
    
    def 检查(self, 指标记录器: 指标记录器) -> Tuple[训练状态, List[str]]:
        """
        检查训练健康状况
        
        返回:
            (状态, 问题列表)
        """
        问题列表 = []
        loss历史 = 指标记录器.获取历史("训练loss")
        
        if len(loss历史) < 3:
            return 训练状态.正常, []
        
        # 检测各种问题
        if self.检测发散(loss历史):
            问题列表.append("⚠️ 检测到 loss 发散，建议降低学习率")
        
        if self.检测平台期(loss历史):
            问题列表.append("📊 检测到训练平台期，loss 变化很小")
        
        if self.检测尖峰(loss历史):
            问题列表.append("📈 检测到 loss 尖峰，可能存在异常样本")
        
        # 确定状态
        if any("发散" in p for p in 问题列表):
            状态 = 训练状态.异常
        elif 问题列表:
            状态 = 训练状态.警告
        else:
            状态 = 训练状态.正常
        
        return 状态, 问题列表

    def 检测平台期(self, loss历史: List[float], 窗口: int = None) -> bool:
        """
        检测 loss 是否停滞
        
        参数:
            loss历史: loss 历史记录
            窗口: 检测窗口大小
            
        返回:
            是否处于平台期
        """
        窗口 = 窗口 or self.配置["平台期检测"]["窗口"]
        阈值 = self.配置["平台期检测"]["阈值"]
        
        if len(loss历史) < 窗口:
            return False
        
        最近数据 = loss历史[-窗口:]
        变化范围 = max(最近数据) - min(最近数据)
        
        return 变化范围 < 阈值
    
    def 检测发散(self, loss历史: List[float], 窗口: int = None) -> bool:
        """
        检测 loss 是否发散
        
        参数:
            loss历史: loss 历史记录
            窗口: 检测窗口大小
            
        返回:
            是否发散
        """
        窗口 = 窗口 or self.配置["发散检测"]["窗口"]
        阈值 = self.配置["发散检测"]["阈值"]
        
        if len(loss历史) < 窗口:
            return False
        
        最近数据 = loss历史[-窗口:]
        
        # 检查是否连续上升
        连续上升 = all(最近数据[i] < 最近数据[i+1] for i in range(len(最近数据)-1))
        
        if 连续上升:
            上升幅度 = (最近数据[-1] - 最近数据[0]) / (最近数据[0] + 1e-7)
            return 上升幅度 > 阈值
        
        return False
    
    def 检测尖峰(self, loss历史: List[float], 阈值: float = None) -> bool:
        """
        检测 loss 尖峰
        
        参数:
            loss历史: loss 历史记录
            阈值: 标准差倍数阈值
            
        返回:
            是否有尖峰
        """
        阈值 = 阈值 or self.配置["尖峰检测"]["阈值"]
        
        if len(loss历史) < 10:
            return False
        
        数据 = np.array(loss历史)
        均值 = np.mean(数据[:-1])
        标准差 = np.std(数据[:-1])
        
        if 标准差 < 1e-7:
            return False
        
        最新值 = 数据[-1]
        z分数 = abs(最新值 - 均值) / 标准差
        
        return z分数 > 阈值


class 终端输出器:
    """优化的终端训练输出"""
    
    def __init__(self, 静默模式: bool = False):
        """
        初始化输出器
        
        参数:
            静默模式: 是否最小化输出
        """
        self.静默模式 = 静默模式
        self._上次输出时间 = 0
        self._输出间隔 = 0.5  # 秒
    
    def 显示进度条(self, 当前: int, 总数: int, 前缀: str = "", 长度: int = 30):
        """显示进度条"""
        if self.静默模式:
            return
        
        百分比 = 当前 / 总数 if 总数 > 0 else 0
        已完成 = int(长度 * 百分比)
        进度条 = "█" * 已完成 + "░" * (长度 - 已完成)
        
        print(f"\r{前缀} |{进度条}| {百分比*100:.1f}% ({当前}/{总数})", end="", flush=True)

    def 显示批次信息(self, 批次: int, loss: float, 速度: float = None):
        """
        显示批次信息
        
        参数:
            批次: 当前批次
            loss: 当前 loss
            速度: 每秒处理样本数
        """
        if self.静默模式:
            return
        
        当前时间 = time.time()
        if 当前时间 - self._上次输出时间 < self._输出间隔:
            return
        
        self._上次输出时间 = 当前时间
        
        速度文本 = f" | {速度:.1f} 样本/秒" if 速度 else ""
        print(f"\r  批次 {批次}: loss={loss:.4f}{速度文本}    ", end="", flush=True)
    
    def 显示轮次摘要(self, 轮次: int, 训练loss: float, 验证loss: float = None,
                    训练准确率: float = None, 验证准确率: float = None, 耗时: float = 0):
        """显示轮次结束摘要"""
        print()  # 换行
        print(f"\n{'='*50}")
        print(f"📊 轮次 {轮次} 完成")
        print(f"{'='*50}")
        print(f"  训练 Loss: {训练loss:.4f}")
        
        if 验证loss is not None:
            print(f"  验证 Loss: {验证loss:.4f}")
        
        if 训练准确率 is not None:
            print(f"  训练准确率: {训练准确率*100:.2f}%")
        
        if 验证准确率 is not None:
            print(f"  验证准确率: {验证准确率*100:.2f}%")
        
        if 耗时 > 0:
            print(f"  耗时: {耗时:.1f} 秒")
        
        print(f"{'='*50}\n")
    
    def 显示预计时间(self, 已完成: int, 总数: int, 已用时间: float):
        """显示预计剩余时间"""
        if self.静默模式 or 已完成 == 0:
            return
        
        平均时间 = 已用时间 / 已完成
        剩余数量 = 总数 - 已完成
        预计剩余 = 平均时间 * 剩余数量
        
        if 预计剩余 > 3600:
            时间文本 = f"{预计剩余/3600:.1f} 小时"
        elif 预计剩余 > 60:
            时间文本 = f"{预计剩余/60:.1f} 分钟"
        else:
            时间文本 = f"{预计剩余:.0f} 秒"
        
        print(f"  预计剩余时间: {时间文本}")
    
    def 显示警告(self, 消息: str, 状态: 训练状态 = 训练状态.警告):
        """显示带颜色的警告信息"""
        颜色代码 = {
            训练状态.正常: "\033[92m",    # 绿色
            训练状态.警告: "\033[93m",    # 黄色
            训练状态.异常: "\033[91m"     # 红色
        }
        重置 = "\033[0m"
        
        颜色 = 颜色代码.get(状态, "")
        print(f"{颜色}{消息}{重置}")


class 实时图表:
    """实时更新的训练曲线图"""
    
    def __init__(self, 更新间隔: int = 10, 图表配置: Dict = None):
        """
        初始化实时图表
        
        参数:
            更新间隔: 每隔多少批次更新一次
            图表配置: 图表显示配置
        """
        self.更新间隔 = 更新间隔
        self.图表配置 = 图表配置 or {}
        self._图表 = None
        self._子图 = {}
        self._线条 = {}
        self._历史数据 = {}
        self._已启动 = False
        self._锁 = threading.Lock()

    def 启动(self):
        """启动图表窗口（非阻塞）"""
        try:
            import matplotlib.pyplot as plt
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
            plt.rcParams['axes.unicode_minus'] = False
            
            plt.ion()  # 交互模式
            self._图表, axes = plt.subplots(2, 2, figsize=(12, 8))
            self._图表.suptitle('训练监控')
            
            # 初始化子图
            self._子图 = {
                'loss': axes[0, 0],
                '准确率': axes[0, 1],
                '学习率': axes[1, 0],
                '批次loss': axes[1, 1]
            }
            
            for 名称, ax in self._子图.items():
                ax.set_title(名称)
                ax.set_xlabel('轮次' if 名称 != '批次loss' else '批次')
                ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.show(block=False)
            
            self._已启动 = True
            日志.info("实时图表已启动")
            
        except ImportError:
            日志.warning("matplotlib 未安装，无法显示实时图表")
        except Exception as e:
            日志.warning(f"启动图表失败: {e}")
    
    def 更新(self, 指标记录器: 指标记录器):
        """更新图表数据"""
        if not self._已启动:
            return
        
        try:
            import matplotlib.pyplot as plt
            
            with self._锁:
                # 更新 loss 图
                训练loss = 指标记录器.获取历史("训练loss")
                验证loss = 指标记录器.获取历史("验证loss")
                
                ax = self._子图['loss']
                ax.clear()
                ax.set_title('Loss')
                if 训练loss:
                    ax.plot(训练loss, 'b-', label='训练')
                if 验证loss:
                    ax.plot(验证loss, 'r-', label='验证')
                ax.legend()
                ax.grid(True, alpha=0.3)
                
                # 更新准确率图
                训练准确率 = 指标记录器.获取历史("训练准确率")
                验证准确率 = 指标记录器.获取历史("验证准确率")
                
                ax = self._子图['准确率']
                ax.clear()
                ax.set_title('准确率')
                if 训练准确率:
                    ax.plot([a*100 for a in 训练准确率], 'b-', label='训练')
                if 验证准确率:
                    ax.plot([a*100 for a in 验证准确率], 'r-', label='验证')
                ax.set_ylabel('%')
                ax.legend()
                ax.grid(True, alpha=0.3)
                
                # 更新学习率图
                学习率 = 指标记录器.获取历史("学习率")
                ax = self._子图['学习率']
                ax.clear()
                ax.set_title('学习率')
                if 学习率:
                    ax.plot(学习率, 'g-')
                ax.grid(True, alpha=0.3)
                
                # 更新批次 loss 图
                批次数据 = 指标记录器.获取最新批次(100)
                ax = self._子图['批次loss']
                ax.clear()
                ax.set_title('批次 Loss (最近100)')
                if 批次数据:
                    ax.plot([m.loss for m in 批次数据], 'b-', alpha=0.7)
                ax.grid(True, alpha=0.3)
                
                self._图表.canvas.draw_idle()
                self._图表.canvas.flush_events()
                
        except Exception as e:
            日志.warning(f"更新图表失败: {e}")
    
    def 叠加历史(self, 历史数据: Dict, 标签: str):
        """叠加历史训练数据"""
        self._历史数据[标签] = 历史数据
    
    def 关闭(self):
        """关闭图表窗口"""
        if self._已启动:
            try:
                import matplotlib.pyplot as plt
                plt.close(self._图表)
            except:
                pass
            self._已启动 = False


class 可视化回调:
    """训练可视化回调函数"""
    
    def __init__(self, 启用图表: bool = True, 启用终端: bool = True,
                 更新间隔: int = 10, 日志目录: str = "日志/训练"):
        """
        初始化回调
        
        参数:
            启用图表: 是否启用实时图表
            启用终端: 是否启用终端输出
            更新间隔: 图表更新间隔（批次数）
            日志目录: 日志保存目录
        """
        self.启用图表 = 启用图表
        self.启用终端 = 启用终端
        self.更新间隔 = 更新间隔
        
        self.记录器 = 指标记录器(日志目录)
        self.监控器 = 训练监控器()
        self.输出器 = 终端输出器(静默模式=not 启用终端)
        self.图表 = 实时图表(更新间隔) if 启用图表 else None
        
        self._总轮次 = 0
        self._每轮批次 = 0
        self._当前轮次 = 0
        self._轮次开始时间 = 0
        self._训练开始时间 = 0
        self._批次计数 = 0
    
    def on_train_begin(self, 总轮次: int, 每轮批次: int):
        """训练开始时调用"""
        self._总轮次 = 总轮次
        self._每轮批次 = 每轮批次
        self._训练开始时间 = time.time()
        
        print("\n" + "=" * 60)
        print("🚀 开始训练")
        print(f"   总轮次: {总轮次}, 每轮批次: {每轮批次}")
        print("=" * 60 + "\n")
        
        if self.图表:
            self.图表.启动()
    
    def on_epoch_begin(self, 轮次: int):
        """每个轮次开始时调用"""
        self._当前轮次 = 轮次
        self._轮次开始时间 = time.time()
        self._批次计数 = 0
        
        print(f"\n📌 轮次 {轮次}/{self._总轮次}")
    
    def on_batch_end(self, 批次: int, loss: float, **指标):
        """每个批次结束时调用"""
        self._批次计数 += 1
        
        # 记录指标
        self.记录器.记录批次(批次, loss, **指标)
        
        # 显示进度
        self.输出器.显示进度条(self._批次计数, self._每轮批次, f"  轮次 {self._当前轮次}")
        
        # 更新图表
        if self.图表 and self._批次计数 % self.更新间隔 == 0:
            self.图表.更新(self.记录器)
    
    def on_epoch_end(self, 轮次: int, 训练loss: float = None, 验证loss: float = None,
                     训练准确率: float = None, 验证准确率: float = None,
                     学习率: float = None, **其他指标):
        """每个轮次结束时调用"""
        耗时 = time.time() - self._轮次开始时间
        
        # 记录轮次指标
        self.记录器.记录轮次(
            轮次, 训练loss or 0, 验证loss,
            训练准确率, 验证准确率, 学习率, 耗时
        )
        
        # 显示摘要
        self.输出器.显示轮次摘要(
            轮次, 训练loss or 0, 验证loss,
            训练准确率, 验证准确率, 耗时
        )
        
        # 检查训练健康状况
        状态, 问题列表 = self.监控器.检查(self.记录器)
        for 问题 in 问题列表:
            self.输出器.显示警告(问题, 状态)
        
        # 显示预计时间
        已用时间 = time.time() - self._训练开始时间
        self.输出器.显示预计时间(轮次, self._总轮次, 已用时间)
        
        # 更新图表
        if self.图表:
            self.图表.更新(self.记录器)
    
    def on_train_end(self):
        """训练结束时调用"""
        总耗时 = time.time() - self._训练开始时间
        
        print("\n" + "=" * 60)
        print("✅ 训练完成!")
        print(f"   总耗时: {总耗时/60:.1f} 分钟")
        print("=" * 60 + "\n")
        
        # 保存日志
        self.记录器.保存()
        
        # 关闭图表
        if self.图表:
            self.图表.关闭()
    
    def 获取记录器(self) -> 指标记录器:
        """获取指标记录器"""
        return self.记录器
