# -*- coding: utf-8 -*-
"""
错误处理服务组件

实现统一的错误处理机制，包括:
- 后台线程错误捕获
- 错误日志记录
- 错误通知显示
- 全局异常处理
"""

import sys
import traceback
import logging
from datetime import datetime
from typing import Optional, Callable, List, Any
from dataclasses import dataclass, field
from pathlib import Path
from functools import wraps

from PySide6.QtCore import QObject, Signal, Slot, QThread


@dataclass
class 错误记录:
    """错误记录数据类"""
    时间戳: str
    错误类型: str
    错误消息: str
    堆栈跟踪: Optional[str] = None
    来源: str = "未知"
    严重级别: str = "错误"  # "警告", "错误", "严重"
    
    def 格式化(self) -> str:
        """格式化为显示字符串"""
        基本信息 = f"[{self.时间戳}] [{self.严重级别}] [{self.来源}] {self.错误类型}: {self.错误消息}"
        if self.堆栈跟踪:
            return f"{基本信息}\n堆栈跟踪:\n{self.堆栈跟踪}"
        return 基本信息
    
    def 简短格式(self) -> str:
        """格式化为简短显示字符串"""
        return f"[{self.时间戳}] {self.错误消息}"


class ErrorHandler(QObject):
    """
    错误处理服务
    
    提供统一的错误处理机制，包括:
    - 捕获和记录错误
    - 发送错误通知信号
    - 管理错误历史记录
    - 支持全局异常处理
    """
    
    # 信号定义
    错误发生 = Signal(str, str, str)  # 标题, 内容, 详情
    警告发生 = Signal(str, str)  # 标题, 内容
    日志记录 = Signal(str, str)  # 级别, 消息
    
    # 单例实例
    _实例: Optional['ErrorHandler'] = None
    
    def __new__(cls, *args, **kwargs):
        """单例模式"""
        if cls._实例 is None:
            cls._实例 = super().__new__(cls)
        return cls._实例
    
    def __init__(self, parent=None):
        """
        初始化错误处理服务
        
        参数:
            parent: 父对象
        """
        # 避免重复初始化
        if hasattr(self, '_已初始化') and self._已初始化:
            return
        
        super().__init__(parent)
        
        # 错误历史记录
        self._错误历史: List[错误记录] = []
        
        # 最大历史记录数
        self._最大历史数 = 100
        
        # 日志目录
        self._日志目录 = Path("日志")
        self._日志目录.mkdir(exist_ok=True)
        
        # 设置日志记录器
        self._设置日志记录器()
        
        # 标记已初始化
        self._已初始化 = True
    
    def _设置日志记录器(self) -> None:
        """设置Python日志记录器"""
        self._日志记录器 = logging.getLogger("MMORPG_AI_助手")
        self._日志记录器.setLevel(logging.DEBUG)
        
        # 如果已有处理器，不重复添加
        if self._日志记录器.handlers:
            return
        
        # 文件处理器
        日志文件 = self._日志目录 / f"错误日志_{datetime.now().strftime('%Y%m%d')}.log"
        文件处理器 = logging.FileHandler(日志文件, encoding='utf-8')
        文件处理器.setLevel(logging.DEBUG)
        
        # 格式化器
        格式化器 = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        文件处理器.setFormatter(格式化器)
        
        self._日志记录器.addHandler(文件处理器)
    
    @classmethod
    def 获取实例(cls) -> 'ErrorHandler':
        """
        获取错误处理服务单例实例
        
        返回:
            ErrorHandler实例
        """
        if cls._实例 is None:
            cls._实例 = cls()
        return cls._实例
    
    def 处理错误(
        self,
        错误: Exception,
        来源: str = "未知",
        严重级别: str = "错误",
        显示通知: bool = True
    ) -> 错误记录:
        """
        处理捕获的错误
        
        参数:
            错误: 异常对象
            来源: 错误来源描述
            严重级别: 严重级别 ("警告", "错误", "严重")
            显示通知: 是否显示通知
            
        返回:
            错误记录对象
        """
        # 获取堆栈跟踪
        堆栈跟踪 = traceback.format_exc()
        
        # 创建错误记录
        记录 = 错误记录(
            时间戳=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            错误类型=type(错误).__name__,
            错误消息=str(错误),
            堆栈跟踪=堆栈跟踪,
            来源=来源,
            严重级别=严重级别
        )
        
        # 添加到历史记录
        self._添加到历史(记录)
        
        # 写入日志文件
        self._写入日志(记录)
        
        # 发送信号
        if 显示通知:
            if 严重级别 == "警告":
                self.警告发生.emit(f"{来源}警告", str(错误))
            else:
                self.错误发生.emit(
                    f"{来源}错误",
                    str(错误),
                    堆栈跟踪
                )
        
        # 发送日志记录信号
        self.日志记录.emit(严重级别, 记录.简短格式())
        
        return 记录
    
    def 记录错误消息(
        self,
        消息: str,
        来源: str = "未知",
        严重级别: str = "错误",
        显示通知: bool = True
    ) -> 错误记录:
        """
        记录错误消息（非异常）
        
        参数:
            消息: 错误消息
            来源: 错误来源描述
            严重级别: 严重级别
            显示通知: 是否显示通知
            
        返回:
            错误记录对象
        """
        # 创建错误记录
        记录 = 错误记录(
            时间戳=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            错误类型="消息",
            错误消息=消息,
            堆栈跟踪=None,
            来源=来源,
            严重级别=严重级别
        )
        
        # 添加到历史记录
        self._添加到历史(记录)
        
        # 写入日志文件
        self._写入日志(记录)
        
        # 发送信号
        if 显示通知:
            if 严重级别 == "警告":
                self.警告发生.emit(f"{来源}警告", 消息)
            else:
                self.错误发生.emit(f"{来源}错误", 消息, "")
        
        # 发送日志记录信号
        self.日志记录.emit(严重级别, 记录.简短格式())
        
        return 记录
    
    def _添加到历史(self, 记录: 错误记录) -> None:
        """
        添加错误记录到历史
        
        参数:
            记录: 错误记录
        """
        self._错误历史.append(记录)
        
        # 限制历史记录数量
        if len(self._错误历史) > self._最大历史数:
            self._错误历史 = self._错误历史[-self._最大历史数:]
    
    def _写入日志(self, 记录: 错误记录) -> None:
        """
        写入错误到日志文件
        
        参数:
            记录: 错误记录
        """
        try:
            级别映射 = {
                "警告": logging.WARNING,
                "错误": logging.ERROR,
                "严重": logging.CRITICAL
            }
            级别 = 级别映射.get(记录.严重级别, logging.ERROR)
            
            日志消息 = f"[{记录.来源}] {记录.错误类型}: {记录.错误消息}"
            if 记录.堆栈跟踪:
                日志消息 += f"\n{记录.堆栈跟踪}"
            
            self._日志记录器.log(级别, 日志消息)
        except Exception:
            # 日志写入失败时静默处理
            pass
    
    def 获取错误历史(self) -> List[错误记录]:
        """
        获取错误历史记录
        
        返回:
            错误记录列表的副本
        """
        return self._错误历史.copy()
    
    def 清空历史(self) -> None:
        """清空错误历史记录"""
        self._错误历史.clear()
    
    def 获取最近错误(self, 数量: int = 10) -> List[错误记录]:
        """
        获取最近的错误记录
        
        参数:
            数量: 要获取的记录数量
            
        返回:
            最近的错误记录列表
        """
        return self._错误历史[-数量:] if self._错误历史 else []
    
    def 安装全局异常处理(self) -> None:
        """安装全局异常处理器"""
        sys.excepthook = self._全局异常处理器
    
    def _全局异常处理器(self, 异常类型, 异常值, 异常追踪) -> None:
        """
        全局异常处理器
        
        参数:
            异常类型: 异常类型
            异常值: 异常值
            异常追踪: 异常追踪对象
        """
        # 获取堆栈跟踪
        堆栈跟踪 = ''.join(traceback.format_exception(异常类型, 异常值, 异常追踪))
        
        # 创建错误记录
        记录 = 错误记录(
            时间戳=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            错误类型=异常类型.__name__,
            错误消息=str(异常值),
            堆栈跟踪=堆栈跟踪,
            来源="全局",
            严重级别="严重"
        )
        
        # 添加到历史记录
        self._添加到历史(记录)
        
        # 写入日志文件
        self._写入日志(记录)
        
        # 发送信号
        self.错误发生.emit("严重错误", str(异常值), 堆栈跟踪)


