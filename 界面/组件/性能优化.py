# -*- coding: utf-8 -*-
"""
性能优化模块

提供UI性能优化相关的组件和工具，包括:
- 延迟加载页面管理器: 页面按需创建，已创建的从缓存获取
- 状态更新节流器: 避免过于频繁的UI更新
- 性能监控器: 监控UI性能指标

符合设计规范:
- 首次加载时间: < 500ms
- 页面切换时间: < 100ms
- 状态更新延迟: < 50ms
"""

import time
from typing import Dict, Optional, Type, Callable, Any
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QTimer, QObject, Signal


class 延迟加载页面管理器:
    """
    页面延迟加载管理器
    
    实现页面的按需创建和缓存管理:
    - 页面在首次访问时才创建
    - 已创建的页面从缓存获取
    - 支持页面预加载
    - 支持页面销毁和重建
    
    性能目标:
    - 首次加载时间: < 500ms
    - 页面切换时间: < 100ms
    """
    
    def __init__(self):
        """初始化延迟加载管理器"""
        # 页面缓存: 页面名称 -> 页面实例
        self._页面缓存: Dict[str, QWidget] = {}
        
        # 页面类映射: 页面名称 -> 页面类
        self._页面类映射: Dict[str, Type[QWidget]] = {}
        
        # 页面创建参数: 页面名称 -> 创建参数字典
        self._页面参数映射: Dict[str, Dict[str, Any]] = {}
        
        # 页面创建回调: 页面名称 -> 创建后的回调函数
        self._页面回调映射: Dict[str, Callable[[QWidget], None]] = {}
        
        # 性能统计
        self._创建时间记录: Dict[str, float] = {}
    
    def 注册页面类(
        self, 
        页面名称: str, 
        页面类: Type[QWidget],
        创建参数: Optional[Dict[str, Any]] = None,
        创建回调: Optional[Callable[[QWidget], None]] = None
    ) -> None:
        """
        注册页面类
        
        参数:
            页面名称: 页面的唯一标识名称
            页面类: 页面的类（继承自QWidget）
            创建参数: 创建页面时传递的参数字典
            创建回调: 页面创建后的回调函数
        """
        self._页面类映射[页面名称] = 页面类
        if 创建参数:
            self._页面参数映射[页面名称] = 创建参数
        if 创建回调:
            self._页面回调映射[页面名称] = 创建回调
    
    def 获取页面(self, 页面名称: str) -> Optional[QWidget]:
        """
        获取页面实例（按需创建）
        
        如果页面已缓存，直接返回缓存的实例
        如果页面未创建，则创建新实例并缓存
        
        参数:
            页面名称: 页面的唯一标识名称
        
        返回:
            页面实例，如果页面类未注册则返回None
        """
        # 如果已缓存，直接返回
        if 页面名称 in self._页面缓存:
            return self._页面缓存[页面名称]
        
        # 如果页面类已注册，创建新实例
        if 页面名称 in self._页面类映射:
            return self._创建页面(页面名称)
        
        return None
    
    def _创建页面(self, 页面名称: str) -> QWidget:
        """
        创建页面实例
        
        参数:
            页面名称: 页面的唯一标识名称
        
        返回:
            新创建的页面实例
        """
        开始时间 = time.time()
        
        页面类 = self._页面类映射[页面名称]
        参数 = self._页面参数映射.get(页面名称, {})
        
        # 创建页面实例
        页面实例 = 页面类(**参数)
        
        # 缓存页面
        self._页面缓存[页面名称] = 页面实例
        
        # 记录创建时间
        创建时间 = (time.time() - 开始时间) * 1000  # 转换为毫秒
        self._创建时间记录[页面名称] = 创建时间
        
        # 执行创建回调
        if 页面名称 in self._页面回调映射:
            self._页面回调映射[页面名称](页面实例)
        
        return 页面实例
    
    def 预加载页面(self, 页面名称: str) -> None:
        """
        预加载页面（在后台创建）
        
        参数:
            页面名称: 页面的唯一标识名称
        """
        if 页面名称 not in self._页面缓存 and 页面名称 in self._页面类映射:
            self._创建页面(页面名称)
    
    def 预加载所有页面(self) -> None:
        """预加载所有已注册的页面"""
        for 页面名称 in self._页面类映射:
            self.预加载页面(页面名称)
    
    def 销毁页面(self, 页面名称: str) -> None:
        """
        销毁页面实例（从缓存移除）
        
        参数:
            页面名称: 页面的唯一标识名称
        """
        if 页面名称 in self._页面缓存:
            页面 = self._页面缓存.pop(页面名称)
            页面.deleteLater()
            
            # 清除创建时间记录
            if 页面名称 in self._创建时间记录:
                del self._创建时间记录[页面名称]
    
    def 销毁所有页面(self) -> None:
        """销毁所有缓存的页面"""
        for 页面名称 in list(self._页面缓存.keys()):
            self.销毁页面(页面名称)
    
    def 重建页面(self, 页面名称: str) -> Optional[QWidget]:
        """
        重建页面（销毁后重新创建）
        
        参数:
            页面名称: 页面的唯一标识名称
        
        返回:
            新创建的页面实例
        """
        self.销毁页面(页面名称)
        return self.获取页面(页面名称)
    
    def 是否已缓存(self, 页面名称: str) -> bool:
        """
        检查页面是否已缓存
        
        参数:
            页面名称: 页面的唯一标识名称
        
        返回:
            是否已缓存
        """
        return 页面名称 in self._页面缓存
    
    def 是否已注册(self, 页面名称: str) -> bool:
        """
        检查页面类是否已注册
        
        参数:
            页面名称: 页面的唯一标识名称
        
        返回:
            是否已注册
        """
        return 页面名称 in self._页面类映射
    
    def 获取已缓存页面列表(self) -> list:
        """
        获取已缓存的页面名称列表
        
        返回:
            已缓存的页面名称列表
        """
        return list(self._页面缓存.keys())
    
    def 获取已注册页面列表(self) -> list:
        """
        获取已注册的页面名称列表
        
        返回:
            已注册的页面名称列表
        """
        return list(self._页面类映射.keys())
    
    def 获取页面创建时间(self, 页面名称: str) -> Optional[float]:
        """
        获取页面的创建时间（毫秒）
        
        参数:
            页面名称: 页面的唯一标识名称
        
        返回:
            创建时间（毫秒），如果未记录则返回None
        """
        return self._创建时间记录.get(页面名称)
    
    def 获取性能统计(self) -> Dict[str, Any]:
        """
        获取性能统计信息
        
        返回:
            包含性能统计的字典
        """
        总创建时间 = sum(self._创建时间记录.values())
        平均创建时间 = 总创建时间 / len(self._创建时间记录) if self._创建时间记录 else 0
        
        return {
            "已注册页面数": len(self._页面类映射),
            "已缓存页面数": len(self._页面缓存),
            "总创建时间_ms": 总创建时间,
            "平均创建时间_ms": 平均创建时间,
            "各页面创建时间": dict(self._创建时间记录)
        }



