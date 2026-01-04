"""
智能缓存模块
实现检测结果的智能缓存，根据画面变化决定是否重新检测

功能:
- 封装检测器
- 缓存存储和查询
- 基于帧相似度的缓存决策
- 缓存过期机制
- 缓存统计

需求: 2.1, 2.2, 4.1, 4.2, 4.3, 4.4
"""

import time
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Any, TYPE_CHECKING
import numpy as np

from 核心.帧比较 import 帧比较器
from 核心.缓存策略 import 缓存策略, 获取默认缓存策略

if TYPE_CHECKING:
    from 核心.数据类型 import 检测结果

# 配置日志
logging.basicConfig(level=logging.INFO)
日志 = logging.getLogger(__name__)


@dataclass
class 缓存统计:
    """
    缓存性能统计
    
    跟踪缓存命中/未命中/过期统计，计算命中率
    
    需求: 2.4
    """
    总请求数: int = 0
    缓存命中数: int = 0
    缓存未命中数: int = 0
    过期失效数: int = 0
    区域失效数: int = 0
    相似度失效数: int = 0
    无缓存失效数: int = 0
    强制刷新数: int = 0
    
    @property
    def 命中率(self) -> float:
        """
        计算缓存命中率
        
        返回:
            命中率 (0.0-1.0)，如果没有请求则返回 0.0
        """
        if self.总请求数 == 0:
            return 0.0
        return self.缓存命中数 / self.总请求数
    
    @property
    def 未命中率(self) -> float:
        """
        计算缓存未命中率
        
        返回:
            未命中率 (0.0-1.0)，如果没有请求则返回 0.0
        """
        if self.总请求数 == 0:
            return 0.0
        return self.缓存未命中数 / self.总请求数
    
    @property
    def 过期失效率(self) -> float:
        """
        计算过期导致的失效率（相对于未命中数）
        
        返回:
            过期失效率 (0.0-1.0)
        """
        if self.缓存未命中数 == 0:
            return 0.0
        return self.过期失效数 / self.缓存未命中数
    
    @property
    def 区域失效率(self) -> float:
        """
        计算区域变化导致的失效率（相对于未命中数）
        
        返回:
            区域失效率 (0.0-1.0)
        """
        if self.缓存未命中数 == 0:
            return 0.0
        return self.区域失效数 / self.缓存未命中数
    
    @property
    def 相似度失效率(self) -> float:
        """
        计算相似度不足导致的失效率（相对于未命中数）
        
        返回:
            相似度失效率 (0.0-1.0)
        """
        if self.缓存未命中数 == 0:
            return 0.0
        return self.相似度失效数 / self.缓存未命中数
    
    def 记录命中(self) -> None:
        """记录一次缓存命中"""
        self.总请求数 += 1
        self.缓存命中数 += 1
    
    def 记录未命中(self, 原因: str = "") -> None:
        """
        记录一次缓存未命中
        
        参数:
            原因: 未命中原因 ("过期", "区域变化", "相似度不足", "无缓存")
        """
        self.总请求数 += 1
        self.缓存未命中数 += 1
        
        if "过期" in 原因:
            self.过期失效数 += 1
        elif "区域" in 原因:
            self.区域失效数 += 1
        elif "相似度" in 原因:
            self.相似度失效数 += 1
        elif "无缓存" in 原因:
            self.无缓存失效数 += 1
    
    def 记录强制刷新(self) -> None:
        """记录一次强制刷新"""
        self.强制刷新数 += 1
    
    def 重置(self) -> None:
        """重置所有统计"""
        self.总请求数 = 0
        self.缓存命中数 = 0
        self.缓存未命中数 = 0
        self.过期失效数 = 0
        self.区域失效数 = 0
        self.相似度失效数 = 0
        self.无缓存失效数 = 0
        self.强制刷新数 = 0
    
    def 获取摘要(self) -> str:
        """
        获取统计摘要字符串
        
        返回:
            格式化的统计摘要
        """
        return (
            f"缓存统计: 总请求={self.总请求数}, "
            f"命中={self.缓存命中数}({self.命中率:.1%}), "
            f"未命中={self.缓存未命中数}({self.未命中率:.1%}), "
            f"过期={self.过期失效数}, 区域={self.区域失效数}, "
            f"相似度={self.相似度失效数}, 强制刷新={self.强制刷新数}"
        )
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "总请求数": self.总请求数,
            "缓存命中数": self.缓存命中数,
            "缓存未命中数": self.缓存未命中数,
            "过期失效数": self.过期失效数,
            "区域失效数": self.区域失效数,
            "相似度失效数": self.相似度失效数,
            "无缓存失效数": self.无缓存失效数,
            "强制刷新数": self.强制刷新数,
            "命中率": self.命中率,
            "未命中率": self.未命中率,
            "过期失效率": self.过期失效率,
            "区域失效率": self.区域失效率,
            "相似度失效率": self.相似度失效率
        }
    
    @classmethod
    def from_dict(cls, 数据: dict) -> '缓存统计':
        """
        从字典创建缓存统计实例
        
        参数:
            数据: 统计数据字典
            
        返回:
            缓存统计实例
        """
        return cls(
            总请求数=数据.get("总请求数", 0),
            缓存命中数=数据.get("缓存命中数", 0),
            缓存未命中数=数据.get("缓存未命中数", 0),
            过期失效数=数据.get("过期失效数", 0),
            区域失效数=数据.get("区域失效数", 0),
            相似度失效数=数据.get("相似度失效数", 0),
            无缓存失效数=数据.get("无缓存失效数", 0),
            强制刷新数=数据.get("强制刷新数", 0)
        )