def 安全执行(来源: str = "未知", 显示通知: bool = True):
    """
    装饰器：安全执行函数，捕获并处理异常
    
    参数:
        来源: 错误来源描述
        显示通知: 是否显示通知
        
    用法:
        @安全执行("数据处理")
        def 处理数据():
            ...
    """
    def 装饰器(函数: Callable) -> Callable:
        @wraps(函数)
        def 包装器(*args, **kwargs) -> Any:
            try:
                return 函数(*args, **kwargs)
            except Exception as e:
                错误处理器 = ErrorHandler.获取实例()
                错误处理器.处理错误(e, 来源, "错误", 显示通知)
                return None
        return 包装器
    return 装饰器


class SafeThread(QThread):
    """
    安全线程基类
    
    提供统一的错误处理机制，子类只需重写 _执行任务 方法。
    """
    
    # 信号定义
    进度更新 = Signal(int, str)  # 进度百分比, 状态消息
    任务完成 = Signal(bool, str)  # 是否成功, 结果消息
    错误发生 = Signal(str, str)  # 错误消息, 堆栈跟踪
    
    def __init__(self, 任务名称: str = "后台任务", parent=None):
        """
        初始化安全线程
        
        参数:
            任务名称: 任务名称，用于错误报告
            parent: 父对象
        """
        super().__init__(parent)
        
        self._任务名称 = 任务名称
        self._停止标志 = False
        self._错误处理器 = ErrorHandler.获取实例()
    
    def run(self) -> None:
        """线程执行入口，包含错误处理"""
        try:
            self._执行任务()
        except Exception as e:
            # 获取堆栈跟踪
            堆栈跟踪 = traceback.format_exc()
            
            # 记录错误
            self._错误处理器.处理错误(
                e, 
                self._任务名称, 
                "错误", 
                显示通知=False  # 通过信号通知
            )
            
            # 发送错误信号
            self.错误发生.emit(str(e), 堆栈跟踪)
            self.任务完成.emit(False, f"{self._任务名称}失败: {str(e)}")
    
    def _执行任务(self) -> None:
        """
        执行任务的主逻辑，子类需要重写此方法
        
        子类实现时应该:
        1. 定期检查 self._停止标志
        2. 使用 self.进度更新.emit() 报告进度
        3. 完成时使用 self.任务完成.emit() 报告结果
        """
        raise NotImplementedError("子类必须实现 _执行任务 方法")
    
    def 请求停止(self) -> None:
        """请求停止线程"""
        self._停止标志 = True
    
    def 是否应该停止(self) -> bool:
        """检查是否应该停止"""
        return self._停止标志
    
    def 安全执行(self, 操作: Callable, 操作名称: str = "操作") -> Any:
        """
        安全执行操作，捕获异常
        
        参数:
            操作: 要执行的操作（可调用对象）
            操作名称: 操作名称，用于错误报告
            
        返回:
            操作的返回值，如果发生异常则返回None
        """
        try:
            return 操作()
        except Exception as e:
            self._错误处理器.处理错误(
                e,
                f"{self._任务名称}.{操作名称}",
                "警告",
                显示通知=False
            )
            return None


# 便捷函数
def 获取错误处理器() -> ErrorHandler:
    """
    获取错误处理服务实例
    
    返回:
        ErrorHandler单例实例
    """
    return ErrorHandler.获取实例()


def 记录错误(消息: str, 来源: str = "未知") -> None:
    """
    便捷函数：记录错误消息
    
    参数:
        消息: 错误消息
        来源: 错误来源
    """
    获取错误处理器().记录错误消息(消息, 来源)


def 记录警告(消息: str, 来源: str = "未知") -> None:
    """
    便捷函数：记录警告消息
    
    参数:
        消息: 警告消息
        来源: 警告来源
    """
    获取错误处理器().记录错误消息(消息, 来源, "警告")
