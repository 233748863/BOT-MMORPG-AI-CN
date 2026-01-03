"""
异步检测模块
将 YOLO 目标检测从主循环分离到独立线程

功能:
- 异步检测处理
- 线程安全的结果缓存
- 检测频率控制
- 性能监控
"""

import time
import queue
import threading
from typing import List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import deque
import numpy as np
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
日志 = logging.getLogger(__name__)


@dataclass
class 检测任务:
    """检测任务"""
    图像: np.ndarray
    提交时间: float
    帧编号: int


@dataclass
class 性能统计:
    """性能统计"""
    平均延迟: float = 0.0  # 毫秒
    最小延迟: float = 0.0
    最大延迟: float = 0.0
    检测次数: int = 0
    队列深度: int = 0
    溢出次数: int = 0
    缓存年龄: float = 0.0  # 秒
    
    def to_dict(self) -> dict:
        return {
            '平均延迟': round(self.平均延迟, 2),
            '最小延迟': round(self.最小延迟, 2),
            '最大延迟': round(self.最大延迟, 2),
            '检测次数': self.检测次数,
            '队列深度': self.队列深度,
            '溢出次数': self.溢出次数,
            '缓存年龄': round(self.缓存年龄, 3)
        }


class 检测队列:
    """线程安全的检测任务队列"""
    
    def __init__(self, 最大大小: int = 3):
        """
        初始化检测队列
        
        参数:
            最大大小: 队列最大容量
        """
        self._队列: queue.Queue = queue.Queue(maxsize=最大大小)
        self._溢出计数: int = 0
        self._帧计数: int = 0
        self._锁 = threading.Lock()
    
    def 放入(self, 图像: np.ndarray) -> bool:
        """
        放入图像帧
        
        参数:
            图像: 输入图像
            
        返回:
            是否成功放入
        """
        with self._锁:
            self._帧计数 += 1
            帧编号 = self._帧计数
        
        任务 = 检测任务(
            图像=图像.copy(),
            提交时间=time.time(),
            帧编号=帧编号
        )
        
        try:
            self._队列.put_nowait(任务)
            return True
        except queue.Full:
            with self._锁:
                self._溢出计数 += 1
            return False
    
    def 取出(self, 超时: float = 1.0) -> Optional[检测任务]:
        """
        取出检测任务
        
        参数:
            超时: 超时时间（秒）
            
        返回:
            检测任务，超时返回 None
        """
        try:
            return self._队列.get(timeout=超时)
        except queue.Empty:
            return None
    
    def 清空(self):
        """清空队列"""
        while not self._队列.empty():
            try:
                self._队列.get_nowait()
            except queue.Empty:
                break
    
    def 获取深度(self) -> int:
        """获取当前队列深度"""
        return self._队列.qsize()
    
    def 获取溢出计数(self) -> int:
        """获取队列溢出次数"""
        with self._锁:
            return self._溢出计数


class 结果缓存:
    """线程安全的检测结果缓存"""
    
    def __init__(self):
        self._结果: List[Any] = []
        self._时间戳: float = 0.0
        self._帧编号: int = 0
        self._锁 = threading.Lock()
    
    def 更新(self, 结果: List[Any], 帧编号: int = 0):
        """
        更新缓存结果
        
        参数:
            结果: 检测结果列表
            帧编号: 对应的帧编号
        """
        with self._锁:
            self._结果 = 结果
            self._时间戳 = time.time()
            self._帧编号 = 帧编号
    
    def 获取(self) -> Tuple[List[Any], float, int]:
        """
        获取缓存结果
        
        返回:
            (结果列表, 时间戳, 帧编号)
        """
        with self._锁:
            return self._结果.copy(), self._时间戳, self._帧编号
    
    def 获取年龄(self) -> float:
        """
        获取缓存结果的年龄
        
        返回:
            年龄（秒）
        """
        with self._锁:
            if self._时间戳 == 0:
                return float('inf')
            return time.time() - self._时间戳
    
    def 是否有效(self, 最大年龄: float = 1.0) -> bool:
        """
        检查缓存是否有效
        
        参数:
            最大年龄: 最大有效年龄（秒）
            
        返回:
            是否有效
        """
        return self.获取年龄() <= 最大年龄


