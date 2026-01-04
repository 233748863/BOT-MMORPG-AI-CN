"""
屏幕截取优化模块
提供高性能的屏幕截取功能

功能:
- DXGI Desktop Duplication 截取（Windows 8+，高性能）
- MSS 截取（跨平台，中等性能）
- PIL/GDI 截取（回退方案）
- 自动后端选择
- 性能统计

需求: 2.1 - 检测当前系统是否支持 DXGI
需求: 2.2 - 如果 DXGI 可用，默认使用 DXGI 截取器
需求: 2.3 - 如果 DXGI 不可用，回退到其他截取器
需求: 2.4 - 记录正在使用的截取后端
"""

import time
import ctypes
import platform
import sys
from typing import Tuple, Optional, Dict, Any, List
from dataclasses import dataclass, field
from collections import deque
import numpy as np
import logging

# 配置日志
日志 = logging.getLogger(__name__)


@dataclass
class 截取统计:
    """截取性能统计"""
    平均延迟: float = 0.0  # 毫秒
    最小延迟: float = 0.0
    最大延迟: float = 0.0
    截取次数: int = 0
    失败次数: int = 0
    恢复次数: int = 0
    后端类型: str = ""
    
    def to_dict(self) -> dict:
        return {
            '平均延迟': round(self.平均延迟, 2),
            '最小延迟': round(self.最小延迟, 2),
            '最大延迟': round(self.最大延迟, 2),
            '截取次数': self.截取次数,
            '失败次数': self.失败次数,
            '恢复次数': self.恢复次数,
            '后端类型': self.后端类型
        }


@dataclass
class 系统图形信息:
    """系统图形信息"""
    操作系统: str = ""
    操作系统版本: str = ""
    是否Windows: bool = False
    Windows版本号: int = 0  # Windows 主版本号 (8, 10, 11 等)
    DXGI可用: bool = False
    显示器数量: int = 0
    主显示器分辨率: Tuple[int, int] = (0, 0)
    可用后端: List[str] = field(default_factory=list)
    推荐后端: str = ""
    
    def to_dict(self) -> dict:
        return {
            '操作系统': self.操作系统,
            '操作系统版本': self.操作系统版本,
            '是否Windows': self.是否Windows,
            'Windows版本号': self.Windows版本号,
            'DXGI可用': self.DXGI可用,
            '显示器数量': self.显示器数量,
            '主显示器分辨率': self.主显示器分辨率,
            '可用后端': self.可用后端,
            '推荐后端': self.推荐后端
        }


class 后端检测器:
    """
    检测可用的截取后端
    
    需求: 2.1 - 检测当前系统是否支持 DXGI
    """
    
    # 缓存检测结果
    _缓存: Dict[str, Any] = {}
    
    @staticmethod
    def 检测DXGI可用() -> bool:
        """
        检测 DXGI Desktop Duplication 是否可用
        
        DXGI 要求:
        - Windows 8 或更高版本
        - 安装了 dxcam 或 d3dshot 库
        
        需求: 2.1 - 检测当前系统是否支持 DXGI
        
        返回:
            bool: DXGI 是否可用
        """
        缓存键 = "dxgi_available"
        if 缓存键 in 后端检测器._缓存:
            return 后端检测器._缓存[缓存键]
        
        结果 = False
        
        # 检查是否为 Windows 系统
        if platform.system() != "Windows":
            日志.debug("非 Windows 系统，DXGI 不可用")
            后端检测器._缓存[缓存键] = False
            return False
        
        # 检查 Windows 版本 (需要 Windows 8+)
        try:
            版本信息 = sys.getwindowsversion()
            主版本 = 版本信息.major
            次版本 = 版本信息.minor
            
            # Windows 8 是 6.2，Windows 10/11 是 10.0
            if 主版本 < 6 or (主版本 == 6 and 次版本 < 2):
                日志.debug(f"Windows 版本过低 ({主版本}.{次版本})，DXGI 需要 Windows 8+")
                后端检测器._缓存[缓存键] = False
                return False
        except Exception as e:
            日志.warning(f"无法获取 Windows 版本: {e}")
        
        # 优先检测 dxcam（更现代、更快）
        try:
            import dxcam
            日志.debug("dxcam 库可用")
            结果 = True
        except ImportError:
            日志.debug("dxcam 库不可用")
        
        # 如果 dxcam 不可用，检测 d3dshot
        if not 结果:
            try:
                import d3dshot
                日志.debug("d3dshot 库可用")
                结果 = True
            except ImportError:
                日志.debug("d3dshot 库不可用")
        
        后端检测器._缓存[缓存键] = 结果
        return 结果
    
    @staticmethod
    def 检测MSS可用() -> bool:
        """检测 MSS 是否可用"""
        缓存键 = "mss_available"
        if 缓存键 in 后端检测器._缓存:
            return 后端检测器._缓存[缓存键]
        
        try:
            import mss
            后端检测器._缓存[缓存键] = True
            return True
        except ImportError:
            后端检测器._缓存[缓存键] = False
            return False
    
    @staticmethod
    def 检测PIL可用() -> bool:
        """检测 PIL 是否可用"""
        缓存键 = "pil_available"
        if 缓存键 in 后端检测器._缓存:
            return 后端检测器._缓存[缓存键]
        
        try:
            from PIL import ImageGrab
            后端检测器._缓存[缓存键] = True
            return True
        except ImportError:
            后端检测器._缓存[缓存键] = False
            return False
    
    @staticmethod
    def 检测GDI可用() -> bool:
        """检测 GDI (win32) 是否可用"""
        缓存键 = "gdi_available"
        if 缓存键 in 后端检测器._缓存:
            return 后端检测器._缓存[缓存键]
        
        # GDI 仅在 Windows 上可用
        if platform.system() != "Windows":
            后端检测器._缓存[缓存键] = False
            return False
        
        try:
            import win32gui
            import win32ui
            import win32con
            后端检测器._缓存[缓存键] = True
            return True
        except ImportError:
            后端检测器._缓存[缓存键] = False
            return False
    
    @staticmethod
    def 获取可用后端列表() -> List[str]:
        """
        获取所有可用的截取后端列表
        
        返回:
            List[str]: 可用后端列表，按性能排序
        """
        可用后端 = []
        
        if 后端检测器.检测DXGI可用():
            可用后端.append("dxgi")
        
        if 后端检测器.检测MSS可用():
            可用后端.append("mss")
        
        if 后端检测器.检测GDI可用():
            可用后端.append("gdi")
        
        if 后端检测器.检测PIL可用():
            可用后端.append("pil")
        
        return 可用后端
    
    @staticmethod
    def 获取最佳后端() -> str:
        """
        获取当前系统的最佳截取后端
        
        优先级:
        1. DXGI (最快，Windows 8+ 专用)
        2. MSS (跨平台，较快)
        3. GDI (Windows 原生)
        4. PIL (通用回退)
        
        需求: 2.2 - 如果 DXGI 可用，默认使用 DXGI 截取器
        需求: 2.3 - 如果 DXGI 不可用，回退到其他截取器
        
        返回:
            str: 最佳后端名称 ("dxgi", "mss", "gdi", "pil", "none")
        """
        if 后端检测器.检测DXGI可用():
            日志.info("选择 DXGI 作为最佳后端（高性能）")
            return "dxgi"
        
        if 后端检测器.检测MSS可用():
            日志.info("选择 MSS 作为最佳后端（DXGI 不可用）")
            return "mss"
        
        if 后端检测器.检测GDI可用():
            日志.info("选择 GDI 作为最佳后端（MSS 不可用）")
            return "gdi"
        
        if 后端检测器.检测PIL可用():
            日志.info("选择 PIL 作为最佳后端（回退方案）")
            return "pil"
        
        日志.error("没有可用的截取后端")
        return "none"
    
    @staticmethod
    def 获取系统图形信息() -> 系统图形信息:
        """
        获取系统图形信息
        
        需求: 2.1 - 检测当前系统是否支持 DXGI
        
        返回:
            系统图形信息: 包含系统和图形相关信息
        """
        信息 = 系统图形信息()
        
        # 操作系统信息
        信息.操作系统 = platform.system()
        信息.操作系统版本 = platform.version()
        信息.是否Windows = 信息.操作系统 == "Windows"
        
        # Windows 版本号
        if 信息.是否Windows:
            try:
                版本信息 = sys.getwindowsversion()
                if 版本信息.major >= 10:
                    # Windows 10 或 11
                    if 版本信息.build >= 22000:
                        信息.Windows版本号 = 11
                    else:
                        信息.Windows版本号 = 10
                elif 版本信息.major == 6:
                    if 版本信息.minor == 3:
                        信息.Windows版本号 = 8  # Windows 8.1
                    elif 版本信息.minor == 2:
                        信息.Windows版本号 = 8  # Windows 8
                    elif 版本信息.minor == 1:
                        信息.Windows版本号 = 7  # Windows 7
                    else:
                        信息.Windows版本号 = 6  # Vista
                else:
                    信息.Windows版本号 = 版本信息.major
            except Exception as e:
                日志.warning(f"无法获取 Windows 版本号: {e}")
        
        # DXGI 可用性
        信息.DXGI可用 = 后端检测器.检测DXGI可用()
        
        # 显示器信息
        try:
            if 信息.是否Windows:
                import win32api
                import win32con
                
                # 获取显示器数量
                信息.显示器数量 = win32api.GetSystemMetrics(win32con.SM_CMONITORS)
                
                # 获取主显示器分辨率
                宽度 = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
                高度 = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
                信息.主显示器分辨率 = (宽度, 高度)
            else:
                # 非 Windows 系统，尝试使用 mss 获取
                if 后端检测器.检测MSS可用():
                    import mss
                    with mss.mss() as sct:
                        信息.显示器数量 = len(sct.monitors) - 1  # 减去虚拟显示器
                        if len(sct.monitors) > 1:
                            主显示器 = sct.monitors[1]
                            信息.主显示器分辨率 = (主显示器["width"], 主显示器["height"])
        except Exception as e:
            日志.warning(f"无法获取显示器信息: {e}")
        
        # 可用后端
        信息.可用后端 = 后端检测器.获取可用后端列表()
        信息.推荐后端 = 后端检测器.获取最佳后端()
        
        return 信息
    
    @staticmethod
    def 清除缓存():
        """清除检测结果缓存"""
        后端检测器._缓存.clear()
        日志.debug("后端检测缓存已清除")
    
    @staticmethod
    def 打印系统信息():
        """打印系统图形信息"""
        信息 = 后端检测器.获取系统图形信息()
        
        print("\n=== 系统图形信息 ===")
        print(f"操作系统: {信息.操作系统} {信息.操作系统版本}")
        if 信息.是否Windows:
            print(f"Windows 版本: {信息.Windows版本号}")
        print(f"DXGI 可用: {'是' if 信息.DXGI可用 else '否'}")
        print(f"显示器数量: {信息.显示器数量}")
        print(f"主显示器分辨率: {信息.主显示器分辨率[0]}x{信息.主显示器分辨率[1]}")
        print(f"可用后端: {', '.join(信息.可用后端) if 信息.可用后端 else '无'}")
        print(f"推荐后端: {信息.推荐后端}")
        print("=" * 25)


