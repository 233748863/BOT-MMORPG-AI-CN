"""
屏幕截取模块
用于捕获游戏画面

集成屏幕截取优化和自动窗口检测功能。
支持窗口跟踪，自动更新截取区域。

需求: 3.2 - 窗口移动时自动更新截取区域
需求: 4.1 - 窗口标识配置
需求: 5.1 - 提供与当前 截取屏幕 函数相同的 API
需求: 5.4 - 是当前实现的直接替代品
需求: 2.4 - 记录正在使用的截取后端
"""

import cv2
import numpy as np
import win32gui
import win32ui
import win32con
import win32api
import logging
from typing import Optional, Tuple, Callable, Dict, Any

# 尝试导入屏幕截取优化模块
try:
    from 核心.屏幕截取优化 import (
        屏幕截取器 as 优化屏幕截取器,
        后端检测器,
        截取统计,
        系统图形信息
    )
    屏幕截取优化可用 = True
except ImportError:
    屏幕截取优化可用 = False
    优化屏幕截取器 = None
    后端检测器 = None

# 尝试导入窗口检测模块
try:
    from 核心.窗口检测 import 自动窗口检测器, 窗口查找器, 窗口跟踪器, 窗口变化事件, 窗口信息
    窗口检测可用 = True
except ImportError:
    窗口检测可用 = False

# 配置日志
logger = logging.getLogger(__name__)

# 全局优化截取器实例
_优化截取器实例: Optional['优化屏幕截取器'] = None
_窗口检测器实例: Optional['自动窗口检测器'] = None
_当前截取区域: Optional[Tuple[int, int, int, int]] = None
_已初始化 = False

# 截取配置 - 需求 2.4
_截取配置: Dict[str, Any] = {
    "首选后端": "auto",  # "auto", "dxgi", "mss", "gdi", "pil"
    "启用回退": True,     # 是否启用自动回退机制
    "启用性能监控": True, # 是否启用性能监控
    "显示器索引": 0,      # 要截取的显示器索引
}


def _获取配置设置():
    """
    从配置文件获取窗口检测设置
    
    返回:
        dict: 窗口检测配置，如果导入失败则返回默认值
    """
    try:
        from 配置.设置 import (
            启用自动窗口检测, 窗口标识类型, 窗口标识值,
            启用窗口跟踪, 窗口配置路径, 更新窗口区域
        )
        return {
            "启用自动检测": 启用自动窗口检测,
            "标识类型": 窗口标识类型,
            "标识值": 窗口标识值,
            "启用跟踪": 启用窗口跟踪,
            "配置路径": 窗口配置路径,
            "更新区域回调": 更新窗口区域
        }
    except ImportError as e:
        logger.warning(f"无法导入配置设置，使用默认值: {e}")
        return {
            "启用自动检测": False,
            "标识类型": "process",
            "标识值": "",
            "启用跟踪": False,
            "配置路径": "配置/窗口配置.json",
            "更新区域回调": None
        }


def _加载截取配置():
    """
    从配置文件加载截取配置
    
    需求: 2.4 - 记录正在使用的截取后端
    """
    global _截取配置
    
    try:
        from 配置.设置 import (
            首选截取后端, 启用截取回退, 启用截取性能监控, 截取显示器索引
        )
        _截取配置 = {
            "首选后端": 首选截取后端,
            "启用回退": 启用截取回退,
            "启用性能监控": 启用截取性能监控,
            "显示器索引": 截取显示器索引
        }
        logger.debug(f"截取配置已加载: {_截取配置}")
    except ImportError as e:
        logger.warning(f"无法导入截取配置，使用默认值: {e}")


# 模块加载时自动加载截取配置
_加载截取配置()


def _获取窗口检测器() -> Optional['自动窗口检测器']:
    """获取或创建窗口检测器实例"""
    global _窗口检测器实例
    
    if not 窗口检测可用:
        return None
    
    if _窗口检测器实例 is None:
        配置 = _获取配置设置()
        配置路径 = 配置.get("配置路径", "配置/窗口配置.json")
        _窗口检测器实例 = 自动窗口检测器(配置路径)
    
    return _窗口检测器实例


