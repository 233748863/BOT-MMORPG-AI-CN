"""
YOLO目标检测工具
用于游戏画面中的目标检测，如怪物、NPC、物品等

功能:
- 边界框处理
- 非极大值抑制 (NMS)
- 目标绘制
- IoU计算
"""

import numpy as np
import cv2
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class 边界框:
    """边界框类，用于存储检测到的目标信息"""
    
    def __init__(self, x最小, y最小, x最大, y最大, 置信度=None, 类别概率=None):
        """
        初始化边界框
        
        参数:
            x最小: 左边界
            y最小: 上边界
            x最大: 右边界
            y最大: 下边界
            置信度: 检测置信度
            类别概率: 各类别的概率数组
        """
        self.x最小 = x最小
        self.y最小 = y最小
        self.x最大 = x最大
        self.y最大 = y最大
        self.置信度 = 置信度
        self.类别概率 = 类别概率
        self._标签 = -1
        self._分数 = -1
    
    def 获取标签(self):
        """获取预测的类别标签"""
        if self._标签 == -1 and self.类别概率 is not None:
            self._标签 = np.argmax(self.类别概率)
        return self._标签
    
    def 获取分数(self):
        """获取预测分数"""
        if self._分数 == -1 and self.类别概率 is not None:
            self._分数 = self.类别概率[self.获取标签()]
        return self._分数
    
    def 获取宽度(self):
        """获取边界框宽度"""
        return self.x最大 - self.x最小
    
    def 获取高度(self):
        """获取边界框高度"""
        return self.y最大 - self.y最小
    
    def 获取面积(self):
        """获取边界框面积"""
        return self.获取宽度() * self.获取高度()
    
    def 获取中心(self):
        """获取边界框中心点"""
        中心x = (self.x最小 + self.x最大) / 2
        中心y = (self.y最小 + self.y最大) / 2
        return 中心x, 中心y


class 权重读取器:
    """用于读取预训练权重文件"""
    
    def __init__(self, 权重文件):
        """
        初始化权重读取器
        
        参数:
            权重文件: 权重文件路径
        """
        self.偏移量 = 4
        self.所有权重 = np.fromfile(权重文件, dtype='float32')
    
    def 读取字节(self, 大小):
        """读取指定大小的权重数据"""
        self.偏移量 = self.偏移量 + 大小
        return self.所有权重[self.偏移量 - 大小:self.偏移量]
    
    def 重置(self):
        """重置读取位置"""
        self.偏移量 = 4


def 计算IoU(框1, 框2):
    """
    计算两个边界框的交并比 (IoU)
    
    参数:
        框1: 第一个边界框
        框2: 第二个边界框
    
    返回:
        float: IoU值
    """
    # 计算交集
    交集宽度 = _区间重叠([框1.x最小, 框1.x最大], [框2.x最小, 框2.x最大])
    交集高度 = _区间重叠([框1.y最小, 框1.y最大], [框2.y最小, 框2.y最大])
    交集面积 = 交集宽度 * 交集高度
    
    # 计算并集
    宽1, 高1 = 框1.x最大 - 框1.x最小, 框1.y最大 - 框1.y最小
    宽2, 高2 = 框2.x最大 - 框2.x最小, 框2.y最大 - 框2.y最小
    并集面积 = 宽1 * 高1 + 宽2 * 高2 - 交集面积
    
    if 并集面积 == 0:
        return 0
    
    return float(交集面积) / 并集面积


def _区间重叠(区间a, 区间b):
    """计算两个区间的重叠长度"""
    x1, x2 = 区间a
    x3, x4 = 区间b
    
    if x3 < x1:
        if x4 < x1:
            return 0
        else:
            return min(x2, x4) - x1
    else:
        if x2 < x3:
            return 0
        else:
            return min(x2, x4) - x3


def _sigmoid(x):
    """Sigmoid激活函数"""
    return 1.0 / (1.0 + np.exp(-x))


