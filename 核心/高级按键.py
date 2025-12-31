"""
高级按键控制模块
支持按键队列、线程处理、鼠标控制等高级功能

功能:
- 按键队列处理 (线程安全)
- 支持按键组合字符串解析
- 支持直接键码和虚拟键码
- 支持鼠标移动和点击
- 支持按键延迟控制
"""

import ctypes
from threading import Thread
from time import sleep
from queue import Queue


class 高级按键:
    """高级按键控制类"""
    
    # 按键类型常量
    直接键码 = 0x0008
    虚拟键码 = 0x0000
    按键按下 = 0x0000
    按键释放 = 0x0002
    
    # 鼠标常量
    鼠标移动 = 0x0001
    鼠标左键按下 = 0x0002
    鼠标左键释放 = 0x0004
    鼠标右键按下 = 0x0008
    鼠标右键释放 = 0x0010
    鼠标中键按下 = 0x0020
    鼠标中键释放 = 0x0040
    
    # DirectInput 扫描码
    直接键码表 = {
        "1": 0x02, "2": 0x03, "3": 0x04, "4": 0x05, "5": 0x06,
        "6": 0x07, "7": 0x08, "8": 0x09, "9": 0x0A, "0": 0x0B,
        
        "小键盘1": 0x4F, "小键盘2": 0x50, "小键盘3": 0x51,
        "小键盘4": 0x4B, "小键盘5": 0x4C, "小键盘6": 0x4D,
        "小键盘7": 0x47, "小键盘8": 0x48, "小键盘9": 0x49,
        "小键盘0": 0x52,
        
        "A": 0x1E, "B": 0x30, "C": 0x2E, "D": 0x20, "E": 0x12,
        "F": 0x21, "G": 0x22, "H": 0x23, "I": 0x17, "J": 0x24,
        "K": 0x25, "L": 0x26, "M": 0x32, "N": 0x31, "O": 0x18,
        "P": 0x19, "Q": 0x10, "R": 0x13, "S": 0x1F, "T": 0x14,
        "U": 0x16, "V": 0x2F, "W": 0x11, "X": 0x2D, "Y": 0x15,
        "Z": 0x2C,
        
        "F1": 0x3B, "F2": 0x3C, "F3": 0x3D, "F4": 0x3E,
        "F5": 0x3F, "F6": 0x40, "F7": 0x41, "F8": 0x42,
        "F9": 0x43, "F10": 0x44, "F11": 0x57, "F12": 0x58,
        
        "上": 0xC8, "左": 0xCB, "右": 0xCD, "下": 0xD0,
        "UP": 0xC8, "LEFT": 0xCB, "RIGHT": 0xCD, "DOWN": 0xD0,
        
        "ESC": 0x01, "空格": 0x39, "SPACE": 0x39,
        "回车": 0x1C, "ENTER": 0x1C, "RETURN": 0x1C,
        "TAB": 0x0F, "退格": 0x0E, "BACK": 0x0E,
        
        "左CTRL": 0x1D, "右CTRL": 0x9D, "LCTRL": 0x1D, "RCTRL": 0x9D,
        "左SHIFT": 0x2A, "右SHIFT": 0x36, "LSHIFT": 0x2A, "RSHIFT": 0x36,
        "左ALT": 0x38, "右ALT": 0xB8, "LALT": 0x38, "RALT": 0xB8,
    }
    
    # 虚拟键码表
    虚拟键码表 = {
        "1": 0x31, "2": 0x32, "3": 0x33, "4": 0x34, "5": 0x35,
        "6": 0x36, "7": 0x37, "8": 0x38, "9": 0x39, "0": 0x30,
        
        "A": 0x41, "B": 0x42, "C": 0x43, "D": 0x44, "E": 0x45,
        "F": 0x46, "G": 0x47, "H": 0x48, "I": 0x49, "J": 0x4A,
        "K": 0x4B, "L": 0x4C, "M": 0x4D, "N": 0x4E, "O": 0x4F,
        "P": 0x50, "Q": 0x51, "R": 0x52, "S": 0x53, "T": 0x54,
        "U": 0x55, "V": 0x56, "W": 0x57, "X": 0x58, "Y": 0x59,
        "Z": 0x5A,
        
        "F1": 0x70, "F2": 0x71, "F3": 0x72, "F4": 0x73,
        "F5": 0x74, "F6": 0x75, "F7": 0x76, "F8": 0x77,
        "F9": 0x78, "F10": 0x79, "F11": 0x7A, "F12": 0x7B,
        
        "上": 0x26, "左": 0x25, "右": 0x27, "下": 0x28,
        "UP": 0x26, "LEFT": 0x25, "RIGHT": 0x27, "DOWN": 0x28,
        
        "ESC": 0x1B, "空格": 0x20, "SPACE": 0x20,
        "回车": 0x0D, "ENTER": 0x0D, "RETURN": 0x0D,
        "TAB": 0x09, "退格": 0x08, "BACK": 0x08,
        
        "左CTRL": 0xA2, "右CTRL": 0xA3, "LCTRL": 0xA2, "RCTRL": 0xA3,
        "左SHIFT": 0xA0, "右SHIFT": 0xA1, "LSHIFT": 0xA0, "RSHIFT": 0xA1,
        "左ALT": 0xA4, "右ALT": 0xA5, "LALT": 0xA4, "RALT": 0xA5,
    }
    
    def __init__(self):
        """初始化高级按键控制"""
        self._工作线程 = None
        self._按键队列 = Queue()
    
    def 解析按键字符串(self, 按键字符串):
        """
        解析按键字符串并添加到队列
        
        格式示例:
        - "W" - 按下并释放W键
        - "W_DOWN" - 只按下W键
        - "W_UP" - 只释放W键
        - "-100" - 暂停100毫秒
        - "W,-50,A" - 按W，暂停50ms，按A
        - "VK,W" - 使用虚拟键码
        - "DK,W" - 使用直接键码(默认)
        - "0x11" - 使用十六进制键码
        
        参数:
            按键字符串: 按键序列字符串
        
        返回:
            True 成功, 或错误列表
        """
        按键队列 = []
        错误列表 = []
        当前键码类型 = self.直接键码
        
        # 按逗号分割
        按键列表 = 按键字符串.upper().split(",")
        
        for 按键 in 按键列表:
            按键 = 按键.strip()
            if not 按键:
                continue
            
            # 解析按下/释放方向
            按下 = True
            释放 = True
            
            if "_DOWN" in 按键:
                按键 = 按键.replace("_DOWN", "")
                释放 = False
            elif "_UP" in 按键:
                按键 = 按键.replace("_UP", "")
                按下 = False
            
            # 切换到虚拟键码
            if 按键 == "VK":
                当前键码类型 = self.虚拟键码
                continue
            
            # 切换到直接键码
            if 按键 == "DK":
                当前键码类型 = self.直接键码
                continue
            
            # 十六进制键码
            if 按键.startswith("0X"):
                try:
                    键码 = int(按键, 16)
                    if 0 < 键码 < 256:
                        按键队列.append({
                            "键码": 键码,
                            "延迟": 0,
                            "按下": 按下,
                            "释放": 释放,
                            "类型": 当前键码类型,
                        })
                    else:
                        错误列表.append(按键)
                except ValueError:
                    错误列表.append(按键)
                continue
            
            # 暂停
            if 按键.startswith("-"):
                try:
                    延迟 = float(按键[1:]) / 1000  # 毫秒转秒
                    if 0 < 延迟 <= 10:
                        按键队列.append({
                            "键码": None,
                            "延迟": 延迟,
                            "按下": False,
                            "释放": False,
                            "类型": None,
                        })
                    else:
                        错误列表.append(按键)
                except ValueError:
                    错误列表.append(按键)
                continue
            
            # 查找键码
            键码表 = self.直接键码表 if 当前键码类型 == self.直接键码 else self.虚拟键码表
            if 按键 in 键码表:
                按键队列.append({
                    "键码": 键码表[按键],
                    "延迟": 0,
                    "按下": 按下,
                    "释放": 释放,
                    "类型": 当前键码类型,
                })
            else:
                错误列表.append(按键)
        
        # 如果有错误，不处理
        if 错误列表:
            return 错误列表
        
        # 启动工作线程
        if self._工作线程 is None or not self._工作线程.is_alive():
            self._工作线程 = Thread(target=self._处理队列, daemon=True)
            self._工作线程.start()
        
        # 添加到队列
        for 项 in 按键队列:
            self._按键队列.put(项)
        self._按键队列.put(None)  # 结束标记
        
        return True
    
    def _处理队列(self):
        """处理按键队列的工作线程"""
        while True:
            项 = self._按键队列.get()
            
            if 项 is None:
                self._按键队列.task_done()
                if self._按键队列.empty():
                    return
                continue
            
            if 项["键码"] is not None:
                # 按下
                if 项["按下"]:
                    self._发送按键(项["键码"], self.按键按下 | 项["类型"])
                
                # 延迟
                if 项["延迟"] > 0:
                    sleep(项["延迟"])
                
                # 释放
                if 项["释放"]:
                    self._发送按键(项["键码"], self.按键释放 | 项["类型"])
            else:
                # 纯延迟
                sleep(项["延迟"])
            
            self._按键队列.task_done()
    
    def 直接按键(self, 按键, 方向=None, 类型=None):
        """
        直接发送按键
        
        参数:
            按键: 按键名称或十六进制码
            方向: 按键按下/按键释放 (None表示按下)
            类型: 直接键码/虚拟键码 (None表示直接键码)
        """
        if 类型 is None:
            类型 = self.直接键码
        if 方向 is None:
            方向 = self.按键按下
        
        if isinstance(按键, str):
            按键 = 按键.upper()
            if 按键.startswith("0X"):
                按键 = int(按键, 16)
            else:
                键码表 = self.直接键码表 if 类型 == self.直接键码 else self.虚拟键码表
                按键 = 键码表.get(按键, 0x00)
        
        self._发送按键(按键, 方向 | 类型)
    
    def 直接鼠标(self, dx=0, dy=0, 按钮=0):
        """
        直接发送鼠标操作
        
        参数:
            dx: X方向移动量
            dy: Y方向移动量
            按钮: 鼠标按钮标志
        """
        if dx != 0 or dy != 0:
            按钮 |= self.鼠标移动
        self._发送鼠标(dx, dy, 按钮)
    
    def _发送按键(self, 键码, 标志):
        """发送键盘输入"""
        输入 = _键盘输入(键码, 标志)
        _发送输入(输入)
    
    def _发送鼠标(self, dx, dy, 按钮):
        """发送鼠标输入"""
        输入 = _鼠标输入(按钮, dx, dy, 0)
        _发送输入(输入)


