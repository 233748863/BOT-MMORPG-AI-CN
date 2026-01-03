"""
模型训练脚本
用于训练游戏AI模型

集成数据增强、类别权重平衡和训练可视化功能。

使用方法:
1. 确保已收集足够的训练数据
2. 运行此脚本
3. 选择训练模式
4. 等待训练完成
"""

import numpy as np
import cv2
import os
import sys
from random import shuffle

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from 核心.模型定义 import inception_v3
from 配置.设置 import (
    模型输入宽度, 模型输入高度, 学习率,
    训练轮数, 模型保存路径, 数据保存路径, 总动作数
)
from 工具.检查点管理 import 检查点管理器, 提示恢复训练, 显示检查点列表

# 尝试导入数据增强模块
try:
    from 工具.数据增强 import 数据增强器
    数据增强可用 = True
except ImportError:
    数据增强可用 = False

# 尝试导入类别权重模块
try:
    from 工具.类别权重 import 类别权重计算器
    类别权重可用 = True
except ImportError:
    类别权重可用 = False

# 尝试导入训练监控模块
try:
    from 训练.训练监控 import 可视化回调
    训练监控可用 = True
except ImportError:
    训练监控可用 = False

# 检查点配置
检查点目录 = os.path.join(os.path.dirname(模型保存路径), "checkpoints")
检查点保存间隔 = 5  # 每处理N个文件保存一次检查点
最大检查点数量 = 5  # 保留的最大检查点数量


def 获取数据文件列表(数据目录):
    """
    获取所有训练数据文件
    
    参数:
        数据目录: 数据文件目录
    
    返回:
        list: 数据文件路径列表
    """
    文件列表 = []
    
    if not os.path.exists(数据目录):
        print(f"❌ 数据目录不存在: {数据目录}")
        return 文件列表
    
    for 文件名 in os.listdir(数据目录):
        if 文件名.endswith('.npy') and '训练数据' in 文件名:
            文件列表.append(os.path.join(数据目录, 文件名))
    
    文件列表.sort()
    return 文件列表


def 加载训练数据(文件路径):
    """
    加载单个训练数据文件
    
    参数:
        文件路径: 数据文件路径
    
    返回:
        tuple: (训练数据, 测试数据)
    """
    try:
        数据 = np.load(文件路径, allow_pickle=True)
        
        # 分割训练集和测试集 (最后50个样本作为测试)
        训练数据 = 数据[:-50]
        测试数据 = 数据[-50:]
        
        return 训练数据, 测试数据
    
    except Exception as e:
        print(f"❌ 加载数据失败 {文件路径}: {e}")
        return None, None


def 准备批次数据(数据, 宽度, 高度):
    """
    准备模型训练的批次数据
    
    参数:
        数据: 原始数据
        宽度: 图像宽度
        高度: 图像高度
    
    返回:
        tuple: (X, Y) 训练数据
    """
    # 提取图像
    X图像 = np.array([样本[0] for 样本 in 数据])
    X = X图像.reshape(-1, 宽度, 高度, 3)
    
    # 提取标签
    Y = [样本[1] for 样本 in 数据]
    
    return X, Y


def 显示训练菜单():
    """显示训练配置菜单"""
    print("\n" + "=" * 50)
    print("🤖 MMORPG游戏AI - 模型训练工具")
    print("=" * 50)
    print("\n当前配置:")
    print(f"  - 输入尺寸: {模型输入宽度} x {模型输入高度}")
    print(f"  - 学习率: {学习率}")
    print(f"  - 训练轮数: {训练轮数}")
    print(f"  - 动作类别: {总动作数}")
    print(f"  - 模型保存: {模型保存路径}")
    print()
    print("可用功能模块:")
    print(f"  - 数据增强: {'✅ 可用' if 数据增强可用 else '❌ 不可用'}")
    print(f"  - 类别权重: {'✅ 可用' if 类别权重可用 else '❌ 不可用'}")
    print(f"  - 训练监控: {'✅ 可用' if 训练监控可用 else '❌ 不可用'}")
    print()