class 截取器基类:
    """截取器基类"""
    
    def __init__(self):
        self._延迟记录: deque = deque(maxlen=100)
        self._截取次数: int = 0
        self._失败次数: int = 0
        self._恢复次数: int = 0
    
    def 截取(self, 区域: Tuple[int, int, int, int] = None) -> Optional[np.ndarray]:
        """
        截取屏幕
        
        参数:
            区域: (x, y, width, height)，None 表示全屏
            
        返回:
            截取的图像 (BGR 格式)
        """
        raise NotImplementedError
    
    def 获取统计(self) -> 截取统计:
        """获取性能统计"""
        if not self._延迟记录:
            return 截取统计(
                后端类型=self.__class__.__name__,
                失败次数=self._失败次数,
                恢复次数=self._恢复次数
            )
        
        延迟列表 = list(self._延迟记录)
        return 截取统计(
            平均延迟=np.mean(延迟列表),
            最小延迟=np.min(延迟列表),
            最大延迟=np.max(延迟列表),
            截取次数=self._截取次数,
            失败次数=self._失败次数,
            恢复次数=self._恢复次数,
            后端类型=self.__class__.__name__
        )
    
    def _记录延迟(self, 延迟: float):
        """记录延迟"""
        self._延迟记录.append(延迟)
        self._截取次数 += 1
    
    def _记录失败(self):
        """记录失败"""
        self._失败次数 += 1
    
    def _记录恢复(self):
        """记录恢复"""
        self._恢复次数 += 1
    
    def 释放(self):
        """释放资源"""
        pass


class MSS截取器(截取器基类):
    """使用 MSS 库截取屏幕"""
    
    def __init__(self):
        super().__init__()
        self._mss = None
        self._初始化()
    
    def _初始化(self):
        """初始化 MSS"""
        try:
            import mss
            self._mss = mss.mss()
            日志.info("MSS 截取器初始化成功")
        except ImportError:
            日志.error("MSS 未安装，请运行: pip install mss")
            raise
    
    def 截取(self, 区域: Tuple[int, int, int, int] = None) -> Optional[np.ndarray]:
        """截取屏幕"""
        if self._mss is None:
            return None
        
        开始时间 = time.perf_counter()
        
        try:
            if 区域:
                x, y, w, h = 区域
                监视器 = {"left": x, "top": y, "width": w, "height": h}
            else:
                监视器 = self._mss.monitors[1]  # 主显示器
            
            截图 = self._mss.grab(监视器)
            
            # 转换为 numpy 数组 (BGRA -> BGR)
            图像 = np.array(截图)[:, :, :3]
            
            延迟 = (time.perf_counter() - 开始时间) * 1000
            self._记录延迟(延迟)
            
            return 图像
            
        except Exception as e:
            日志.error(f"MSS 截取失败: {e}")
            return None
    
    def 释放(self):
        """释放资源"""
        if self._mss:
            self._mss.close()
            self._mss = None


class PIL截取器(截取器基类):
    """使用 PIL 截取屏幕"""
    
    def __init__(self):
        super().__init__()
        self._检查依赖()
    
    def _检查依赖(self):
        """检查依赖"""
        try:
            from PIL import ImageGrab
            日志.info("PIL 截取器初始化成功")
        except ImportError:
            日志.error("PIL 未安装，请运行: pip install Pillow")
            raise
    
    def 截取(self, 区域: Tuple[int, int, int, int] = None) -> Optional[np.ndarray]:
        """截取屏幕"""
        from PIL import ImageGrab
        import cv2
        
        开始时间 = time.perf_counter()
        
        try:
            if 区域:
                x, y, w, h = 区域
                bbox = (x, y, x + w, y + h)
                截图 = ImageGrab.grab(bbox=bbox)
            else:
                截图 = ImageGrab.grab()
            
            # 转换为 numpy 数组 (RGB -> BGR)
            图像 = cv2.cvtColor(np.array(截图), cv2.COLOR_RGB2BGR)
            
            延迟 = (time.perf_counter() - 开始时间) * 1000
            self._记录延迟(延迟)
            
            return 图像
            
        except Exception as e:
            日志.error(f"PIL 截取失败: {e}")
            return None