def _区域更新回调(新区域: Tuple[int, int, int, int]):
    """
    窗口位置变化时的回调，自动更新截取区域
    
    需求: 3.2 - 窗口移动时自动更新截取区域
    """
    global _当前截取区域
    _当前截取区域 = 新区域
    logger.info(f"截取区域已自动更新: {新区域}")
    
    # 同步更新配置文件中的窗口区域
    配置 = _获取配置设置()
    更新回调 = 配置.get("更新区域回调")
    if 更新回调:
        try:
            更新回调(新区域)
        except Exception as e:
            logger.warning(f"更新配置区域失败: {e}")


def 初始化窗口检测():
    """
    根据配置文件初始化窗口检测
    
    如果配置中启用了自动窗口检测，会自动检测游戏窗口。
    如果配置中启用了窗口跟踪，会自动启动跟踪。
    
    需求: 4.1 - 窗口标识配置
    需求: 3.2 - 窗口移动时自动更新截取区域
    
    返回:
        bool: 是否成功初始化
    """
    global _已初始化, _当前截取区域
    
    if _已初始化:
        return True
    
    if not 窗口检测可用:
        logger.info("窗口检测模块不可用，跳过初始化")
        return False
    
    配置 = _获取配置设置()
    
    if not 配置.get("启用自动检测", False):
        logger.info("自动窗口检测未启用")
        _已初始化 = True
        return True
    
    检测器 = _获取窗口检测器()
    if 检测器 is None:
        return False
    
    try:
        # 根据配置的标识类型和值进行检测
        标识类型 = 配置.get("标识类型", "process")
        标识值 = 配置.get("标识值", "")
        
        窗口 = None
        if 标识值:
            if 标识类型 == "process":
                窗口 = 检测器.自动检测(进程名=标识值)
            else:
                窗口 = 检测器.自动检测(标题=标识值)
        else:
            # 尝试从保存的配置加载
            窗口 = 检测器.自动检测()
        
        if 窗口:
            _当前截取区域 = 窗口.获取区域()
            logger.info(f"自动检测到游戏窗口: {窗口.标题}, 区域: {_当前截取区域}")
            
            # 同步更新配置
            更新回调 = 配置.get("更新区域回调")
            if 更新回调:
                try:
                    更新回调(_当前截取区域)
                except Exception as e:
                    logger.warning(f"更新配置区域失败: {e}")
            
            # 如果启用了跟踪，自动启动
            if 配置.get("启用跟踪", False):
                启动窗口跟踪()
        else:
            logger.warning("未能自动检测到游戏窗口")
        
        _已初始化 = True
        return 窗口 is not None
        
    except Exception as e:
        logger.error(f"初始化窗口检测失败: {e}")
        return False


def 从配置自动检测() -> Optional[Tuple[int, int, int, int]]:
    """
    根据配置文件中的设置自动检测游戏窗口
    
    需求: 4.1 - 窗口标识配置
    
    返回:
        tuple: (x, y, width, height) 或 None
    """
    global _当前截取区域
    
    配置 = _获取配置设置()
    
    if not 配置.get("启用自动检测", False):
        logger.info("自动窗口检测未启用")
        return None
    
    标识类型 = 配置.get("标识类型", "process")
    标识值 = 配置.get("标识值", "")
    
    if 标识类型 == "process" and 标识值:
        return 自动检测游戏窗口(进程名=标识值)
    elif 标识类型 == "title" and 标识值:
        return 自动检测游戏窗口(窗口标题关键字=标识值)
    else:
        # 尝试从保存的配置加载
        return 自动检测游戏窗口()