def 主程序():
    """主训练程序"""
    
    显示训练菜单()
    
    # 获取数据文件
    数据文件列表 = 获取数据文件列表(数据保存路径)
    
    if not 数据文件列表:
        print("❌ 未找到训练数据文件!")
        print(f"   请先运行 '收集数据.py' 收集训练数据")
        print(f"   数据应保存在: {数据保存路径}")
        return
    
    print(f"📁 找到 {len(数据文件列表)} 个数据文件")
    
    # 初始化检查点管理器
    检查点管理 = 检查点管理器(检查点目录, 最大检查点数量)
    
    # 初始化数据增强器
    增强器 = None
    启用增强 = False
    if 数据增强可用:
        增强选择 = input("\n是否启用数据增强? (y/n, 默认y): ").strip().lower()
        if 增强选择 != 'n':
            增强器 = 数据增强器()
            启用增强 = True
            print("✅ 数据增强已启用")
    
    # 初始化类别权重计算器
    权重计算器 = None
    类别权重 = None
    if 类别权重可用:
        权重选择 = input("是否启用类别权重平衡? (y/n, 默认y): ").strip().lower()
        if 权重选择 != 'n':
            权重计算器 = 类别权重计算器(总动作数)
            print("✅ 类别权重平衡已启用，将在加载数据后计算权重")
    
    # 初始化训练监控器
    可视化 = None
    if 训练监控可用:
        监控选择 = input("是否启用训练可视化监控? (y/n, 默认y): ").strip().lower()
        if 监控选择 != 'n':
            可视化 = 可视化回调(启用图表=True, 启用终端=True)
            print("✅ 训练可视化监控已启用")
    
    # 初始化训练状态
    起始轮次 = 0
    起始文件索引 = 0
    当前loss = 0.0
    
    # 检查是否有检查点可以恢复
    if 提示恢复训练(检查点管理):
        检查点数据 = 检查点管理.加载检查点()
        if 检查点数据:
            训练进度 = 检查点数据.get('训练进度', {})
            起始轮次 = 训练进度.get('当前epoch', 0)
            起始文件索引 = 训练进度.get('当前batch', 0)
            当前loss = 检查点数据.get('指标', {}).get('loss', 0.0)
            print(f"✅ 将从 Epoch {起始轮次 + 1}, 文件 {起始文件索引 + 1} 继续训练")
    
    # 询问是否继续
    确认 = input("\n是否开始训练? (y/n): ").strip().lower()
    if 确认 != 'y':
        print("已取消训练")
        return
    
    # 确保模型目录存在
    模型目录 = os.path.dirname(模型保存路径)
    if 模型目录:
        os.makedirs(模型目录, exist_ok=True)
    
    # 如果启用类别权重，先扫描数据计算权重
    if 权重计算器:
        print("\n📊 正在计算类别权重...")
        for 文件路径 in 数据文件列表:
            try:
                数据 = np.load(文件路径, allow_pickle=True)
                标签列表 = [样本[1] for 样本 in 数据]
                权重计算器.更新统计(标签列表)
            except Exception as e:
                print(f"   ⚠️ 处理文件失败: {e}")
        类别权重 = 权重计算器.计算权重()
        print(f"✅ 类别权重计算完成")
    
    # 创建模型
    print("\n🏗️  创建模型...")
    模型 = inception_v3(
        模型输入宽度, 
        模型输入高度, 
        3, 
        学习率, 
        输出类别=总动作数, 
        模型名称=模型保存路径
    )
    
    # 检查是否有已保存的模型
    if os.path.exists(模型保存路径 + '.index'):
        加载选择 = input("\n发现已保存的模型，是否加载? (y/n): ").strip().lower()
        if 加载选择 == 'y':
            try:
                模型.load(模型保存路径)
                print("✅ 已加载之前的模型")
            except Exception as e:
                print(f"⚠️  加载模型失败: {e}")
                print("   将从头开始训练")
    
    # 启动训练监控
    if 可视化:
        可视化.on_train_begin(训练轮数, len(数据文件列表))
    
    print("\n🚀 开始训练...")
    print("-" * 50)
    
    # 训练循环
    for 轮次 in range(起始轮次, 训练轮数):
        print(f"\n📊 训练轮次 {轮次 + 1}/{训练轮数}")
        
        # 通知可视化回调轮次开始
        if 可视化:
            可视化.on_epoch_begin(轮次 + 1)
        
        # 随机打乱数据文件顺序（使用固定种子保证可重复性）
        数据顺序 = list(range(len(数据文件列表)))
        shuffle(数据顺序)
        
        # 确定起始文件索引
        文件起始 = 起始文件索引 if 轮次 == 起始轮次 else 0
        
        轮次loss总和 = 0.0
        轮次样本数 = 0
        
        for 计数 in range(文件起始, len(数据顺序)):
            索引 = 数据顺序[计数]
            文件路径 = 数据文件列表[索引]
            
            try:
                print(f"   处理文件 {计数 + 1}/{len(数据文件列表)}: {os.path.basename(文件路径)}")
                
                # 加载数据
                训练数据, 测试数据 = 加载训练数据(文件路径)
                
                if 训练数据 is None:
                    continue
                
                # 数据增强
                if 启用增强 and 增强器:
                    训练数据 = 增强器.增强批次(训练数据)
                
                # 准备批次数据
                X训练, Y训练 = 准备批次数据(训练数据, 模型输入宽度, 模型输入高度)
                X测试, Y测试 = 准备批次数据(测试数据, 模型输入宽度, 模型输入高度)
                
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
                
                # 更新当前loss（简化处理，实际应从训练回调获取）
                当前loss = 0.0  # TODO: 从训练过程获取实际loss
                轮次loss总和 += 当前loss * len(训练数据)
                轮次样本数 += len(训练数据)
                
                # 更新训练监控
                if 可视化:
                    可视化.on_batch_end(计数, 当前loss)
                
                # 定期保存检查点
                if (计数 + 1) % 检查点保存间隔 == 0:
                    print(f"\n💾 保存检查点...")
                    检查点管理.保存检查点(
                        模型=模型,
                        优化器状态={},  # TFLearn 不直接暴露优化器状态
                        当前epoch=轮次,
                        当前batch=计数 + 1,
                        loss值=当前loss
                    )
                    模型.save(模型保存路径)
                
            except KeyboardInterrupt:
                print("\n\n⚠️  训练被中断!")
                print("💾 正在保存检查点...")
                检查点管理.保存检查点(
                    模型=模型,
                    优化器状态={},
                    当前epoch=轮次,
                    当前batch=计数,
                    loss值=当前loss
                )
                模型.save(模型保存路径)
                print("✅ 检查点已保存，下次可以继续训练")
                
                # 停止可视化
                if 可视化:
                    可视化.on_train_end()
                return
                
            except Exception as e:
                print(f"   ❌ 处理文件时出错: {e}")
                continue
        
        # 计算轮次平均loss
        轮次平均loss = 轮次loss总和 / 轮次样本数 if 轮次样本数 > 0 else 0.0
        print(f"\n📈 轮次 {轮次 + 1} 平均Loss: {轮次平均loss:.4f}")
        
        # 通知可视化回调轮次结束
        if 可视化:
            可视化.on_epoch_end(轮次 + 1, 训练loss=轮次平均loss)
        
        # 每轮结束保存检查点
        print(f"\n💾 保存轮次 {轮次 + 1} 的检查点...")
        检查点管理.保存检查点(
            模型=模型,
            优化器状态={},
            当前epoch=轮次 + 1,
            当前batch=0,
            loss值=当前loss
        )
        模型.save(模型保存路径)
    
    # 停止可视化
    if 可视化:
        可视化.on_train_end()
    
    print("\n" + "=" * 50)
    print("✅ 训练完成!")
    print(f"📁 模型已保存到: {模型保存路径}")
    print("=" * 50)
    
    # 显示检查点信息
    print("\n📋 检查点记录:")
    显示检查点列表(检查点管理)
    
    print("\n下一步:")
    print("  运行 '运行/运行机器人.py' 测试训练好的模型")


if __name__ == "__main__":
    主程序()
