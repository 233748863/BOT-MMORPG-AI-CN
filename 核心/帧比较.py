"""
帧比较模块
用于计算视频帧之间的相似度

功能:
- 直方图比较
- 结构相似度 (SSIM)
- 区域比较
"""

import cv2
import numpy as np
from typing import Tuple, List, Optional
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
日志 = logging.getLogger(__name__)


class 帧比较器:
    """计算帧之间的相似度"""
    
    支持的方法 = ["histogram", "ssim", "mse", "hash"]
    
    def __init__(self, 方法: str = "histogram"):
        """
        初始化比较器
        
        参数:
            方法: 比较方法 - "histogram", "ssim", "mse", "hash"
        """
        if 方法 not in self.支持的方法:
            日志.warning(f"不支持的方法 {方法}，使用默认方法 histogram")
            方法 = "histogram"
        
        self.方法 = 方法
    
    def 比较(self, 帧1: np.ndarray, 帧2: np.ndarray) -> float:
        """
        比较两帧的相似度
        
        参数:
            帧1: 第一帧图像
            帧2: 第二帧图像
            
        返回:
            相似度分数 (0.0-1.0)，1.0 表示完全相同
        """
        if 帧1 is None or 帧2 is None:
            return 0.0
        
        # 确保尺寸相同
        if 帧1.shape != 帧2.shape:
            帧2 = cv2.resize(帧2, (帧1.shape[1], 帧1.shape[0]))
        
        try:
            if self.方法 == "histogram":
                return self._直方图比较(帧1, 帧2)
            elif self.方法 == "ssim":
                return self._SSIM比较(帧1, 帧2)
            elif self.方法 == "mse":
                return self._MSE比较(帧1, 帧2)
            elif self.方法 == "hash":
                return self._哈希比较(帧1, 帧2)
            else:
                return self._直方图比较(帧1, 帧2)
        except Exception as e:
            日志.warning(f"帧比较失败: {e}")
            return 0.0
    
    def _直方图比较(self, 帧1: np.ndarray, 帧2: np.ndarray) -> float:
        """使用直方图比较"""
        # 转换为灰度图
        if len(帧1.shape) == 3:
            灰度1 = cv2.cvtColor(帧1, cv2.COLOR_BGR2GRAY)
            灰度2 = cv2.cvtColor(帧2, cv2.COLOR_BGR2GRAY)
        else:
            灰度1, 灰度2 = 帧1, 帧2
        
        # 计算直方图
        hist1 = cv2.calcHist([灰度1], [0], None, [256], [0, 256])
        hist2 = cv2.calcHist([灰度2], [0], None, [256], [0, 256])
        
        # 归一化
        cv2.normalize(hist1, hist1)
        cv2.normalize(hist2, hist2)
        
        # 比较直方图（使用相关性方法）
        相似度 = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
        
        # 将结果映射到 0-1 范围
        return max(0.0, min(1.0, (相似度 + 1) / 2))
    
    def _SSIM比较(self, 帧1: np.ndarray, 帧2: np.ndarray) -> float:
        """使用结构相似度 (SSIM) 比较"""
        # 转换为灰度图
        if len(帧1.shape) == 3:
            灰度1 = cv2.cvtColor(帧1, cv2.COLOR_BGR2GRAY)
            灰度2 = cv2.cvtColor(帧2, cv2.COLOR_BGR2GRAY)
        else:
            灰度1, 灰度2 = 帧1, 帧2
        
        # 简化的 SSIM 计算
        C1 = 6.5025  # (0.01 * 255)^2
        C2 = 58.5225  # (0.03 * 255)^2
        
        灰度1 = 灰度1.astype(np.float64)
        灰度2 = 灰度2.astype(np.float64)
        
        # 计算均值
        mu1 = cv2.GaussianBlur(灰度1, (11, 11), 1.5)
        mu2 = cv2.GaussianBlur(灰度2, (11, 11), 1.5)
        
        mu1_sq = mu1 ** 2
        mu2_sq = mu2 ** 2
        mu1_mu2 = mu1 * mu2
        
        # 计算方差和协方差
        sigma1_sq = cv2.GaussianBlur(灰度1 ** 2, (11, 11), 1.5) - mu1_sq
        sigma2_sq = cv2.GaussianBlur(灰度2 ** 2, (11, 11), 1.5) - mu2_sq
        sigma12 = cv2.GaussianBlur(灰度1 * 灰度2, (11, 11), 1.5) - mu1_mu2
        
        # SSIM 公式
        ssim_map = ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / \
                   ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))
        
        return float(np.mean(ssim_map))
    
    def _MSE比较(self, 帧1: np.ndarray, 帧2: np.ndarray) -> float:
        """使用均方误差 (MSE) 比较"""
        mse = np.mean((帧1.astype(np.float64) - 帧2.astype(np.float64)) ** 2)
        # 将 MSE 转换为相似度（MSE 越小，相似度越高）
        # 假设最大 MSE 为 255^2
        相似度 = 1.0 - (mse / (255 ** 2))
        return max(0.0, min(1.0, 相似度))
    
    def _哈希比较(self, 帧1: np.ndarray, 帧2: np.ndarray) -> float:
        """使用感知哈希比较"""
        hash1 = self._计算感知哈希(帧1)
        hash2 = self._计算感知哈希(帧2)
        
        # 计算汉明距离
        距离 = bin(hash1 ^ hash2).count('1')
        
        # 转换为相似度（64位哈希）
        相似度 = 1.0 - (距离 / 64.0)
        return 相似度
    
    def _计算感知哈希(self, 图像: np.ndarray) -> int:
        """计算图像的感知哈希"""
        # 缩小到 8x8
        缩小图 = cv2.resize(图像, (8, 8))
        
        # 转换为灰度
        if len(缩小图.shape) == 3:
            灰度图 = cv2.cvtColor(缩小图, cv2.COLOR_BGR2GRAY)
        else:
            灰度图 = 缩小图
        
        # 计算均值
        均值 = np.mean(灰度图)
        
        # 生成哈希
        哈希值 = 0
        for i in range(8):
            for j in range(8):
                if 灰度图[i, j] > 均值:
                    哈希值 |= 1 << (i * 8 + j)
        
        return 哈希值
    
    def 比较区域(self, 帧1: np.ndarray, 帧2: np.ndarray,
                 区域: Tuple[int, int, int, int]) -> float:
        """
        比较指定区域的相似度
        
        参数:
            帧1: 第一帧图像
            帧2: 第二帧图像
            区域: (x, y, width, height) 区域坐标
            
        返回:
            区域相似度分数
        """
        x, y, w, h = 区域
        
        # 提取区域
        区域1 = 帧1[y:y+h, x:x+w]
        区域2 = 帧2[y:y+h, x:x+w]
        
        return self.比较(区域1, 区域2)
    
    def 比较多区域(self, 帧1: np.ndarray, 帧2: np.ndarray,
                   区域列表: List[Tuple[int, int, int, int]]) -> List[float]:
        """
        比较多个区域的相似度
        
        返回:
            各区域相似度列表
        """
        return [self.比较区域(帧1, 帧2, 区域) for 区域 in 区域列表]


def 快速帧差异检测(帧1: np.ndarray, 帧2: np.ndarray, 阈值: float = 0.1) -> bool:
    """
    快速检测两帧是否有显著差异
    
    参数:
        帧1: 第一帧
        帧2: 第二帧
        阈值: 差异阈值
        
    返回:
        True 表示有显著差异
    """
    if 帧1 is None or 帧2 is None:
        return True
    
    if 帧1.shape != 帧2.shape:
        return True
    
    # 快速计算差异
    差异 = np.abs(帧1.astype(np.float32) - 帧2.astype(np.float32))
    平均差异 = np.mean(差异) / 255.0
    
    return 平均差异 > 阈值