class 状态更新节流器(QObject):
    """
    状态更新节流器
    
    避免过于频繁的UI更新，通过节流机制控制更新频率:
    - 设置最小更新间隔（默认50ms）
    - 在间隔内的多次更新请求只执行最后一次
    - 支持立即更新和延迟更新
    
    性能目标:
    - 状态更新延迟: < 50ms
    """
    
    # 信号：当需要执行更新时发出
    更新触发 = Signal(dict)
    
    def __init__(self, 最小间隔ms: int = 50, parent: Optional[QObject] = None):
        """
        初始化状态更新节流器
        
        参数:
            最小间隔ms: 最小更新间隔（毫秒），默认50ms
            parent: 父对象
        """
        super().__init__(parent)
        
        self._最小间隔 = 最小间隔ms
        self._上次更新时间: float = 0
        self._待更新数据: Optional[Dict[str, Any]] = None
        self._更新回调: Optional[Callable[[Dict[str, Any]], None]] = None
        
        # 创建定时器用于延迟更新
        self._定时器 = QTimer(self)
        self._定时器.setSingleShot(True)
        self._定时器.timeout.connect(self._执行延迟更新)
    
    def 设置回调(self, 回调: Callable[[Dict[str, Any]], None]) -> None:
        """
        设置更新回调函数
        
        参数:
            回调: 执行更新时调用的函数，接收数据字典作为参数
        """
        self._更新回调 = 回调
    
    def 请求更新(self, 数据: Dict[str, Any]) -> None:
        """
        请求更新（自动节流）
        
        如果距离上次更新已超过最小间隔，立即执行更新
        否则，延迟到间隔结束后执行
        
        参数:
            数据: 要更新的数据字典
        """
        当前时间 = time.time() * 1000  # 转换为毫秒
        
        if 当前时间 - self._上次更新时间 >= self._最小间隔:
            # 立即更新
            self._执行更新(数据)
            self._上次更新时间 = 当前时间
        else:
            # 延迟更新
            self._待更新数据 = 数据
            if not self._定时器.isActive():
                剩余时间 = self._最小间隔 - (当前时间 - self._上次更新时间)
                self._定时器.start(int(max(1, 剩余时间)))
    
    def 强制更新(self, 数据: Dict[str, Any]) -> None:
        """
        强制立即更新（忽略节流）
        
        参数:
            数据: 要更新的数据字典
        """
        # 停止待处理的延迟更新
        if self._定时器.isActive():
            self._定时器.stop()
        self._待更新数据 = None
        
        # 立即执行更新
        self._执行更新(数据)
        self._上次更新时间 = time.time() * 1000
    
    def _执行更新(self, 数据: Dict[str, Any]) -> None:
        """
        执行更新
        
        参数:
            数据: 要更新的数据字典
        """
        # 发出信号
        self.更新触发.emit(数据)
        
        # 调用回调
        if self._更新回调:
            self._更新回调(数据)
    
    def _执行延迟更新(self) -> None:
        """执行延迟的更新"""
        if self._待更新数据 is not None:
            self._执行更新(self._待更新数据)
            self._上次更新时间 = time.time() * 1000
            self._待更新数据 = None
    
    def 取消待处理更新(self) -> None:
        """取消待处理的延迟更新"""
        if self._定时器.isActive():
            self._定时器.stop()
        self._待更新数据 = None
    
    def 设置最小间隔(self, 间隔ms: int) -> None:
        """
        设置最小更新间隔
        
        参数:
            间隔ms: 最小更新间隔（毫秒）
        """
        self._最小间隔 = max(1, 间隔ms)
    
    def 获取最小间隔(self) -> int:
        """
        获取最小更新间隔
        
        返回:
            最小更新间隔（毫秒）
        """
        return self._最小间隔
    
    def 是否有待处理更新(self) -> bool:
        """
        检查是否有待处理的更新
        
        返回:
            是否有待处理的更新
        """
        return self._定时器.isActive() or self._待更新数据 is not None


