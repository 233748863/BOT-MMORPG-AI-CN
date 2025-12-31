"""
数据预处理与增强工具
用于对训练数据进行预处理和数据增强，提高模型泛化能力

功能:
- 图像增强 (亮度、对比度、模糊、噪声等)
- 数据标准化
- 批量预处理
"""

import numpy as np
import cv2
import os
import sys
from random import random, uniform, randint

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from 配置.设置 import 数据保存路径, 模型输入宽度, 模型输入高度


class 图像增强器:
    """图像增强类，提供多种数据增强方法"""
    
    def __init__(self, 增强概率=0.5):
        """
        初始化增强器
        
        参数:
            增强概率: 每种增强方法的应用概率
        """
        self.增强概率 = 增强概率
    
    def 随机亮度(self, 图像, 范围=(-30, 30)):
        """随机调整亮度"""
        if random() > self.增强概率:
            return 图像
        
        值 = randint(范围[0], 范围[1])
        hsv = cv2.cvtColor(图像, cv2.COLOR_RGB2HSV)
        hsv = hsv.astype(np.float32)
        hsv[:, :, 2] = np.clip(hsv[:, :, 2] + 值, 0, 255)
        hsv = hsv.astype(np.uint8)
        return cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
    
    def 随机对比度(self, 图像, 范围=(0.8, 1.2)):
        """随机调整对比度"""
        if random() > self.增强概率:
            return 图像
        
        因子 = uniform(范围[0], 范围[1])
        均值 = np.mean(图像)
        return np.clip((图像 - 均值) * 因子 + 均值, 0, 255).astype(np.uint8)
    
    def 高斯模糊(self, 图像, 核大小范围=(3, 7)):
        """随机高斯模糊"""
        if random() > self.增强概率:
            return 图像
        
        核大小 = randint(核大小范围[0] // 2, 核大小范围[1] // 2) * 2 + 1
        return cv2.GaussianBlur(图像, (核大小, 核大小), 0)
    
    def 均值模糊(self, 图像, 核大小范围=(2, 5)):
        """随机均值模糊"""
        if random() > self.增强概率:
            return 图像
        
        核大小 = randint(核大小范围[0], 核大小范围[1])
        return cv2.blur(图像, (核大小, 核大小))
    
    def 高斯噪声(self, 图像, 标准差范围=(5, 15)):
        """添加高斯噪声"""
        if random() > self.增强概率:
            return 图像
        
        标准差 = uniform(标准差范围[0], 标准差范围[1])
        噪声 = np.random.normal(0, 标准差, 图像.shape)
        return np.clip(图像 + 噪声, 0, 255).astype(np.uint8)
    
    def 随机裁剪缩放(self, 图像, 缩放范围=(0.9, 1.0)):
        """随机裁剪并缩放回原尺寸"""
        if random() > self.增强概率:
            return 图像
        
        高, 宽 = 图像.shape[:2]
        缩放因子 = uniform(缩放范围[0], 缩放范围[1])
        
        新高 = int(高 * 缩放因子)
        新宽 = int(宽 * 缩放因子)
        
        起始y = randint(0, 高 - 新高)
        起始x = randint(0, 宽 - 新宽)
        
        裁剪图像 = 图像[起始y:起始y+新高, 起始x:起始x+新宽]
        return cv2.resize(裁剪图像, (宽, 高))
    
    def 锐化(self, 图像, 强度范围=(0.5, 1.5)):
        """图像锐化"""
        if random() > self.增强概率:
            return 图像
        
        强度 = uniform(强度范围[0], 强度范围[1])
        核 = np.array([
            [0, -强度, 0],
            [-强度, 1 + 4*强度, -强度],
            [0, -强度, 0]
        ])
        return np.clip(cv2.filter2D(图像, -1, 核), 0, 255).astype(np.uint8)
    
    def 增强图像(self, 图像, 增强列表=None):
        """
        应用多种增强方法
        
        参数:
            图像: 输入图像
            增强列表: 要应用的增强方法列表 (None表示全部)
        
        返回:
            增强后的图像
        """
        if 增强列表 is None:
            增强列表 = ['亮度', '对比度', '模糊', '噪声']
        
        结果 = 图像.copy()
        
        if '亮度' in 增强列表:
            结果 = self.随机亮度(结果)
        if '对比度' in 增强列表:
            结果 = self.随机对比度(结果)
        if '模糊' in 增强列表:
            if random() > 0.5:
                结果 = self.高斯模糊(结果)
            else:
                结果 = self.均值模糊(结果)
        if '噪声' in 增强列表:
            结果 = self.高斯噪声(结果)
        if '裁剪' in 增强列表:
            结果 = self.随机裁剪缩放(结果)
        if '锐化' in 增强列表:
            结果 = self.锐化(结果)
        
        return 结果


def 标准化图像(图像, 方法='归一化'):
    """
    图像标准化
    
    参数:
        图像: 输入图像
        方法: '归一化' (0-1) 或 '标准化' (均值0, 标准差1)
    
    返回:
        标准化后的图像
    """
    if 方法 == '归一化':
        return 图像.astype(np.float32) / 255.0
    elif 方法 == '标准化':
        图像 = 图像.astype(np.float32)
        均值 = np.mean(图像)
        标准差 = np.std(图像)
        return (图像 - 均值) / (标准差 + 1e-7)
    else:
        return 图像


def 预处理图像(图像, 目标宽度=None, 目标高度=None, 颜色转换=True):
    """
    预处理单张图像
    
    参数:
        图像: 输入图像 (BGR格式)
        目标宽度: 目标宽度 (None使用配置值)
        目标高度: 目标高度 (None使用配置值)
        颜色转换: 是否转换为RGB
    
    返回:
        预处理后的图像
    """
    if 目标宽度 is None:
        目标宽度 = 模型输入宽度
    if 目标高度 is None:
        目标高度 = 模型输入高度
    
    # 调整尺寸
    结果 = cv2.resize(图像, (目标宽度, 目标高度))
    
    # 颜色转换
    if 颜色转换:
        结果 = cv2.cvtColor(结果, cv2.COLOR_BGR2RGB)
    
    return 结果


def 增强训练数据(训练数据, 增强倍数=2, 增强概率=0.5):
    """
    增强训练数据集
    
    参数:
        训练数据: 原始训练数据 [(图像, 动作), ...]
        增强倍数: 数据增强倍数
        增强概率: 每种增强方法的应用概率
    
    返回:
        增强后的训练数据
    """
    增强器 = 图像增强器(增强概率=增强概率)
    增强后数据 = list(训练数据)  # 保留原始数据
    
    print(f"📊 原始数据量: {len(训练数据)}")
    print(f"🔄 增强倍数: {增强倍数}")
    
    for 倍数 in range(增强倍数 - 1):
        print(f"   处理第 {倍数 + 1} 轮增强...")
        for 图像, 动作 in 训练数据:
            增强图像 = 增强器.增强图像(图像)
            增强后数据.append([增强图像, 动作])
    
    print(f"✅ 增强后数据量: {len(增强后数据)}")
    
    return 增强后数据


def 预处理数据文件(文件路径, 输出路径=None, 增强=True, 增强倍数=2):
    """
    预处理单个数据文件
    
    参数:
        文件路径: 输入文件路径
        输出路径: 输出文件路径
        增强: 是否进行数据增强
        增强倍数: 数据增强倍数
    """
    print(f"\n📂 加载数据: {文件路径}")
    
    try:
        数据 = np.load(文件路径, allow_pickle=True)
        print(f"   原始样本数: {len(数据)}")
        
        处理后数据 = list(数据)
        
        # 数据增强
        if 增强:
            处理后数据 = 增强训练数据(处理后数据, 增强倍数=增强倍数)
        
        # 保存
        if 输出路径 is None:
            输出路径 = 文件路径.replace('.npy', '_augmented.npy')
        
        np.save(输出路径, 处理后数据)
        print(f"💾 已保存到: {输出路径}")
        
    except Exception as e:
        print(f"❌ 处理失败: {e}")


def 批量预处理数据():
    """批量预处理所有训练数据文件"""
    
    print("\n" + "=" * 50)
    print("🔧 数据预处理工具")
    print("=" * 50)
    
    # 获取所有数据文件
    数据文件列表 = []
    if os.path.exists(数据保存路径):
        for 文件名 in os.listdir(数据保存路径):
            if 文件名.endswith('.npy') and 'augmented' not in 文件名 and 'cleaned' not in 文件名:
                数据文件列表.append(os.path.join(数据保存路径, 文件名))
    
    if not 数据文件列表:
        print(f"❌ 未找到数据文件: {数据保存路径}")
        return
    
    print(f"\n📁 找到 {len(数据文件列表)} 个数据文件")
    
    # 询问增强参数
    print("\n请选择预处理选项:")
    print("  1. 仅数据增强 (2倍)")
    print("  2. 数据增强 (3倍)")
    print("  3. 不增强，仅标准化")
    
    选择 = input("\n请输入选项 (1/2/3): ").strip()
    
    增强 = 选择 in ['1', '2']
    增强倍数 = 3 if 选择 == '2' else 2
    
    for 文件路径 in 数据文件列表:
        预处理数据文件(文件路径, 增强=增强, 增强倍数=增强倍数)
    
    print("\n" + "=" * 50)
    print("✅ 批量预处理完成!")
    print("=" * 50)


if __name__ == "__main__":
    批量预处理数据()