def 截取屏幕(区域=None, 使用优化=True):
    """
    截取屏幕指定区域
    
    需求: 5.1 - 提供与当前 截取屏幕 函数相同的 API
    需求: 5.2 - 支持相同的区域参数格式（左, 上, 右, 下）
    需求: 5.3 - 返回相同格式的图像（numpy 数组，RGB）
    需求: 5.4 - 是当前实现的直接替代品
    
    参数:
        区域: tuple (左, 上, 右, 下) 或 None (全屏)
        使用优化: 是否使用优化截取器
    
    返回:
        numpy数组: RGB格式的图像
    """
    global _优化截取器实例
    
    # 尝试使用优化截取器
    if 使用优化 and 屏幕截取优化可用:
        try:
            if _优化截取器实例 is None:
                _优化截取器实例 = 优化屏幕截取器(
                    首选后端=_截取配置.get("首选后端", "auto"),
                    启用回退=_截取配置.get("启用回退", True),
                    启用性能监控=_截取配置.get("启用性能监控", True)
                )
                logger.info(f"优化截取器已初始化，后端: {_优化截取器实例.获取当前后端()}")
            
            # 转换区域格式：(左, 上, 右, 下) -> (x, y, width, height)
            优化区域 = None
            if 区域:
                左, 上, 右, 下 = 区域
                优化区域 = (左, 上, 右 - 左, 下 - 上)
            
            图像 = _优化截取器实例.截取(优化区域)
            
            if 图像 is not None:
                # 优化截取器返回 BGR 格式，转换为 RGB 以保持兼容性
                return cv2.cvtColor(图像, cv2.COLOR_BGR2RGB)
            else:
                logger.warning("优化截取器返回 None，回退到标准方式")
        except Exception as e:
            logger.warning(f"优化截取器失败，回退到标准方式: {e}")
    
    # 标准截取方式（GDI）
    return _标准GDI截取(区域)


def 截取并缩放(区域=None, 目标尺寸=(480, 270), 使用优化=True):
    """
    截取屏幕并缩放到指定尺寸
    
    参数:
        区域: tuple (左, 上, 右, 下) 或 None (全屏)
        目标尺寸: tuple (宽度, 高度)
        使用优化: 是否使用优化截取器
    
    返回:
        numpy数组: 缩放后的RGB图像
    """
    图像 = 截取屏幕(区域, 使用优化)
    图像 = cv2.resize(图像, 目标尺寸)
    return 图像


def _标准GDI截取(区域=None):
    """
    标准 GDI 截取方式（回退方案）
    
    参数:
        区域: tuple (左, 上, 右, 下) 或 None (全屏)
    
    返回:
        numpy数组: RGB格式的图像
    """
    桌面窗口 = win32gui.GetDesktopWindow()

    if 区域:
        左, 上, 右, 下 = 区域
        宽度 = 右 - 左 + 1
        高度 = 下 - 上 + 1
    else:
        宽度 = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
        高度 = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
        左 = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
        上 = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)

    窗口DC = win32gui.GetWindowDC(桌面窗口)
    源DC = win32ui.CreateDCFromHandle(窗口DC)
    内存DC = 源DC.CreateCompatibleDC()
    位图 = win32ui.CreateBitmap()
    位图.CreateCompatibleBitmap(源DC, 宽度, 高度)
    内存DC.SelectObject(位图)
    内存DC.BitBlt((0, 0), (宽度, 高度), 源DC, (左, 上), win32con.SRCCOPY)
    
    图像数据 = 位图.GetBitmapBits(True)
    图像 = np.frombuffer(图像数据, dtype='uint8')
    图像.shape = (高度, 宽度, 4)

    源DC.DeleteDC()
    内存DC.DeleteDC()
    win32gui.ReleaseDC(桌面窗口, 窗口DC)
    win32gui.DeleteObject(位图.GetHandle())

    return cv2.cvtColor(图像, cv2.COLOR_BGRA2RGB)