class GDI截取器(截取器基类):
    """
    基于 GDI (Windows Graphics Device Interface) 的截取器
    
    使用 win32gui/win32ui 库实现 Windows 原生 GDI 截图功能。
    这是传统的截图方式，兼容性好但性能较 DXGI 低。
    
    需求: 2.3 - 如果 DXGI 不可用，回退到 GDI 截取器
    需求: 5.4 - 是当前实现的直接替代品
    """
    
    def __init__(self):
        """初始化 GDI 截取器"""
        super().__init__()
        self._已初始化 = False
        self._屏幕宽度 = 0
        self._屏幕高度 = 0
        self._初始化()
    
    def _初始化(self) -> bool:
        """
        初始化 GDI 资源
        
        返回:
            bool: 初始化是否成功
        """
        try:
            # 检查依赖
            import win32gui
            import win32ui
            import win32con
            import win32api
            
            # 获取屏幕尺寸
            self._屏幕宽度 = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
            self._屏幕高度 = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
            
            self._已初始化 = True
            日志.info(f"GDI 截取器初始化成功，屏幕尺寸: {self._屏幕宽度}x{self._屏幕高度}")
            return True
            
        except ImportError as e:
            日志.error(f"GDI 依赖库未安装: {e}，请运行: pip install pywin32")
            self._已初始化 = False
            return False
        except Exception as e:
            日志.error(f"GDI 截取器初始化失败: {e}")
            self._已初始化 = False
            return False
    
    def 截取(self, 区域: Tuple[int, int, int, int] = None) -> Optional[np.ndarray]:
        """
        使用 GDI 截取屏幕
        
        需求: 5.3 - 返回相同格式的图像（numpy 数组，BGR）
        需求: 5.2 - 支持相同的区域参数格式
        
        参数:
            区域: (x, y, width, height)，None 表示全屏
            
        返回:
            截取的图像 (BGR 格式的 numpy 数组)
        """
        if not self._已初始化:
            日志.error("GDI 截取器未初始化")
            self._记录失败()
            return None
        
        开始时间 = time.perf_counter()
        
        try:
            import win32gui
            import win32ui
            import win32con
            import win32api
            import cv2
            
            桌面窗口 = win32gui.GetDesktopWindow()
            
            if 区域:
                x, y, w, h = 区域
                左 = x
                上 = y
                宽度 = w
                高度 = h
            else:
                宽度 = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
                高度 = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
                左 = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
                上 = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)
            
            # 创建设备上下文
            窗口DC = win32gui.GetWindowDC(桌面窗口)
            源DC = win32ui.CreateDCFromHandle(窗口DC)
            内存DC = 源DC.CreateCompatibleDC()
            
            # 创建位图
            位图 = win32ui.CreateBitmap()
            位图.CreateCompatibleBitmap(源DC, 宽度, 高度)
            内存DC.SelectObject(位图)
            
            # 执行 BitBlt 复制
            内存DC.BitBlt((0, 0), (宽度, 高度), 源DC, (左, 上), win32con.SRCCOPY)
            
            # 获取位图数据
            图像数据 = 位图.GetBitmapBits(True)
            图像 = np.frombuffer(图像数据, dtype='uint8')
            图像.shape = (高度, 宽度, 4)  # BGRA 格式
            
            # 释放资源
            源DC.DeleteDC()
            内存DC.DeleteDC()
            win32gui.ReleaseDC(桌面窗口, 窗口DC)
            win32gui.DeleteObject(位图.GetHandle())
            
            # 转换为 BGR 格式（去掉 Alpha 通道）
            图像 = cv2.cvtColor(图像, cv2.COLOR_BGRA2BGR)
            
            延迟 = (time.perf_counter() - 开始时间) * 1000
            self._记录延迟(延迟)
            
            return 图像
            
        except Exception as e:
            日志.error(f"GDI 截取失败: {e}")
            self._记录失败()
            return None
    
    def 是否已初始化(self) -> bool:
        """检查是否已初始化"""
        return self._已初始化
    
    def 获取屏幕尺寸(self) -> Tuple[int, int]:
        """获取屏幕尺寸"""
        return (self._屏幕宽度, self._屏幕高度)
    
    def 获取后端类型(self) -> str:
        """获取后端类型"""
        return "gdi"


