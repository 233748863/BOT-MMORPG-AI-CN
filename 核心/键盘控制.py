"""
键盘控制模块
用于模拟键盘输入，支持技能键和组合键
"""

import ctypes
import time

# Windows API
SendInput = ctypes.windll.user32.SendInput

# ==================== 按键扫描码 ====================
# 移动键
W = 0x11
A = 0x1E
S = 0x1F
D = 0x20

# 技能数字键
数字1 = 0x02
数字2 = 0x03
数字3 = 0x04
数字4 = 0x05
数字5 = 0x06
数字6 = 0x07
数字7 = 0x08
数字8 = 0x09
数字9 = 0x0A
数字0 = 0x0B

# 常用技能键
Q = 0x10
E = 0x12
R = 0x13
F = 0x21
G = 0x22
Z = 0x2C
X = 0x2D
C = 0x2E
V = 0x2F

# 功能键
F1 = 0x3B
F2 = 0x3C
F3 = 0x3D
F4 = 0x3E
F5 = 0x3F
F6 = 0x40

# 特殊键
空格 = 0x39
回车 = 0x1C
ESC = 0x01
TAB = 0x0F
SHIFT = 0x2A
CTRL = 0x1D
ALT = 0x38

# 小键盘
小键盘2 = 0x50
小键盘4 = 0x4B
小键盘6 = 0x4D
小键盘8 = 0x48


# ==================== C结构体定义 ====================
PUL = ctypes.POINTER(ctypes.c_ulong)


class KeyBdInput(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.c_ushort),
        ("wScan", ctypes.c_ushort),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", PUL)
    ]


class HardwareInput(ctypes.Structure):
    _fields_ = [
        ("uMsg", ctypes.c_ulong),
        ("wParamL", ctypes.c_short),
        ("wParamH", ctypes.c_ushort)
    ]


class MouseInput(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", PUL)
    ]


class Input_I(ctypes.Union):
    _fields_ = [
        ("ki", KeyBdInput),
        ("mi", MouseInput),
        ("hi", HardwareInput)
    ]


class Input(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_ulong),
        ("ii", Input_I)
    ]


# ==================== 基础按键函数 ====================

def 按下按键(按键码):
    """按下指定按键"""
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.ki = KeyBdInput(0, 按键码, 0x0008, 0, ctypes.pointer(extra))
    x = Input(ctypes.c_ulong(1), ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))


def 释放按键(按键码):
    """释放指定按键"""
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.ki = KeyBdInput(0, 按键码, 0x0008 | 0x0002, 0, ctypes.pointer(extra))
    x = Input(ctypes.c_ulong(1), ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))


def 点击按键(按键码, 持续时间=0.05):
    """点击按键 (按下后释放)"""
    按下按键(按键码)
    time.sleep(持续时间)
    释放按键(按键码)


def 组合键(修饰键, 按键码, 持续时间=0.05):
    """
    按下组合键 (如 Shift+1, Ctrl+Q)
    
    参数:
        修饰键: SHIFT, CTRL, ALT
        按键码: 要组合的按键
        持续时间: 按下持续时间
    """
    按下按键(修饰键)
    time.sleep(0.02)
    点击按键(按键码, 持续时间)
    time.sleep(0.02)
    释放按键(修饰键)


# ==================== 移动动作函数 ====================

def 前进():
    """向前移动 (W)"""
    按下按键(W)
    释放按键(A)
    释放按键(D)
    释放按键(S)


def 后退():
    """向后移动 (S)"""
    按下按键(S)
    释放按键(A)
    释放按键(W)
    释放按键(D)


def 左移():
    """向左移动 (A)"""
    按下按键(A)
    释放按键(W)
    释放按键(D)
    释放按键(S)


def 右移():
    """向右移动 (D)"""
    按下按键(D)
    释放按键(W)
    释放按键(A)
    释放按键(S)


def 前进左移():
    """向前左移动 (W+A)"""
    按下按键(W)
    按下按键(A)
    释放按键(D)
    释放按键(S)


def 前进右移():
    """向前右移动 (W+D)"""
    按下按键(W)
    按下按键(D)
    释放按键(A)
    释放按键(S)


def 后退左移():
    """向后左移动 (S+A)"""
    按下按键(S)
    按下按键(A)
    释放按键(W)
    释放按键(D)


def 后退右移():
    """向后右移动 (S+D)"""
    按下按键(S)
    按下按键(D)
    释放按键(W)
    释放按键(A)


def 无操作():
    """释放所有移动键"""
    释放按键(W)
    释放按键(A)
    释放按键(S)
    释放按键(D)


def 释放所有按键():
    """释放所有常用按键"""
    释放按键(W)
    释放按键(A)
    释放按键(S)
    释放按键(D)
    释放按键(SHIFT)
    释放按键(CTRL)
    释放按键(ALT)


# ==================== 技能动作函数 ====================

def 技能1(): 点击按键(数字1)
def 技能2(): 点击按键(数字2)
def 技能3(): 点击按键(数字3)
def 技能4(): 点击按键(数字4)
def 技能5(): 点击按键(数字5)
def 技能6(): 点击按键(数字6)
def 技能7(): 点击按键(数字7)
def 技能8(): 点击按键(数字8)
def 技能9(): 点击按键(数字9)
def 技能0(): 点击按键(数字0)

def 技能Q(): 点击按键(Q)
def 技能E(): 点击按键(E)
def 技能R(): 点击按键(R)
def 技能G(): 点击按键(G)
def 技能C(): 点击按键(C)

def 跳跃(): 点击按键(空格)
def 交互(): 点击按键(F)  # F键用于交互
def 闪避(): 点击按键(空格)  # 很多游戏空格是闪避
def 切换目标(): 点击按键(TAB)
def 交互(): 点击按键(F)

# Shift组合技能
def Shift技能1(): 组合键(SHIFT, 数字1)
def Shift技能2(): 组合键(SHIFT, 数字2)
def Shift技能3(): 组合键(SHIFT, 数字3)
def Shift技能4(): 组合键(SHIFT, 数字4)
def Shift技能Q(): 组合键(SHIFT, Q)
def Shift技能E(): 组合键(SHIFT, E)
def Shift技能R(): 组合键(SHIFT, R)

# Ctrl组合技能
def Ctrl技能1(): 组合键(CTRL, 数字1)
def Ctrl技能2(): 组合键(CTRL, 数字2)
def Ctrl技能3(): 组合键(CTRL, 数字3)
def Ctrl技能4(): 组合键(CTRL, 数字4)
def Ctrl技能Q(): 组合键(CTRL, Q)


# 兼容原项目的函数名
PressKey = 按下按键
ReleaseKey = 释放按键


if __name__ == '__main__':
    print("键盘控制模块测试")
    print("3秒后按下W键1秒...")
    time.sleep(3)
    
    按下按键(W)
    time.sleep(1)
    释放按键(W)
    
    print("测试完成!")
