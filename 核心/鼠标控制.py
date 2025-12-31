"""
鼠标控制模块
用于模拟鼠标输入
"""

import ctypes
import time

# Windows API
user32 = ctypes.windll.user32

# 鼠标事件常量
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_ABSOLUTE = 0x8000


def 获取屏幕尺寸():
    """获取屏幕分辨率"""
    宽度 = user32.GetSystemMetrics(0)
    高度 = user32.GetSystemMetrics(1)
    return 宽度, 高度


def 获取鼠标位置():
    """获取当前鼠标位置"""
    class POINT(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
    
    pt = POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y


def 移动鼠标(x, y):
    """
    移动鼠标到指定位置
    
    参数:
        x: 目标X坐标
        y: 目标Y坐标
    """
    user32.SetCursorPos(x, y)


def 相对移动鼠标(dx, dy):
    """
    相对移动鼠标
    
    参数:
        dx: X方向偏移量
        dy: Y方向偏移量
    """
    user32.mouse_event(MOUSEEVENTF_MOVE, dx, dy, 0, 0)


def 左键按下():
    """按下鼠标左键"""
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)


def 左键释放():
    """释放鼠标左键"""
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)


def 左键点击(x=None, y=None, 持续时间=0.05):
    """
    鼠标左键点击
    
    参数:
        x: 点击X坐标 (None表示当前位置)
        y: 点击Y坐标 (None表示当前位置)
        持续时间: 按下持续时间
    """
    if x is not None and y is not None:
        移动鼠标(x, y)
        time.sleep(0.01)
    
    左键按下()
    time.sleep(持续时间)
    左键释放()


def 右键按下():
    """按下鼠标右键"""
    user32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)


def 右键释放():
    """释放鼠标右键"""
    user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)


def 右键点击(x=None, y=None, 持续时间=0.05):
    """
    鼠标右键点击
    
    参数:
        x: 点击X坐标 (None表示当前位置)
        y: 点击Y坐标 (None表示当前位置)
        持续时间: 按下持续时间
    """
    if x is not None and y is not None:
        移动鼠标(x, y)
        time.sleep(0.01)
    
    右键按下()
    time.sleep(持续时间)
    右键释放()


def 中键点击(持续时间=0.05):
    """鼠标中键点击"""
    user32.mouse_event(MOUSEEVENTF_MIDDLEDOWN, 0, 0, 0, 0)
    time.sleep(持续时间)
    user32.mouse_event(MOUSEEVENTF_MIDDLEUP, 0, 0, 0, 0)


if __name__ == "__main__":
    print("鼠标控制模块测试")
    print(f"屏幕尺寸: {获取屏幕尺寸()}")
    print(f"当前鼠标位置: {获取鼠标位置()}")