class 性能监控器:
    """检测性能监控"""
    
    def __init__(self, 窗口大小: int = 100):
        """
        初始化性能监控器
        
        参数:
            窗口大小: 统计窗口大小
        """
        self._延迟记录: deque = deque(maxlen=窗口大小)
        self._检测次数: int = 0
        self._锁 = threading.Lock()
    
    def 记录延迟(self, 延迟: float):
        """
        记录一次检测延迟
        
        参数:
            延迟: 延迟时间（毫秒）
        """
        with self._锁:
            self._延迟记录.append(延迟)
            self._检测次数 += 1
    
    def 获取统计(self) -> dict:
        """
        获取统计信息
        
        返回:
            统计字典
        """
        with self._锁:
            if not self._延迟记录:
                return {
                    '平均延迟': 0.0,
                    '最小延迟': 0.0,
                    '最大延迟': 0.0,
                    '检测次数': self._检测次数
                }
            
            延迟列表 = list(self._延迟记录)
            return {
                '平均延迟': np.mean(延迟列表),
                '最小延迟': np.min(延迟列表),
                '最大延迟': np.max(延迟列表),
                '检测次数': self._检测次数
            }
    
    def 重置(self):
        """重置统计"""
        with self._锁:
            self._延迟记录.clear()
            self._检测次数 = 0


