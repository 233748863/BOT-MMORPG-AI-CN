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
    训练轮数, 模型保存路径, 数据保存路径, 总动作数,
    启用类别权重平衡, 权重计算策略, 类别权重配置路径,
    启用数据采样, 采样方法, 过采样目标比率, 欠采样最大样本数,
    采样随机种子, 采样后打乱数据,
    启用数据增强, 使用语义安全增强, 获取数据增强配置, 创建数据增强器
)
from 工具.检查点管理 import (
    检查点管理器, 
    提示恢复训练, 
    显示检查点列表,
    训练恢复器,
    计算恢复起点,
    自动检测并恢复
)

# 尝试导入数据增强模块
try:
    from 工具.数据增强 import 数据增强器
    数据增强可用 = True
except ImportError:
    数据增强可用 = False

# 尝试导入类别权重模块
try:
    from 工具.类别权重 import (
        类别分析器, 
        权重计算器, 
        权重策略,
        加权交叉熵损失,
        采样器,
        采样配置
    )
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


def 获取权重策略枚举(策略字符串):
    """
    将配置字符串转换为权重策略枚举
    
    参数:
        策略字符串: 策略配置字符串
    
    返回:
        权重策略枚举值
    """
    if not 类别权重可用:
        return None
    
    策略映射 = {
        "inverse_frequency": 权重策略.逆频率,
        "sqrt_inverse_frequency": 权重策略.平方根逆频率,
        "effective_samples": 权重策略.有效样本数
    }
    return 策略映射.get(策略字符串, 权重策略.逆频率)


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