def _softmax(x, axis=-1, t=-100.0):
    """Softmax激活函数"""
    x = x - np.max(x)
    
    if np.min(x) < t:
        x = x / np.min(x) * t
    
    e_x = np.exp(x)
    return e_x / e_x.sum(axis, keepdims=True)


def 绘制边界框(图像, 边界框列表, 标签列表, 颜色=(0, 255, 0), 线宽=2):
    """
    在图像上绘制边界框
    
    参数:
        图像: 输入图像
        边界框列表: 边界框对象列表
        标签列表: 类别标签名称列表
        颜色: 边界框颜色 (BGR)
        线宽: 线条宽度
    
    返回:
        绘制后的图像
    """
    图像高度, 图像宽度, _ = 图像.shape
    
    for 框 in 边界框列表:
        x最小 = int(框.x最小 * 图像宽度)
        y最小 = int(框.y最小 * 图像高度)
        x最大 = int(框.x最大 * 图像宽度)
        y最大 = int(框.y最大 * 图像高度)
        
        # 绘制矩形
        cv2.rectangle(图像, (x最小, y最小), (x最大, y最大), 颜色, 线宽)
        
        # 绘制标签
        标签索引 = 框.获取标签()
        if 标签索引 < len(标签列表):
            标签文本 = f"{标签列表[标签索引]} {框.获取分数():.2f}"
        else:
            标签文本 = f"类别{标签索引} {框.获取分数():.2f}"
        
        cv2.putText(
            图像, 标签文本,
            (x最小, y最小 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5, 颜色, 1
        )
    
    return 图像


def 解码网络输出(网络输出, 锚框, 类别数, 目标阈值=0.3, NMS阈值=0.3):
    """
    解码YOLO网络输出
    
    参数:
        网络输出: 网络输出张量
        锚框: 锚框列表
        类别数: 类别数量
        目标阈值: 目标置信度阈值
        NMS阈值: 非极大值抑制阈值
    
    返回:
        list: 检测到的边界框列表
    """
    网格高度, 网格宽度, 框数量 = 网络输出.shape[:3]
    边界框列表 = []
    
    # 解码网络输出
    网络输出[..., 4] = _sigmoid(网络输出[..., 4])
    网络输出[..., 5:] = 网络输出[..., 4][..., np.newaxis] * _softmax(网络输出[..., 5:])
    网络输出[..., 5:] *= 网络输出[..., 5:] > 目标阈值
    
    for 行 in range(网格高度):
        for 列 in range(网格宽度):
            for b in range(框数量):
                类别概率 = 网络输出[行, 列, b, 5:]
                
                if np.sum(类别概率) > 0:
                    x, y, w, h = 网络输出[行, 列, b, :4]
                    
                    x = (列 + _sigmoid(x)) / 网格宽度
                    y = (行 + _sigmoid(y)) / 网格高度
                    w = 锚框[2 * b + 0] * np.exp(w) / 网格宽度
                    h = 锚框[2 * b + 1] * np.exp(h) / 网格高度
                    置信度 = 网络输出[行, 列, b, 4]
                    
                    框 = 边界框(x - w/2, y - h/2, x + w/2, y + h/2, 置信度, 类别概率)
                    边界框列表.append(框)
    
    # 非极大值抑制
    for c in range(类别数):
        排序索引 = list(reversed(np.argsort([框.类别概率[c] for 框 in 边界框列表])))
        
        for i in range(len(排序索引)):
            索引i = 排序索引[i]
            
            if 边界框列表[索引i].类别概率[c] == 0:
                continue
            
            for j in range(i + 1, len(排序索引)):
                索引j = 排序索引[j]
                
                if 计算IoU(边界框列表[索引i], 边界框列表[索引j]) >= NMS阈值:
                    边界框列表[索引j].类别概率[c] = 0
    
    # 过滤低置信度的框
    边界框列表 = [框 for 框 in 边界框列表 if 框.获取分数() > 目标阈值]
    
    return 边界框列表


def 计算重叠矩阵(a, b):
    """
    计算两组边界框之间的重叠矩阵
    
    参数:
        a: (N, 4) 边界框数组
        b: (K, 4) 边界框数组
    
    返回:
        (N, K) 重叠矩阵
    """
    面积 = (b[:, 2] - b[:, 0]) * (b[:, 3] - b[:, 1])
    
    交集宽度 = np.minimum(np.expand_dims(a[:, 2], axis=1), b[:, 2]) - \
               np.maximum(np.expand_dims(a[:, 0], 1), b[:, 0])
    交集高度 = np.minimum(np.expand_dims(a[:, 3], axis=1), b[:, 3]) - \
               np.maximum(np.expand_dims(a[:, 1], 1), b[:, 1])
    
    交集宽度 = np.maximum(交集宽度, 0)
    交集高度 = np.maximum(交集高度, 0)
    
    并集面积 = np.expand_dims((a[:, 2] - a[:, 0]) * (a[:, 3] - a[:, 1]), axis=1) + \
               面积 - 交集宽度 * 交集高度
    
    并集面积 = np.maximum(并集面积, np.finfo(float).eps)
    
    交集面积 = 交集宽度 * 交集高度
    
    return 交集面积 / 并集面积


def 计算平均精度(召回率, 精确率):
    """
    计算平均精度 (AP)
    
    参数:
        召回率: 召回率曲线
        精确率: 精确率曲线
    
    返回:
        float: 平均精度值
    """
    # 添加哨兵值
    mrec = np.concatenate(([0.], 召回率, [1.]))
    mpre = np.concatenate(([0.], 精确率, [0.]))
    
    # 计算精确率包络
    for i in range(mpre.size - 1, 0, -1):
        mpre[i - 1] = np.maximum(mpre[i - 1], mpre[i])
    
    # 找到召回率变化的点
    i = np.where(mrec[1:] != mrec[:-1])[0]
    
    # 计算AP
    ap = np.sum((mrec[i + 1] - mrec[i]) * mpre[i + 1])
    
    return ap


# 游戏目标检测相关的辅助函数
def 检测游戏目标(图像, 模型=None, 标签列表=None, 置信度阈值=0.5):
    """
    检测游戏画面中的目标
    
    参数:
        图像: 游戏画面图像
        模型: 检测模型 (如果为None则返回空列表)
        标签列表: 目标类别标签
        置信度阈值: 检测置信度阈值
    
    返回:
        list: 检测到的目标列表 [(类别, 边界框, 置信度), ...]
    """
    if 模型 is None:
        return []
    
    if 标签列表 is None:
        标签列表 = ['怪物', 'NPC', '物品', '玩家']
    
    # 这里需要根据实际使用的模型来实现
    # 目前返回空列表作为占位
    检测结果 = []
    
    return 检测结果


def 查找最近目标(边界框列表, 参考点=None):
    """
    查找距离参考点最近的目标
    
    参数:
        边界框列表: 检测到的边界框列表
        参考点: 参考点坐标 (x, y)，默认为画面中心
    
    返回:
        边界框: 最近的目标边界框，如果没有则返回None
    """
    if not 边界框列表:
        return None
    
    if 参考点 is None:
        参考点 = (0.5, 0.5)  # 画面中心
    
    最近距离 = float('inf')
    最近目标 = None
    
    for 框 in 边界框列表:
        中心x, 中心y = 框.获取中心()
        距离 = ((中心x - 参考点[0]) ** 2 + (中心y - 参考点[1]) ** 2) ** 0.5
        
        if 距离 < 最近距离:
            最近距离 = 距离
            最近目标 = 框
    
    return 最近目标


if __name__ == "__main__":
    print("=" * 50)
    print("🎯 YOLO目标检测工具")
    print("=" * 50)
    print("\n此模块提供目标检测相关功能:")
    print("  - 边界框类: 存储和处理检测结果")
    print("  - IoU计算: 计算边界框重叠度")
    print("  - NMS: 非极大值抑制去除重复检测")
    print("  - 绘制功能: 在图像上绘制检测结果")
    print("\n使用示例:")
    print("  from 工具.目标检测 import 边界框, 计算IoU, 绘制边界框")