class 异步检测器:
    """异步 YOLO 目标检测器"""
    
    def __init__(self, 检测器=None, 
                 队列大小: int = 3,
                 检测间隔: int = 3,
                 最大缓存年龄: float = 1.0):
        """
        初始化异步检测器
        
        参数:
            检测器: YOLO 检测器实例
            队列大小: 检测队列最大大小
            检测间隔: 每 N 帧检测一次
            最大缓存年龄: 缓存最大有效年龄（秒）
        """
        self.检测器 = 检测器
        self.检测间隔 = max(1, 检测间隔)
        self.最大缓存年龄 = 最大缓存年龄
        
        self._队列 = 检测队列(队列大小)
        self._缓存 = 结果缓存()
        self._监控器 = 性能监控器()
        
        self._运行中 = False
        self._线程: Optional[threading.Thread] = None
        self._帧计数 = 0
        self._停止事件 = threading.Event()
        
        # 错误处理
        self._连续错误数 = 0
        self._最大连续错误 = 5
        self._回退到同步 = False
    
    def 设置检测器(self, 检测器):
        """设置检测器"""
        self.检测器 = 检测器
    
    def 启动(self) -> bool:
        """
        启动检测线程
        
        返回:
            是否成功启动
        """
        if self._运行中:
            日志.warning("检测线程已在运行")
            return True
        
        if self.检测器 is None:
            日志.error("检测器未设置，无法启动")
            return False
        
        self._停止事件.clear()
        self._运行中 = True
        self._回退到同步 = False
        
        try:
            self._线程 = threading.Thread(target=self._检测循环, daemon=True)
            self._线程.start()
            日志.info("异步检测线程已启动")
            return True
        except Exception as e:
            日志.error(f"启动检测线程失败: {e}")
            self._运行中 = False
            self._回退到同步 = True
            return False
    
    def 停止(self, 超时: float = 1.0) -> bool:
        """
        停止检测线程
        
        参数:
            超时: 等待线程结束的超时时间（秒）
            
        返回:
            是否成功停止
        """
        if not self._运行中:
            return True
        
        日志.info("正在停止异步检测线程...")
        self._停止事件.set()
        self._运行中 = False
        
        if self._线程 and self._线程.is_alive():
            self._线程.join(timeout=超时)
            
            if self._线程.is_alive():
                日志.warning("检测线程未能在超时时间内停止")
                return False
        
        日志.info("异步检测线程已停止")
        return True
    
    def _检测循环(self):
        """检测工作线程主循环"""
        日志.info("检测工作线程开始运行")
        
        while not self._停止事件.is_set():
            try:
                # 从队列获取任务
                任务 = self._队列.取出(超时=0.5)
                
                if 任务 is None:
                    continue
                
                # 执行检测
                开始时间 = time.time()
                
                try:
                    结果 = self.检测器.检测(任务.图像)
                    self._连续错误数 = 0
                except Exception as e:
                    日志.error(f"检测执行失败: {e}")
                    self._连续错误数 += 1
                    
                    if self._连续错误数 >= self._最大连续错误:
                        日志.error("连续错误过多，回退到同步模式")
                        self._回退到同步 = True
                        break
                    continue
                
                # 计算延迟
                延迟 = (time.time() - 开始时间) * 1000
                self._监控器.记录延迟(延迟)
                
                # 更新缓存
                self._缓存.更新(结果, 任务.帧编号)
                
            except Exception as e:
                日志.error(f"检测循环异常: {e}")
                continue
        
        日志.info("检测工作线程结束")
    
    def 提交帧(self, 图像: np.ndarray) -> bool:
        """
        提交图像帧进行检测
        
        参数:
            图像: 输入图像
            
        返回:
            是否成功提交
        """
        self._帧计数 += 1
        
        # 检查是否需要跳过
        if self._帧计数 % self.检测间隔 != 0:
            return False
        
        # 如果回退到同步模式，直接执行检测
        if self._回退到同步:
            return self._同步检测(图像)
        
        # 提交到队列
        return self._队列.放入(图像)
    
    def _同步检测(self, 图像: np.ndarray) -> bool:
        """同步执行检测（回退模式）"""
        if self.检测器 is None:
            return False
        
        try:
            开始时间 = time.time()
            结果 = self.检测器.检测(图像)
            延迟 = (time.time() - 开始时间) * 1000
            
            self._监控器.记录延迟(延迟)
            self._缓存.更新(结果, self._帧计数)
            return True
        except Exception as e:
            日志.error(f"同步检测失败: {e}")
            return False
    
    def 获取结果(self) -> List[Any]:
        """
        获取最新检测结果（非阻塞）
        
        返回:
            检测结果列表
        """
        结果, 时间戳, 帧编号 = self._缓存.获取()
        return 结果
    
    def 获取结果带时间戳(self) -> Tuple[List[Any], float, int]:
        """
        获取检测结果及其时间戳
        
        返回:
            (结果列表, 时间戳, 帧编号)
        """
        return self._缓存.获取()
    
    def 获取统计(self) -> 性能统计:
        """获取性能统计信息"""
        监控统计 = self._监控器.获取统计()
        
        return 性能统计(
            平均延迟=监控统计['平均延迟'],
            最小延迟=监控统计['最小延迟'],
            最大延迟=监控统计['最大延迟'],
            检测次数=监控统计['检测次数'],
            队列深度=self._队列.获取深度(),
            溢出次数=self._队列.获取溢出计数(),
            缓存年龄=self._缓存.获取年龄()
        )
    
    def 打印统计(self):
        """打印性能统计"""
        统计 = self.获取统计()
        print("\n异步检测统计:")
        print(f"  检测次数: {统计.检测次数}")
        print(f"  平均延迟: {统计.平均延迟:.2f} ms")
        print(f"  最小延迟: {统计.最小延迟:.2f} ms")
        print(f"  最大延迟: {统计.最大延迟:.2f} ms")
        print(f"  队列深度: {统计.队列深度}")
        print(f"  溢出次数: {统计.溢出次数}")
        print(f"  缓存年龄: {统计.缓存年龄:.3f} s")
        print(f"  运行模式: {'同步' if self._回退到同步 else '异步'}")
    
    def 是否运行中(self) -> bool:
        """检查是否正在运行"""
        return self._运行中
    
    def 是否同步模式(self) -> bool:
        """检查是否处于同步回退模式"""
        return self._回退到同步
    
    def 强制刷新(self, 图像: np.ndarray) -> List[Any]:
        """
        强制执行检测并返回结果
        
        参数:
            图像: 输入图像
            
        返回:
            检测结果
        """
        if self.检测器 is None:
            return []
        
        try:
            结果 = self.检测器.检测(图像)
            self._缓存.更新(结果, self._帧计数)
            return 结果
        except Exception as e:
            日志.error(f"强制刷新失败: {e}")
            return self.获取结果()
    
    def __enter__(self):
        """上下文管理器入口"""
        self.启动()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.停止()
        return False


# 默认配置
默认异步检测配置 = {
    "队列大小": 3,
    "检测间隔": 3,
    "最大缓存年龄": 1.0
}