# ==================== Windows API 结构体 ====================

LONG = ctypes.c_long
DWORD = ctypes.c_ulong
ULONG_PTR = ctypes.POINTER(DWORD)
WORD = ctypes.c_ushort


class _MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ('dx', LONG),
        ('dy', LONG),
        ('mouseData', DWORD),
        ('dwFlags', DWORD),
        ('time', DWORD),
        ('dwExtraInfo', ULONG_PTR)
    ]


class _KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ('wVk', WORD),
        ('wScan', WORD),
        ('dwFlags', DWORD),
        ('time', DWORD),
        ('dwExtraInfo', ULONG_PTR)
    ]


class _HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ('uMsg', DWORD),
        ('wParamL', WORD),
        ('wParamH', WORD)
    ]


class _INPUTunion(ctypes.Union):
    _fields_ = [
        ('mi', _MOUSEINPUT),
        ('ki', _KEYBDINPUT),
        ('hi', _HARDWAREINPUT)
    ]


class _INPUT(ctypes.Structure):
    _fields_ = [
        ('type', DWORD),
        ('union', _INPUTunion)
    ]


def _键盘输入(键码, 标志):
    """创建键盘输入结构"""
    ki = _KEYBDINPUT(键码, 键码, 标志, 0, None)
    return _INPUT(1, _INPUTunion(ki=ki))


