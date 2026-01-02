"""
模块管理器
负责管理智能训练系统的三个核心模块，实现错误降级机制。

需求: 10.4 - WHEN 任一新模块出错 THEN 系统 SHALL 降级到基础功能继续运行
"""

import logging
from typing import Optional, Dict, Any, Callable
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

# 配置日志
logger = logging.getLogger(__name__)


class 模块状态(Enum):
    """模块运行状态"""
    正常 = "normal"
    降级 = "degraded"
    禁用 = "disabled"
    错误 = "error"


@dataclass
class 模块信息:
    """模块信息数据类"""
    名称: str
    状态: 模块状态 = 模块状态.禁用
    实例: Any = None
    错误信息: str = ""
    错误次数: int = 0
    最后错误时间: Optional[datetime] = None
    降级原因: str = ""


class 模块管理器:
    """模块管理器
    
    负责管理智能录制、配置管理、自动调参三个模块的生命周期，
    实现错误检测和自动降级机制。
    
    降级策略:
    - 单个模块出错时，该模块降级到基础功能
    - 连续错误超过阈值时，禁用该模块
    - 其他模块继续正常运行
    - 提供手动恢复接口
    """
    
    # 错误阈值配置
    MAX_ERROR_COUNT = 5  # 最大连续错误次数
    ERROR_RESET_INTERVAL = 300.0  # 错误计数重置间隔（秒）
    
    def __init__(self):
        """初始化模块管理器"""
        self._modules: Dict[str, 模块信息] = {
            "智能录制": 模块信息(名称="智能录制"),
            "配置管理": 模块信息(名称="配置管理"),
            "自动调参": 模块信息(名称="自动调参"),
        }
        
        # 初始化各模块
        self._初始化智能录制模块()
        self._初始化配置管理模块()
        self._初始化自动调参模块()
        
        logger.info("模块管理器初始化完成")

    def _初始化智能录制模块(self) -> None:
        """初始化智能录制模块"""
        try:
            from 核心.智能录制 import (
                ValueEvaluator, DataFilter, StatisticsService
            )
            
            # 创建模块实例
            实例 = {
                "value_evaluator": ValueEvaluator(),
                "data_filter": DataFilter(),
                "statistics_service": StatisticsService()
            }
            
            self._modules["智能录制"].实例 = 实例
            self._modules["智能录制"].状态 = 模块状态.正常
            logger.info("智能录制模块初始化成功")
            
        except ImportError as e:
            self._modules["智能录制"].状态 = 模块状态.禁用
            self._modules["智能录制"].错误信息 = f"导入失败: {e}"
            logger.warning(f"智能录制模块不可用: {e}")
        except Exception as e:
            self._处理模块错误("智能录制", e)
    
    def _初始化配置管理模块(self) -> None:
        """初始化配置管理模块"""
        try:
            from 核心.配置管理 import ConfigManager
            
            实例 = ConfigManager(auto_load_last=True)
            
            self._modules["配置管理"].实例 = 实例
            self._modules["配置管理"].状态 = 模块状态.正常
            logger.info("配置管理模块初始化成功")
            
        except ImportError as e:
            self._modules["配置管理"].状态 = 模块状态.禁用
            self._modules["配置管理"].错误信息 = f"导入失败: {e}"
            logger.warning(f"配置管理模块不可用: {e}")
        except Exception as e:
            self._处理模块错误("配置管理", e)
    
    def _初始化自动调参模块(self) -> None:
        """初始化自动调参模块"""
        try:
            from 核心.自动调参 import AutoTuner, AggressivenessLevel
            
            实例 = AutoTuner(enabled=False, aggressiveness=AggressivenessLevel.BALANCED)
            
            self._modules["自动调参"].实例 = 实例
            self._modules["自动调参"].状态 = 模块状态.正常
            logger.info("自动调参模块初始化成功")
            
        except ImportError as e:
            self._modules["自动调参"].状态 = 模块状态.禁用
            self._modules["自动调参"].错误信息 = f"导入失败: {e}"
            logger.warning(f"自动调参模块不可用: {e}")
        except Exception as e:
            self._处理模块错误("自动调参", e)
    
    def _处理模块错误(self, 模块名: str, 错误: Exception) -> None:
        """处理模块错误，实现降级逻辑
        
        Args:
            模块名: 出错的模块名称
            错误: 异常对象
        """
        module = self._modules.get(模块名)
        if not module:
            return
        
        当前时间 = datetime.now()
        
        # 检查是否需要重置错误计数
        if module.最后错误时间:
            时间差 = (当前时间 - module.最后错误时间).total_seconds()
            if 时间差 > self.ERROR_RESET_INTERVAL:
                module.错误次数 = 0
        
        # 更新错误信息
        module.错误次数 += 1
        module.最后错误时间 = 当前时间
        module.错误信息 = str(错误)
        
        # 根据错误次数决定状态
        if module.错误次数 >= self.MAX_ERROR_COUNT:
            module.状态 = 模块状态.禁用
            module.降级原因 = f"连续错误{module.错误次数}次，已禁用"
            logger.error(f"模块 {模块名} 已禁用: 连续错误{module.错误次数}次")
        else:
            module.状态 = 模块状态.降级
            module.降级原因 = f"发生错误，已降级运行"
            logger.warning(f"模块 {模块名} 已降级: {错误}")

    def 安全执行(self, 模块名: str, 操作: Callable, *args, **kwargs) -> Any:
        """安全执行模块操作，自动处理错误和降级
        
        Args:
            模块名: 模块名称
            操作: 要执行的操作（函数）
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            操作结果，如果出错则返回None
        """
        module = self._modules.get(模块名)
        if not module:
            logger.warning(f"未知模块: {模块名}")
            return None
        
        # 检查模块状态
        if module.状态 == 模块状态.禁用:
            logger.debug(f"模块 {模块名} 已禁用，跳过操作")
            return None
        
        try:
            result = 操作(*args, **kwargs)
            
            # 操作成功，如果之前是降级状态，尝试恢复
            if module.状态 == 模块状态.降级:
                module.错误次数 = max(0, module.错误次数 - 1)
                if module.错误次数 == 0:
                    module.状态 = 模块状态.正常
                    module.降级原因 = ""
                    logger.info(f"模块 {模块名} 已恢复正常")
            
            return result
            
        except Exception as e:
            self._处理模块错误(模块名, e)
            return None
    
    def 获取模块状态(self, 模块名: str) -> Dict[str, Any]:
        """获取指定模块的状态信息
        
        Args:
            模块名: 模块名称
            
        Returns:
            状态信息字典
        """
        module = self._modules.get(模块名)
        if not module:
            return {"存在": False}
        
        return {
            "存在": True,
            "名称": module.名称,
            "状态": module.状态.value,
            "可用": module.状态 in (模块状态.正常, 模块状态.降级),
            "错误信息": module.错误信息,
            "错误次数": module.错误次数,
            "降级原因": module.降级原因
        }
    
    def 获取所有模块状态(self) -> Dict[str, Dict[str, Any]]:
        """获取所有模块的状态信息
        
        Returns:
            所有模块的状态信息字典
        """
        return {名称: self.获取模块状态(名称) for 名称 in self._modules}
    
    def 模块可用(self, 模块名: str) -> bool:
        """检查模块是否可用
        
        Args:
            模块名: 模块名称
            
        Returns:
            模块是否可用
        """
        module = self._modules.get(模块名)
        if not module:
            return False
        return module.状态 in (模块状态.正常, 模块状态.降级)
    
    def 获取模块实例(self, 模块名: str) -> Any:
        """获取模块实例
        
        Args:
            模块名: 模块名称
            
        Returns:
            模块实例，如果不可用则返回None
        """
        module = self._modules.get(模块名)
        if not module or not self.模块可用(模块名):
            return None
        return module.实例

    def 尝试恢复模块(self, 模块名: str) -> bool:
        """尝试恢复被禁用的模块
        
        Args:
            模块名: 模块名称
            
        Returns:
            恢复是否成功
        """
        module = self._modules.get(模块名)
        if not module:
            return False
        
        # 重置错误计数
        module.错误次数 = 0
        module.错误信息 = ""
        module.降级原因 = ""
        
        # 重新初始化模块
        if 模块名 == "智能录制":
            self._初始化智能录制模块()
        elif 模块名 == "配置管理":
            self._初始化配置管理模块()
        elif 模块名 == "自动调参":
            self._初始化自动调参模块()
        
        return self.模块可用(模块名)
    
    def 禁用模块(self, 模块名: str) -> None:
        """手动禁用模块
        
        Args:
            模块名: 模块名称
        """
        module = self._modules.get(模块名)
        if module:
            module.状态 = 模块状态.禁用
            module.降级原因 = "手动禁用"
            logger.info(f"模块 {模块名} 已手动禁用")
    
    def 启用模块(self, 模块名: str) -> bool:
        """手动启用模块
        
        Args:
            模块名: 模块名称
            
        Returns:
            启用是否成功
        """
        return self.尝试恢复模块(模块名)
    
    # ==================== 便捷访问方法 ====================
    
    @property
    def 智能录制(self) -> Any:
        """获取智能录制模块实例"""
        return self.获取模块实例("智能录制")
    
    @property
    def 配置管理(self) -> Any:
        """获取配置管理模块实例"""
        return self.获取模块实例("配置管理")
    
    @property
    def 自动调参(self) -> Any:
        """获取自动调参模块实例"""
        return self.获取模块实例("自动调参")
    
    @property
    def 智能录制可用(self) -> bool:
        """智能录制模块是否可用"""
        return self.模块可用("智能录制")
    
    @property
    def 配置管理可用(self) -> bool:
        """配置管理模块是否可用"""
        return self.模块可用("配置管理")
    
    @property
    def 自动调参可用(self) -> bool:
        """自动调参模块是否可用"""
        return self.模块可用("自动调参")


# ==================== 全局模块管理器实例 ====================
_global_manager: Optional[模块管理器] = None


def 获取模块管理器() -> 模块管理器:
    """获取全局模块管理器实例
    
    Returns:
        模块管理器实例
    """
    global _global_manager
    if _global_manager is None:
        _global_manager = 模块管理器()
    return _global_manager


def 重置模块管理器() -> None:
    """重置全局模块管理器"""
    global _global_manager
    _global_manager = None