@dataclass
class 缓存条目:
    """
    缓存条目
    
    存储检测结果及相关元数据
    """
    结果: List['检测结果']  # 检测结果列表
    时间戳: float  # 缓存创建时间
    参考帧: np.ndarray  # 用于比较的参考帧
    
    @property
    def 年龄(self) -> float:
        """
        获取缓存年龄（秒）
        
        返回:
            缓存已存在的时间
        """
        return time.time() - self.时间戳


class 智能缓存:
    """
    智能检测结果缓存
    
    根据画面变化程度决定是否重新执行检测，减少不必要的计算开销
    
    需求: 2.1, 2.2, 4.1, 4.2, 4.3, 4.4
    """
    
    def __init__(self, 
                 检测器: Any = None,
                 策略: 缓存策略 = None,
                 相似度阈值: float = None,
                 过期时间: float = None):
        """
        初始化智能缓存
        
        参数:
            检测器: 检测器实例（可选，用于封装检测器）
            策略: 缓存策略实例，如果为 None 则使用默认策略
            相似度阈值: 使用缓存的相似度阈值（覆盖策略设置）
            过期时间: 缓存过期时间（秒）（覆盖策略设置）
            
        需求: 2.1, 2.2
        """
        self._检测器 = 检测器
        
        # 初始化策略
        if 策略 is not None:
            self._策略 = 策略
        else:
            self._策略 = 获取默认缓存策略()
        
        # 覆盖策略参数（如果提供）
        if 相似度阈值 is not None:
            self._策略.全局阈值 = 相似度阈值
        if 过期时间 is not None:
            self._策略.过期时间 = 过期时间
        
        # 初始化帧比较器
        self._帧比较器 = 帧比较器(方法=self._策略.比较方法)
        
        # 缓存存储
        self._缓存条目: Optional[缓存条目] = None
        
        # 统计信息
        self._统计 = 缓存统计()
        
        # 预热状态
        self._预热完成 = False
        
        日志.info(f"智能缓存初始化完成: 阈值={self._策略.全局阈值}, "
                  f"过期时间={self._策略.过期时间}s, "
                  f"比较方法={self._策略.比较方法}")
    
    @property
    def 策略(self) -> 缓存策略:
        """获取当前缓存策略"""
        return self._策略
    
    @策略.setter
    def 策略(self, 新策略: 缓存策略) -> None:
        """设置新的缓存策略"""
        self._策略 = 新策略
        self._帧比较器 = 帧比较器(方法=新策略.比较方法)
        日志.info(f"缓存策略已更新: 阈值={新策略.全局阈值}, 过期时间={新策略.过期时间}s")
    
    def 获取(self, 图像: np.ndarray) -> Optional[List['检测结果']]:
        """
        尝试从缓存获取检测结果
        
        参数:
            图像: 当前帧图像
            
        返回:
            如果缓存有效则返回缓存的检测结果，否则返回 None
            
        需求: 2.1, 2.2
        """
        # 检查是否有缓存
        if self._缓存条目 is None:
            self._统计.记录未命中("无缓存")
            日志.debug("缓存未命中: 无缓存")
            return None
        
        # 计算缓存年龄
        缓存年龄 = self._缓存条目.年龄
        
        # 计算全局相似度
        全局相似度 = self._帧比较器.比较(图像, self._缓存条目.参考帧)
        
        # 计算优先区域相似度
        区域相似度列表 = self._计算区域相似度(图像, self._缓存条目.参考帧)
        
        # 使用策略判断是否应该使用缓存
        if self._策略.应该使用缓存(全局相似度, 区域相似度列表, 缓存年龄):
            self._统计.记录命中()
            日志.debug(f"缓存命中: 相似度={全局相似度:.3f}, 年龄={缓存年龄:.3f}s")
            return self._缓存条目.结果
        
        # 获取失效原因并记录
        失效原因 = self._策略.获取失效原因(全局相似度, 区域相似度列表, 缓存年龄)
        self._统计.记录未命中(失效原因)
        日志.debug(f"缓存未命中: {失效原因}")
        
        return None
    
    def _计算区域相似度(self, 图像: np.ndarray, 参考帧: np.ndarray) -> List[float]:
        """
        计算所有优先区域的相似度
        
        参数:
            图像: 当前帧
            参考帧: 参考帧
            
        返回:
            各优先区域的相似度列表
        """
        if not self._策略.优先区域列表:
            return []
        
        if 图像 is None or 参考帧 is None:
            return [0.0] * len(self._策略.优先区域列表)
        
        # 获取图像尺寸
        高度, 宽度 = 图像.shape[:2]
        
        # 获取像素坐标区域列表
        像素区域列表 = self._策略.获取像素区域列表(宽度, 高度)
        
        # 计算各区域相似度
        return self._帧比较器.比较多区域(图像, 参考帧, 像素区域列表)
    
    def 存储(self, 图像: np.ndarray, 结果: List['检测结果']) -> None:
        """
        存储检测结果到缓存
        
        参数:
            图像: 当前帧图像（作为参考帧）
            结果: 检测结果列表
        """
        self._缓存条目 = 缓存条目(
            结果=结果,
            时间戳=time.time(),
            参考帧=图像.copy() if 图像 is not None else None
        )
        日志.debug(f"缓存已更新: {len(结果)} 个检测结果")
    
    def 检测(self, 图像: np.ndarray) -> List['检测结果']:
        """
        智能检测（自动决定是否使用缓存）
        
        如果缓存有效则返回缓存结果，否则执行新检测
        
        参数:
            图像: 输入图像
            
        返回:
            检测结果列表
            
        需求: 2.1, 2.2
        """
        if self._检测器 is None:
            日志.warning("未设置检测器，无法执行检测")
            return []
        
        # 尝试从缓存获取
        缓存结果 = self.获取(图像)
        if 缓存结果 is not None:
            return 缓存结果
        
        # 执行新检测
        return self.强制刷新(图像)
    
    def 强制刷新(self, 图像: np.ndarray) -> List['检测结果']:
        """
        强制执行新检测（忽略缓存）
        
        参数:
            图像: 输入图像
            
        返回:
            检测结果列表
        """
        if self._检测器 is None:
            日志.warning("未设置检测器，无法执行检测")
            return []
        
        # 记录强制刷新
        self._统计.记录强制刷新()
        
        try:
            # 执行检测（禁用检测器内部缓存以避免循环）
            if hasattr(self._检测器, '检测'):
                结果 = self._检测器.检测(图像, 使用缓存=False)
            else:
                结果 = self._检测器(图像)
            
            # 存储到缓存
            self.存储(图像, 结果)
            
            return 结果
            
        except Exception as e:
            日志.error(f"检测执行失败: {e}")
            # 如果有缓存，返回缓存结果
            if self._缓存条目 is not None:
                return self._缓存条目.结果
            return []
    
    def 清空(self) -> None:
        """清空缓存"""
        self._缓存条目 = None
        日志.debug("缓存已清空")
    
    def 是否有缓存(self) -> bool:
        """检查是否有缓存"""
        return self._缓存条目 is not None
    
    def 是否过期(self) -> bool:
        """
        检查缓存是否已过期
        
        返回:
            如果缓存已过期或不存在则返回 True
            
        需求: 4.1, 4.2
        """
        if self._缓存条目 is None:
            return True
        
        if not self._策略.启用时间过期:
            return False
        
        已过期 = self._缓存条目.年龄 > self._策略.过期时间
        
        # 记录过期事件（需求 4.4）
        if 已过期:
            日志.debug(f"缓存过期: 年龄={self._缓存条目.年龄:.3f}s > 过期时间={self._策略.过期时间}s")
        
        return 已过期
    
    def 获取缓存年龄(self) -> float:
        """
        获取当前缓存的年龄
        
        返回:
            缓存年龄（秒），如果无缓存则返回 -1
        """
        if self._缓存条目 is None:
            return -1.0
        return self._缓存条目.年龄
    
    def 获取统计(self) -> dict:
        """
        获取缓存统计信息
        
        返回:
            统计信息字典
            
        需求: 2.4
        """
        统计字典 = self._统计.to_dict()
        统计字典["有缓存"] = self.是否有缓存()
        统计字典["缓存年龄"] = self.获取缓存年龄()
        统计字典["是否过期"] = self.是否过期()
        统计字典["预热完成"] = self._预热完成
        return 统计字典
    
    def 重置统计(self) -> None:
        """重置统计信息"""
        self._统计.重置()
        日志.debug("统计信息已重置")
    
    def 设置检测器(self, 检测器: Any) -> None:
        """
        设置检测器
        
        参数:
            检测器: 检测器实例
        """
        self._检测器 = 检测器
        日志.info("检测器已设置")
    
    def 设置相似度阈值(self, 阈值: float) -> None:
        """
        设置相似度阈值
        
        参数:
            阈值: 新的相似度阈值 (0.0-1.0)
        """
        if 0.0 <= 阈值 <= 1.0:
            self._策略.全局阈值 = 阈值
            日志.info(f"相似度阈值已更新: {阈值}")
        else:
            日志.warning(f"无效的阈值: {阈值}，必须在 0.0-1.0 范围内")
    
    def 设置过期时间(self, 过期时间: float) -> None:
        """
        设置缓存过期时间
        
        参数:
            过期时间: 新的过期时间（秒）
            
        需求: 4.1, 4.3
        """
        if 过期时间 >= 0:
            self._策略.过期时间 = 过期时间
            日志.info(f"过期时间已更新: {过期时间}s")
        else:
            日志.warning(f"无效的过期时间: {过期时间}，必须 >= 0")
    
    def 启用时间过期(self, 启用: bool = True) -> None:
        """
        启用或禁用基于时间的过期
        
        参数:
            启用: 是否启用时间过期
            
        需求: 4.3
        """
        self._策略.启用时间过期 = 启用
        日志.info(f"时间过期已{'启用' if 启用 else '禁用'}")
    
    def 禁用时间过期(self) -> None:
        """
        禁用基于时间的过期
        
        需求: 4.3
        """
        self.启用时间过期(False)
    
    def 检查并处理过期(self) -> bool:
        """
        检查缓存是否过期，如果过期则清空缓存
        
        返回:
            如果缓存已过期并被清空则返回 True
            
        需求: 4.1, 4.2, 4.4
        """
        if self._缓存条目 is None:
            return False
        
        if not self._策略.启用时间过期:
            return False
        
        缓存年龄 = self._缓存条目.年龄
        
        if 缓存年龄 > self._策略.过期时间:
            # 记录过期事件（需求 4.4）
            日志.info(f"缓存过期事件: 年龄={缓存年龄:.3f}s, 过期时间={self._策略.过期时间}s")
            self.清空()
            return True
        
        return False
    
    def 获取过期信息(self) -> dict:
        """
        获取缓存过期相关信息
        
        返回:
            包含过期状态的字典
            
        需求: 4.4
        """
        if self._缓存条目 is None:
            return {
                "有缓存": False,
                "启用时间过期": self._策略.启用时间过期,
                "过期时间设置": self._策略.过期时间
            }
        
        缓存年龄 = self._缓存条目.年龄
        剩余时间 = max(0, self._策略.过期时间 - 缓存年龄)
        
        return {
            "有缓存": True,
            "启用时间过期": self._策略.启用时间过期,
            "过期时间设置": self._策略.过期时间,
            "缓存年龄": 缓存年龄,
            "剩余时间": 剩余时间 if self._策略.启用时间过期 else None,
            "是否过期": self.是否过期()
        }
    
    # ==================== 预热功能 ====================
    # 需求: 5.1, 5.2, 5.3
    
    @property
    def 预热完成(self) -> bool:
        """
        检查预热是否完成
        
        返回:
            预热是否已完成
            
        需求: 5.2
        """
        return self._预热完成
    
    @property
    def 正在预热(self) -> bool:
        """
        检查是否正在预热中
        
        返回:
            是否正在预热（检测器已设置但预热未完成）
            
        需求: 5.2
        """
        return self._检测器 is not None and not self._预热完成
    
    def 预热(self, 图像: np.ndarray) -> bool:
        """
        执行缓存预热
        
        启动时执行初始检测以填充缓存
        
        参数:
            图像: 用于预热的初始图像
            
        返回:
            预热是否成功
            
        需求: 5.1, 5.2
        """
        if self._检测器 is None:
            日志.warning("未设置检测器，无法执行预热")
            return False
        
        if self._预热完成:
            日志.debug("预热已完成，跳过")
            return True
        
        日志.info("开始缓存预热...")
        
        try:
            # 执行初始检测
            if hasattr(self._检测器, '检测'):
                结果 = self._检测器.检测(图像, 使用缓存=False)
            else:
                结果 = self._检测器(图像)
            
            # 存储到缓存
            self.存储(图像, 结果)
            
            # 标记预热完成
            self._预热完成 = True
            
            日志.info(f"缓存预热完成: {len(结果)} 个检测结果")
            return True
            
        except Exception as e:
            日志.error(f"缓存预热失败: {e}")
            return False
    
    def 异步预热(self, 图像: np.ndarray, 回调: callable = None) -> None:
        """
        异步执行缓存预热（非阻塞）
        
        在后台线程中执行预热，不阻塞主线程
        
        参数:
            图像: 用于预热的初始图像
            回调: 预热完成后的回调函数，接收布尔参数表示是否成功
            
        需求: 5.1, 5.3
        """
        import threading
        
        def _预热任务():
            成功 = self.预热(图像)
            if 回调 is not None:
                try:
                    回调(成功)
                except Exception as e:
                    日志.error(f"预热回调执行失败: {e}")
        
        线程 = threading.Thread(target=_预热任务, daemon=True)
        线程.start()
        日志.debug("异步预热任务已启动")
    
    def 检测_带预热(self, 图像: np.ndarray) -> List['检测结果']:
        """
        智能检测（带预热支持）
        
        如果预热未完成，返回空结果而非阻塞
        如果预热已完成，正常执行智能检测
        
        参数:
            图像: 输入图像
            
        返回:
            检测结果列表，预热中返回空列表
            
        需求: 5.3
        """
        # 如果正在预热，返回空结果
        if self.正在预热:
            日志.debug("正在预热中，返回空结果")
            return []
        
        # 如果预热未开始且有检测器，自动开始预热
        if not self._预热完成 and self._检测器 is not None:
            self.异步预热(图像)
            return []
        
        # 正常执行检测
        return self.检测(图像)
    
    def 重置预热状态(self) -> None:
        """
        重置预热状态
        
        用于重新启动预热流程
        """
        self._预热完成 = False
        日志.debug("预热状态已重置")
    
    def 获取预热状态(self) -> dict:
        """
        获取预热状态信息
        
        返回:
            预热状态字典
            
        需求: 5.2
        """
        return {
            "预热完成": self._预热完成,
            "正在预热": self.正在预热,
            "有检测器": self._检测器 is not None,
            "有缓存": self.是否有缓存()
        }


# 为了兼容目标检测器中的导入，提供别名
智能检测缓存 = 智能缓存