class DXGI截取器(截取器基类):
    """
    基于 DXGI Desktop Duplication 的高性能截取器
    
    使用 dxcam 库实现 Windows Desktop Duplication API
    支持 60+ FPS 的高速截取
    
    需求: 1.1 - 使用 Windows Desktop Duplication API 进行屏幕截取
    需求: 1.2 - 以 60+ FPS 的速度截取帧
    需求: 1.3 - 返回与 GDI 实现相同格式的图像（numpy 数组，RGB/BGR）
    需求: 1.4 - 支持截取屏幕的特定区域
    需求: 3.1 - 重用帧缓冲区以最小化内存分配
    需求: 3.2 - 支持零拷贝访问帧数据
    需求: 3.3 - 正确释放 GPU 资源
    需求: 4.1 - 如果 DXGI 截取失败，尝试重新初始化截取会话
    需求: 4.4 - 优雅地处理显示模式变化（分辨率、刷新率）
    """
    
    # 错误恢复相关常量
    最大重试次数: int = 3
    重试间隔秒: float = 0.1
    连续失败阈值: int = 5  # 连续失败多少次后触发重新初始化
    
    def __init__(self, 显示器索引: int = 0, 输出格式: str = "BGR", 缓冲区大小: int = 2):
        """
        初始化 DXGI 截取器
        
        参数:
            显示器索引: 要截取的显示器索引（0 为主显示器）
            输出格式: 输出图像格式，"BGR" 或 "RGB"
            缓冲区大小: 帧缓冲区数量（用于双缓冲或多缓冲）
        """
        super().__init__()
        self._显示器索引 = 显示器索引
        self._输出格式 = 输出格式
        self._缓冲区大小 = 缓冲区大小
        self._camera = None
        self._使用dxcam = False
        self._使用d3dshot = False
        self._已初始化 = False
        self._屏幕宽度 = 0
        self._屏幕高度 = 0
        
        # 需求 3.1: 帧缓冲区重用
        self._帧缓冲区: Optional[np.ndarray] = None
        self._区域缓冲区: Dict[Tuple[int, int, int, int], np.ndarray] = {}  # 区域截取缓冲区
        self._上一帧: Optional[np.ndarray] = None  # 用于帧获取失败时返回
        self._缓冲区命中次数: int = 0
        self._缓冲区未命中次数: int = 0
        
        # 资源管理
        self._资源已释放 = False
        
        # 需求 4.1, 4.4: 错误恢复相关状态
        self._连续失败次数: int = 0
        self._重新初始化次数: int = 0
        self._最后错误信息: str = ""
        self._显示模式变化检测: bool = True
        self._上次屏幕尺寸: Tuple[int, int] = (0, 0)
        
        self._初始化()
    
    def _初始化(self) -> bool:
        """
        初始化 DXGI 资源
        
        需求: 1.1 - 使用 Windows Desktop Duplication API 进行屏幕截取
        需求: 4.1 - 如果 DXGI 截取失败，尝试重新初始化截取会话
        
        返回:
            bool: 初始化是否成功
        """
        # 优先尝试 dxcam（更现代、更快）
        if self._尝试初始化dxcam():
            self._使用dxcam = True
            self._已初始化 = True
            self._资源已释放 = False
            self._连续失败次数 = 0  # 重置连续失败计数
            self._上次屏幕尺寸 = (self._屏幕宽度, self._屏幕高度)
            日志.info(f"DXGI 截取器初始化成功 (dxcam)，显示器: {self._显示器索引}，分辨率: {self._屏幕宽度}x{self._屏幕高度}")
            return True
        
        # 回退到 d3dshot
        if self._尝试初始化d3dshot():
            self._使用d3dshot = True
            self._已初始化 = True
            self._资源已释放 = False
            self._连续失败次数 = 0  # 重置连续失败计数
            self._上次屏幕尺寸 = (self._屏幕宽度, self._屏幕高度)
            日志.info(f"DXGI 截取器初始化成功 (d3dshot)，显示器: {self._显示器索引}，分辨率: {self._屏幕宽度}x{self._屏幕高度}")
            return True
        
        self._最后错误信息 = "DXGI 截取器初始化失败：dxcam 和 d3dshot 都不可用"
        日志.error(self._最后错误信息)
        return False
    
    def _尝试初始化dxcam(self) -> bool:
        """尝试使用 dxcam 初始化"""
        try:
            import dxcam
            
            # 创建 dxcam 实例
            # dxcam.create() 返回一个 Camera 对象
            self._camera = dxcam.create(
                device_idx=0,  # GPU 设备索引
                output_idx=self._显示器索引,  # 显示器索引
                output_color=self._输出格式  # 输出颜色格式
            )
            
            if self._camera is None:
                日志.warning("dxcam.create() 返回 None")
                return False
            
            # 获取屏幕尺寸
            self._屏幕宽度 = self._camera.width
            self._屏幕高度 = self._camera.height
            
            # 需求 3.1: 预分配帧缓冲区
            self._帧缓冲区 = np.empty((self._屏幕高度, self._屏幕宽度, 3), dtype=np.uint8)
            
            日志.debug(f"dxcam 初始化成功，屏幕尺寸: {self._屏幕宽度}x{self._屏幕高度}")
            return True
            
        except ImportError:
            日志.debug("dxcam 库未安装")
            return False
        except Exception as e:
            日志.warning(f"dxcam 初始化失败: {e}")
            return False
    
    def _尝试初始化d3dshot(self) -> bool:
        """尝试使用 d3dshot 初始化"""
        try:
            import d3dshot
            
            # 创建 d3dshot 实例
            # 需求 3.1: 使用帧缓冲区
            self._camera = d3dshot.create(
                capture_output="numpy",
                frame_buffer_size=self._缓冲区大小  # 双缓冲或多缓冲
            )
            
            if self._camera is None:
                日志.warning("d3dshot.create() 返回 None")
                return False
            
            # 获取显示器信息
            显示器列表 = self._camera.displays
            if self._显示器索引 >= len(显示器列表):
                日志.warning(f"显示器索引 {self._显示器索引} 超出范围，共 {len(显示器列表)} 个显示器")
                self._显示器索引 = 0
            
            显示器 = 显示器列表[self._显示器索引]
            self._屏幕宽度 = 显示器.width
            self._屏幕高度 = 显示器.height
            
            # 设置目标显示器
            self._camera.display = 显示器
            
            # 需求 3.1: 预分配帧缓冲区
            self._帧缓冲区 = np.empty((self._屏幕高度, self._屏幕宽度, 3), dtype=np.uint8)
            
            日志.debug(f"d3dshot 初始化成功，屏幕尺寸: {self._屏幕宽度}x{self._屏幕高度}")
            return True
            
        except ImportError:
            日志.debug("d3dshot 库未安装")
            return False
        except Exception as e:
            日志.warning(f"d3dshot 初始化失败: {e}")
            return False
    
    def _获取或创建区域缓冲区(self, 区域: Tuple[int, int, int, int]) -> np.ndarray:
        """
        获取或创建区域截取的缓冲区
        
        需求 3.1: 重用帧缓冲区以最小化内存分配
        
        参数:
            区域: (x, y, width, height)
            
        返回:
            预分配的缓冲区
        """
        x, y, w, h = 区域
        缓冲区键 = (w, h)  # 使用尺寸作为键
        
        if 缓冲区键 in self._区域缓冲区:
            self._缓冲区命中次数 += 1
            return self._区域缓冲区[缓冲区键]
        
        # 创建新缓冲区
        self._缓冲区未命中次数 += 1
        新缓冲区 = np.empty((h, w, 3), dtype=np.uint8)
        
        # 限制缓存大小，避免内存泄漏
        if len(self._区域缓冲区) >= 10:
            # 移除最早的缓冲区
            最早键 = next(iter(self._区域缓冲区))
            del self._区域缓冲区[最早键]
        
        self._区域缓冲区[缓冲区键] = 新缓冲区
        return 新缓冲区
    
    def 截取(self, 区域: Tuple[int, int, int, int] = None) -> Optional[np.ndarray]:
        """
        执行屏幕截取
        
        需求: 1.2 - 以 60+ FPS 的速度截取帧
        需求: 1.3 - 返回与 GDI 实现相同格式的图像
        需求: 1.4 - 支持截取屏幕的特定区域
        需求: 3.1 - 重用帧缓冲区以最小化内存分配
        需求: 3.2 - 支持零拷贝访问帧数据
        需求: 4.1 - 如果 DXGI 截取失败，尝试重新初始化截取会话
        需求: 4.4 - 优雅地处理显示模式变化
        
        参数:
            区域: (x, y, width, height)，None 表示全屏
            
        返回:
            截取的图像 (BGR/RGB 格式的 numpy 数组)
        """
        if not self._已初始化 or self._camera is None:
            self._最后错误信息 = "DXGI 截取器未初始化"
            日志.error(self._最后错误信息)
            self._记录失败()
            return None
        
        if self._资源已释放:
            self._最后错误信息 = "DXGI 资源已释放"
            日志.error(self._最后错误信息)
            self._记录失败()
            return None
        
        开始时间 = time.perf_counter()
        
        try:
            # 需求 4.4: 检测显示模式变化
            if self._显示模式变化检测 and self._检测显示模式变化():
                日志.warning("检测到显示模式变化，重新初始化 DXGI 截取器...")
                if self.重新初始化():
                    self._记录恢复()
                    日志.info("显示模式变化后重新初始化成功")
                else:
                    self._最后错误信息 = "显示模式变化后重新初始化失败"
                    日志.error(self._最后错误信息)
                    self._记录失败()
                    return None
            
            # 获取帧
            帧 = self._获取帧(区域)
            
            if 帧 is None:
                self._连续失败次数 += 1
                self._最后错误信息 = f"帧获取失败，连续失败次数: {self._连续失败次数}"
                日志.debug(self._最后错误信息)
                
                # 需求 4.1: 连续失败达到阈值时尝试重新初始化
                if self._连续失败次数 >= self.连续失败阈值:
                    日志.warning(f"连续失败 {self._连续失败次数} 次，尝试重新初始化...")
                    if self._尝试带重试的重新初始化():
                        self._记录恢复()
                        # 重新初始化后再次尝试截取
                        帧 = self._获取帧(区域)
                        if 帧 is not None:
                            self._连续失败次数 = 0
                            延迟 = (time.perf_counter() - 开始时间) * 1000
                            self._记录延迟(延迟)
                            self._上一帧 = 帧
                            return 帧
                
                # 如果获取失败，尝试返回上一帧
                if self._上一帧 is not None:
                    日志.debug("帧获取失败，返回上一帧")
                    return self._上一帧.copy()
                
                self._记录失败()
                return None
            
            # 成功获取帧，重置连续失败计数
            self._连续失败次数 = 0
            
            # 需求 3.1: 帧缓冲区重用 - 保存当前帧作为备份
            self._上一帧 = 帧
            
            延迟 = (time.perf_counter() - 开始时间) * 1000
            self._记录延迟(延迟)
            
            return 帧
            
        except Exception as e:
            self._连续失败次数 += 1
            self._最后错误信息 = f"DXGI 截取异常: {str(e)}"
            日志.error(self._最后错误信息)
            self._记录失败()
            
            # 需求 4.1: 尝试重新初始化
            if self._尝试带重试的重新初始化():
                self._记录恢复()
                # 重新初始化后再次尝试截取
                return self._获取帧(区域)
            
            return None
    
    def _检测显示模式变化(self) -> bool:
        """
        检测显示模式是否发生变化
        
        需求: 4.4 - 优雅地处理显示模式变化（分辨率、刷新率）
        
        返回:
            bool: 是否检测到显示模式变化
        """
        try:
            # 获取当前屏幕尺寸
            当前宽度 = 0
            当前高度 = 0
            
            if platform.system() == "Windows":
                import win32api
                import win32con
                当前宽度 = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
                当前高度 = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
            
            if 当前宽度 == 0 or 当前高度 == 0:
                return False
            
            # 比较与上次记录的尺寸
            if self._上次屏幕尺寸 != (0, 0):
                if (当前宽度, 当前高度) != self._上次屏幕尺寸:
                    日志.info(f"显示模式变化: {self._上次屏幕尺寸} -> ({当前宽度}, {当前高度})")
                    return True
            
            return False
            
        except Exception as e:
            日志.debug(f"检测显示模式变化时出错: {e}")
            return False
    
    def _尝试带重试的重新初始化(self) -> bool:
        """
        带重试机制的重新初始化
        
        需求: 4.1 - 如果 DXGI 截取失败，尝试重新初始化截取会话
        
        返回:
            bool: 重新初始化是否成功
        """
        for 尝试次数 in range(self.最大重试次数):
            日志.info(f"重新初始化尝试 {尝试次数 + 1}/{self.最大重试次数}...")
            
            if self.重新初始化():
                日志.info(f"重新初始化成功（第 {尝试次数 + 1} 次尝试）")
                return True
            
            # 等待一段时间后重试
            if 尝试次数 < self.最大重试次数 - 1:
                time.sleep(self.重试间隔秒)
        
        self._最后错误信息 = f"重新初始化失败，已尝试 {self.最大重试次数} 次"
        日志.error(self._最后错误信息)
        return False
    
    def _获取帧(self, 区域: Tuple[int, int, int, int] = None) -> Optional[np.ndarray]:
        """
        获取帧数据
        
        需求: 1.4 - 支持截取屏幕的特定区域
        需求: 3.2 - 支持零拷贝访问帧数据
        
        参数:
            区域: (x, y, width, height)，None 表示全屏
            
        返回:
            帧数据 (numpy 数组)
        """
        if self._使用dxcam:
            return self._dxcam获取帧(区域)
        elif self._使用d3dshot:
            return self._d3dshot获取帧(区域)
        return None
    
    def _dxcam获取帧(self, 区域: Tuple[int, int, int, int] = None) -> Optional[np.ndarray]:
        """
        使用 dxcam 获取帧
        
        需求: 1.4 - 支持截取屏幕的特定区域
        需求: 1.3 - 返回与 GDI 实现相同格式的图像（numpy 数组，BGR）
        """
        try:
            if 区域:
                x, y, w, h = 区域
                # 验证区域边界
                x = max(0, min(x, self._屏幕宽度 - 1))
                y = max(0, min(y, self._屏幕高度 - 1))
                w = max(1, min(w, self._屏幕宽度 - x))
                h = max(1, min(h, self._屏幕高度 - y))
                
                # dxcam 使用 (left, top, right, bottom) 格式
                region = (x, y, x + w, y + h)
                帧 = self._camera.grab(region=region)
            else:
                帧 = self._camera.grab()
            
            if 帧 is None:
                return None
            
            # 需求 1.3: 确保输出为 BGR 格式（与 GDI/PIL 一致）
            # dxcam 默认输出格式由初始化时指定
            if self._输出格式 == "RGB":
                # 转换为 BGR 以保持与其他截取器一致
                import cv2
                帧 = cv2.cvtColor(帧, cv2.COLOR_RGB2BGR)
            
            return 帧
            
        except Exception as e:
            日志.debug(f"dxcam 获取帧失败: {e}")
            return None
    
    def _d3dshot获取帧(self, 区域: Tuple[int, int, int, int] = None) -> Optional[np.ndarray]:
        """
        使用 d3dshot 获取帧
        
        需求: 1.4 - 支持截取屏幕的特定区域
        需求: 1.3 - 返回与 GDI 实现相同格式的图像（numpy 数组，BGR）
        """
        try:
            if 区域:
                x, y, w, h = 区域
                # 验证区域边界
                x = max(0, min(x, self._屏幕宽度 - 1))
                y = max(0, min(y, self._屏幕高度 - 1))
                w = max(1, min(w, self._屏幕宽度 - x))
                h = max(1, min(h, self._屏幕高度 - y))
                
                # d3dshot 使用 (left, top, right, bottom) 格式
                region = (x, y, x + w, y + h)
                帧 = self._camera.screenshot(region=region)
            else:
                帧 = self._camera.screenshot()
            
            if 帧 is None:
                return None
            
            # 需求 1.3: d3dshot 返回 RGB 格式，转换为 BGR 以保持一致性
            import cv2
            帧 = cv2.cvtColor(帧, cv2.COLOR_RGB2BGR)
            
            return 帧
            
        except Exception as e:
            日志.debug(f"d3dshot 获取帧失败: {e}")
            return None
    
    def 重新初始化(self) -> bool:
        """
        重新初始化 DXGI 资源（用于错误恢复）
        
        需求: 4.1 - 如果 DXGI 截取失败，尝试重新初始化截取会话
        需求: 4.4 - 优雅地处理显示模式变化
        
        返回:
            bool: 重新初始化是否成功
        """
        self._重新初始化次数 += 1
        日志.info(f"尝试重新初始化 DXGI 截取器（第 {self._重新初始化次数} 次）...")
        
        # 先释放现有资源
        self.释放()
        
        # 重置状态
        self._使用dxcam = False
        self._使用d3dshot = False
        self._已初始化 = False
        self._资源已释放 = False
        self._连续失败次数 = 0
        
        # 清空区域缓冲区缓存（分辨率可能已变化）
        self._区域缓冲区.clear()
        
        # 短暂等待，让系统有时间释放资源
        time.sleep(0.05)
        
        # 重新初始化
        成功 = self._初始化()
        
        if 成功:
            日志.info(f"DXGI 截取器重新初始化成功，新分辨率: {self._屏幕宽度}x{self._屏幕高度}")
        else:
            日志.error(f"DXGI 截取器重新初始化失败: {self._最后错误信息}")
        
        return 成功
    
    def 释放(self):
        """
        释放 DXGI 资源
        
        需求: 3.3 - 正确释放 GPU 资源
        """
        if self._资源已释放:
            return
        
        if self._camera is not None:
            try:
                if self._使用dxcam:
                    # dxcam 需要调用 release() 或 stop()
                    if hasattr(self._camera, 'release'):
                        self._camera.release()
                    elif hasattr(self._camera, 'stop'):
                        self._camera.stop()
                elif self._使用d3dshot:
                    # d3dshot 需要调用 stop()
                    if hasattr(self._camera, 'stop'):
                        self._camera.stop()
                
                日志.debug("DXGI 资源已释放")
            except Exception as e:
                日志.warning(f"释放 DXGI 资源时出错: {e}")
            finally:
                self._camera = None
        
        # 需求 3.3: 清理帧缓冲区，释放内存
        self._帧缓冲区 = None
        self._上一帧 = None
        self._区域缓冲区.clear()
        
        self._已初始化 = False
        self._资源已释放 = True
        
        日志.debug(f"DXGI 截取器资源已完全释放，缓冲区命中率: {self._获取缓冲区命中率():.1f}%")
    
    def _获取缓冲区命中率(self) -> float:
        """获取缓冲区命中率"""
        总次数 = self._缓冲区命中次数 + self._缓冲区未命中次数
        if 总次数 == 0:
            return 0.0
        return (self._缓冲区命中次数 / 总次数) * 100
    
    def 获取资源统计(self) -> Dict[str, Any]:
        """
        获取资源使用统计
        
        需求: 3.4 - 提供性能指标
        需求: 4.3 - 记录截取错误及诊断信息
        
        返回:
            资源统计字典
        """
        return {
            '缓冲区命中次数': self._缓冲区命中次数,
            '缓冲区未命中次数': self._缓冲区未命中次数,
            '缓冲区命中率': self._获取缓冲区命中率(),
            '区域缓冲区数量': len(self._区域缓冲区),
            '已初始化': self._已初始化,
            '资源已释放': self._资源已释放,
            '后端类型': self.获取后端类型(),
            '连续失败次数': self._连续失败次数,
            '重新初始化次数': self._重新初始化次数,
            '最后错误信息': self._最后错误信息,
            '屏幕尺寸': (self._屏幕宽度, self._屏幕高度)
        }
    
    def 获取最后错误信息(self) -> str:
        """
        获取最后一次错误的诊断信息
        
        需求: 4.3 - 记录截取错误及诊断信息
        
        返回:
            错误信息字符串
        """
        return self._最后错误信息
    
    def 获取重新初始化次数(self) -> int:
        """
        获取重新初始化的次数
        
        返回:
            重新初始化次数
        """
        return self._重新初始化次数
    
    def 设置显示模式变化检测(self, 启用: bool):
        """
        设置是否启用显示模式变化检测
        
        参数:
            启用: 是否启用
        """
        self._显示模式变化检测 = 启用
        日志.debug(f"显示模式变化检测已{'启用' if 启用 else '禁用'}")
    
    def 是否已初始化(self) -> bool:
        """检查是否已初始化"""
        return self._已初始化
    
    def 获取屏幕尺寸(self) -> Tuple[int, int]:
        """获取屏幕尺寸"""
        return (self._屏幕宽度, self._屏幕高度)
    
    def 获取后端类型(self) -> str:
        """获取使用的后端类型"""
        if self._使用dxcam:
            return "dxcam"
        elif self._使用d3dshot:
            return "d3dshot"
        return "unknown"
    
    def __del__(self):
        """析构函数，确保资源被释放"""
        self.释放()


