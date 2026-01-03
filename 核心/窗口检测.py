"""
自动窗口检测模块
自动检测和跟踪游戏窗口

功能:
- 按进程名/标题查找窗口
- 窗口位置跟踪
- 点击选择模式
- 配置保存和加载
"""

import os
import json
import time
import ctypes
import threading
from typing import Dict, List, Optional, Tuple, Callable, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
日志 = logging.getLogger(__name__)

# Windows API 常量
GWL_STYLE = -16
WS_VISIBLE = 0x10000000
WS_MINIMIZE = 0x20000000
DWMWA_EXTENDED_FRAME_BOUNDS = 9


@dataclass
class 窗口信息:
    """窗口信息数据类"""
    句柄: int
    标题: str
    进程名: str
    进程ID: int
    位置: Tuple[int, int]  # (x, y)
    大小: Tuple[int, int]  # (width, height)
    是否可见: bool = True
    是否最小化: bool = False
    
    def 获取区域(self) -> Tuple[int, int, int, int]:
        """获取截取区域 (x, y, width, height)"""
        return (self.位置[0], self.位置[1], self.大小[0], self.大小[1])
    
    def to_dict(self) -> dict:
        return asdict(self)


class 窗口查找器:
    """查找和定位游戏窗口"""
    
    def __init__(self):
        self._user32 = ctypes.windll.user32
        self._kernel32 = ctypes.windll.kernel32
        self._psapi = ctypes.windll.psapi
    
    def 按进程名查找(self, 进程名: str) -> List[窗口信息]:
        """
        通过进程名查找窗口
        
        参数:
            进程名: 进程名称（如 "game.exe"）
            
        返回:
            匹配的窗口信息列表
        """
        所有窗口 = self.获取所有窗口()
        进程名小写 = 进程名.lower()
        
        匹配窗口 = [w for w in 所有窗口 if 进程名小写 in w.进程名.lower()]
        return 匹配窗口
    
    def 按标题查找(self, 标题: str, 模糊匹配: bool = True) -> List[窗口信息]:
        """
        通过窗口标题查找窗口
        
        参数:
            标题: 窗口标题（支持部分匹配）
            模糊匹配: 是否启用模糊匹配
            
        返回:
            匹配的窗口信息列表
        """
        所有窗口 = self.获取所有窗口()
        标题小写 = 标题.lower()
        
        if 模糊匹配:
            匹配窗口 = [w for w in 所有窗口 if 标题小写 in w.标题.lower()]
        else:
            匹配窗口 = [w for w in 所有窗口 if w.标题.lower() == 标题小写]
        
        return 匹配窗口
    
    def 获取所有窗口(self, 仅可见: bool = True) -> List[窗口信息]:
        """
        获取所有窗口列表
        
        参数:
            仅可见: 是否只返回可见窗口
            
        返回:
            窗口信息列表
        """
        窗口列表 = []
        
        def 枚举回调(句柄, _):
            try:
                信息 = self.获取窗口信息(句柄)
                if 信息:
                    if not 仅可见 or 信息.是否可见:
                        窗口列表.append(信息)
            except:
                pass
            return True
        
        枚举函数类型 = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
        self._user32.EnumWindows(枚举函数类型(枚举回调), 0)
        
        return 窗口列表
    
    def 获取窗口信息(self, 句柄: int) -> Optional[窗口信息]:
        """
        获取指定窗口的详细信息
        
        参数:
            句柄: 窗口句柄
            
        返回:
            窗口信息，无效句柄返回 None
        """
        if not self._user32.IsWindow(句柄):
            return None
        
        # 获取标题
        长度 = self._user32.GetWindowTextLengthW(句柄) + 1
        缓冲区 = ctypes.create_unicode_buffer(长度)
        self._user32.GetWindowTextW(句柄, 缓冲区, 长度)
        标题 = 缓冲区.value
        
        # 跳过无标题窗口
        if not 标题:
            return None
        
        # 获取进程信息
        进程ID = ctypes.c_ulong()
        self._user32.GetWindowThreadProcessId(句柄, ctypes.byref(进程ID))
        进程名 = self._获取进程名(进程ID.value)
        
        # 获取窗口位置和大小
        矩形 = ctypes.wintypes.RECT()
        self._user32.GetWindowRect(句柄, ctypes.byref(矩形))
        
        位置 = (矩形.left, 矩形.top)
        大小 = (矩形.right - 矩形.left, 矩形.bottom - 矩形.top)
        
        # 检查可见性
        样式 = self._user32.GetWindowLongW(句柄, GWL_STYLE)
        是否可见 = bool(样式 & WS_VISIBLE)
        是否最小化 = bool(样式 & WS_MINIMIZE)
        
        return 窗口信息(
            句柄=句柄, 标题=标题, 进程名=进程名,
            进程ID=进程ID.value, 位置=位置, 大小=大小,
            是否可见=是否可见, 是否最小化=是否最小化
        )

    def _获取进程名(self, 进程ID: int) -> str:
        """获取进程名称"""
        try:
            PROCESS_QUERY_INFORMATION = 0x0400
            PROCESS_VM_READ = 0x0010
            
            进程句柄 = self._kernel32.OpenProcess(
                PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, 进程ID
            )
            
            if 进程句柄:
                缓冲区 = ctypes.create_unicode_buffer(260)
                self._psapi.GetModuleBaseNameW(进程句柄, None, 缓冲区, 260)
                self._kernel32.CloseHandle(进程句柄)
                return 缓冲区.value or "未知"
        except:
            pass
        return "未知"
    
    def 获取前台窗口(self) -> Optional[窗口信息]:
        """获取当前前台窗口"""
        句柄 = self._user32.GetForegroundWindow()
        return self.获取窗口信息(句柄)
    
    def 获取鼠标位置窗口(self) -> Optional[窗口信息]:
        """获取鼠标位置下的窗口"""
        点 = ctypes.wintypes.POINT()
        self._user32.GetCursorPos(ctypes.byref(点))
        句柄 = self._user32.WindowFromPoint(点)
        
        # 获取顶层窗口
        顶层句柄 = self._user32.GetAncestor(句柄, 2)  # GA_ROOT = 2
        return self.获取窗口信息(顶层句柄 or 句柄)