def 自动检测游戏窗口(窗口标题关键字: str = None, 进程名: str = None):
    """
    自动检测游戏窗口并返回其区域
    
    参数:
        窗口标题关键字: 窗口标题包含的关键字
        进程名: 进程名称
    
    返回:
        tuple: (x, y, width, height) 或 None
    """
    global _当前截取区域
    
    检测器 = _获取窗口检测器()
    if 检测器 is None:
        logger.warning("窗口检测模块不可用")
        return None
    
    try:
        窗口 = 检测器.自动检测(进程名=进程名, 标题=窗口标题关键字)
        if 窗口:
            _当前截取区域 = 窗口.获取区域()
            return _当前截取区域
        return None
    except Exception as e:
        logger.error(f"自动检测游戏窗口失败: {e}")
        return None


def 启动窗口跟踪(大小变化回调: Callable = None, 窗口关闭回调: Callable = None):
    """
    启动窗口位置跟踪
    
    当窗口移动时，会自动更新截取区域。
    当窗口大小变化时，会调用大小变化回调通知用户。
    
    参数:
        大小变化回调: 窗口大小变化时的回调函数
        窗口关闭回调: 窗口关闭时的回调函数
    
    返回:
        bool: 是否成功启动跟踪
    """
    检测器 = _获取窗口检测器()
    if 检测器 is None:
        logger.warning("窗口检测模块不可用")
        return False
    
    if 检测器.获取当前窗口() is None:
        logger.warning("未选择窗口，请先调用 自动检测游戏窗口 或 手动选择窗口")
        return False
    
    try:
        # 设置区域更新回调
        检测器.设置区域更新回调(_区域更新回调)
        
        # 设置大小变化通知回调
        if 大小变化回调:
            检测器.设置大小变化通知回调(大小变化回调)
        
        # 设置窗口关闭通知回调
        if 窗口关闭回调:
            检测器.设置窗口关闭通知回调(窗口关闭回调)
        
        # 启动跟踪
        检测器.启动跟踪(自动更新区域=True)
        logger.info("窗口跟踪已启动")
        return True
    except Exception as e:
        logger.error(f"启动窗口跟踪失败: {e}")
        return False


def 停止窗口跟踪():
    """停止窗口位置跟踪"""
    检测器 = _获取窗口检测器()
    if 检测器:
        检测器.停止跟踪()
        logger.info("窗口跟踪已停止")


def 是否正在跟踪() -> bool:
    """检查是否正在跟踪窗口"""
    检测器 = _获取窗口检测器()
    if 检测器:
        return 检测器.是否正在跟踪()
    return False


def 获取当前截取区域() -> Optional[Tuple[int, int, int, int]]:
    """
    获取当前的截取区域
    
    如果启用了窗口跟踪，会返回最新的窗口位置。
    
    返回:
        tuple: (x, y, width, height) 或 None
    """
    global _当前截取区域
    
    检测器 = _获取窗口检测器()
    if 检测器:
        区域 = 检测器.获取截取区域()
        if 区域:
            _当前截取区域 = 区域
            return 区域
    
    return _当前截取区域


def 截取游戏窗口(窗口标题关键字: str = None, 目标尺寸=None, 使用优化=True, 使用跟踪区域=True):
    """
    自动检测并截取游戏窗口
    
    参数:
        窗口标题关键字: 窗口标题包含的关键字
        目标尺寸: 可选的目标尺寸 (宽度, 高度)
        使用优化: 是否使用优化截取器
        使用跟踪区域: 是否使用跟踪器的最新区域
    
    返回:
        numpy数组: RGB格式的图像，失败返回None
    """
    区域 = None
    
    # 优先使用跟踪器的最新区域
    if 使用跟踪区域:
        区域 = 获取当前截取区域()
    
    # 如果没有跟踪区域，尝试自动检测
    if 区域 is None:
        区域 = 自动检测游戏窗口(窗口标题关键字)
    
    if 区域 is None:
        logger.warning("未检测到游戏窗口，使用全屏截取")
    else:
        # 转换为 (左, 上, 右, 下) 格式
        x, y, w, h = 区域
        区域 = (x, y, x + w, y + h)
    
    if 目标尺寸:
        return 截取并缩放(区域, 目标尺寸, 使用优化)
    else:
        return 截取屏幕(区域, 使用优化)