class 屏幕截取器:
    """
    统一的屏幕截取接口
    
    提供与当前 截取屏幕 函数相同的 API，支持自动后端选择和回退机制。
    
    需求: 5.1 - 提供与当前 截取屏幕 函数相同的 API
    需求: 5.2 - 支持相同的区域参数格式（左, 上, 右, 下）
    需求: 5.3 - 返回相同格式的图像（numpy 数组，RGB/BGR）
    需求: 2.2 - 如果 DXGI 可用，默认使用 DXGI 截取器
    需求: 2.3 - 如果 DXGI 不可用，回退到其他截取器
    需求: 2.4 - 记录正在使用的截取后端
    需求: 3.4 - 提供性能指标（截取时间、内存使用）
    需求: 4.2 - 如果重新初始化失败，回退到 GDI 截取
    需求: 4.3 - 记录截取错误及诊断信息
    """
    
    def __init__(self, 首选后端: str = "auto", 启用回退: bool = True, 启用性能监控: bool = True):
        """
        初始化屏幕截取器
        
        参数:
            首选后端: "auto", "dxgi", "mss", "gdi", "pil"
                     "auto" 会自动选择最佳后端
            启用回退: 是否启用自动回退机制
            启用性能监控: 是否启用性能监控
        """
        self._截取器: Optional[截取器基类] = None
        self._后端类型: str = ""
        self._回退启用: bool = 启用回退
        self._首选后端: str = 首选后端
        self._启用性能监控: bool = 启用性能监控
        
        # 性能统计 - 需求 3.4
        self._总截取次数: int = 0
        self._总失败次数: int = 0
        self._回退次数: int = 0
        self._恢复次数: int = 0
        self._截取时间记录: deque = deque(maxlen=100)  # 最近100次截取时间
        
        # 需求 4.3: 错误诊断信息
        self._错误日志: deque = deque(maxlen=50)  # 最近50条错误记录
        self._最后错误信息: str = ""
        self._回退历史: List[Dict[str, Any]] = []  # 回退历史记录
        
        self._初始化后端(首选后端)
    
    def _初始化后端(self, 首选后端: str):
        """
        初始化截取后端
        
        需求: 2.2 - 如果 DXGI 可用，默认使用 DXGI 截取器
        需求: 2.3 - 如果 DXGI 不可用，回退到其他截取器
        需求: 4.2 - 如果重新初始化失败，回退到 GDI 截取
        需求: 4.3 - 记录截取错误及诊断信息
        """
        # 自动选择最佳后端
        if 首选后端 == "auto":
            首选后端 = 后端检测器.获取最佳后端()
            日志.info(f"自动选择截取后端: {首选后端}")
        
        日志.info(f"尝试初始化截取后端: {首选后端}")
        
        try:
            if 首选后端 == "dxgi":
                # 尝试初始化 DXGI 截取器
                try:
                    self._截取器 = DXGI截取器()
                    if self._截取器.是否已初始化():
                        self._后端类型 = "dxgi"
                        日志.info("DXGI 截取器初始化成功")
                    else:
                        raise RuntimeError("DXGI 截取器初始化失败")
                except Exception as e:
                    错误信息 = f"DXGI 截取器初始化失败: {e}"
                    self._记录错误(错误信息, "dxgi")
                    日志.warning(f"{错误信息}，尝试回退到 MSS")
                    
                    # 需求 4.2: 回退到其他后端
                    self._执行回退初始化("dxgi", str(e))
                    
            elif 首选后端 == "mss":
                try:
                    self._截取器 = MSS截取器()
                    self._后端类型 = "mss"
                except Exception as e:
                    错误信息 = f"MSS 截取器初始化失败: {e}"
                    self._记录错误(错误信息, "mss")
                    self._执行回退初始化("mss", str(e))
                    
            elif 首选后端 == "gdi":
                try:
                    self._截取器 = GDI截取器()
                    if self._截取器.是否已初始化():
                        self._后端类型 = "gdi"
                        日志.info("GDI 截取器初始化成功")
                    else:
                        raise RuntimeError("GDI 截取器初始化失败")
                except Exception as e:
                    错误信息 = f"GDI 截取器初始化失败: {e}"
                    self._记录错误(错误信息, "gdi")
                    日志.warning(f"{错误信息}，尝试回退到 PIL")
                    self._执行回退初始化("gdi", str(e))
                
            elif 首选后端 == "pil":
                self._截取器 = PIL截取器()
                self._后端类型 = "pil"
            else:
                # 尝试按优先级初始化
                self._尝试初始化可用后端()
            
            # 需求: 2.4 - 记录正在使用的截取后端
            日志.info(f"截取后端初始化成功: {self._后端类型}")
            
        except Exception as e:
            错误信息 = f"截取后端初始化失败: {e}"
            self._记录错误(错误信息, 首选后端)
            日志.error(错误信息)
            # 尝试回退
            self._尝试初始化可用后端()
    
    def _执行回退初始化(self, 失败后端: str, 错误原因: str):
        """
        执行回退初始化
        
        需求: 4.2 - 如果重新初始化失败，回退到 GDI 截取
        需求: 4.3 - 记录截取错误及诊断信息
        
        参数:
            失败后端: 失败的后端名称
            错误原因: 失败原因
        """
        回退记录 = {
            '时间': time.strftime('%Y-%m-%d %H:%M:%S'),
            '失败后端': 失败后端,
            '错误原因': 错误原因,
            '回退到': None
        }
        
        # 按优先级尝试回退
        回退顺序 = ["mss", "gdi", "pil"]
        
        for 后端 in 回退顺序:
            if 后端 == 失败后端:
                continue
            
            try:
                if 后端 == "mss":
                    self._截取器 = MSS截取器()
                    self._后端类型 = "mss"
                elif 后端 == "gdi":
                    self._截取器 = GDI截取器()
                    if not self._截取器.是否已初始化():
                        continue
                    self._后端类型 = "gdi"
                elif 后端 == "pil":
                    self._截取器 = PIL截取器()
                    self._后端类型 = "pil"
                
                回退记录['回退到'] = 后端
                self._回退历史.append(回退记录)
                日志.info(f"成功回退到 {后端} 后端")
                return
                
            except Exception as e:
                self._记录错误(f"回退到 {后端} 失败: {e}", 后端)
                continue
        
        # 所有回退都失败
        回退记录['回退到'] = "失败"
        self._回退历史.append(回退记录)
        raise RuntimeError("所有截取后端初始化都失败")
    
    def _尝试初始化可用后端(self):
        """尝试初始化任何可用的后端"""
        可用后端 = 后端检测器.获取可用后端列表()
        
        for 后端 in 可用后端:
            try:
                if 后端 == "dxgi":
                    self._截取器 = DXGI截取器()
                    if self._截取器.是否已初始化():
                        self._后端类型 = "dxgi"
                        return
                    else:
                        continue
                elif 后端 == "mss":
                    self._截取器 = MSS截取器()
                    self._后端类型 = "mss"
                    return
                elif 后端 == "gdi":
                    self._截取器 = GDI截取器()
                    if self._截取器.是否已初始化():
                        self._后端类型 = "gdi"
                        return
                    else:
                        continue
                elif 后端 == "pil":
                    self._截取器 = PIL截取器()
                    self._后端类型 = "pil"
                    return
            except Exception as e:
                日志.warning(f"初始化 {后端} 失败: {e}")
                continue
        
        raise RuntimeError("没有可用的截取后端")
    
    def 截取(self, 区域: Tuple[int, int, int, int] = None) -> Optional[np.ndarray]:
        """
        截取屏幕
        
        需求: 5.1 - 提供与当前 截取屏幕 函数相同的 API
        需求: 5.2 - 支持相同的区域参数格式（左, 上, 右, 下）
        需求: 5.3 - 返回相同格式的图像（numpy 数组，BGR）
        
        参数:
            区域: (x, y, width, height)，None 表示全屏
            
        返回:
            截取的图像 (BGR 格式的 numpy 数组)
        """
        if self._截取器 is None:
            日志.error("截取器未初始化")
            self._总失败次数 += 1
            return None
        
        开始时间 = time.perf_counter()
        
        图像 = self._截取器.截取(区域)
        
        # 如果失败且启用回退，尝试其他后端
        if 图像 is None and self._回退启用:
            self._总失败次数 += 1
            图像 = self._尝试回退截取(区域)
            if 图像 is not None:
                self._回退次数 += 1
        
        # 记录性能统计 - 需求 3.4
        if 图像 is not None:
            self._总截取次数 += 1
            if self._启用性能监控:
                截取时间 = (time.perf_counter() - 开始时间) * 1000  # 毫秒
                self._截取时间记录.append(截取时间)
        
        return 图像
    
    def 截取并缩放(self, 区域: Tuple[int, int, int, int] = None, 
                   目标尺寸: Tuple[int, int] = (480, 270)) -> Optional[np.ndarray]:
        """
        截取屏幕并缩放到指定尺寸
        
        需求: 5.1 - 提供与当前 截取屏幕 函数相同的 API
        
        参数:
            区域: (x, y, width, height)，None 表示全屏
            目标尺寸: (宽度, 高度)，默认 480x270
            
        返回:
            缩放后的图像 (BGR 格式的 numpy 数组)
        """
        图像 = self.截取(区域)
        
        if 图像 is None:
            return None
        
        try:
            import cv2
            缩放图像 = cv2.resize(图像, 目标尺寸, interpolation=cv2.INTER_LINEAR)
            return 缩放图像
        except Exception as e:
            日志.error(f"图像缩放失败: {e}")
            return 图像  # 返回原图像
        
        return 图像
    
    def _尝试回退截取(self, 区域: Tuple[int, int, int, int] = None) -> Optional[np.ndarray]:
        """
        尝试使用回退后端截取
        
        需求: 4.2 - 如果重新初始化失败，回退到 GDI 截取
        需求: 4.3 - 记录截取错误及诊断信息
        
        参数:
            区域: 截取区域
            
        返回:
            截取的图像，失败返回 None
        """
        日志.warning(f"主截取器 ({self._后端类型}) 失败，尝试回退...")
        
        回退后端列表 = ["dxgi", "mss", "gdi", "pil"]
        原后端 = self._后端类型
        
        for 后端 in 回退后端列表:
            if 后端 == self._后端类型:
                continue
            
            try:
                日志.info(f"尝试回退到 {后端} 后端...")
                
                if 后端 == "dxgi":
                    回退截取器 = DXGI截取器()
                    if not 回退截取器.是否已初始化():
                        self._记录错误(f"DXGI 回退初始化失败", "dxgi")
                        continue
                elif 后端 == "mss":
                    回退截取器 = MSS截取器()
                elif 后端 == "gdi":
                    回退截取器 = GDI截取器()
                    if not 回退截取器.是否已初始化():
                        self._记录错误(f"GDI 回退初始化失败", "gdi")
                        continue
                elif 后端 == "pil":
                    回退截取器 = PIL截取器()
                else:
                    continue
                
                图像 = 回退截取器.截取(区域)
                
                if 图像 is not None:
                    # 记录回退历史
                    回退记录 = {
                        '时间': time.strftime('%Y-%m-%d %H:%M:%S'),
                        '失败后端': 原后端,
                        '错误原因': self._最后错误信息,
                        '回退到': 后端
                    }
                    self._回退历史.append(回退记录)
                    
                    日志.info(f"成功回退到 {后端}，从 {原后端} 切换")
                    
                    # 切换到回退后端
                    self._截取器.释放()
                    self._截取器 = 回退截取器
                    self._后端类型 = 后端
                    self._恢复次数 += 1
                    return 图像
                else:
                    self._记录错误(f"{后端} 回退截取返回 None", 后端)
                
            except Exception as e:
                错误信息 = f"回退到 {后端} 失败: {e}"
                self._记录错误(错误信息, 后端)
                日志.warning(错误信息)
                continue
        
        self._最后错误信息 = "所有回退后端都失败"
        日志.error(self._最后错误信息)
        return None
    
    def _记录错误(self, 错误信息: str, 后端: str = ""):
        """
        记录错误信息
        
        需求: 4.3 - 记录截取错误及诊断信息
        
        参数:
            错误信息: 错误描述
            后端: 相关后端名称
        """
        self._最后错误信息 = 错误信息
        
        错误记录 = {
            '时间': time.strftime('%Y-%m-%d %H:%M:%S'),
            '后端': 后端,
            '错误信息': 错误信息
        }
        self._错误日志.append(错误记录)
        
        日志.debug(f"错误记录: {错误记录}")
    
    def 获取统计(self) -> 截取统计:
        """
        获取底层截取器的性能统计
        
        返回:
            截取统计对象
        """
        if self._截取器:
            return self._截取器.获取统计()
        return 截取统计()
    
    def 获取当前后端(self) -> str:
        """
        获取当前使用的截取后端
        
        需求: 2.4 - 记录正在使用的截取后端
        
        返回:
            后端名称 ("dxgi", "mss", "gdi", "pil")
        """
        return self._后端类型
    
    def 获取后端类型(self) -> str:
        """
        获取当前后端类型（别名方法）
        
        返回:
            后端名称
        """
        return self._后端类型
    
    def 获取性能统计(self) -> Dict[str, Any]:
        """
        获取截取性能统计
        
        需求: 3.4 - 提供性能指标（截取时间、内存使用）
        需求: 4.3 - 记录截取错误及诊断信息
        
        返回:
            性能统计字典，包含:
            - 后端类型: 当前使用的后端
            - 总截取次数: 成功截取的总次数
            - 总失败次数: 截取失败的总次数
            - 回退次数: 回退到其他后端的次数
            - 恢复次数: 从错误中恢复的次数
            - 平均截取时间: 平均截取时间（毫秒）
            - 最小截取时间: 最小截取时间（毫秒）
            - 最大截取时间: 最大截取时间（毫秒）
            - 成功率: 截取成功率（百分比）
            - 最后错误信息: 最后一次错误的信息
            - 错误日志: 最近的错误记录
            - 回退历史: 回退操作的历史记录
        """
        # 计算截取时间统计
        平均截取时间 = 0.0
        最小截取时间 = 0.0
        最大截取时间 = 0.0
        
        if self._截取时间记录:
            时间列表 = list(self._截取时间记录)
            平均截取时间 = np.mean(时间列表)
            最小截取时间 = np.min(时间列表)
            最大截取时间 = np.max(时间列表)
        
        # 计算成功率
        总尝试次数 = self._总截取次数 + self._总失败次数
        成功率 = (self._总截取次数 / 总尝试次数 * 100) if 总尝试次数 > 0 else 100.0
        
        # 获取底层截取器的统计
        底层统计 = {}
        if self._截取器:
            底层统计 = self._截取器.获取统计().to_dict()
        
        return {
            '后端类型': self._后端类型,
            '总截取次数': self._总截取次数,
            '总失败次数': self._总失败次数,
            '回退次数': self._回退次数,
            '恢复次数': self._恢复次数,
            '平均截取时间': round(平均截取时间, 2),
            '最小截取时间': round(最小截取时间, 2),
            '最大截取时间': round(最大截取时间, 2),
            '成功率': round(成功率, 2),
            '底层统计': 底层统计,
            '最后错误信息': self._最后错误信息,
            '错误日志数量': len(self._错误日志),
            '回退历史数量': len(self._回退历史)
        }
    
    def 获取错误日志(self) -> List[Dict[str, Any]]:
        """
        获取错误日志
        
        需求: 4.3 - 记录截取错误及诊断信息
        
        返回:
            错误日志列表
        """
        return list(self._错误日志)
    
    def 获取回退历史(self) -> List[Dict[str, Any]]:
        """
        获取回退历史
        
        需求: 4.3 - 记录截取错误及诊断信息
        
        返回:
            回退历史列表
        """
        return self._回退历史.copy()
    
    def 获取最后错误信息(self) -> str:
        """
        获取最后一次错误的信息
        
        需求: 4.3 - 记录截取错误及诊断信息
        
        返回:
            错误信息字符串
        """
        return self._最后错误信息
    
    def 获取诊断信息(self) -> Dict[str, Any]:
        """
        获取完整的诊断信息
        
        需求: 4.3 - 记录截取错误及诊断信息
        
        返回:
            诊断信息字典
        """
        诊断信息 = {
            '当前后端': self._后端类型,
            '首选后端': self._首选后端,
            '回退启用': self._回退启用,
            '性能监控启用': self._启用性能监控,
            '性能统计': self.获取性能统计(),
            '错误日志': self.获取错误日志(),
            '回退历史': self.获取回退历史(),
            '系统信息': 后端检测器.获取系统图形信息().to_dict()
        }
        
        # 如果是 DXGI 截取器，获取额外的资源统计
        if self._后端类型 == "dxgi" and isinstance(self._截取器, DXGI截取器):
            诊断信息['DXGI资源统计'] = self._截取器.获取资源统计()
        
        return 诊断信息
    
    def 清除错误日志(self):
        """清除错误日志"""
        self._错误日志.clear()
        self._最后错误信息 = ""
        日志.debug("错误日志已清除")
    
    def 清除回退历史(self):
        """清除回退历史"""
        self._回退历史.clear()
        日志.debug("回退历史已清除")
    
    def 打印统计(self):
        """打印性能统计"""
        统计 = self.获取性能统计()
        print(f"\n屏幕截取统计 ({统计['后端类型']}):")
        print(f"  总截取次数: {统计['总截取次数']}")
        print(f"  总失败次数: {统计['总失败次数']}")
        print(f"  回退次数: {统计['回退次数']}")
        print(f"  恢复次数: {统计['恢复次数']}")
        print(f"  成功率: {统计['成功率']:.2f}%")
        print(f"  平均截取时间: {统计['平均截取时间']:.2f} ms")
        print(f"  最小截取时间: {统计['最小截取时间']:.2f} ms")
        print(f"  最大截取时间: {统计['最大截取时间']:.2f} ms")
        
        # 打印错误信息（如果有）
        if 统计['最后错误信息']:
            print(f"  最后错误: {统计['最后错误信息']}")
        if 统计['错误日志数量'] > 0:
            print(f"  错误日志数量: {统计['错误日志数量']}")
        if 统计['回退历史数量'] > 0:
            print(f"  回退历史数量: {统计['回退历史数量']}")
    
    def 打印诊断信息(self):
        """
        打印完整的诊断信息
        
        需求: 4.3 - 记录截取错误及诊断信息
        """
        诊断 = self.获取诊断信息()
        
        print("\n" + "=" * 50)
        print("屏幕截取诊断信息")
        print("=" * 50)
        
        print(f"\n当前后端: {诊断['当前后端']}")
        print(f"首选后端: {诊断['首选后端']}")
        print(f"回退启用: {'是' if 诊断['回退启用'] else '否'}")
        print(f"性能监控: {'是' if 诊断['性能监控启用'] else '否'}")
        
        print("\n--- 性能统计 ---")
        统计 = 诊断['性能统计']
        print(f"  成功率: {统计['成功率']:.2f}%")
        print(f"  平均截取时间: {统计['平均截取时间']:.2f} ms")
        
        if 诊断['错误日志']:
            print("\n--- 最近错误 ---")
            for 错误 in list(诊断['错误日志'])[-5:]:  # 只显示最近5条
                print(f"  [{错误['时间']}] {错误['后端']}: {错误['错误信息']}")
        
        if 诊断['回退历史']:
            print("\n--- 回退历史 ---")
            for 记录 in 诊断['回退历史'][-5:]:  # 只显示最近5条
                print(f"  [{记录['时间']}] {记录['失败后端']} -> {记录['回退到']}")
        
        print("\n--- 系统信息 ---")
        系统 = 诊断['系统信息']
        print(f"  操作系统: {系统['操作系统']} {系统['操作系统版本']}")
        print(f"  DXGI 可用: {'是' if 系统['DXGI可用'] else '否'}")
        print(f"  可用后端: {', '.join(系统['可用后端'])}")
        
        print("=" * 50)
    
    def 重置统计(self):
        """重置性能统计"""
        self._总截取次数 = 0
        self._总失败次数 = 0
        self._回退次数 = 0
        self._恢复次数 = 0
        self._截取时间记录.clear()
        日志.debug("性能统计已重置")
    
    def 设置回退启用(self, 启用: bool):
        """设置是否启用回退机制"""
        self._回退启用 = 启用
        日志.debug(f"回退机制已{'启用' if 启用 else '禁用'}")
    
    def 设置性能监控(self, 启用: bool):
        """设置是否启用性能监控"""
        self._启用性能监控 = 启用
        日志.debug(f"性能监控已{'启用' if 启用 else '禁用'}")
    
    def 释放(self):
        """释放资源"""
        if self._截取器:
            self._截取器.释放()
            self._截取器 = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.释放()
        return False