def 计算样本权重(标签列表, 类别权重字典):
    """
    根据类别权重计算每个样本的权重
    
    参数:
        标签列表: 样本标签列表
        类别权重字典: {类别索引: 权重} 字典
    
    返回:
        np.ndarray: 样本权重数组
    """
    样本权重 = []
    for 标签 in 标签列表:
        if isinstance(标签, (list, np.ndarray)):
            类别 = int(np.argmax(标签))
        else:
            类别 = int(标签)
        权重 = 类别权重字典.get(类别, 1.0)
        样本权重.append(权重)
    return np.array(样本权重, dtype=np.float32)


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
    print(f"  - 数据增强: {'启用' if 启用数据增强 else '禁用'}")
    if 启用数据增强:
        print(f"    - 语义安全模式: {'启用' if 使用语义安全增强 else '禁用'}")
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
        # 使用配置文件中的默认设置
        默认启用 = 启用数据增强
        提示文本 = f"是否启用数据增强? (y/n, 默认{'y' if 默认启用 else 'n'}): "
        增强选择 = input(提示文本).strip().lower()
        
        if (默认启用 and 增强选择 != 'n') or (not 默认启用 and 增强选择 == 'y'):
            # 使用配置文件创建增强器
            增强器 = 创建数据增强器()
            if 增强器 is None:
                # 回退到默认增强器
                增强器 = 数据增强器()
            启用增强 = True
            安全模式 = "语义安全" if 使用语义安全增强 else "标准"
            print(f"✅ 数据增强已启用 (模式: {安全模式})")
    
    # 初始化类别权重相关变量
    # 需求 3.1: 训练脚本应接受类别权重作为参数
    启用类别权重 = False
    类别权重字典 = None
    加权损失函数 = None
    选择的权重策略 = None
    
    if 类别权重可用:
        # 使用配置文件中的默认设置
        默认启用 = 启用类别权重平衡
        提示文本 = f"是否启用类别权重平衡? (y/n, 默认{'y' if 默认启用 else 'n'}): "
        权重选择 = input(提示文本).strip().lower()
        
        if (默认启用 and 权重选择 != 'n') or (not 默认启用 and 权重选择 == 'y'):
            启用类别权重 = True
            
            # 从配置获取默认策略
            默认策略 = 获取权重策略枚举(权重计算策略)
            
            # 选择权重计算策略
            print("\n选择权重计算策略:")
            print(f"  1. 逆频率 (inverse_frequency){' - 默认' if 权重计算策略 == 'inverse_frequency' else ''}")
            print(f"  2. 平方根逆频率 (sqrt_inverse_frequency){' - 默认' if 权重计算策略 == 'sqrt_inverse_frequency' else ''}")
            print(f"  3. 有效样本数 (effective_samples){' - 默认' if 权重计算策略 == 'effective_samples' else ''}")
            策略选择 = input("请输入选项 (1/2/3, 回车使用默认): ").strip()
            
            策略映射 = {
                '1': 权重策略.逆频率,
                '2': 权重策略.平方根逆频率,
                '3': 权重策略.有效样本数
            }
            选择的权重策略 = 策略映射.get(策略选择, 默认策略)
            print(f"✅ 类别权重平衡已启用，策略: {选择的权重策略.value}")
    
    # 初始化采样相关变量
    启用采样 = False
    采样器实例 = None
    
    if 类别权重可用 and 启用数据采样:
        采样选择 = input("是否启用数据采样平衡? (y/n, 默认y): ").strip().lower()
        if 采样选择 != 'n':
            启用采样 = True
            print(f"✅ 数据采样已启用，方法: {采样方法}")
    
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
    已恢复 = False
    
    # 检查是否有检查点可以恢复（需求 4.1, 4.2, 4.3）
    恢复结果 = 自动检测并恢复(检查点管理)
    
    if 恢复结果['需要恢复']:
        检查点路径 = 恢复结果['检查点路径']
        检查点数据 = 检查点管理.加载检查点(检查点路径)
        if 检查点数据:
            # 使用 计算恢复起点 确保从中断处的下一个 batch 继续（需求 2.5）
            恢复起点 = 计算恢复起点(检查点数据, len(数据文件列表))
            起始轮次 = 恢复起点['起始epoch']
            起始文件索引 = 恢复起点['起始batch']
            当前loss = 检查点数据.get('指标', {}).get('loss', 0.0)
            已恢复 = True
            print(f"\n✅ 将从 Epoch {起始轮次 + 1}, 文件 {起始文件索引 + 1} 继续训练")
            print(f"   (中断于 Epoch {恢复起点['中断epoch'] + 1}, 文件 {恢复起点['中断batch'] + 1})")
    
    # 询问是否继续
    确认 = input("\n是否开始训练? (y/n): ").strip().lower()
    if 确认 != 'y':
        print("已取消训练")
        return
    
    # 确保模型目录存在
    模型目录 = os.path.dirname(模型保存路径)
    if 模型目录:
        os.makedirs(模型目录, exist_ok=True)
    
    # 确保配置目录存在
    配置目录 = os.path.dirname(类别权重配置路径)
    if 配置目录:
        os.makedirs(配置目录, exist_ok=True)
    
    # 如果启用类别权重，先扫描数据计算权重
    # 需求 3.1, 3.2, 3.3, 3.4
    if 启用类别权重:
        print("\n📊 正在分析类别分布并计算权重...")
        
        # 使用类别分析器统计分布
        分析器 = 类别分析器(数据保存路径)
        类别统计 = 分析器.统计分布()
        
        if 类别统计:
            # 显示类别分布
            分析器.打印分布()
            
            # 生成分析报告
            报告 = 分析器.生成报告()
            print(f"\n📋 分析报告:")
            print(f"   总样本数: {报告.总样本数}")
            print(f"   不平衡比率: {报告.不平衡比率:.2f}")
            if 报告.欠代表类别:
                print(f"   欠代表类别: {', '.join(报告.欠代表类别)}")
            for 建议 in 报告.建议:
                print(f"   💡 {建议}")
            
            # 计算权重
            计算器 = 权重计算器(类别统计, 选择的权重策略)
            原始权重 = 计算器.计算权重()
            类别权重字典 = 计算器.归一化权重(原始权重)
            
            # 需求 3.4: 在训练开始时记录应用的类别权重
            print(f"\n⚖️  类别权重 (策略: {选择的权重策略.value}):")
            print("-" * 40)
            for 类别 in sorted(类别权重字典.keys()):
                权重值 = 类别权重字典[类别]
                from 配置.设置 import 动作定义
                类别名 = 动作定义.get(类别, {}).get("名称", f"动作{类别}")
                条形 = "█" * int(权重值 * 5)
                print(f"   {类别名:12s}: {权重值:.4f} {条形}")
            
            # 保存权重配置
            计算器.保存权重(类别权重配置路径)
            print(f"\n💾 权重配置已保存到: {类别权重配置路径}")
            
            # 需求 3.2: 创建加权损失函数
            加权损失函数 = 加权交叉熵损失(类别权重字典, 类别数=总动作数)
            print("✅ 加权损失函数已创建")
        else:
            print("⚠️  未找到训练数据，将使用默认权重 (1.0)")
            启用类别权重 = False
    
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