def 获取窗口列表():
    """
    获取所有可见窗口列表
    
    返回:
        list: 窗口信息列表 [(句柄, 标题, 区域), ...]
    """
    if not 窗口检测可用:
        logger.warning("窗口检测模块不可用")
        return []
    
    try:
        查找器 = 窗口查找器()
        窗口列表 = 查找器.获取所有窗口()
        return [(w.句柄, w.标题, w.获取区域()) for w in 窗口列表]
    except Exception as e:
        logger.error(f"获取窗口列表失败: {e}")
        return []


def 手动选择窗口(过滤关键词: str = None) -> Optional[Tuple[int, int, int, int]]:
    """
    手动选择窗口
    
    参数:
        过滤关键词: 过滤窗口的关键词
    
    返回:
        tuple: (x, y, width, height) 或 None
    """
    global _当前截取区域
    
    检测器 = _获取窗口检测器()
    if 检测器 is None:
        logger.warning("窗口检测模块不可用")
        return None
    
    try:
        窗口 = 检测器.手动选择(过滤关键词)
        if 窗口:
            _当前截取区域 = 窗口.获取区域()
            return _当前截取区域
        return None
    except Exception as e:
        logger.error(f"手动选择窗口失败: {e}")
        return None


def 点击选择窗口() -> Optional[Tuple[int, int, int, int]]:
    """
    点击选择窗口
    
    返回:
        tuple: (x, y, width, height) 或 None
    """
    global _当前截取区域
    
    检测器 = _获取窗口检测器()
    if 检测器 is None:
        logger.warning("窗口检测模块不可用")
        return None
    
    try:
        窗口 = 检测器.点击选择()
        if 窗口:
            _当前截取区域 = 窗口.获取区域()
            return _当前截取区域
        return None
    except Exception as e:
        logger.error(f"点击选择窗口失败: {e}")
        return None


def 保存窗口配置(使用进程名: bool = True):
    """
    保存当前窗口配置
    
    参数:
        使用进程名: 是否使用进程名作为标识（否则使用窗口标题）
    """
    检测器 = _获取窗口检测器()
    if 检测器:
        检测器.保存当前配置(使用进程名)


def 获取截取器状态():
    """
    获取截取器状态信息
    
    需求: 2.4 - 记录正在使用的截取后端
    
    返回:
        dict: 状态信息
    """
    检测器 = _获取窗口检测器()
    配置 = _获取配置设置()
    
    # 获取优化截取器的详细状态
    优化截取器状态 = {}
    if _优化截取器实例 is not None:
        优化截取器状态 = {
            "当前后端": _优化截取器实例.获取当前后端(),
            "性能统计": _优化截取器实例.获取性能统计()
        }
    
    return {
        "优化截取可用": 屏幕截取优化可用,
        "窗口检测可用": 窗口检测可用,
        "优化截取器已初始化": _优化截取器实例 is not None,
        "优化截取器状态": 优化截取器状态,
        "窗口检测器已初始化": 检测器 is not None,
        "正在跟踪窗口": 检测器.是否正在跟踪() if 检测器 else False,
        "当前截取区域": _当前截取区域,
        "已初始化": _已初始化,
        "截取配置": _截取配置.copy(),
        "配置": {
            "启用自动检测": 配置.get("启用自动检测", False),
            "标识类型": 配置.get("标识类型", ""),
            "标识值": 配置.get("标识值", ""),
            "启用跟踪": 配置.get("启用跟踪", False)
        }
    }


# ============== 截取配置函数 ==============
# 需求: 2.4 - 记录正在使用的截取后端

def 设置截取后端(后端: str):
    """
    设置首选截取后端
    
    需求: 2.4 - 记录正在使用的截取后端
    
    参数:
        后端: "auto", "dxgi", "mss", "gdi", "pil"
    """
    global _优化截取器实例, _截取配置
    
    有效后端 = ["auto", "dxgi", "mss", "gdi", "pil"]
    if 后端 not in 有效后端:
        logger.warning(f"无效的后端: {后端}，有效值: {有效后端}")
        return
    
    _截取配置["首选后端"] = 后端
    logger.info(f"截取后端已设置为: {后端}")
    
    # 如果已有截取器实例，需要重新初始化
    if _优化截取器实例 is not None:
        _优化截取器实例.释放()
        _优化截取器实例 = None
        logger.info("截取器实例已重置，下次截取时将使用新后端")


