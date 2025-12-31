"""
类别权重分配工具
用于自动调整各动作类别的权重，优化模型预测分布

使用方法:
1. 准备验证数据集
2. 运行此脚本
3. 自动迭代优化权重
4. 将优化后的权重应用到配置文件
"""

import numpy as np
import os
import sys
from collections import Counter

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from 配置.设置 import 总动作数, 动作定义, 数据保存路径


# 动作映射字典
动作映射 = {i: 动作定义.get(i, {}).get("名称", f"动作{i}") for i in range(总动作数)}

# 相近动作字典 - 定义哪些动作可以被认为是"接近正确"的
# 格式: {正确动作: {预测动作: 相似度分数}}
相近动作 = {
    0: {4: 0.3, 5: 0.3, 8: 0.05},   # 前进 -> 前进+左/右, 无操作
    1: {6: 0.3, 7: 0.3, 8: 0.05},   # 后退 -> 后退+左/右, 无操作
    2: {4: 0.3, 6: 0.3},             # 左移 -> 前进+左, 后退+左
    3: {5: 0.3, 7: 0.3},             # 右移 -> 前进+右, 后退+右
    4: {0: 0.5, 2: 0.5},             # 前进+左 -> 前进, 左移
    5: {0: 0.5, 3: 0.5},             # 前进+右 -> 前进, 右移
    6: {1: 0.3, 2: 0.3},             # 后退+左 -> 后退, 左移
    7: {1: 0.3, 3: 0.3},             # 后退+右 -> 后退, 右移
    8: {i: 0.05 for i in range(8)},  # 无操作 -> 任何移动都算接近
}


class 权重优化器:
    """动作类别权重优化器"""
    
    def __init__(self, 初始权重=None, 衰减率=0.9):
        """
        初始化优化器
        
        参数:
            初始权重: 初始权重列表 (None表示全1)
            衰减率: 权重衰减率
        """
        if 初始权重 is None:
            self.权重 = [1.0] * 总动作数
        else:
            self.权重 = list(初始权重)
        
        self.衰减率 = 衰减率
        self.历史记录 = []
    
    def 评估(self, 验证数据, 模型):
        """
        评估当前权重的效果
        
        参数:
            验证数据: 验证数据集 [(图像, 动作), ...]
            模型: 训练好的模型
        
        返回:
            tuple: (准确率, 相似度准确率, 分布统计)
        """
        总数 = 0
        正确数 = 0
        相似度分数 = 0
        分布统计 = Counter()
        
        for 图像, 真实动作 in 验证数据:
            总数 += 1
            
            # 获取真实标签
            if isinstance(真实动作, (list, np.ndarray)):
                真实标签 = np.argmax(真实动作)
            else:
                真实标签 = 真实动作
            
            # 模型预测
            预测结果 = 模型.predict([图像.reshape(-1, 图像.shape[0], 图像.shape[1], 图像.shape[2])])[0]
            
            # 应用权重
            加权预测 = np.array(预测结果) * np.array(self.权重)
            预测标签 = np.argmax(加权预测)
            
            分布统计[预测标签] += 1
            
            # 计算准确率
            if 预测标签 == 真实标签:
                正确数 += 1
                相似度分数 += 1
            elif 真实标签 in 相近动作 and 预测标签 in 相近动作[真实标签]:
                相似度分数 += 相近动作[真实标签][预测标签]
        
        准确率 = 正确数 / 总数 if 总数 > 0 else 0
        相似度准确率 = 相似度分数 / 总数 if 总数 > 0 else 0
        
        return 准确率, 相似度准确率, dict(分布统计)
    
    def 优化一步(self, 分布统计):
        """
        执行一步权重优化
        
        参数:
            分布统计: 预测分布统计字典
        """
        if not 分布统计:
            return
        
        # 找到预测最多的类别
        最大类别 = max(分布统计, key=分布统计.get)
        
        # 降低该类别的权重
        self.权重[最大类别] *= self.衰减率
        
        # 记录历史
        self.历史记录.append({
            '权重': self.权重.copy(),
            '分布': 分布统计.copy()
        })
    
    def 迭代优化(self, 验证数据, 模型, 迭代次数=10):
        """
        迭代优化权重
        
        参数:
            验证数据: 验证数据集
            模型: 训练好的模型
            迭代次数: 优化迭代次数
        """
        print("\n🔄 开始权重优化...")
        print("-" * 60)
        
        for 轮次 in range(迭代次数):
            准确率, 相似度准确率, 分布统计 = self.评估(验证数据, 模型)
            
            print(f"\n轮次 {轮次 + 1}/{迭代次数}")
            print(f"  准确率: {准确率:.3f}")
            print(f"  相似度准确率: {相似度准确率:.3f}")
            print(f"  分布: {分布统计}")
            
            self.优化一步(分布统计)
        
        print("\n" + "-" * 60)
        print("✅ 优化完成!")
        print(f"\n最终权重:")
        for i, w in enumerate(self.权重):
            动作名 = 动作映射.get(i, f"动作{i}")
            print(f"  {动作名}: {w:.4f}")
    
    def 获取权重(self):
        """获取当前权重"""
        return self.权重.copy()
    
    def 导出权重(self, 文件路径):
        """导出权重到文件"""
        with open(文件路径, 'w', encoding='utf-8') as f:
            f.write("# 优化后的动作权重\n")
            f.write("# 可以复制到 配置/设置.py 中使用\n\n")
            f.write("动作权重 = [\n")
            for i, w in enumerate(self.权重):
                动作名 = 动作映射.get(i, f"动作{i}")
                f.write(f"    {w:.4f},  # {i}: {动作名}\n")
            f.write("]\n")
        print(f"💾 权重已导出到: {文件路径}")


