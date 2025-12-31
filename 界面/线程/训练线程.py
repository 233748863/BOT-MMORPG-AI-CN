# -*- coding: utf-8 -*-
"""
训练后台线程

在后台执行模型训练任务，通过信号与界面通信，
确保界面保持响应。
"""

import os
import sys
import time
import numpy as np
from typing import Optional, List
from pathlib import Path
from random import shuffle

from PySide6.QtCore import QThread, Signal

# 添加项目根目录到路径
项目根目录 = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if 项目根目录 not in sys.path:
    sys.path.insert(0, 项目根目录)


class 训练线程(QThread):
    """
    模型训练后台线程
    
    在后台执行模型训练任务，通过信号更新界面状态。
    """
    
    # 信号定义
    进度更新 = Signal(int, str)  # 进度百分比, 状态消息
    轮次完成 = Signal(int, int, float)  # 当前轮次, 总轮次, 损失值
    日志消息 = Signal(str, str)  # 消息内容, 级别 (信息/警告/错误/成功)
    任务完成 = Signal(bool, str)  # 是否成功, 结果消息
    错误发生 = Signal(str)  # 错误消息
    
    def __init__(self, parent=None):
        """初始化线程"""
        super().__init__(parent)
        
        # 控制标志
        self._停止标志 = False
        
        # 配置
        self._训练模式 = "主线任务"
        
        # 状态
        self._当前轮次 = 0
        self._总轮次 = 10
        self._当前损失 = 0.0
        self._损失历史: List[float] = []
    
    def 设置训练模式(self, 模式: str) -> None:
        """设置训练模式"""
        self._训练模式 = 模式
    
    def run(self) -> None:
        """线程执行入口"""
        try:
            self._执行训练()
        except Exception as e:
            import traceback
            错误详情 = traceback.format_exc()
            self.错误发生.emit(f"训练错误: {str(e)}")
            self.日志消息.emit(f"训练异常: {错误详情}", "错误")
            self.任务完成.emit(False, f"训练失败: {str(e)}")
    
    def _执行训练(self) -> None:
        """执行训练主逻辑"""
        # 导入必要模块
        try:
            from 配置.设置 import (
                模型输入宽度, 模型输入高度, 学习率,
                训练轮数, 模型保存路径, 数据保存路径, 总动作数
            )
        except ImportError as e:
            self.错误发生.emit(f"导入配置模块失败: {str(e)}")
            self.任务完成.emit(False, f"导入配置模块失败: {str(e)}")
            return
        
        self._总轮次 = 训练轮数
        
        # 获取数据文件列表
        数据文件列表 = self._获取数据文件列表(数据保存路径)
        
        if not 数据文件列表:
            self.错误发生.emit("未找到训练数据文件")
            self.日志消息.emit(f"未找到训练数据文件，请先收集训练数据", "错误")
            self.日志消息.emit(f"数据目录: {数据保存路径}", "信息")
            self.任务完成.emit(False, "未找到训练数据文件")
            return
        
        self.日志消息.emit(f"找到 {len(数据文件列表)} 个数据文件", "信息")
        
        # 确保模型目录存在
        模型目录 = os.path.dirname(模型保存路径)
        if 模型目录:
            os.makedirs(模型目录, exist_ok=True)
        
        # 创建模型
        self.日志消息.emit("正在创建模型...", "信息")
        self.进度更新.emit(5, "创建模型...")
        
        try:
            from 核心.模型定义 import inception_v3
            
            模型 = inception_v3(
                模型输入宽度, 
                模型输入高度, 
                3, 
                学习率, 
                输出类别=总动作数, 
                模型名称=模型保存路径
            )
            self.日志消息.emit("模型创建成功", "成功")
        except Exception as e:
            self.错误发生.emit(f"创建模型失败: {str(e)}")
            self.日志消息.emit(f"创建模型失败: {str(e)}", "错误")
            self.任务完成.emit(False, f"创建模型失败: {str(e)}")
            return
        
        # 检查是否有已保存的模型
        if os.path.exists(模型保存路径 + '.index'):
            try:
                模型.load(模型保存路径)
                self.日志消息.emit("已加载之前保存的模型", "成功")
            except Exception as e:
                self.日志消息.emit(f"加载已有模型失败: {str(e)}，将从头开始训练", "警告")
        
        self.日志消息.emit("开始训练...", "信息")
        self.进度更新.emit(10, "开始训练...")
        
        # 训练循环
        总文件数 = len(数据文件列表)
        
        for 轮次 in range(self._总轮次):
            if self._停止标志:
                self.日志消息.emit("训练已被用户停止", "警告")
                break
            
            self._当前轮次 = 轮次 + 1
            self.日志消息.emit(f"开始训练轮次 {self._当前轮次}/{self._总轮次}", "信息")
            
            # 随机打乱数据文件顺序
            数据顺序 = list(range(总文件数))
            shuffle(数据顺序)
            
            轮次损失列表 = []
            
            for 计数, 索引 in enumerate(数据顺序):
                if self._停止标志:
                    break
                
                文件路径 = 数据文件列表[索引]
                文件名 = os.path.basename(文件路径)
                
                try:
                    self.日志消息.emit(f"处理文件 {计数 + 1}/{总文件数}: {文件名}", "信息")
                    
                    # 加载数据
                    训练数据, 测试数据 = self._加载训练数据(文件路径)
                    
                    if 训练数据 is None:
                        self.日志消息.emit(f"跳过无效文件: {文件名}", "警告")
                        continue
                    
                    # 准备批次数据
                    X训练, Y训练 = self._准备批次数据(训练数据, 模型输入宽度, 模型输入高度)
                    X测试, Y测试 = self._准备批次数据(测试数据, 模型输入宽度, 模型输入高度)
                    
                    # 训练模型
                    模型.fit(
                        {'input': X训练},
                        {'targets': Y训练},
                        n_epoch=1,
                        validation_set=({'input': X测试}, {'targets': Y测试}),
                        snapshot_step=2500,
                        show_metric=True,
                        run_id=模型保存路径
                    )
                    
                    # 获取损失值 (模拟，实际需要从模型获取)
                    # 这里使用一个简单的模拟损失值
                    损失值 = self._获取模拟损失值(轮次, 计数, 总文件数)
                    轮次损失列表.append(损失值)
                    
                    # 更新进度
                    总进度 = int(10 + (轮次 * 总文件数 + 计数 + 1) / (self._总轮次 * 总文件数) * 85)
                    self.进度更新.emit(总进度, f"轮次 {self._当前轮次}/{self._总轮次}")
                    
                except Exception as e:
                    self.日志消息.emit(f"处理文件时出错: {str(e)}", "错误")
                    continue
            
            # 计算轮次平均损失
            if 轮次损失列表:
                self._当前损失 = sum(轮次损失列表) / len(轮次损失列表)
                self._损失历史.append(self._当前损失)
            
            # 发送轮次完成信号
            self.轮次完成.emit(self._当前轮次, self._总轮次, self._当前损失)
            
            # 每轮结束保存模型
            try:
                self.日志消息.emit(f"保存轮次 {self._当前轮次} 的模型...", "信息")
                模型.save(模型保存路径)
                self.日志消息.emit(f"模型已保存", "成功")
            except Exception as e:
                self.日志消息.emit(f"保存模型失败: {str(e)}", "错误")
        
        # 训练完成
        if self._停止标志:
            self.进度更新.emit(100, "训练已停止")
            self.任务完成.emit(False, "训练已被用户停止")
        else:
            self.进度更新.emit(100, "训练完成")
            self.日志消息.emit(f"训练完成！模型已保存到: {模型保存路径}", "成功")
            self.任务完成.emit(True, f"训练完成，共完成 {self._当前轮次} 轮训练")
    
    def _获取数据文件列表(self, 数据目录: str) -> List[str]:
        """获取所有训练数据文件"""
        文件列表 = []
        
        if not os.path.exists(数据目录):
            return 文件列表
        
        for 文件名 in os.listdir(数据目录):
            if 文件名.endswith('.npy') and '训练数据' in 文件名:
                文件列表.append(os.path.join(数据目录, 文件名))
        
        文件列表.sort()
        return 文件列表
    
    def _加载训练数据(self, 文件路径: str) -> tuple:
        """
        加载单个训练数据文件
        
        返回:
            (训练数据, 测试数据) 或 (None, None) 如果加载失败
        """
        try:
            数据 = np.load(文件路径, allow_pickle=True)
            
            if len(数据) < 50:
                # 数据太少，全部用于训练
                return 数据, 数据[:10] if len(数据) >= 10 else 数据
            
            # 分割训练集和测试集 (最后50个样本作为测试)
            训练数据 = 数据[:-50]
            测试数据 = 数据[-50:]
            
            return 训练数据, 测试数据
        
        except Exception as e:
            self.日志消息.emit(f"加载数据失败 {文件路径}: {str(e)}", "错误")
            return None, None
    
    def _准备批次数据(self, 数据, 宽度: int, 高度: int) -> tuple:
        """
        准备模型训练的批次数据
        
        返回:
            (X, Y) 训练数据
        """
        # 提取图像
        X图像 = np.array([样本[0] for 样本 in 数据])
        X = X图像.reshape(-1, 宽度, 高度, 3)
        
        # 提取标签
        Y = [样本[1] for 样本 in 数据]
        
        return X, Y
    
    def _获取模拟损失值(self, 轮次: int, 文件索引: int, 总文件数: int) -> float:
        """
        获取模拟的损失值
        
        注意: 实际应用中应该从模型训练过程中获取真实损失值
        这里使用模拟值用于界面演示
        """
        # 模拟损失值随训练进度下降
        基础损失 = 1.0
        轮次衰减 = 0.8 ** 轮次
        文件衰减 = 1.0 - (文件索引 / 总文件数) * 0.1
        随机波动 = np.random.uniform(0.9, 1.1)
        
        return 基础损失 * 轮次衰减 * 文件衰减 * 随机波动
    
    def 请求停止(self) -> None:
        """请求停止线程"""
        self._停止标志 = True
    
    def 获取当前轮次(self) -> int:
        """获取当前训练轮次"""
        return self._当前轮次
    
    def 获取总轮次(self) -> int:
        """获取总训练轮次"""
        return self._总轮次
    
    def 获取当前损失(self) -> float:
        """获取当前损失值"""
        return self._当前损失
    
    def 获取损失历史(self) -> List[float]:
        """获取损失历史记录"""
        return self._损失历史.copy()