def 获取当前后端() -> str:
    """
    获取当前使用的截取后端
    
    需求: 2.4 - 记录正在使用的截取后端
    
    返回:
        str: 后端名称
    """
    if _优化截取器实例 is not None:
        return _优化截取器实例.获取当前后端()
    return _截取配置.get("首选后端", "auto")


def 设置性能监控(启用: bool):
    """
    设置是否启用性能监控
    
    参数:
        启用: 是否启用
    """
    global _截取配置
    _截取配置["启用性能监控"] = 启用
    
    if _优化截取器实例 is not None:
        _优化截取器实例.设置性能监控(启用)
    
    logger.info(f"性能监控已{'启用' if 启用 else '禁用'}")


def 设置回退机制(启用: bool):
    """
    设置是否启用自动回退机制
    
    参数:
        启用: 是否启用
    """
    global _截取配置
    _截取配置["启用回退"] = 启用
    
    if _优化截取器实例 is not None:
        _优化截取器实例.设置回退启用(启用)
    
    logger.info(f"回退机制已{'启用' if 启用 else '禁用'}")


def 获取截取配置() -> Dict[str, Any]:
    """
    获取当前截取配置
    
    返回:
        dict: 截取配置
    """
    return _截取配置.copy()


def 设置截取配置(配置: Dict[str, Any]):
    """
    设置截取配置
    
    参数:
        配置: 配置字典，可包含:
            - 首选后端: "auto", "dxgi", "mss", "gdi", "pil"
            - 启用回退: bool
            - 启用性能监控: bool
            - 显示器索引: int
    """
    global _截取配置, _优化截取器实例
    
    需要重新初始化 = False
    
    if "首选后端" in 配置:
        if 配置["首选后端"] != _截取配置.get("首选后端"):
            需要重新初始化 = True
        _截取配置["首选后端"] = 配置["首选后端"]
    
    if "启用回退" in 配置:
        _截取配置["启用回退"] = 配置["启用回退"]
    
    if "启用性能监控" in 配置:
        _截取配置["启用性能监控"] = 配置["启用性能监控"]
    
    if "显示器索引" in 配置:
        if 配置["显示器索引"] != _截取配置.get("显示器索引"):
            需要重新初始化 = True
        _截取配置["显示器索引"] = 配置["显示器索引"]
    
    # 如果需要重新初始化截取器
    if 需要重新初始化 and _优化截取器实例 is not None:
        _优化截取器实例.释放()
        _优化截取器实例 = None
        logger.info("截取器实例已重置，下次截取时将使用新配置")
    
    logger.info(f"截取配置已更新: {_截取配置}")


def 获取性能统计() -> Dict[str, Any]:
    """
    获取截取性能统计
    
    需求: 3.4 - 提供性能指标（截取时间、内存使用）
    
    返回:
        dict: 性能统计信息
    """
    if _优化截取器实例 is not None:
        return _优化截取器实例.获取性能统计()
    return {}


def 获取可用后端列表() -> list:
    """
    获取所有可用的截取后端列表
    
    返回:
        list: 可用后端列表
    """
    if 屏幕截取优化可用 and 后端检测器 is not None:
        return 后端检测器.获取可用后端列表()
    return ["gdi"]  # 默认 GDI 可用


def 获取系统图形信息() -> Dict[str, Any]:
    """
    获取系统图形信息
    
    返回:
        dict: 系统图形信息
    """
    if 屏幕截取优化可用 and 后端检测器 is not None:
        return 后端检测器.获取系统图形信息().to_dict()
    return {
        "操作系统": "Windows",
        "DXGI可用": False,
        "可用后端": ["gdi"],
        "推荐后端": "gdi"
    }