# 兼容性别名
优化截取器 = 屏幕截取器


# 测试代码
if __name__ == "__main__":
    print("=" * 50)
    print("屏幕截取优化模块测试")
    print("=" * 50)
    
    # 测试后端检测器
    print("\n1. 测试后端检测器")
    后端检测器.打印系统信息()
    
    # 获取详细信息
    信息 = 后端检测器.获取系统图形信息()
    print(f"\n系统信息字典: {信息.to_dict()}")
    
    # 测试各后端可用性
    print("\n2. 测试各后端可用性")
    print(f"  DXGI 可用: {后端检测器.检测DXGI可用()}")
    print(f"  MSS 可用: {后端检测器.检测MSS可用()}")
    print(f"  GDI 可用: {后端检测器.检测GDI可用()}")
    print(f"  PIL 可用: {后端检测器.检测PIL可用()}")
    print(f"  可用后端列表: {后端检测器.获取可用后端列表()}")
    print(f"  最佳后端: {后端检测器.获取最佳后端()}")
    
    # 测试 DXGI 截取器（如果可用）
    print("\n3. 测试 DXGI 截取器")
    if 后端检测器.检测DXGI可用():
        try:
            dxgi = DXGI截取器()
            if dxgi.是否已初始化():
                print(f"  DXGI 后端类型: {dxgi.获取后端类型()}")
                print(f"  屏幕尺寸: {dxgi.获取屏幕尺寸()}")
                
                # 执行几次截取
                for i in range(5):
                    图像 = dxgi.截取()
                    if 图像 is not None:
                        print(f"  截取 {i+1}: 成功, 尺寸 {图像.shape}")
                    else:
                        print(f"  截取 {i+1}: 失败")
                
                # 测试区域截取
                print("\n  测试区域截取:")
                区域图像 = dxgi.截取((100, 100, 200, 200))
                if 区域图像 is not None:
                    print(f"  区域截取: 成功, 尺寸 {区域图像.shape}")
                else:
                    print(f"  区域截取: 失败")
                
                # 测试多次相同区域截取（测试缓冲区重用）
                print("\n  测试缓冲区重用:")
                for i in range(3):
                    区域图像 = dxgi.截取((100, 100, 200, 200))
                
                # 打印资源统计
                资源统计 = dxgi.获取资源统计()
                print(f"  资源统计: {资源统计}")
                
                # 打印统计
                统计 = dxgi.获取统计()
                print(f"\n  DXGI 统计:")
                print(f"    截取次数: {统计.截取次数}")
                print(f"    平均延迟: {统计.平均延迟:.2f} ms")
                
                dxgi.释放()
                print(f"\n  资源释放后状态: 已初始化={dxgi.是否已初始化()}")
            else:
                print("  DXGI 截取器初始化失败")
        except Exception as e:
            print(f"  DXGI 截取器测试失败: {e}")
    else:
        print("  DXGI 不可用，跳过测试")
    
    # 测试屏幕截取器
    print("\n4. 测试屏幕截取器")
    try:
        with 屏幕截取器() as 截取器:
            print(f"  当前后端: {截取器.获取后端类型()}")
            
            # 执行几次截取
            for i in range(5):
                图像 = 截取器.截取()
                if 图像 is not None:
                    print(f"  截取 {i+1}: 成功, 尺寸 {图像.shape}")
                else:
                    print(f"  截取 {i+1}: 失败")
            
            # 打印统计
            截取器.打印统计()
            
    except Exception as e:
        print(f"  截取器测试失败: {e}")
    
    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)