class 窗口跟踪器:
    """跟踪窗口位置变化"""
    
    def __init__(self, 句柄: int, 回调: Callable[[窗口信息], None] = None):
        """
        初始化跟踪器
        
        参数:
            句柄: 要跟踪的窗口句柄
            回调: 位置变化时的回调函数
        """
        self._句柄 = 句柄
        self._回调 = 回调
        self._查找器 = 窗口查找器()
        self._运行中 = False
        self._线程: Optional[threading.Thread] = None
        self._上次位置: Optional[Tuple[int, int, int, int]] = None
        self._检查间隔 = 0.5  # 秒
    
    def 启动(self):
        """启动位置跟踪（后台线程）"""
        if self._运行中:
            return
        
        self._运行中 = True
        self._线程 = threading.Thread(target=self._跟踪循环, daemon=True)
        self._线程.start()
        日志.info(f"窗口跟踪已启动: 句柄={self._句柄}")
    
    def 停止(self):
        """停止位置跟踪"""
        self._运行中 = False
        if self._线程:
            self._线程.join(timeout=1.0)
        日志.info("窗口跟踪已停止")
    
    def _跟踪循环(self):
        """跟踪循环"""
        while self._运行中:
            try:
                信息 = self._查找器.获取窗口信息(self._句柄)
                
                if 信息 is None:
                    日志.warning("跟踪的窗口已关闭")
                    self._运行中 = False
                    break
                
                当前位置 = 信息.获取区域()
                
                if self._上次位置 != 当前位置:
                    self._上次位置 = 当前位置
                    if self._回调:
                        self._回调(信息)
                
                time.sleep(self._检查间隔)
                
            except Exception as e:
                日志.error(f"跟踪错误: {e}")
                time.sleep(1.0)
    
    def 获取当前位置(self) -> Optional[Tuple[int, int, int, int]]:
        """获取窗口当前位置 (x, y, width, height)"""
        信息 = self._查找器.获取窗口信息(self._句柄)
        if 信息:
            return 信息.获取区域()
        return None
    
    def 窗口是否存在(self) -> bool:
        """检查窗口是否仍然存在"""
        return ctypes.windll.user32.IsWindow(self._句柄) != 0
    
    def 窗口是否移动(self) -> bool:
        """检查窗口是否移动"""
        当前位置 = self.获取当前位置()
        if 当前位置 and self._上次位置:
            return 当前位置[:2] != self._上次位置[:2]
        return False


