"""
屏幕截取模块
用于捕获游戏画面
"""

import cv2
import numpy as np
import win32gui
import win32ui
import win32con
import win32api


def 截取屏幕(区域=None):
    """
    截取屏幕指定区域
    
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


def 截取并缩放(区域=None, 目标尺寸=(480, 270)):
    """
    截取屏幕并缩放到指定尺寸
    
    参数:
        区域: tuple (左, 上, 右, 下) 或 None (全屏)
        目标尺寸: tuple (宽度, 高度)
    
    返回:
        numpy数组: 缩放后的RGB图像
    """
    图像 = 截取屏幕(区域)
    图像 = cv2.resize(图像, 目标尺寸)
    return 图像


# 兼容原项目的函数名
grab_screen = 截取屏幕


if __name__ == "__main__":
    # 测试截图功能
    print("测试屏幕截取...")
    
    图像 = 截取屏幕()
    print(f"全屏截图尺寸: {图像.shape}")
    
    图像 = 截取屏幕(区域=(0, 40, 1920, 1120))
    print(f"区域截图尺寸: {图像.shape}")
    
    图像 = 截取并缩放(区域=(0, 40, 1920, 1120))
    print(f"缩放后尺寸: {图像.shape}")
    
    # 显示截图
    cv2.imshow("截图测试", cv2.cvtColor(图像, cv2.COLOR_RGB2BGR))
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    print("测试完成!")