class 性能监控器(QObject):
    """
    UI性能监控器
    
    监控UI性能指标，包括:
    - 帧率统计
    - 页面切换时间
    - 状态更新延迟
    
    性能指标目标:
    - 首次加载时间: < 500ms
    - 页面切换时间: < 100ms
    - 状态更新延迟: < 50ms
    - 帧率: ≥ 30fps
    """
    
    # 信号：当性能警告时发出
    性能警告 = Signal(str, float)  # 警告类型, 当前值
    
    def __init__(self, parent: Optional[QObject] = None):
        """初始化性能监控器"""
        super().__init__(parent)
        
        # 帧率统计
        self._帧计数: int = 0
        self._上次统计时间: float = time.time()
        self._当前帧率: float = 0.0
        
        # 页面切换时间记录
        self._页面切换时间记录: Dict[str, float] = {}
        
        # 状态更新延迟记录
        self._更新延迟记录: list = []
        self._最大延迟记录数 = 100
        
        # 性能阈值
        self._帧率阈值 = 30.0
        self._页面切换阈值 = 100.0  # 毫秒
        self._更新延迟阈值 = 50.0  # 毫秒
    
    def 记录帧(self) -> None:
        """记录一帧渲染"""
        self._帧计数 += 1
        当前时间 = time.time()
        
        # 每秒统计一次帧率
        if 当前时间 - self._上次统计时间 >= 1.0:
            self._当前帧率 = self._帧计数 / (当前时间 - self._上次统计时间)
            
            # 检查帧率是否过低
            if self._当前帧率 < self._帧率阈值:
                self.性能警告.emit("帧率过低", self._当前帧率)
            
            self._帧计数 = 0
            self._上次统计时间 = 当前时间
    
    def 记录页面切换(self, 页面名称: str, 切换时间ms: float) -> None:
        """
        记录页面切换时间
        
        参数:
            页面名称: 切换到的页面名称
            切换时间ms: 切换耗时（毫秒）
        """
        self._页面切换时间记录[页面名称] = 切换时间ms
        
        # 检查是否超过阈值
        if 切换时间ms > self._页面切换阈值:
            self.性能警告.emit(f"页面切换过慢: {页面名称}", 切换时间ms)
    
    def 记录更新延迟(self, 延迟ms: float) -> None:
        """
        记录状态更新延迟
        
        参数:
            延迟ms: 更新延迟（毫秒）
        """
        self._更新延迟记录.append(延迟ms)
        
        # 限制记录数量
        if len(self._更新延迟记录) > self._最大延迟记录数:
            self._更新延迟记录.pop(0)
        
        # 检查是否超过阈值
        if 延迟ms > self._更新延迟阈值:
            self.性能警告.emit("更新延迟过高", 延迟ms)
    
    def 获取当前帧率(self) -> float:
        """
        获取当前帧率
        
        返回:
            当前帧率（FPS）
        """
        return self._当前帧率
    
    def 获取平均更新延迟(self) -> float:
        """
        获取平均更新延迟
        
        返回:
            平均更新延迟（毫秒）
        """
        if not self._更新延迟记录:
            return 0.0
        return sum(self._更新延迟记录) / len(self._更新延迟记录)
    
    def 获取性能报告(self) -> Dict[str, Any]:
        """
        获取性能报告
        
        返回:
            包含性能指标的字典
        """
        return {
            "当前帧率": self._当前帧率,
            "帧率达标": self._当前帧率 >= self._帧率阈值,
            "页面切换时间": dict(self._页面切换时间记录),
            "平均更新延迟_ms": self.获取平均更新延迟(),
            "更新延迟达标": self.获取平均更新延迟() <= self._更新延迟阈值,
        }
    
    def 重置统计(self) -> None:
        """重置所有统计数据"""
        self._帧计数 = 0
        self._上次统计时间 = time.time()
        self._当前帧率 = 0.0
        self._页面切换时间记录.clear()
        self._更新延迟记录.clear()


