"""
游戏AI机器人运行脚本
用于运行训练好的AI模型自动玩游戏

使用方法:
1. 确保已训练好模型
2. 运行此脚本
3. 切换到游戏窗口
4. 按 T 暂停/继续
5. 按 ESC 退出

支持的模式:
- 主线任务: 自动做主线任务
- 自动战斗: 自动战斗打怪
"""

import numpy as np
import cv2
import time
import os
import sys
import random
import msvcrt
from collections import deque
from statistics import mean

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from 核心.屏幕截取 import 截取屏幕
from 核心.键盘控制 import (
    按下按键, 释放按键, W, A, S, D,
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
from 配置.设置 import (
    游戏窗口区域, 游戏宽度, 游戏高度,
    模型输入宽度, 模型输入高度, 学习率,
    模型保存路径, 预训练模型路径, 总动作数, 训练模式,
    运动检测阈值, 运动日志长度
)


class 游戏AI机器人:
    """游戏AI机器人类"""
    
    def __init__(self, 模式='主线任务'):
        """
        初始化机器人
        
        参数:
            模式: '主线任务' 或 '自动战斗'
        """
        self.模式 = 模式
        self.模型 = None
        self.动作权重 = None
        self.运动日志 = deque(maxlen=运动日志长度)
        self.选择历史 = deque(maxlen=5)
        
        # 设置动作权重
        if 模式 == '主线任务':
            self.动作权重 = np.array(训练模式.主线任务['动作权重'])
        else:
            self.动作权重 = np.array(训练模式.自动战斗['动作权重'])
        
        # 动作名称映射 (32个动作)
        self.动作名称 = {
            # 移动动作 (0-8)
            0: '前进', 1: '后退', 2: '左移', 3: '右移',
            4: '前进+左', 5: '前进+右', 6: '后退+左', 7: '后退+右',
            8: '无操作',
            # 技能动作 (9-18)
            9: '技能1', 10: '技能2', 11: '技能3', 12: '技能4',
            13: '技能5', 14: '技能6', 15: '技能Q', 16: '技能E',
            17: '技能R', 18: '技能F',
            # 特殊动作 (19-21)
            19: '跳跃/闪避', 20: '切换目标', 21: '交互',
            # 鼠标动作 (22-24)
            22: '鼠标左键', 23: '鼠标右键', 24: '鼠标中键',
            # Shift组合 (25-28)
            25: 'Shift+1', 26: 'Shift+2', 27: 'Shift+Q', 28: 'Shift+E',
            # Ctrl组合 (29-31)
            29: 'Ctrl+1', 30: 'Ctrl+2', 31: 'Ctrl+Q',
        }
    
    def 加载模型(self):
        """加载训练好的模型"""
        print("🔄 加载AI模型...")
        
        self.模型 = inception_v3(
            模型输入宽度, 模型输入高度, 3, 学习率,
            输出类别=总动作数
        )
        
        # 优先加载用户训练的模型，否则加载预训练模型
        模型路径列表 = [模型保存路径, 预训练模型路径]
        
        for 路径 in 模型路径列表:
            try:
                if os.path.exists(路径 + '.index') or os.path.exists(路径 + '.meta'):
                    self.模型.load(路径)
                    print(f"✅ 模型加载成功: {路径}")
                    return True
            except Exception as e:
                print(f"⚠️  尝试加载 {路径} 失败: {e}")
                continue
        
        print("❌ 未找到可用的模型文件")
        print("   请先运行训练或确保预训练模型存在")
        return False
    
    def 预测动作(self, 屏幕):
        """
        根据屏幕画面预测动作
        
        参数:
            屏幕: 游戏屏幕图像
        
        返回:
            tuple: (动作索引, 预测值)
        """
        # 预测
        预测结果 = self.模型.predict([屏幕.reshape(模型输入宽度, 模型输入高度, 3)])[0]
        预测结果 = np.round(预测结果, decimals=2)
        
        # 应用动作权重
        加权预测 = np.array(预测结果) * self.动作权重
        
        # 获取最佳动作
        动作索引 = np.argmax(np.abs(加权预测))
        预测值 = 加权预测[动作索引]
        
        return 动作索引, 预测值
    
    def 执行动作(self, 动作索引, 预测值):
        """
        执行预测的动作
        
        参数:
            动作索引: 动作编号 (0-31)
            预测值: 预测值
        
        返回:
            str: 执行的动作名称
        """
        动作名称 = self.动作名称.get(动作索引, f'未知动作{动作索引}')
        
        # ==================== 移动动作 (0-8) ====================
        if 动作索引 == 0:
            前进()
        elif 动作索引 == 1:
            后退()
        elif 动作索引 == 2:
            左移()
        elif 动作索引 == 3:
            右移()
        elif 动作索引 == 4:
            前进左移()
        elif 动作索引 == 5:
            前进右移()
        elif 动作索引 == 6:
            后退左移()
        elif 动作索引 == 7:
            后退右移()
        elif 动作索引 == 8:
            无操作()
        
        # ==================== 技能动作 (9-18) ====================
        elif 动作索引 == 9:
            技能1()
        elif 动作索引 == 10:
            技能2()
        elif 动作索引 == 11:
            技能3()
        elif 动作索引 == 12:
            技能4()
        elif 动作索引 == 13:
            技能5()
        elif 动作索引 == 14:
            技能6()
        elif 动作索引 == 15:
            技能Q()
        elif 动作索引 == 16:
            技能E()
        elif 动作索引 == 17:
            技能R()
        elif 动作索引 == 18:
            技能F()
        
        # ==================== 特殊动作 (19-21) ====================
        elif 动作索引 == 19:
            跳跃()
        elif 动作索引 == 20:
            切换目标()
        elif 动作索引 == 21:
            交互()
        
        # ==================== 鼠标动作 (22-24) ====================
        elif 动作索引 == 22:
            左键点击()
        elif 动作索引 == 23:
            右键点击()
        elif 动作索引 == 24:
            中键点击()
        
        # ==================== Shift组合 (25-28) ====================
        elif 动作索引 == 25:
            Shift技能1()
        elif 动作索引 == 26:
            Shift技能2()
        elif 动作索引 == 27:
            Shift技能Q()
        elif 动作索引 == 28:
            Shift技能E()
        
        # ==================== Ctrl组合 (29-31) ====================
        elif 动作索引 == 29:
            Ctrl技能1()
        elif 动作索引 == 30:
            Ctrl技能2()
        elif 动作索引 == 31:
            Ctrl技能Q()
        
        return 动作名称
    
    def 处理卡住(self):
        """处理角色卡住的情况"""
        print("⚠️  检测到角色可能卡住，执行脱困动作...")
        
        # 随机选择脱困策略
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
            # 跳跃脱困
            跳跃()
            time.sleep(0.5)
            前进()
            time.sleep(random.uniform(1, 2))
        elif 策略 == 5:
            # 战斗模式下尝试切换目标
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
        
        # 加载模型
        if not self.加载模型():
            return
        
        print("\n" + "=" * 50)
        print(f"🎮 游戏AI机器人 - {self.模式}模式")
        print("=" * 50)
        print("\n📋 操作说明:")
        print("  - 按 T 暂停/继续")
        print("  - 按 ESC 退出")
        print()
        
        # 倒计时
        print("⏱️  准备启动...")
        for i in range(4, 0, -1):
            print(f"   {i}...")
            time.sleep(1)
        
        print("\n🚀 机器人已启动!")
        print("-" * 50)
        
        已暂停 = False
        
        # 初始化帧缓存 (用于运动检测)
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
                if msvcrt.kbhit() and ord(msvcrt.getch()) == 27:
                    print("\n🛑 用户按下ESC，退出...")
                    break
                
                # 检查暂停键
                按键 = 检测按键()
                if 'T' in 按键:
                    已暂停 = not 已暂停
                    if 已暂停:
                        print("\n⏸️  已暂停")
                        无操作()
                    else:
                        print("\n▶️  继续运行")
                    time.sleep(0.5)
                
                if not 已暂停:
                    # 截取屏幕
                    屏幕 = 截取屏幕(region=游戏窗口区域)
                    屏幕 = cv2.cvtColor(屏幕, cv2.COLOR_BGR2RGB)
                    屏幕 = cv2.resize(屏幕, (模型输入宽度, 模型输入高度))
                    
                    # 运动检测
                    动作量 = 检测动作变化(前帧, 当前帧, 后帧, 屏幕)
                    
                    # 更新帧缓存
                    前帧 = 当前帧
                    当前帧 = 后帧
                    后帧 = 屏幕.copy()
                    后帧 = cv2.blur(后帧, (4, 4))
                    
                    # 预测动作
                    动作索引, 预测值 = self.预测动作(屏幕)
                    
                    # 执行动作
                    动作名称 = self.执行动作(动作索引, 预测值)
                    
                    # 记录运动量
                    self.运动日志.append(动作量)
                    平均运动量 = round(mean(self.运动日志), 3) if self.运动日志 else 0
                    
                    # 显示状态
                    当前时间 = time.time()
                    循环时间 = round(当前时间 - 上次时间, 3)
                    print(f"🎯 动作: {动作名称:10s} | 运动量: {平均运动量:8.1f} | 耗时: {循环时间}s")
                    上次时间 = 当前时间
                    
                    # 检测是否卡住
                    if 平均运动量 < 运动检测阈值 and len(self.运动日志) >= 运动日志长度:
                        self.处理卡住()
                
                time.sleep(0.01)  # 小延迟，避免CPU占用过高
        
        except KeyboardInterrupt:
            print("\n\n⚠️  用户中断")
        
        finally:
            # 释放所有按键
            释放所有按键()
            print("\n✅ 机器人已停止")


def 显示模式菜单():
    """显示模式选择菜单"""
    print("\n" + "=" * 50)
    print("🤖 MMORPG游戏AI - 机器人运行工具")
    print("=" * 50)
    print("\n请选择运行模式:")
    print("  1. 主线任务模式 - 自动做主线任务")
    print("  2. 自动战斗模式 - 自动战斗打怪")
    print()
    
    while True:
        选择 = input("请输入选项 (1/2): ").strip()
        if 选择 == '1':
            return '主线任务'
        elif 选择 == '2':
            return '自动战斗'
        print("❌ 无效选项，请重新输入")


def 主程序():
    """主程序入口"""
    
    # 选择模式
    模式 = 显示模式菜单()
    
    # 创建并运行机器人
    机器人 = 游戏AI机器人(模式=模式)
    机器人.运行()


if __name__ == "__main__":
    主程序()
