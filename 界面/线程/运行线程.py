# -*- coding: utf-8 -*-
"""
运行后台线程

在后台执行机器人运行任务，通过信号与界面通信，
确保界面保持响应。支持基础模式和增强模式。
"""

import os
import sys
import time
import numpy as np
import cv2
from typing import Optional, List, Dict
from collections import deque
from statistics import mean

from PySide6.QtCore import QThread, Signal

# 添加项目根目录到路径
项目根目录 = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if 项目根目录 not in sys.path:
    sys.path.insert(0, 项目根目录)


class 运行线程(QThread):
    """
    机器人运行后台线程
    
    在后台执行机器人运行任务，通过信号更新界面状态。
    支持基础模式和增强模式。
    """
    
    # 信号定义
    进度更新 = Signal(int, str)  # 进度百分比, 状态消息
    状态更新 = Signal(dict)  # 状态数据字典
    脱困提示 = Signal(str)  # 脱困提示消息
    性能警告 = Signal(float)  # 帧率
    增强模块状态 = Signal(dict)  # 增强模块状态
    任务完成 = Signal(bool, str)  # 是否成功, 结果消息
    错误发生 = Signal(str)  # 错误消息
    
    def __init__(self, parent=None):
        """初始化线程"""
        super().__init__(parent)
        
        # 控制标志
        self._停止标志 = False
        self._暂停标志 = False
        
        # 配置
        self._子模式 = "主线任务"
        self._启用增强 = False
        
        # 基础模型
        self._模型 = None
        self._动作权重 = None
        
        # 增强模块
        self._YOLO检测器 = None
        self._状态识别器 = None
        self._决策引擎 = None
        
        # 模块状态
        self._YOLO可用 = False
        self._状态识别可用 = False
        self._决策引擎可用 = False
        self._已降级 = False
        
        # 运动检测
        self._运动日志 = deque(maxlen=25)
        
        # 性能监控
        self._帧时间日志 = deque(maxlen=30)
        self._当前帧率 = 30.0
        self._检测计数器 = 0
        self._当前检测间隔 = 3
        
        # 缓存
        self._上次检测结果 = []
        self._上次状态 = "未知"
    
    def 设置子模式(self, 模式: str) -> None:
        """设置子模式 (主线任务/自动战斗)"""
        self._子模式 = 模式
    
    def 设置增强模式(self, 启用: bool) -> None:
        """设置是否启用增强模式"""
        self._启用增强 = 启用
    
    def run(self) -> None:
        """线程执行入口"""
        try:
            self._执行运行()
        except Exception as e:
            import traceback
            错误详情 = traceback.format_exc()
            self.错误发生.emit(f"运行错误: {str(e)}\n{错误详情}")
            self.任务完成.emit(False, f"运行失败: {str(e)}")
    
    def _执行运行(self) -> None:
        """执行运行主逻辑"""
        # 导入必要模块
        try:
            from 核心.屏幕截取 import 截取屏幕
            from 核心.动作检测 import 检测动作变化
            from 核心.模型定义 import inception_v3
            from 配置.设置 import (
                游戏窗口区域, 模型输入宽度, 模型输入高度, 学习率,
                模型保存路径, 预训练模型路径, 总动作数, 训练模式,
                运动检测阈值, 运动日志长度, 动作定义
            )
        except ImportError as e:
            self.错误发生.emit(f"导入模块失败: {str(e)}")
            self.任务完成.emit(False, f"导入模块失败: {str(e)}")
            return
        
        # 加载模型
        self.进度更新.emit(10, "加载AI模型...")
        
        if not self._加载模型(模型输入宽度, 模型输入高度, 学习率, 
                           总动作数, 模型保存路径, 预训练模型路径):
            return
        
        # 设置动作权重
        if self._子模式 == '主线任务':
            self._动作权重 = np.array(训练模式.主线任务['动作权重'])
        else:
            self._动作权重 = np.array(训练模式.自动战斗['动作权重'])
        
        # 初始化增强模块
        if self._启用增强:
            self.进度更新.emit(30, "初始化增强模块...")
            self._初始化增强模块()
        
        # 发送增强模块状态
        self.增强模块状态.emit({
            "YOLO": self._YOLO可用,
            "状态识别": self._状态识别可用,
            "决策引擎": self._决策引擎可用,
            "低性能": self._已降级,
        })
        
        self.进度更新.emit(50, "准备运行...")
        
        # 初始化帧缓存
        try:
            屏幕 = 截取屏幕(region=游戏窗口区域)
            屏幕 = cv2.cvtColor(屏幕, cv2.COLOR_BGR2RGB)
            屏幕 = cv2.resize(屏幕, (模型输入宽度, 模型输入高度))
        except Exception as e:
            self.错误发生.emit(f"截取屏幕失败: {str(e)}")
            self.任务完成.emit(False, f"截取屏幕失败: {str(e)}")
            return
        
        前帧 = 屏幕.copy()
        当前帧 = 屏幕.copy()
        后帧 = 屏幕.copy()
        
        self.进度更新.emit(100, "运行中")
        
        # 主循环
        while not self._停止标志:
            # 检查暂停
            if self._暂停标志:
                time.sleep(0.1)
                continue
            
            循环开始时间 = time.time()
            
            try:
                # 截取屏幕
                屏幕 = 截取屏幕(region=游戏窗口区域)
                屏幕RGB = cv2.cvtColor(屏幕, cv2.COLOR_BGR2RGB)
                屏幕缩放 = cv2.resize(屏幕RGB, (模型输入宽度, 模型输入高度))
                
                # 运动检测
                动作量 = 检测动作变化(前帧, 当前帧, 后帧, 屏幕缩放)
                
                # 更新帧缓存
                前帧 = 当前帧
                当前帧 = 后帧
                后帧 = 屏幕缩放.copy()
                后帧 = cv2.blur(后帧, (4, 4))
                
                # 预测动作
                基础动作索引, 模型预测 = self._预测动作(屏幕缩放, 模型输入宽度, 模型输入高度)
                
                # 决策
                增强可用 = self._YOLO可用 or self._状态识别可用 or self._决策引擎可用
                
                if 增强可用 and self._启用增强:
                    动作索引, 动作名称, 来源 = self._增强决策(屏幕, 模型预测, 动作定义)
                else:
                    动作索引 = 基础动作索引
                    动作名称 = 动作定义.get(动作索引, {}).get("名称", f"动作{动作索引}")
                    来源 = "model"
                
                # 执行动作
                self._执行动作(动作索引)
                
                # 记录运动量
                self._运动日志.append(动作量)
                平均运动量 = round(mean(self._运动日志), 3) if self._运动日志 else 0
                
                # 更新性能监控
                循环时间 = time.time() - 循环开始时间
                self._更新性能监控(循环时间)
                
                # 发送状态更新
                状态数据 = {
                    "当前动作": 动作名称,
                    "动作来源": 来源,
                    "游戏状态": self._上次状态,
                    "帧率": self._当前帧率,
                    "运动量": 平均运动量,
                    "增强模块": {
                        "YOLO": self._YOLO可用,
                        "状态识别": self._状态识别可用,
                        "决策引擎": self._决策引擎可用,
                        "低性能": self._已降级,
                    }
                }
                self.状态更新.emit(状态数据)
                
                # 检测是否卡住
                if 平均运动量 < 运动检测阈值 and len(self._运动日志) >= 运动日志长度:
                    self._处理卡住()
                
                # 短暂休眠
                time.sleep(0.01)
                
            except Exception as e:
                self.错误发生.emit(f"运行循环错误: {str(e)}")
                time.sleep(0.1)
        
        # 释放所有按键
        self._释放所有按键()
        
        self.任务完成.emit(True, "机器人已停止")
    
    def _加载模型(self, 宽度: int, 高度: int, 学习率: float,
                 总动作数: int, 模型路径: str, 预训练路径: str) -> bool:
        """加载AI模型"""
        try:
            from 核心.模型定义 import inception_v3
            
            self._模型 = inception_v3(宽度, 高度, 3, 学习率, 输出类别=总动作数)
            
            # 优先加载用户训练的模型
            模型路径列表 = [模型路径, 预训练路径]
            
            for 路径 in 模型路径列表:
                try:
                    if os.path.exists(路径 + '.index') or os.path.exists(路径 + '.meta'):
                        self._模型.load(路径)
                        self.进度更新.emit(20, f"模型加载成功")
                        return True
                except Exception as e:
                    continue
            
            self.错误发生.emit("未找到可用的模型文件")
            self.任务完成.emit(False, "未找到可用的模型文件，请先训练模型")
            return False
            
        except Exception as e:
            self.错误发生.emit(f"加载模型失败: {str(e)}")
            self.任务完成.emit(False, f"加载模型失败: {str(e)}")
            return False
    
    def _初始化增强模块(self) -> None:
        """初始化增强模块"""
        # 初始化YOLO检测器
        try:
            from 核心.目标检测器 import YOLO检测器
            self._YOLO检测器 = YOLO检测器()
            self._YOLO可用 = self._YOLO检测器.是否已加载()
        except Exception as e:
            self._YOLO可用 = False
        
        # 初始化状态识别器
        try:
            from 核心.状态识别器 import 状态识别器
            self._状态识别器 = 状态识别器()
            self._状态识别可用 = True
        except Exception as e:
            self._状态识别可用 = False
        
        # 初始化决策引擎
        try:
            from 核心.决策引擎 import 决策引擎
            from 核心.决策规则 import 加载预定义规则
            
            self._决策引擎 = 决策引擎()
            
            try:
                规则列表 = 加载预定义规则()
                for 规则 in 规则列表:
                    self._决策引擎.添加规则(规则)
            except Exception:
                pass
            
            self._决策引擎可用 = True
        except Exception as e:
            self._决策引擎可用 = False
    
    def _预测动作(self, 屏幕: np.ndarray, 宽度: int, 高度: int) -> tuple:
        """使用基础模型预测动作"""
        预测结果 = self._模型.predict([屏幕.reshape(宽度, 高度, 3)])[0]
        预测结果 = np.round(预测结果, decimals=2)
        
        加权预测 = np.array(预测结果) * self._动作权重
        动作索引 = np.argmax(np.abs(加权预测))
        
        return 动作索引, list(预测结果)
    
    def _增强决策(self, 屏幕: np.ndarray, 模型预测: List[float], 
                 动作定义: dict) -> tuple:
        """使用增强模块进行决策"""
        检测结果列表 = self._上次检测结果
        当前状态 = self._上次状态
        
        # 执行目标检测（按间隔）
        self._检测计数器 += 1
        if self._YOLO可用 and self._检测计数器 >= self._当前检测间隔:
            self._检测计数器 = 0
            try:
                检测结果列表 = self._YOLO检测器.检测(屏幕)
                self._上次检测结果 = 检测结果列表
            except Exception:
                pass
        
        # 执行状态识别
        if self._状态识别可用:
            try:
                状态结果 = self._状态识别器.识别状态(屏幕, 检测结果列表)
                当前状态 = 状态结果.状态.value if hasattr(状态结果.状态, 'value') else str(状态结果.状态)
                self._上次状态 = 当前状态
            except Exception:
                pass
        
        # 使用决策引擎
        if self._决策引擎可用:
            try:
                from 核心.数据类型 import 决策上下文, 实体类型
                
                附近敌人数量 = len([r for r in 检测结果列表 if hasattr(r, '类型') and r.类型 == 实体类型.怪物])
                
                上下文 = 决策上下文(
                    游戏状态=self._上次状态,
                    检测结果=检测结果列表,
                    模型预测=模型预测,
                    血量百分比=1.0,
                    附近敌人数量=附近敌人数量
                )
                
                决策 = self._决策引擎.决策(上下文)
                self._决策引擎.记录动作执行(决策.动作索引)
                
                return 决策.动作索引, 决策.动作名称, 决策.来源
            except Exception:
                pass
        
        # 降级到基础模型
        动作索引 = np.argmax(np.abs(np.array(模型预测) * self._动作权重))
        动作名称 = 动作定义.get(动作索引, {}).get("名称", f"动作{动作索引}")
        return 动作索引, 动作名称, "fallback"

    def _执行动作(self, 动作索引: int) -> None:
        """执行指定动作"""
        try:
            from 核心.键盘控制 import (
                前进, 后退, 左移, 右移,
                前进左移, 前进右移, 后退左移, 后退右移, 无操作,
                技能1, 技能2, 技能3, 技能4, 技能5, 技能6,
                技能Q, 技能E, 技能R, 技能F,
                跳跃, 切换目标, 交互,
                Shift技能1, Shift技能2, Shift技能Q, Shift技能E,
                Ctrl技能1, Ctrl技能2, Ctrl技能Q
            )
            from 核心.鼠标控制 import 左键点击, 右键点击, 中键点击
            
            动作映射 = {
                0: 前进, 1: 后退, 2: 左移, 3: 右移,
                4: 前进左移, 5: 前进右移, 6: 后退左移, 7: 后退右移,
                8: 无操作,
                9: 技能1, 10: 技能2, 11: 技能3, 12: 技能4,
                13: 技能5, 14: 技能6, 15: 技能Q, 16: 技能E,
                17: 技能R, 18: 技能F,
                19: 跳跃, 20: 切换目标, 21: 交互,
                22: 左键点击, 23: 右键点击, 24: 中键点击,
                25: Shift技能1, 26: Shift技能2, 27: Shift技能Q, 28: Shift技能E,
                29: Ctrl技能1, 30: Ctrl技能2, 31: Ctrl技能Q,
            }
            
            执行函数 = 动作映射.get(动作索引)
            if 执行函数:
                执行函数()
        except Exception as e:
            self.错误发生.emit(f"执行动作失败: {str(e)}")
    
    def _释放所有按键(self) -> None:
        """释放所有按键"""
        try:
            from 核心.键盘控制 import 释放所有按键
            释放所有按键()
        except Exception:
            pass
    
    def _处理卡住(self) -> None:
        """处理角色卡住的情况"""
        import random
        
        self.脱困提示.emit("检测到角色可能卡住，正在执行脱困动作...")
        
        try:
            from 核心.键盘控制 import (
                前进, 后退, 左移, 右移,
                前进左移, 前进右移, 后退左移, 后退右移,
                跳跃, 切换目标, 技能1
            )
            
            策略 = random.randrange(0, 6)
            
            if 策略 == 0:
                后退()
                time.sleep(random.uniform(1, 2))
                前进左移()
                time.sleep(random.uniform(1, 2))
            elif 策略 == 1:
                后退()
                time.sleep(random.uniform(1, 2))
                前进右移()
                time.sleep(random.uniform(1, 2))
            elif 策略 == 2:
                后退左移()
                time.sleep(random.uniform(1, 2))
                前进右移()
                time.sleep(random.uniform(1, 2))
            elif 策略 == 3:
                后退右移()
                time.sleep(random.uniform(1, 2))
                前进左移()
                time.sleep(random.uniform(1, 2))
            elif 策略 == 4:
                跳跃()
                time.sleep(0.5)
                前进()
                time.sleep(random.uniform(1, 2))
            elif 策略 == 5:
                if self._子模式 == '自动战斗':
                    切换目标()
                    time.sleep(0.3)
                    技能1()
                    time.sleep(0.5)
            
            # 清空运动日志
            运动日志长度 = len(self._运动日志)
            for _ in range(运动日志长度 - 2):
                if self._运动日志:
                    self._运动日志.popleft()
                    
        except Exception as e:
            self.错误发生.emit(f"脱困动作执行失败: {str(e)}")
    
    def _更新性能监控(self, 帧时间: float) -> None:
        """更新性能监控并自适应调整"""
        self._帧时间日志.append(帧时间)
        
        if len(self._帧时间日志) >= 10:
            平均帧时间 = mean(self._帧时间日志)
            self._当前帧率 = 1.0 / 平均帧时间 if 平均帧时间 > 0 else 30.0
            
            # 性能自适应
            帧率阈值 = 15
            
            if self._当前帧率 < 帧率阈值 and not self._已降级:
                self._进入低性能模式()
            elif self._当前帧率 >= 帧率阈值 * 1.5 and self._已降级:
                self._退出低性能模式()
    
    def _进入低性能模式(self) -> None:
        """进入低性能模式"""
        self._已降级 = True
        self._当前检测间隔 = 5
        self.性能警告.emit(self._当前帧率)
        
        # 更新增强模块状态
        self.增强模块状态.emit({
            "YOLO": self._YOLO可用,
            "状态识别": self._状态识别可用,
            "决策引擎": self._决策引擎可用,
            "低性能": True,
        })
    
    def _退出低性能模式(self) -> None:
        """退出低性能模式"""
        self._已降级 = False
        self._当前检测间隔 = 3
        
        # 更新增强模块状态
        self.增强模块状态.emit({
            "YOLO": self._YOLO可用,
            "状态识别": self._状态识别可用,
            "决策引擎": self._决策引擎可用,
            "低性能": False,
        })
    
    def 请求停止(self) -> None:
        """请求停止线程"""
        self._停止标志 = True
    
    def 切换暂停(self) -> None:
        """切换暂停状态"""
        self._暂停标志 = not self._暂停标志
    
    def 是否暂停(self) -> bool:
        """返回是否处于暂停状态"""
        return self._暂停标志
    
    def 获取当前帧率(self) -> float:
        """获取当前帧率"""
        return self._当前帧率
    
    def 是否增强模式(self) -> bool:
        """返回是否启用增强模式"""
        return self._启用增强
    
    def 获取增强模块状态(self) -> Dict[str, bool]:
        """获取增强模块状态"""
        return {
            "YOLO": self._YOLO可用,
            "状态识别": self._状态识别可用,
            "决策引擎": self._决策引擎可用,
            "低性能": self._已降级,
        }
