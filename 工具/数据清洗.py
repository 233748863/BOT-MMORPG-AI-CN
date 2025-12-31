"""
数据清洗工具
用于平衡训练数据，避免某些动作类别过多导致模型偏向

使用方法:
1. 运行此脚本
2. 选择要清洗的数据文件
3. 自动平衡各类别样本数量
"""

import numpy as np
import pandas as pd
import os
import sys
from random import shuffle
import matplotlib.pyplot as plt

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from 配置.设置 import 数据保存路径, 总动作数, 动作定义


def 数据帧转数组_输入(数据帧, 索引):
    """将数据帧的一行转换为numpy数组"""
    列表 = 数据帧.loc[[索引]].values.tolist()
    数组 = np.array(列表).ravel()
    return 数组


def 数据帧转数组_图像(图像数据帧, 索引):
    """将图像数据帧的一行转换为numpy数组"""
    图像数据 = 图像数据帧.loc[[索引]].T.to_numpy()
    列表 = 图像数据.tolist()
    展平列表 = [val.tolist() for sublist in 列表 for val in sublist]
    数组 = np.array(展平列表)
    return 数组


def 清洗数据(训练数据, 目标列=0, 显示图表=False):
    """
    清洗训练数据，平衡各类别样本数量
    
    参数:
        训练数据: 原始训练数据 [(图像, 动作), ...]
        目标列: 用于平衡的目标列索引 (默认为第一个动作)
        显示图表: 是否显示分布图表
    
    返回:
        tuple: (清洗后的图像数据帧, 清洗后的输入数据帧)
    """
    # 创建输入数据帧
    输入数据帧 = pd.DataFrame()
    for i in range(len(训练数据)):
        行 = list(训练数据[i][1])
        临时帧 = pd.DataFrame([行])
        输入数据帧 = pd.concat([输入数据帧, 临时帧])
    输入数据帧 = 输入数据帧.reset_index(drop=True)
    
    # 清洗参数
    分箱数 = 25
    # 计算阈值 (非零值的数量)
    阈值 = (输入数据帧[目标列] != 0).astype(int).sum(axis=0)
    每箱样本数 = max(阈值, 100)  # 至少保留100个样本
    
    # 计算直方图
    直方图, 分箱边界 = np.histogram(输入数据帧[目标列], 分箱数)
    中心点 = (分箱边界[:-1] + 分箱边界[1:]) * 0.5
    
    # 清洗过程 - 移除过多的样本
    移除列表 = []
    for j in range(分箱数):
        当前箱列表 = []
        for i in range(len(输入数据帧[目标列])):
            序列 = 输入数据帧[目标列].iloc[[i]]
            值 = 序列.tolist()[0]
            if 值 >= 分箱边界[j] and 值 <= 分箱边界[j+1]:
                当前箱列表.append(i)
        
        # 随机打乱后移除超出阈值的样本
        shuffle(当前箱列表)
        移除列表.extend(当前箱列表[每箱样本数:])
    
    # 执行清洗
    输入数据帧.drop(输入数据帧.index[移除列表], inplace=True)
    print(f'✅ 清洗后剩余样本数: {len(输入数据帧)}')
    输入数据帧 = 输入数据帧.reset_index(drop=True)
    
    if 显示图表:
        # 可视化清洗结果
        直方图, _ = np.histogram(输入数据帧[目标列], 分箱数)
        plt.figure(figsize=(10, 6))
        plt.bar(中心点, 直方图, width=0.05)
        plt.axhline(y=每箱样本数, color='r', linestyle='--', label=f'阈值: {每箱样本数}')
        plt.xlabel('动作值')
        plt.ylabel('样本数量')
        plt.title('数据清洗后的分布')
        plt.legend()
        plt.show()
    
    # 创建图像数据帧
    图像数据帧 = pd.DataFrame()
    for i in range(len(训练数据)):
        行 = list(训练数据[i][0])
        临时帧 = pd.DataFrame([行])
        图像数据帧 = pd.concat([图像数据帧, 临时帧])
    图像数据帧 = 图像数据帧.reset_index(drop=True)
    
    # 同步清洗图像数据
    图像数据帧.drop(图像数据帧.index[移除列表], inplace=True)
    图像数据帧 = 图像数据帧.reset_index(drop=True)
    
    # 验证维度一致
    assert len(输入数据帧) == len(图像数据帧), "❌ 清洗后维度不一致!"
    
    return 图像数据帧, 输入数据帧


