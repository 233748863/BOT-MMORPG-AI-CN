# -*- coding: utf-8 -*-
"""
数据收集后台线程

在后台执行数据收集任务，通过信号与界面通信，
确保界面保持响应。
"""

import os
import sys
import time
import numpy as np
import cv2
from typing import Optional
from pathlib import Path

from PySide6.QtCore import QThread, Signal

# 添加项目根目录到路径
项目根目录 = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if 项目根目录 not in sys.path:
    sys.path.insert(0, 项目根目录)


class 数据收集线程(QThread):
    """
    数据收集后台线程
    
    在后台执行数据收集任务，通过信号更新界面状态。
    """
    
    # 信号定义
    进度更新 = Signal(int, str)  # 进度百分比, 状态消息
    状态更新 = Signal(dict)  # 状态数据字典
    样本收集 = Signal(int, int)  # 样本数量, 文件编号
    帧更新 = Signal(object)  # numpy数组 (帧图像)
    文件保存 = Signal(str, int)  # 文件路径, 样本数
    任务完成 = Signal(bool, str)  # 是否成功, 结果消息
    错误发生 = Signal(str)  # 错误消息
    
    def __init__(self, parent=None):
        """初始化线程"""
        super().__init__(parent)
        
        # 控制标志
        self._停止标志 = False
        self._暂停标志 = False
        
        # 配置
        self._训练模式 = "通用模式"
        
        # 状态
        self._样本数量 = 0
        self._文件编号 = 1
        self._帧率 = 0.0
    
    def 设置训练模式(self, 模式: str) -> None:
        """设置训练模式"""
        self._训练模式 = 模式
    
    def run(self) -> None:
        """线程执行入口"""
        try:
            self._执行数据收集()
        except Exception as e:
            self.错误发生.emit(f"数据收集错误: {str(e)}")
            self.任务完成.emit(False, f"数据收集失败: {str(e)}")
    
    def _执行数据收集(self) -> None:
        """执行数据收集主逻辑"""
        # 导入必要模块
        try:
            from 核心.屏幕截取 import 截取屏幕
            from 核心.按键检测 import 检测按键
            from 配置.设置 import (
                游戏窗口区域, 模型输入宽度, 模型输入高度,
                每文件样本数, 数据保存路径, 总动作数
            )
        except ImportError as e:
            self.错误发生.emit(f"导入模块失败: {str(e)}")
            self.任务完成.emit(False, f"导入模块失败: {str(e)}")
            return
        
        # 确保数据目录存在
        数据目录 = Path(数据保存路径)
        数据目录.mkdir(parents=True, exist_ok=True)
        
        # 获取起始文件编号
        self._文件编号 = self._获取起始文件编号(数据目录)
        文件名 = 数据目录 / f'训练数据-{self._文件编号}.npy'
        
        # 初始化
        训练数据 = []
        self._样本数量 = 0
        上次时间 = time.time()
        帧计数 = 0
        
        self.进度更新.emit(0, "开始数据收集...")
        
        while not self._停止标志:
            # 检查暂停
            if self._暂停标志:
                time.sleep(0.1)
                continue
            
            try:
                # 截取屏幕
                屏幕 = 截取屏幕(region=游戏窗口区域)
                屏幕 = cv2.resize(屏幕, (模型输入宽度, 模型输入高度))
                屏幕_RGB = cv2.cvtColor(屏幕, cv2.COLOR_BGR2RGB)
                
                # 获取输入状态
                按键 = 检测按键()
                鼠标状态 = self._检测鼠标按键()
                修饰键状态 = self._检测修饰键()
                
                # 转换为动作编码
                动作 = self._按键转动作(按键, 鼠标状态, 修饰键状态, 总动作数)
                
                # 添加到训练数据
                训练数据.append([屏幕_RGB, 动作])
                self._样本数量 += 1
                帧计数 += 1
                
                # 计算帧率 (每50帧更新一次)
                if 帧计数 % 50 == 0:
                    当前时间 = time.time()
                    时间差 = 当前时间 - 上次时间
                    if 时间差 > 0:
                        self._帧率 = 50 / 时间差
                    上次时间 = 当前时间
                
                # 获取动作名称
                动作名称 = self._获取动作名称(动作)
                
                # 发送状态更新
                状态数据 = {
                    "样本数量": self._样本数量,
                    "文件编号": self._文件编号,
                    "帧率": self._帧率,
                    "当前动作": 动作名称,
                    "帧图像": 屏幕_RGB,
                }
                self.状态更新.emit(状态数据)
                self.样本收集.emit(self._样本数量, self._文件编号)
                
                # 每10帧发送一次帧更新 (降低频率以减少开销)
                if 帧计数 % 10 == 0:
                    self.帧更新.emit(屏幕_RGB)
                
                # 自动保存
                if len(训练数据) >= 每文件样本数:
                    np.save(str(文件名), 训练数据)
                    self.文件保存.emit(str(文件名), len(训练数据))
                    self.进度更新.emit(100, f"已保存: {文件名}")
                    
                    # 重置
                    训练数据 = []
                    self._文件编号 += 1
                    文件名 = 数据目录 / f'训练数据-{self._文件编号}.npy'
                
                # 短暂休眠以控制帧率
                time.sleep(0.01)
                
            except Exception as e:
                self.错误发生.emit(f"采集帧错误: {str(e)}")
                time.sleep(0.1)
        
        # 保存剩余数据
        if 训练数据:
            np.save(str(文件名), 训练数据)
            self.文件保存.emit(str(文件名), len(训练数据))
        
        self.任务完成.emit(True, f"数据收集完成，共收集 {self._样本数量} 个样本")
    
    def _获取起始文件编号(self, 数据目录: Path) -> int:
        """获取下一个可用的文件编号"""
        编号 = 1
        while True:
            文件名 = 数据目录 / f'训练数据-{编号}.npy'
            if 文件名.exists():
                编号 += 1
            else:
                break
        return 编号
    
    def _检测鼠标按键(self) -> tuple:
        """检测鼠标按键状态"""
        try:
            import win32api
            左键 = win32api.GetAsyncKeyState(0x01) & 0x8000  # VK_LBUTTON
            右键 = win32api.GetAsyncKeyState(0x02) & 0x8000  # VK_RBUTTON
            中键 = win32api.GetAsyncKeyState(0x04) & 0x8000  # VK_MBUTTON
            return 左键, 右键, 中键
        except Exception:
            return False, False, False
    
    def _检测修饰键(self) -> tuple:
        """检测修饰键状态"""
        try:
            import win32api
            shift = win32api.GetAsyncKeyState(0x10) & 0x8000  # VK_SHIFT
            ctrl = win32api.GetAsyncKeyState(0x11) & 0x8000   # VK_CONTROL
            alt = win32api.GetAsyncKeyState(0x12) & 0x8000    # VK_MENU
            return shift, ctrl, alt
        except Exception:
            return False, False, False
    
    def _按键转动作(self, 按键列表: list, 鼠标状态: tuple, 
                   修饰键状态: tuple, 总动作数: int) -> list:
        """将按键转换为动作编码"""
        动作 = [0] * 总动作数
        shift, ctrl, alt = 修饰键状态
        左键, 右键, 中键 = 鼠标状态
        
        # 检测组合键 (优先级最高)
        if shift:
            if '1' in 按键列表:
                动作[25] = 1
                return 动作
            if '2' in 按键列表:
                动作[26] = 1
                return 动作
            if 'Q' in 按键列表:
                动作[27] = 1
                return 动作
            if 'E' in 按键列表:
                动作[28] = 1
                return 动作
        
        if ctrl:
            if '1' in 按键列表:
                动作[29] = 1
                return 动作
            if '2' in 按键列表:
                动作[30] = 1
                return 动作
            if 'Q' in 按键列表:
                动作[31] = 1
                return 动作
        
        # 检测鼠标
        if 左键:
            动作[22] = 1
            return 动作
        if 右键:
            动作[23] = 1
            return 动作
        if 中键:
            动作[24] = 1
            return 动作
        
        # 检测技能键
        技能键映射 = {
            '1': 9, '2': 10, '3': 11, '4': 12, '5': 13, '6': 14,
            'Q': 15, 'E': 16, 'R': 17, 'F': 18
        }
        for 键, 索引 in 技能键映射.items():
            if 键 in 按键列表:
                动作[索引] = 1
                return 动作
        
        # 检测空格
        if ' ' in 按键列表:
            动作[19] = 1
            return 动作
        
        # 检测移动键
        W按下 = 'W' in 按键列表
        A按下 = 'A' in 按键列表
        S按下 = 'S' in 按键列表
        D按下 = 'D' in 按键列表
        
        if W按下 and A按下:
            动作[4] = 1
        elif W按下 and D按下:
            动作[5] = 1
        elif S按下 and A按下:
            动作[6] = 1
        elif S按下 and D按下:
            动作[7] = 1
        elif W按下:
            动作[0] = 1
        elif S按下:
            动作[1] = 1
        elif A按下:
            动作[2] = 1
        elif D按下:
            动作[3] = 1
        else:
            动作[8] = 1  # 无操作
        
        return 动作
    
    def _获取动作名称(self, 动作: list) -> str:
        """根据动作编码获取动作名称"""
        try:
            from 配置.设置 import 动作定义
            索引 = 动作.index(1) if 1 in 动作 else 8
            return 动作定义.get(索引, {}).get("名称", "未知")
        except Exception:
            索引 = 动作.index(1) if 1 in 动作 else 8
            默认名称 = {
                0: "前进", 1: "后退", 2: "左移", 3: "右移",
                4: "前进+左移", 5: "前进+右移", 6: "后退+左移", 7: "后退+右移",
                8: "无操作", 9: "技能1", 10: "技能2", 11: "技能3",
                12: "技能4", 13: "技能5", 14: "技能6",
                15: "Q技能", 16: "E技能", 17: "R技能", 18: "F技能",
                19: "跳跃", 22: "鼠标左键", 23: "鼠标右键", 24: "鼠标中键",
            }
            return 默认名称.get(索引, "未知")
    
    def 请求停止(self) -> None:
        """请求停止线程"""
        self._停止标志 = True
    
    def 切换暂停(self) -> None:
        """切换暂停状态"""
        self._暂停标志 = not self._暂停标志
    
    def 是否暂停(self) -> bool:
        """返回是否处于暂停状态"""
        return self._暂停标志
    
    def 获取样本数量(self) -> int:
        """获取当前样本数量"""
        return self._样本数量
    
    def 获取文件编号(self) -> int:
        """获取当前文件编号"""
        return self._文件编号