class 异步初始化管理器:
    """
    异步初始化管理器
    
    管理组件的异步初始化，实现:
    - 主窗口先显示基础框架
    - 使用QTimer.singleShot延迟初始化其他组件
    - 支持初始化优先级
    - 支持初始化进度回调
    """
    
    def __init__(self):
        """初始化异步初始化管理器"""
        # 初始化任务队列: (优先级, 任务名称, 任务函数)
        self._任务队列: list = []
        
        # 已完成的任务
        self._已完成任务: set = set()
        
        # 进度回调
        self._进度回调: Optional[Callable[[str, int, int], None]] = None
        
        # 完成回调
        self._完成回调: Optional[Callable[[], None]] = None
        
        # 当前任务索引
        self._当前索引: int = 0
        
        # 是否正在执行
        self._正在执行: bool = False
    
    def 添加任务(
        self, 
        任务名称: str, 
        任务函数: Callable[[], None],
        优先级: int = 0,
        延迟ms: int = 0
    ) -> None:
        """
        添加初始化任务
        
        参数:
            任务名称: 任务的唯一标识名称
            任务函数: 要执行的初始化函数
            优先级: 优先级（数字越小优先级越高）
            延迟ms: 执行前的延迟时间（毫秒）
        """
        self._任务队列.append((优先级, 延迟ms, 任务名称, 任务函数))
    
    def 设置进度回调(self, 回调: Callable[[str, int, int], None]) -> None:
        """
        设置进度回调函数
        
        参数:
            回调: 进度回调函数，参数为(任务名称, 当前索引, 总数)
        """
        self._进度回调 = 回调
    
    def 设置完成回调(self, 回调: Callable[[], None]) -> None:
        """
        设置完成回调函数
        
        参数:
            回调: 所有任务完成后调用的函数
        """
        self._完成回调 = 回调
    
    def 开始执行(self) -> None:
        """开始执行初始化任务"""
        if self._正在执行:
            return
        
        self._正在执行 = True
        self._当前索引 = 0
        
        # 按优先级排序
        self._任务队列.sort(key=lambda x: x[0])
        
        # 开始执行第一个任务
        self._执行下一个任务()
    
    def _执行下一个任务(self) -> None:
        """执行下一个任务"""
        if self._当前索引 >= len(self._任务队列):
            # 所有任务完成
            self._正在执行 = False
            if self._完成回调:
                self._完成回调()
            return
        
        优先级, 延迟ms, 任务名称, 任务函数 = self._任务队列[self._当前索引]
        
        # 报告进度
        if self._进度回调:
            self._进度回调(任务名称, self._当前索引 + 1, len(self._任务队列))
        
        # 使用QTimer延迟执行
        def 执行任务():
            try:
                任务函数()
                self._已完成任务.add(任务名称)
            except Exception as e:
                print(f"初始化任务 '{任务名称}' 执行失败: {e}")
            finally:
                self._当前索引 += 1
                # 继续执行下一个任务
                QTimer.singleShot(0, self._执行下一个任务)
        
        QTimer.singleShot(延迟ms, 执行任务)
    
    def 是否已完成(self, 任务名称: str) -> bool:
        """
        检查任务是否已完成
        
        参数:
            任务名称: 任务的唯一标识名称
        
        返回:
            是否已完成
        """
        return 任务名称 in self._已完成任务
    
    def 获取进度(self) -> tuple:
        """
        获取当前进度
        
        返回:
            (已完成数, 总数) 元组
        """
        return (len(self._已完成任务), len(self._任务队列))
    
    def 是否正在执行(self) -> bool:
        """
        检查是否正在执行
        
        返回:
            是否正在执行
        """
        return self._正在执行
    
    def 重置(self) -> None:
        """重置管理器状态"""
        self._任务队列.clear()
        self._已完成任务.clear()
        self._当前索引 = 0
        self._正在执行 = False