def 从数据计算初始权重(数据路径=None):
    """
    根据训练数据计算初始权重 (反比于类别频率)
    
    参数:
        数据路径: 数据目录路径
    
    返回:
        list: 初始权重列表
    """
    if 数据路径 is None:
        数据路径 = 数据保存路径
    
    类别计数 = Counter()
    总样本数 = 0
    
    # 统计各类别数量
    if os.path.exists(数据路径):
        for 文件名 in os.listdir(数据路径):
            if 文件名.endswith('.npy'):
                try:
                    数据 = np.load(os.path.join(数据路径, 文件名), allow_pickle=True)
                    for _, 动作 in 数据:
                        if isinstance(动作, (list, np.ndarray)):
                            类别 = np.argmax(动作)
                        else:
                            类别 = 动作
                        类别计数[类别] += 1
                        总样本数 += 1
                except Exception as e:
                    print(f"⚠️  加载 {文件名} 失败: {e}")
    
    if 总样本数 == 0:
        print("❌ 未找到训练数据")
        return [1.0] * 总动作数
    
    # 计算权重 (反比于频率)
    权重 = []
    for i in range(总动作数):
        频率 = 类别计数.get(i, 1) / 总样本数
        # 使用反比权重，但限制范围
        w = min(1.0 / (频率 * 总动作数 + 0.01), 10.0)
        权重.append(w)
    
    # 归一化
    最大权重 = max(权重)
    权重 = [w / 最大权重 for w in 权重]
    
    return 权重


def 显示数据分布(数据路径=None):
    """显示训练数据的类别分布"""
    if 数据路径 is None:
        数据路径 = 数据保存路径
    
    类别计数 = Counter()
    
    if os.path.exists(数据路径):
        for 文件名 in os.listdir(数据路径):
            if 文件名.endswith('.npy'):
                try:
                    数据 = np.load(os.path.join(数据路径, 文件名), allow_pickle=True)
                    for _, 动作 in 数据:
                        if isinstance(动作, (list, np.ndarray)):
                            类别 = np.argmax(动作)
                        else:
                            类别 = 动作
                        类别计数[类别] += 1
                except:
                    pass
    
    print("\n📊 训练数据类别分布:")
    print("-" * 40)
    总数 = sum(类别计数.values())
    for 类别 in sorted(类别计数.keys()):
        数量 = 类别计数[类别]
        百分比 = 数量 / 总数 * 100 if 总数 > 0 else 0
        动作名 = 动作映射.get(类别, f"动作{类别}")
        条形 = "█" * int(百分比 / 2)
        print(f"  {动作名:12s}: {数量:5d} ({百分比:5.1f}%) {条形}")
    print("-" * 40)
    print(f"  总计: {总数}")


def 主程序():
    """主程序入口"""
    print("\n" + "=" * 50)
    print("⚖️  类别权重分配工具")
    print("=" * 50)
    
    print("\n请选择功能:")
    print("  1. 显示数据分布")
    print("  2. 计算初始权重")
    print("  3. 迭代优化权重 (需要模型)")
    
    选择 = input("\n请输入选项 (1/2/3): ").strip()
    
    if 选择 == '1':
        显示数据分布()
    
    elif 选择 == '2':
        权重 = 从数据计算初始权重()
        print("\n📊 计算得到的初始权重:")
        for i, w in enumerate(权重):
            动作名 = 动作映射.get(i, f"动作{i}")
            print(f"  {动作名}: {w:.4f}")
        
        # 询问是否导出
        导出 = input("\n是否导出权重? (y/n): ").strip().lower()
        if 导出 == 'y':
            优化器 = 权重优化器(初始权重=权重)
            优化器.导出权重("工具/优化权重.txt")
    
    elif 选择 == '3':
        print("\n⚠️  迭代优化需要加载训练好的模型")
        print("   请确保已完成模型训练")
        print("\n此功能需要在代码中调用:")
        print("   from 工具.类别权重 import 权重优化器")
        print("   优化器 = 权重优化器()")
        print("   优化器.迭代优化(验证数据, 模型)")


if __name__ == "__main__":
    主程序()
