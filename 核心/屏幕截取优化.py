"""
屏幕截取优化模块
提供高性能的屏幕截取功能

功能:
- DXGI 截取（Windows）
- GDI 截取（回退）
- 自动后端选择
- 性能统计
"""

import time
import ctypes
from typing import Tuple, Optional, Dict, Any
from dataclasses import dataclass
from collections import deque
import numpy as np
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
日志 = logging.getLogger(__name__)


@dataclass
class 截取统计:
    """截取性能统计"""
    平均延迟: float = 0.0  # 毫秒
    最小延迟: float = 0.0
    最大延迟: float = 0.0
    截取次数: int = 0
    后端类型: str = ""
    
    def to_dict(self) -> dict:
        return {
            '平均延迟': round(self.平均延迟, 2),
            '最小延迟': round(self.最小延迟, 2),
            '最大延迟': round(self.最大延迟, 2),
            '截取次数': self.截取次数,
            '后端类型': self.后端类型
        }


class 后端检测器:
    """检测可用的截取后端"""
    
    @staticmethod
    def 检测DXGI可用() -> bool:
        """检测 DXGI 是否可用"""
        try:
            import d3dshot
            return True
        except ImportError:
            return False
    
    @staticmethod
    def 检测MSS可用() -> bool:
        """检测 MSS 是否可用"""
        try:
            import mss
            return True
        except ImportError:
            return False
    
    @staticmethod
    def 检测PIL可用() -> bool:
        """检测 PIL 是否可用"""
        try:
            from PIL import ImageGrab
            return True
        except ImportError:
            return False
    
    @staticmethod
    def 获取最佳后端() -> str:
        """获取最佳可用后端"""
        if 后端检测器.检测DXGI可用():
            return "dxgi"
        elif 后端检测器.检测MSS可用():
            return "mss"
        elif 后端检测器.检测PIL可用():
            return "pil"
        else:
            return "none"


class 截取器基类:
    """截取器基类"""
    
    def __init__(self):
        self._延迟记录: deque = deque(maxlen=100)
        self._截取次数: int = 0
    
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
            return 截取统计(后端类型=self.__class__.__name__)
        
        延迟列表 = list(self._延迟记录)
        return 截取统计(
            平均延迟=np.mean(延迟列表),
            最小延迟=np.min(延迟列表),
            最大延迟=np.max(延迟列表),
            截取次数=self._截取次数,
            后端类型=self.__class__.__name__
        )
    
    def _记录延迟(self, 延迟: float):
        """记录延迟"""
        self._延迟记录.append(延迟)
        self._截取次数 += 1
    
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


class 屏幕截取器:
    """统一的屏幕截取接口"""
    
    def __init__(self, 首选后端: str = "auto"):
        """
        初始化屏幕截取器
        
        参数:
            首选后端: "auto", "dxgi", "mss", "pil"
        """
        self._截取器: Optional[截取器基类] = None
        self._后端类型: str = ""
        self._回退启用: bool = True
        
        self._初始化后端(首选后端)
    
    def _初始化后端(self, 首选后端: str):
        """初始化截取后端"""
        if 首选后端 == "auto":
            首选后端 = 后端检测器.获取最佳后端()
        
        日志.info(f"尝试初始化截取后端: {首选后端}")
        
        try:
            if 首选后端 == "mss":
                self._截取器 = MSS截取器()
                self._后端类型 = "mss"
            elif 首选后端 == "pil":
                self._截取器 = PIL截取器()
                self._后端类型 = "pil"
            else:
                # 尝试 MSS 作为默认
                try:
                    self._截取器 = MSS截取器()
                    self._后端类型 = "mss"
                except:
                    self._截取器 = PIL截取器()
                    self._后端类型 = "pil"
            
            日志.info(f"截取后端初始化成功: {self._后端类型}")
            
        except Exception as e:
            日志.error(f"截取后端初始化失败: {e}")
            raise
    
    def 截取(self, 区域: Tuple[int, int, int, int] = None) -> Optional[np.ndarray]:
        """
        截取屏幕
        
        参数:
            区域: (x, y, width, height)，None 表示全屏
            
        返回:
            截取的图像 (BGR 格式)
        """
        if self._截取器 is None:
            日志.error("截取器未初始化")
            return None
        
        图像 = self._截取器.截取(区域)
        
        # 如果失败且启用回退，尝试其他后端
        if 图像 is None and self._回退启用:
            图像 = self._尝试回退截取(区域)
        
        return 图像
    
    def _尝试回退截取(self, 区域: Tuple[int, int, int, int] = None) -> Optional[np.ndarray]:
        """尝试使用回退后端截取"""
        日志.warning("主截取器失败，尝试回退...")
        
        回退后端列表 = ["mss", "pil"]
        
        for 后端 in 回退后端列表:
            if 后端 == self._后端类型:
                continue
            
            try:
                if 后端 == "mss":
                    回退截取器 = MSS截取器()
                elif 后端 == "pil":
                    回退截取器 = PIL截取器()
                else:
                    continue
                
                图像 = 回退截取器.截取(区域)
                
                if 图像 is not None:
                    日志.info(f"回退到 {后端} 成功")
                    # 切换到回退后端
                    self._截取器.释放()
                    self._截取器 = 回退截取器
                    self._后端类型 = 后端
                    return 图像
                
            except Exception as e:
                日志.warning(f"回退到 {后端} 失败: {e}")
                continue
        
        return None
    
    def 获取统计(self) -> 截取统计:
        """获取性能统计"""
        if self._截取器:
            return self._截取器.获取统计()
        return 截取统计()
    
    def 获取后端类型(self) -> str:
        """获取当前后端类型"""
        return self._后端类型
    
    def 打印统计(self):
        """打印性能统计"""
        统计 = self.获取统计()
        print(f"\n屏幕截取统计 ({统计.后端类型}):")
        print(f"  截取次数: {统计.截取次数}")
        print(f"  平均延迟: {统计.平均延迟:.2f} ms")
        print(f"  最小延迟: {统计.最小延迟:.2f} ms")
        print(f"  最大延迟: {统计.最大延迟:.2f} ms")
    
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
