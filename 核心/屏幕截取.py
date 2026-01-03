"""
屏幕截取模块
用于捕获游戏画面

集成屏幕截取优化和自动窗口检测功能。
"""

import cv2
import numpy as np
import win32gui
import win32ui
import win32con
import win32api
import logging

# 尝试导入屏幕截取优化模块
try:
    from 核心.屏幕截取优化 import 优化截取器
    屏幕截取优化可用 = True
except ImportError:
    屏幕截取优化可用 = False

# 尝试导入窗口检测模块
try:
    from 核心.窗口检测 import 窗口检测器
    窗口检测可用 = True
except ImportError:
    窗口检测可用 = False

# 配置日志
logger = logging.getLogger(__name__)

# 全局优化截取器实例
_优化截取器实例 = None
_窗口检测器实例 = None


def 截取屏幕(区域=None, 使用优化=True):
    """
    截取屏幕指定区域
    
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
                _优化截取器实例 = 优化截取器()
            return _优化截取器实例.截取(区域)
        except Exception as e:
            logger.warning(f"优化截取器失败，回退到标准方式: {e}")
    
    # 标准截取方式
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


def 自动检测游戏窗口(窗口标题关键字: str = None):
    """
    自动检测游戏窗口并返回其区域
    
    参数:
        窗口标题关键字: 窗口标题包含的关键字
    
    返回:
        tuple: (左, 上, 右, 下) 或 None
    """
    global _窗口检测器实例
    
    if not 窗口检测可用:
        logger.warning("窗口检测模块不可用")
        return None
    
    try:
        if _窗口检测器实例 is None:
            _窗口检测器实例 = 窗口检测器()
        
        if 窗口标题关键字:
            return _窗口检测器实例.按标题查找(窗口标题关键字)
        else:
            return _窗口检测器实例.自动检测游戏窗口()
    except Exception as e:
        logger.error(f"自动检测游戏窗口失败: {e}")
        return None


def 截取游戏窗口(窗口标题关键字: str = None, 目标尺寸=None, 使用优化=True):
    """
    自动检测并截取游戏窗口
    
    参数:
        窗口标题关键字: 窗口标题包含的关键字
        目标尺寸: 可选的目标尺寸 (宽度, 高度)
        使用优化: 是否使用优化截取器
    
    返回:
        numpy数组: RGB格式的图像，失败返回None
    """
    区域 = 自动检测游戏窗口(窗口标题关键字)
    
    if 区域 is None:
        logger.warning("未检测到游戏窗口，使用全屏截取")
        区域 = None
    
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
    global _窗口检测器实例
    
    if not 窗口检测可用:
        logger.warning("窗口检测模块不可用")
        return []
    
    try:
        if _窗口检测器实例 is None:
            _窗口检测器实例 = 窗口检测器()
        
        return _窗口检测器实例.获取窗口列表()
    except Exception as e:
        logger.error(f"获取窗口列表失败: {e}")
        return []


def 获取截取器状态():
    """
    获取截取器状态信息
    
    返回:
        dict: 状态信息
    """
    return {
        "优化截取可用": 屏幕截取优化可用,
        "窗口检测可用": 窗口检测可用,
        "优化截取器已初始化": _优化截取器实例 is not None,
        "窗口检测器已初始化": _窗口检测器实例 is not None
    }


# 兼容原项目的函数名
grab_screen = 截取屏幕


if __name__ == "__main__":
    # 测试截图功能
    print("测试屏幕截取...")
    
    # 显示截取器状态
    状态 = 获取截取器状态()
    print(f"截取器状态: {状态}")
    
    图像 = 截取屏幕()
    print(f"全屏截图尺寸: {图像.shape}")
    
    图像 = 截取屏幕(区域=(0, 40, 1920, 1120))
    print(f"区域截图尺寸: {图像.shape}")
    
    图像 = 截取并缩放(区域=(0, 40, 1920, 1120))
    print(f"缩放后尺寸: {图像.shape}")
    
    # 测试窗口检测
    if 窗口检测可用:
        print("\n测试窗口检测...")
        窗口列表 = 获取窗口列表()
        print(f"检测到 {len(窗口列表)} 个窗口")
        for 句柄, 标题, 区域 in 窗口列表[:5]:
            print(f"  - {标题}: {区域}")
    
    # 显示截图
    cv2.imshow("截图测试", cv2.cvtColor(图像, cv2.COLOR_RGB2BGR))
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    print("测试完成!")