def _鼠标输入(标志, dx, dy, 数据):
    """创建鼠标输入结构"""
    mi = _MOUSEINPUT(dx, dy, 数据, 标志, 0, None)
    return _INPUT(0, _INPUTunion(mi=mi))


def _发送输入(*输入列表):
    """发送输入到系统"""
    数量 = len(输入列表)
    数组类型 = _INPUT * 数量
    输入数组 = 数组类型(*输入列表)
    大小 = ctypes.c_int(ctypes.sizeof(_INPUT))
    return ctypes.windll.user32.SendInput(数量, 输入数组, 大小)


# ==================== 便捷函数 ====================

# 全局实例
_按键实例 = None


def 获取按键实例():
    """获取全局按键实例"""
    global _按键实例
    if _按键实例 is None:
        _按键实例 = 高级按键()
    return _按键实例


def 执行按键序列(按键字符串):
    """
    执行按键序列
    
    示例:
        执行按键序列("W,-100,A,-100,S,-100,D")  # WASD循环
        执行按键序列("1,-50,2,-50,3")  # 快速按123
        执行按键序列("LSHIFT_DOWN,1,-100,LSHIFT_UP")  # Shift+1
    """
    return 获取按键实例().解析按键字符串(按键字符串)


def 快速按键(按键, 持续时间=0.05):
    """
    快速按下并释放按键
    
    参数:
        按键: 按键名称
        持续时间: 按下持续时间(秒)
    """
    实例 = 获取按键实例()
    实例.直接按键(按键, 实例.按键按下)
    sleep(持续时间)
    实例.直接按键(按键, 实例.按键释放)


def 鼠标移动(dx, dy):
    """相对移动鼠标"""
    获取按键实例().直接鼠标(dx, dy)


def 鼠标左键点击():
    """鼠标左键点击"""
    实例 = 获取按键实例()
    实例.直接鼠标(按钮=实例.鼠标左键按下)
    sleep(0.05)
    实例.直接鼠标(按钮=实例.鼠标左键释放)


def 鼠标右键点击():
    """鼠标右键点击"""
    实例 = 获取按键实例()
    实例.直接鼠标(按钮=实例.鼠标右键按下)
    sleep(0.05)
    实例.直接鼠标(按钮=实例.鼠标右键释放)


if __name__ == "__main__":
    print("高级按键模块测试")
    print("3秒后执行测试...")
    sleep(3)
    
    # 测试按键序列
    print("测试: W键")
    执行按键序列("W,-500,W")
    
    sleep(1)
    
    # 测试鼠标移动
    print("测试: 鼠标移动")
    for i in range(50):
        鼠标移动(-2, 0)
        sleep(0.01)
    
    print("测试完成!")