def 按动作类别平衡(训练数据, 最大每类样本数=None):
    """
    按动作类别平衡数据
    
    参数:
        训练数据: 原始训练数据 [(图像, 动作), ...]
        最大每类样本数: 每个类别最多保留的样本数 (None表示自动计算)
    
    返回:
        list: 平衡后的训练数据
    """
    # 统计各类别数量
    类别统计 = {i: [] for i in range(总动作数)}
    
    for 索引, (图像, 动作) in enumerate(训练数据):
        if isinstance(动作, (list, np.ndarray)):
            类别 = np.argmax(动作)
        else:
            类别 = 动作
        类别统计[类别].append(索引)
    
    # 显示原始分布
    print("\n📊 原始数据分布:")
    for 类别, 索引列表 in 类别统计.items():
        if len(索引列表) > 0:
            动作名 = 动作定义.get(类别, {}).get("名称", f"动作{类别}")
            print(f"   {动作名}: {len(索引列表)} 样本")
    
    # 计算平衡阈值
    非空类别数量 = [len(v) for v in 类别统计.values() if len(v) > 0]
    if not 非空类别数量:
        print("❌ 没有有效数据")
        return 训练数据
    
    if 最大每类样本数 is None:
        # 使用中位数作为阈值
        最大每类样本数 = int(np.median(非空类别数量))
    
    print(f"\n🎯 平衡阈值: 每类最多 {最大每类样本数} 样本")
    
    # 平衡数据
    平衡后索引 = []
    for 类别, 索引列表 in 类别统计.items():
        if len(索引列表) > 0:
            shuffle(索引列表)
            平衡后索引.extend(索引列表[:最大每类样本数])
    
    # 打乱顺序
    shuffle(平衡后索引)
    
    # 构建平衡后的数据
    平衡后数据 = [训练数据[i] for i in 平衡后索引]
    
    print(f"\n✅ 平衡后总样本数: {len(平衡后数据)}")
    
    return 平衡后数据


def 清洗数据文件(文件路径, 输出路径=None):
    """
    清洗单个数据文件
    
    参数:
        文件路径: 输入文件路径
        输出路径: 输出文件路径 (None表示覆盖原文件)
    """
    print(f"\n📂 加载数据: {文件路径}")
    
    try:
        数据 = np.load(文件路径, allow_pickle=True)
        print(f"   原始样本数: {len(数据)}")
        
        # 平衡数据
        平衡后数据 = 按动作类别平衡(list(数据))
        
        # 保存
        if 输出路径 is None:
            输出路径 = 文件路径.replace('.npy', '_cleaned.npy')
        
        np.save(输出路径, 平衡后数据)
        print(f"💾 已保存到: {输出路径}")
        
    except Exception as e:
        print(f"❌ 处理失败: {e}")


def 批量清洗数据():
    """批量清洗所有训练数据文件"""
    
    print("\n" + "=" * 50)
    print("🧹 数据清洗工具")
    print("=" * 50)
    
    # 获取所有数据文件
    数据文件列表 = []
    if os.path.exists(数据保存路径):
        for 文件名 in os.listdir(数据保存路径):
            if 文件名.endswith('.npy') and 'cleaned' not in 文件名:
                数据文件列表.append(os.path.join(数据保存路径, 文件名))
    
    if not 数据文件列表:
        print(f"❌ 未找到数据文件: {数据保存路径}")
        return
    
    print(f"\n📁 找到 {len(数据文件列表)} 个数据文件")
    
    for 文件路径 in 数据文件列表:
        清洗数据文件(文件路径)
    
    print("\n" + "=" * 50)
    print("✅ 批量清洗完成!")
    print("=" * 50)


if __name__ == "__main__":
    批量清洗数据()