def 释放截取器():
    """
    释放截取器资源
    """
    global _优化截取器实例
    
    if _优化截取器实例 is not None:
        _优化截取器实例.释放()
        _优化截取器实例 = None
        logger.info("截取器资源已释放")


def 打印截取器诊断信息():
    """
    打印截取器诊断信息
    
    需求: 4.3 - 记录截取错误及诊断信息
    """
    if _优化截取器实例 is not None:
        _优化截取器实例.打印诊断信息()
    else:
        print("截取器未初始化")
        print(f"截取配置: {_截取配置}")
        print(f"优化截取可用: {屏幕截取优化可用}")


# 兼容原项目的函数名
grab_screen = 截取屏幕


if __name__ == "__main__":
    # 测试截图功能
    print("=" * 50)
    print("测试屏幕截取模块")
    print("=" * 50)
    
    # 显示系统图形信息
    print("\n1. 系统图形信息:")
    系统信息 = 获取系统图形信息()
    for 键, 值 in 系统信息.items():
        print(f"  {键}: {值}")
    
    # 显示可用后端
    print(f"\n2. 可用后端: {获取可用后端列表()}")
    
    # 显示截取器状态
    print("\n3. 截取器状态:")
    状态 = 获取截取器状态()
    for 键, 值 in 状态.items():
        if 键 != "优化截取器状态":
            print(f"  {键}: {值}")
    
    # 测试配置初始化
    print("\n4. 测试配置初始化...")
    if 初始化窗口检测():
        print("✅ 窗口检测初始化成功")
        区域 = 获取当前截取区域()
        if 区域:
            print(f"   当前截取区域: {区域}")
    else:
        print("⚠️ 窗口检测初始化失败或未启用")
    
    # 测试截取
    print("\n5. 测试截取功能:")
    图像 = 截取屏幕()
    print(f"  全屏截图尺寸: {图像.shape}")
    print(f"  当前后端: {获取当前后端()}")
    
    图像 = 截取屏幕(区域=(0, 40, 1920, 1120))
    print(f"  区域截图尺寸: {图像.shape}")
    
    图像 = 截取并缩放(区域=(0, 40, 1920, 1120))
    print(f"  缩放后尺寸: {图像.shape}")
    
    # 显示性能统计
    print("\n6. 性能统计:")
    性能统计 = 获取性能统计()
    if 性能统计:
        for 键, 值 in 性能统计.items():
            if 键 != "底层统计":
                print(f"  {键}: {值}")
    else:
        print("  无性能统计数据")
    
    # 测试窗口检测
    if 窗口检测可用:
        print("\n7. 测试窗口检测...")
        窗口列表 = 获取窗口列表()
        print(f"  检测到 {len(窗口列表)} 个窗口")
        for 句柄, 标题, 区域 in 窗口列表[:5]:
            print(f"    - {标题}: {区域}")
        
        # 测试从配置自动检测
        print("\n8. 测试从配置自动检测...")
        区域 = 从配置自动检测()
        if 区域:
            print(f"✅ 从配置检测到窗口: {区域}")
        else:
            print("⚠️ 未从配置检测到窗口")
    
    # 显示最终状态
    print("\n9. 最终截取器状态:")
    状态 = 获取截取器状态()
    print(f"  优化截取可用: {状态['优化截取可用']}")
    print(f"  优化截取器已初始化: {状态['优化截取器已初始化']}")
    if 状态['优化截取器状态']:
        print(f"  当前后端: {状态['优化截取器状态'].get('当前后端', 'N/A')}")
    print(f"  截取配置: {状态['截取配置']}")
    
    # 打印诊断信息
    print("\n10. 诊断信息:")
    打印截取器诊断信息()
    
    # 显示截图
    cv2.imshow("截图测试", cv2.cvtColor(图像, cv2.COLOR_RGB2BGR))
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    # 停止跟踪
    if 是否正在跟踪():
        停止窗口跟踪()
    
    # 释放资源
    释放截取器()
    
    print("\n" + "=" * 50)
    print("测试完成!")
    print("=" * 50)
