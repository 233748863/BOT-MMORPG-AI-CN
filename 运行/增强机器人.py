"""
增强版游戏AI机器人
集成YOLO目标检测、状态识别和智能决策引擎

功能:
- YOLO目标检测: 识别游戏中的实体
- 状态识别: 判断当前游戏状态
- 智能决策: 结合规则和模型做出决策
- 模块降级: 单个模块失败时自动降级
- 性能自适应: 根据帧率自动调整检测频率
"""

import numpy as np
import cv2
import time
import os
import sys
import logging
from collections import deque
from statistics import mean
from typing import Optional, List

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from 核心.屏幕截取 import 截取屏幕
from 核心.键盘控制 import (
    前进, 后退, 左移, 右移,
    前进左移, 前进右移, 后退左移, 后退右移, 无操作, 释放所有按键,
    技能1, 技能2, 技能3, 技能4, 技能5, 技能6,
    技能Q, 技能E, 技能R, 技能F,
    跳跃, 切换目标, 交互,
    Shift技能1, Shift技能2, Shift技能Q, Shift技能E,
    Ctrl技能1, Ctrl技能2, Ctrl技能Q
)
from 核心.鼠标控制 import 左键点击, 右键点击, 中键点击
from 核心.按键检测 import 检测按键
from 核心.动作检测 import 检测动作变化
from 核心.模型定义 import inception_v3
from 核心.数据类型 import 游戏状态, 检测结果, 决策上下文, 实体类型
from 配置.设置 import (
    游戏窗口区域, 模型输入宽度, 模型输入高度, 学习率,
    模型保存路径, 预训练模型路径, 总动作数, 训练模式,
    运动检测阈值, 运动日志长度, 动作定义
)
from 配置.增强设置 import (
    YOLO配置, 状态识别配置, 决策引擎配置, 模块启用配置, 性能配置
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class 增强版游戏AI机器人:
    """
    增强版游戏AI机器人
    
    集成YOLO检测器、状态识别器和决策引擎，
    支持模块降级和性能自适应
    """
    
    def __init__(self, 模式: str = '主线任务', 启用增强: bool = True):
        """
        初始化增强版机器人
        
        Args:
            模式: '主线任务' 或 '自动战斗'
            启用增强: 是否启用增强模块
        """
        self.模式 = 模式
        self.启用增强 = 启用增强
        
        # 基础模型
        self.模型 = None
        self.动作权重 = None
        
        # 增强模块
        self.YOLO检测器 = None
        self.状态识别器 = None
        self.决策引擎 = None
        
        # 模块状态
        self._YOLO可用 = False
        self._状态识别可用 = False
        self._决策引擎可用 = False
        self._已降级 = False
        
        # 运动检测
        self.运动日志 = deque(maxlen=运动日志长度)
        
        # 性能监控
        self.帧时间日志 = deque(maxlen=30)
        self.当前帧率 = 30.0
        self.检测计数器 = 0
        self.当前检测间隔 = YOLO配置.get("检测间隔", 3)
        
        # 上次检测结果缓存
        self._上次检测结果: List[检测结果] = []
        self._上次状态 = 游戏状态.未知
        
        # 设置动作权重
        if 模式 == '主线任务':
            self.动作权重 = np.array(训练模式.主线任务['动作权重'])
        else:
            self.动作权重 = np.array(训练模式.自动战斗['动作权重'])
        
        # 动作执行映射
        self._初始化动作映射()
        
        logger.info(f"增强版机器人初始化完成，模式: {模式}, 增强: {启用增强}")
    
    def _初始化动作映射(self):
        """初始化动作索引到执行函数的映射"""
        self.动作映射 = {
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
    
    def 加载模型(self) -> bool:
        """加载基础AI模型"""
        print("🔄 加载AI模型...")
        
        self.模型 = inception_v3(
            模型输入宽度, 模型输入高度, 3, 学习率,
            输出类别=总动作数
        )
        
        模型路径列表 = [模型保存路径, 预训练模型路径]
        
        for 路径 in 模型路径列表:
            try:
                if os.path.exists(路径 + '.index') or os.path.exists(路径 + '.meta'):
                    self.模型.load(路径)
                    print(f"✅ 模型加载成功: {路径}")
                    return True
            except Exception as e:
                logger.warning(f"尝试加载 {路径} 失败: {e}")
                continue
        
        print("❌ 未找到可用的模型文件")
        return False
    
    def 初始化增强模块(self) -> bool:
        """
        初始化增强模块（YOLO检测器、状态识别器、决策引擎）
        
        Returns:
            是否至少有一个模块初始化成功
        """
        if not self.启用增强:
            logger.info("增强模块已禁用")
            return False
        
        print("🔄 初始化增强模块...")
        
        # 初始化YOLO检测器
        if 模块启用配置.get("YOLO检测器", True):
            self._初始化YOLO检测器()
        
        # 初始化状态识别器
        if 模块启用配置.get("状态识别器", True):
            self._初始化状态识别器()
        
        # 初始化决策引擎
        if 模块启用配置.get("决策引擎", True):
            self._初始化决策引擎()
        
        # 汇总状态
        可用模块数 = sum([self._YOLO可用, self._状态识别可用, self._决策引擎可用])
        print(f"✅ 增强模块初始化完成: {可用模块数}/3 个模块可用")
        
        if self._YOLO可用:
            print("   ✓ YOLO目标检测器")
        else:
            print("   ✗ YOLO目标检测器 (不可用)")
        
        if self._状态识别可用:
            print("   ✓ 状态识别器")
        else:
            print("   ✗ 状态识别器 (不可用)")
        
        if self._决策引擎可用:
            print("   ✓ 决策引擎")
        else:
            print("   ✗ 决策引擎 (不可用)")
        
        return 可用模块数 > 0

    def _初始化YOLO检测器(self):
        """初始化YOLO检测器"""
        try:
            from 核心.目标检测器 import YOLO检测器
            self.YOLO检测器 = YOLO检测器()
            self._YOLO可用 = self.YOLO检测器.是否已加载()
            if self._YOLO可用:
                logger.info("YOLO检测器初始化成功")
            else:
                logger.warning("YOLO检测器模型未加载")
        except Exception as e:
            logger.error(f"YOLO检测器初始化失败: {e}")
            self._YOLO可用 = False
    
    def _初始化状态识别器(self):
        """初始化状态识别器"""
        try:
            from 核心.状态识别器 import 状态识别器
            self.状态识别器 = 状态识别器()
            self._状态识别可用 = True
            
            # 注册状态变更回调
            self.状态识别器.注册状态变更回调(self._状态变更处理)
            logger.info("状态识别器初始化成功")
        except Exception as e:
            logger.error(f"状态识别器初始化失败: {e}")
            self._状态识别可用 = False
    
    def _初始化决策引擎(self):
        """初始化决策引擎"""
        try:
            from 核心.决策引擎 import 决策引擎
            from 核心.决策规则 import 加载预定义规则
            
            self.决策引擎 = 决策引擎()
            
            # 加载预定义规则
            try:
                规则列表 = 加载预定义规则()
                for 规则 in 规则列表:
                    self.决策引擎.添加规则(规则)
                logger.info(f"加载了 {len(规则列表)} 条预定义规则")
            except Exception as e:
                logger.warning(f"加载预定义规则失败: {e}")
            
            self._决策引擎可用 = True
            logger.info("决策引擎初始化成功")
        except Exception as e:
            logger.error(f"决策引擎初始化失败: {e}")
            self._决策引擎可用 = False
    
    def _状态变更处理(self, 旧状态: 游戏状态, 新状态: 游戏状态):
        """状态变更回调处理"""
        logger.info(f"游戏状态变更: {旧状态.value} -> {新状态.value}")
        
        # 根据状态变更调整行为
        if 新状态 == 游戏状态.死亡:
            logger.warning("检测到死亡状态，暂停动作")
        elif 新状态 == 游戏状态.加载:
            logger.info("检测到加载状态，等待加载完成")
    
    def 预测动作(self, 屏幕: np.ndarray) -> tuple:
        """
        使用基础模型预测动作
        
        Args:
            屏幕: 游戏屏幕图像
            
        Returns:
            (动作索引, 预测值列表)
        """
        预测结果 = self.模型.predict([屏幕.reshape(模型输入宽度, 模型输入高度, 3)])[0]
        预测结果 = np.round(预测结果, decimals=2)
        
        加权预测 = np.array(预测结果) * self.动作权重
        动作索引 = np.argmax(np.abs(加权预测))
        
        return 动作索引, list(预测结果)
    
    def 增强决策(self, 屏幕: np.ndarray, 模型预测: List[float]) -> tuple:
        """
        使用增强模块进行决策
        
        Args:
            屏幕: 游戏屏幕图像
            模型预测: 基础模型的预测结果
            
        Returns:
            (动作索引, 动作名称, 决策来源)
        """
        检测结果列表 = self._上次检测结果
        当前状态 = self._上次状态
        
        # 执行目标检测（按间隔）
        self.检测计数器 += 1
        if self._YOLO可用 and self.检测计数器 >= self.当前检测间隔:
            self.检测计数器 = 0
            try:
                检测结果列表 = self.YOLO检测器.检测(屏幕)
                self._上次检测结果 = 检测结果列表
            except Exception as e:
                logger.warning(f"YOLO检测失败: {e}")
        
        # 执行状态识别
        if self._状态识别可用:
            try:
                状态结果 = self.状态识别器.识别状态(屏幕, 检测结果列表)
                当前状态 = 状态结果.状态
                self._上次状态 = 当前状态
            except Exception as e:
                logger.warning(f"状态识别失败: {e}")
        
        # 使用决策引擎
        if self._决策引擎可用:
            try:
                # 统计附近敌人
                附近敌人数量 = len([r for r in 检测结果列表 if r.类型 == 实体类型.怪物])
                
                # 构建决策上下文
                上下文 = 决策上下文(
                    游戏状态=当前状态,
                    检测结果=检测结果列表,
                    模型预测=模型预测,
                    血量百分比=1.0,  # TODO: 实现血量检测
                    附近敌人数量=附近敌人数量
                )
                
                # 执行决策
                决策 = self.决策引擎.决策(上下文)
                
                # 记录动作执行
                self.决策引擎.记录动作执行(决策.动作索引)
                
                return 决策.动作索引, 决策.动作名称, 决策.来源
            except Exception as e:
                logger.warning(f"决策引擎失败: {e}")
        
        # 降级到基础模型
        动作索引 = np.argmax(np.abs(np.array(模型预测) * self.动作权重))
        动作名称 = 动作定义.get(动作索引, {}).get("名称", f"动作{动作索引}")
        return 动作索引, 动作名称, "fallback"
    
    def 执行动作(self, 动作索引: int) -> str:
        """
        执行指定动作
        
        Args:
            动作索引: 动作编号 (0-31)
            
        Returns:
            执行的动作名称
        """
        动作名称 = 动作定义.get(动作索引, {}).get("名称", f"动作{动作索引}")
        
        执行函数 = self.动作映射.get(动作索引)
        if 执行函数:
            try:
                执行函数()
            except Exception as e:
                logger.error(f"动作执行失败 ({动作名称}): {e}")
        
        return 动作名称
    
    def 更新性能监控(self, 帧时间: float):
        """
        更新性能监控并自适应调整
        
        Args:
            帧时间: 当前帧耗时（秒）
        """
        self.帧时间日志.append(帧时间)
        
        if len(self.帧时间日志) >= 10:
            平均帧时间 = mean(self.帧时间日志)
            self.当前帧率 = 1.0 / 平均帧时间 if 平均帧时间 > 0 else 30.0
            
            # 性能自适应
            if 性能配置.get("自动降级", True):
                帧率阈值 = 性能配置.get("帧率阈值", 15)
                
                if self.当前帧率 < 帧率阈值 and not self._已降级:
                    self._进入低性能模式()
                elif self.当前帧率 >= 帧率阈值 * 1.5 and self._已降级:
                    self._退出低性能模式()
    
    def _进入低性能模式(self):
        """进入低性能模式"""
        self._已降级 = True
        self.当前检测间隔 = 性能配置.get("低性能模式检测间隔", 5)
        logger.warning(f"性能不足，进入低性能模式，检测间隔: {self.当前检测间隔}")
        print(f"⚠️  性能不足 (帧率: {self.当前帧率:.1f})，降低检测频率")
    
    def _退出低性能模式(self):
        """退出低性能模式"""
        self._已降级 = False
        self.当前检测间隔 = YOLO配置.get("检测间隔", 3)
        logger.info(f"性能恢复，退出低性能模式，检测间隔: {self.当前检测间隔}")
        print(f"✅ 性能恢复 (帧率: {self.当前帧率:.1f})，恢复正常检测频率")
    
    def 降级到基础模式(self):
        """降级到基础模仿学习模式"""
        logger.warning("增强模块全部失败，降级到基础模式")
        print("⚠️  增强模块不可用，使用基础模仿学习模式")
        self.启用增强 = False
        self._YOLO可用 = False
        self._状态识别可用 = False
        self._决策引擎可用 = False

    def 处理卡住(self):
        """处理角色卡住的情况"""
        import random
        
        print("⚠️  检测到角色可能卡住，执行脱困动作...")
        
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
            if self.模式 == '自动战斗':
                切换目标()
                time.sleep(0.3)
                技能1()
                time.sleep(0.5)
        
        # 清空运动日志
        for _ in range(运动日志长度 - 2):
            if self.运动日志:
                self.运动日志.popleft()
    
    def 运行(self):
        """运行机器人主循环"""
        import msvcrt
        
        # 加载基础模型
        if not self.加载模型():
            return
        
        # 初始化增强模块
        if self.启用增强:
            self.初始化增强模块()
        
        # 检查是否有可用的增强模块
        增强可用 = self._YOLO可用 or self._状态识别可用 or self._决策引擎可用
        
        print("\n" + "=" * 60)
        if 增强可用:
            print(f"🎮 增强版游戏AI机器人 - {self.模式}模式")
        else:
            print(f"🎮 游戏AI机器人 - {self.模式}模式 (基础模式)")
        print("=" * 60)
        print("\n📋 操作说明:")
        print("  - 按 T 暂停/继续")
        print("  - 按 ESC 退出")
        if 增强可用:
            print("  - 按 I 显示增强模块状态")
        print()
        
        # 倒计时
        print("⏱️  准备启动...")
        for i in range(4, 0, -1):
            print(f"   {i}...")
            time.sleep(1)
        
        print("\n🚀 机器人已启动!")
        print("-" * 60)
        
        已暂停 = False
        
        # 初始化帧缓存
        屏幕 = 截取屏幕(region=游戏窗口区域)
        屏幕 = cv2.cvtColor(屏幕, cv2.COLOR_BGR2RGB)
        屏幕 = cv2.resize(屏幕, (模型输入宽度, 模型输入高度))
        
        前帧 = 屏幕.copy()
        当前帧 = 屏幕.copy()
        后帧 = 屏幕.copy()
        
        上次时间 = time.time()
        
        try:
            while True:
                # 检查ESC键
                if msvcrt.kbhit():
                    键值 = ord(msvcrt.getch())
                    if 键值 == 27:  # ESC
                        print("\n🛑 用户按下ESC，退出...")
                        break
                
                # 检查暂停键和信息键
                按键 = 检测按键()
                if 'T' in 按键:
                    已暂停 = not 已暂停
                    if 已暂停:
                        print("\n⏸️  已暂停")
                        无操作()
                    else:
                        print("\n▶️  继续运行")
                    time.sleep(0.5)
                
                if 'I' in 按键 and 增强可用:
                    self._显示增强状态()
                    time.sleep(0.5)
                
                if not 已暂停:
                    循环开始时间 = time.time()
                    
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
                    基础动作索引, 模型预测 = self.预测动作(屏幕缩放)
                    
                    # 决策
                    if 增强可用 and self.启用增强:
                        动作索引, 动作名称, 来源 = self.增强决策(屏幕, 模型预测)
                    else:
                        动作索引 = 基础动作索引
                        动作名称 = 动作定义.get(动作索引, {}).get("名称", f"动作{动作索引}")
                        来源 = "model"
                    
                    # 执行动作
                    self.执行动作(动作索引)
                    
                    # 记录运动量
                    self.运动日志.append(动作量)
                    平均运动量 = round(mean(self.运动日志), 3) if self.运动日志 else 0
                    
                    # 更新性能监控
                    循环时间 = time.time() - 循环开始时间
                    self.更新性能监控(循环时间)
                    
                    # 显示状态
                    状态标签 = f"[{self._上次状态.value}]" if 增强可用 else ""
                    来源标签 = f"({来源})" if 增强可用 else ""
                    print(f"🎯 {状态标签} {动作名称:10s} {来源标签} | 运动量: {平均运动量:8.1f} | 帧率: {self.当前帧率:.1f}")
                    
                    # 检测是否卡住
                    if 平均运动量 < 运动检测阈值 and len(self.运动日志) >= 运动日志长度:
                        self.处理卡住()
                
                time.sleep(0.01)
        
        except KeyboardInterrupt:
            print("\n\n⚠️  用户中断")
        
        finally:
            释放所有按键()
            print("\n✅ 机器人已停止")
            
            # 显示统计信息
            if 增强可用 and self._决策引擎可用:
                self._显示决策统计()
    
    def _显示增强状态(self):
        """显示增强模块状态"""
        print("\n" + "=" * 40)
        print("📊 增强模块状态")
        print("=" * 40)
        print(f"  YOLO检测器: {'✓ 可用' if self._YOLO可用 else '✗ 不可用'}")
        print(f"  状态识别器: {'✓ 可用' if self._状态识别可用 else '✗ 不可用'}")
        print(f"  决策引擎:   {'✓ 可用' if self._决策引擎可用 else '✗ 不可用'}")
        print(f"  当前状态:   {self._上次状态.value}")
        print(f"  检测间隔:   每 {self.当前检测间隔} 帧")
        print(f"  当前帧率:   {self.当前帧率:.1f} FPS")
        print(f"  性能模式:   {'低性能' if self._已降级 else '正常'}")
        print("=" * 40 + "\n")
    
    def _显示决策统计(self):
        """显示决策统计信息"""
        if not self.决策引擎:
            return
        
        统计 = self.决策引擎.获取统计信息()
        
        print("\n" + "=" * 40)
        print("📈 决策统计")
        print("=" * 40)
        print(f"  总决策数:   {统计.get('总决策数', 0)}")
        print(f"  规则决策:   {统计.get('规则决策数', 0)}")
        print(f"  模型决策:   {统计.get('模型决策数', 0)}")
        print(f"  混合决策:   {统计.get('混合决策数', 0)}")
        print(f"  规则数量:   {统计.get('规则数量', 0)}")
        if 统计.get('总决策数', 0) > 0:
            print(f"  规则比例:   {统计.get('规则决策比例', 0):.1%}")
        print("=" * 40)


def 显示模式菜单() -> tuple:
    """
    显示模式选择菜单
    
    Returns:
        (模式, 是否启用增强)
    """
    print("\n" + "=" * 60)
    print("🤖 增强版MMORPG游戏AI - 机器人运行工具")
    print("=" * 60)
    print("\n请选择运行模式:")
    print("  1. 主线任务模式 (增强) - 智能做主线任务")
    print("  2. 自动战斗模式 (增强) - 智能战斗打怪")
    print("  3. 主线任务模式 (基础) - 基础模仿学习")
    print("  4. 自动战斗模式 (基础) - 基础模仿学习")
    print()
    
    while True:
        选择 = input("请输入选项 (1-4): ").strip()
        if 选择 == '1':
            return '主线任务', True
        elif 选择 == '2':
            return '自动战斗', True
        elif 选择 == '3':
            return '主线任务', False
        elif 选择 == '4':
            return '自动战斗', False
        print("❌ 无效选项，请重新输入")


def 主程序():
    """主程序入口"""
    模式, 启用增强 = 显示模式菜单()
    
    机器人 = 增强版游戏AI机器人(模式=模式, 启用增强=启用增强)
    机器人.运行()


if __name__ == "__main__":
    主程序()