class 窗口选择器:
    """窗口选择界面"""
    
    def __init__(self, 查找器: 窗口查找器 = None):
        self._查找器 = 查找器 or 窗口查找器()
    
    def 显示列表(self, 过滤关键词: str = None) -> Optional[int]:
        """
        显示窗口列表供用户选择
        
        参数:
            过滤关键词: 过滤窗口的关键词
            
        返回:
            选中的窗口句柄，取消返回 None
        """
        窗口列表 = self._查找器.获取所有窗口()
        
        # 过滤
        if 过滤关键词:
            关键词小写 = 过滤关键词.lower()
            窗口列表 = [w for w in 窗口列表 
                       if 关键词小写 in w.标题.lower() or 关键词小写 in w.进程名.lower()]
        
        if not 窗口列表:
            print("❌ 未找到匹配的窗口")
            return None
        
        print("\n" + "=" * 60)
        print("🪟 可用窗口列表")
        print("=" * 60)
        
        for i, 窗口 in enumerate(窗口列表, 1):
            状态 = "🔲" if 窗口.是否最小化 else "🟢"
            print(f"  {i:2d}. {状态} {窗口.标题[:30]:<30s}")
            print(f"      进程: {窗口.进程名}, 大小: {窗口.大小[0]}x{窗口.大小[1]}")
        
        print("=" * 60)
        print("  0. 取消选择")
        
        try:
            选择 = input("\n请输入窗口编号: ").strip()
            索引 = int(选择) - 1
            
            if 索引 == -1:
                return None
            
            if 0 <= 索引 < len(窗口列表):
                选中窗口 = 窗口列表[索引]
                print(f"\n✅ 已选择: {选中窗口.标题}")
                return 选中窗口.句柄
            else:
                print("❌ 无效的选择")
                return None
                
        except ValueError:
            print("❌ 请输入有效的数字")
            return None
    
    def 点击选择模式(self, 倒计时: int = 3) -> Optional[int]:
        """
        启动点击选择模式
        
        参数:
            倒计时: 进入选择模式前的倒计时秒数
            
        返回:
            选中的窗口句柄
        """
        print("\n🖱️ 点击选择模式")
        print(f"   请在 {倒计时} 秒后点击要选择的窗口...")
        
        for i in range(倒计时, 0, -1):
            print(f"   {i}...", end=" ", flush=True)
            time.sleep(1)
        
        print("\n   请点击目标窗口!")
        
        # 等待用户点击
        time.sleep(0.5)
        
        # 获取前台窗口
        窗口 = self._查找器.获取前台窗口()
        
        if 窗口:
            print(f"\n✅ 已选择: {窗口.标题}")
            print(f"   进程: {窗口.进程名}")
            print(f"   位置: {窗口.位置}, 大小: {窗口.大小}")
            return 窗口.句柄
        
        print("❌ 未能获取窗口信息")
        return None
    
    def 确认选择(self, 句柄: int) -> bool:
        """确认窗口选择"""
        信息 = self._查找器.获取窗口信息(句柄)
        
        if not 信息:
            print("❌ 窗口不存在")
            return False
        
        print(f"\n确认选择以下窗口?")
        print(f"  标题: {信息.标题}")
        print(f"  进程: {信息.进程名}")
        print(f"  大小: {信息.大小[0]}x{信息.大小[1]}")
        
        确认 = input("\n确认? (y/n): ").strip().lower()
        return 确认 == 'y'


class 窗口配置管理器:
    """管理窗口配置的保存和加载"""
    
    def __init__(self, 配置路径: str = "配置/窗口配置.json"):
        self._配置路径 = 配置路径
        self._配置: Dict = {"默认": None, "配置列表": {}}
        self._加载配置文件()
    
    def _加载配置文件(self):
        """加载配置文件"""
        if os.path.exists(self._配置路径):
            try:
                with open(self._配置路径, 'r', encoding='utf-8') as f:
                    self._配置 = json.load(f)
            except Exception as e:
                日志.warning(f"加载窗口配置失败: {e}")
    
    def _保存配置文件(self):
        """保存配置文件"""
        try:
            os.makedirs(os.path.dirname(self._配置路径), exist_ok=True)
            with open(self._配置路径, 'w', encoding='utf-8') as f:
                json.dump(self._配置, f, ensure_ascii=False, indent=2)
        except Exception as e:
            日志.error(f"保存窗口配置失败: {e}")
    
    def 保存配置(self, 窗口标识: str, 窗口信息: 窗口信息):
        """
        保存窗口配置
        
        参数:
            窗口标识: 窗口标识符（进程名或标题）
            窗口信息: 窗口信息对象
        """
        配置项 = {
            "标识类型": "process" if 窗口标识 == 窗口信息.进程名 else "title",
            "标识值": 窗口标识,
            "上次位置": list(窗口信息.获取区域()),
            "进程名": 窗口信息.进程名,
            "标题": 窗口信息.标题,
            "上次使用": datetime.now().isoformat()
        }
        
        self._配置["配置列表"][窗口标识] = 配置项
        self._保存配置文件()
        日志.info(f"窗口配置已保存: {窗口标识}")
    
    def 加载配置(self, 窗口标识: str = None) -> Optional[Dict]:
        """
        加载窗口配置
        
        参数:
            窗口标识: 窗口标识符，None 表示加载默认配置
            
        返回:
            窗口配置字典
        """
        if 窗口标识 is None:
            窗口标识 = self._配置.get("默认")
        
        if 窗口标识 is None:
            return None
        
        return self._配置.get("配置列表", {}).get(窗口标识)
    
    def 获取所有配置(self) -> List[Dict]:
        """获取所有保存的窗口配置"""
        配置列表 = []
        for 标识, 配置 in self._配置.get("配置列表", {}).items():
            配置["标识"] = 标识
            配置列表.append(配置)
        return 配置列表
    
    def 删除配置(self, 窗口标识: str):
        """删除指定窗口配置"""
        if 窗口标识 in self._配置.get("配置列表", {}):
            del self._配置["配置列表"][窗口标识]
            if self._配置.get("默认") == 窗口标识:
                self._配置["默认"] = None
            self._保存配置文件()
            日志.info(f"窗口配置已删除: {窗口标识}")
    
    def 设置默认(self, 窗口标识: str):
        """设置默认窗口配置"""
        if 窗口标识 in self._配置.get("配置列表", {}):
            self._配置["默认"] = 窗口标识
            self._保存配置文件()
            日志.info(f"默认窗口已设置: {窗口标识}")


class 自动窗口检测器:
    """自动窗口检测的统一接口"""
    
    def __init__(self, 配置路径: str = "配置/窗口配置.json"):
        self._查找器 = 窗口查找器()
        self._选择器 = 窗口选择器(self._查找器)
        self._配置管理器 = 窗口配置管理器(配置路径)
        self._跟踪器: Optional[窗口跟踪器] = None
        self._当前窗口: Optional[窗口信息] = None
    
    def 自动检测(self, 进程名: str = None, 标题: str = None) -> Optional[窗口信息]:
        """
        自动检测游戏窗口
        
        参数:
            进程名: 进程名称
            标题: 窗口标题
            
        返回:
            检测到的窗口信息
        """
        # 尝试从配置加载
        配置 = self._配置管理器.加载配置()
        if 配置:
            标识值 = 配置.get("标识值")
            标识类型 = 配置.get("标识类型")
            
            if 标识类型 == "process":
                窗口列表 = self._查找器.按进程名查找(标识值)
            else:
                窗口列表 = self._查找器.按标题查找(标识值)
            
            if 窗口列表:
                self._当前窗口 = 窗口列表[0]
                日志.info(f"从配置加载窗口: {self._当前窗口.标题}")
                return self._当前窗口
        
        # 按参数查找
        if 进程名:
            窗口列表 = self._查找器.按进程名查找(进程名)
            if 窗口列表:
                self._当前窗口 = 窗口列表[0]
                return self._当前窗口
        
        if 标题:
            窗口列表 = self._查找器.按标题查找(标题)
            if 窗口列表:
                self._当前窗口 = 窗口列表[0]
                return self._当前窗口
        
        return None
    
    def 手动选择(self, 过滤关键词: str = None) -> Optional[窗口信息]:
        """手动选择窗口"""
        句柄 = self._选择器.显示列表(过滤关键词)
        
        if 句柄:
            self._当前窗口 = self._查找器.获取窗口信息(句柄)
            return self._当前窗口
        
        return None
    
    def 点击选择(self) -> Optional[窗口信息]:
        """点击选择窗口"""
        句柄 = self._选择器.点击选择模式()
        
        if 句柄:
            self._当前窗口 = self._查找器.获取窗口信息(句柄)
            return self._当前窗口
        
        return None
    
    def 启动跟踪(self, 回调: Callable[[窗口信息], None] = None):
        """启动窗口位置跟踪"""
        if self._当前窗口 is None:
            日志.warning("未选择窗口，无法启动跟踪")
            return
        
        self.停止跟踪()
        self._跟踪器 = 窗口跟踪器(self._当前窗口.句柄, 回调)
        self._跟踪器.启动()
    
    def 停止跟踪(self):
        """停止窗口位置跟踪"""
        if self._跟踪器:
            self._跟踪器.停止()
            self._跟踪器 = None
    
    def 保存当前配置(self, 使用进程名: bool = True):
        """保存当前窗口配置"""
        if self._当前窗口 is None:
            日志.warning("未选择窗口，无法保存配置")
            return
        
        标识 = self._当前窗口.进程名 if 使用进程名 else self._当前窗口.标题
        self._配置管理器.保存配置(标识, self._当前窗口)
        self._配置管理器.设置默认(标识)
    
    def 获取截取区域(self) -> Optional[Tuple[int, int, int, int]]:
        """获取当前窗口的截取区域"""
        if self._当前窗口:
            # 如果有跟踪器，获取最新位置
            if self._跟踪器:
                位置 = self._跟踪器.获取当前位置()
                if 位置:
                    return 位置
            return self._当前窗口.获取区域()
        return None
    
    def 获取当前窗口(self) -> Optional[窗口信息]:
        """获取当前选中的窗口"""
        return self._当前窗口


def 主程序():
    """主程序入口"""
    print("\n" + "=" * 50)
    print("🪟 自动窗口检测工具")
    print("=" * 50)
    
    检测器 = 自动窗口检测器()
    
    print("\n请选择功能:")
    print("  1. 列表选择窗口")
    print("  2. 点击选择窗口")
    print("  3. 按进程名查找")
    print("  4. 查看已保存配置")
    
    选择 = input("\n请输入选项 (1/2/3/4): ").strip()
    
    if 选择 == '1':
        关键词 = input("输入过滤关键词 (留空显示全部): ").strip()
        窗口 = 检测器.手动选择(关键词 if 关键词 else None)
        if 窗口:
            保存 = input("\n是否保存配置? (y/n): ").strip().lower()
            if 保存 == 'y':
                检测器.保存当前配置()
    
    elif 选择 == '2':
        窗口 = 检测器.点击选择()
        if 窗口:
            保存 = input("\n是否保存配置? (y/n): ").strip().lower()
            if 保存 == 'y':
                检测器.保存当前配置()
    
    elif 选择 == '3':
        进程名 = input("输入进程名: ").strip()
        窗口 = 检测器.自动检测(进程名=进程名)
        if 窗口:
            print(f"\n✅ 找到窗口: {窗口.标题}")
        else:
            print("❌ 未找到匹配的窗口")
    
    elif 选择 == '4':
        配置列表 = 检测器._配置管理器.获取所有配置()
        if 配置列表:
            print("\n已保存的窗口配置:")
            for 配置 in 配置列表:
                print(f"  - {配置.get('标识')}: {配置.get('标题', '未知')}")
        else:
            print("❌ 没有保存的配置")


if __name__ == "__main__":
    主程序()
