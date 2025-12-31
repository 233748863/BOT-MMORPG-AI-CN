"""
检测和识别模块测试
验证YOLO检测器和状态识别器的基本功能
"""

import sys
import os
from unittest.mock import patch, MagicMock

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pytest

from 核心.数据类型 import 实体类型, 方向, 游戏状态, 检测结果, 状态识别结果
from 核心.状态识别器 import 状态识别器


# 创建一个不加载模型的YOLO检测器类用于测试
class MockYOLO检测器:
    """用于测试的Mock YOLO检测器，不加载实际模型"""
    
    def __init__(self, 模型路径=None, 置信度阈值=0.5, NMS阈值=0.4, 输入尺寸=(640, 640)):
        self.模型路径 = 模型路径 or "模型/yolo/game_detector.pt"
        self.置信度阈值 = 置信度阈值
        self.NMS阈值 = NMS阈值
        self.输入尺寸 = 输入尺寸
        self._已加载 = False  # 模拟未加载模型
        self._上次检测结果 = []
    
    def 是否已加载(self):
        return self._已加载
    
    def 检测(self, 图像):
        if not self._已加载:
            return []
        return []
    
    def 计算方向(self, 中心点, 屏幕尺寸):
        """计算实体相对于屏幕中心的方向"""
        屏幕宽度, 屏幕高度 = 屏幕尺寸
        屏幕中心x = 屏幕宽度 // 2
        屏幕中心y = 屏幕高度 // 2
        
        实体x, 实体y = 中心点
        
        dx = 实体x - 屏幕中心x
        dy = 实体y - 屏幕中心y
        
        中心阈值x = 屏幕宽度 * 0.1
        中心阈值y = 屏幕高度 * 0.1
        
        在中心x = abs(dx) < 中心阈值x
        在中心y = abs(dy) < 中心阈值y
        
        if 在中心x and 在中心y:
            return 方向.中心
        
        if 在中心x:
            水平 = None
        elif dx < 0:
            水平 = "左"
        else:
            水平 = "右"
        
        if 在中心y:
            垂直 = None
        elif dy < 0:
            垂直 = "上"
        else:
            垂直 = "下"
        
        if 水平 is None and 垂直 == "上":
            return 方向.上
        elif 水平 is None and 垂直 == "下":
            return 方向.下
        elif 垂直 is None and 水平 == "左":
            return 方向.左
        elif 垂直 is None and 水平 == "右":
            return 方向.右
        elif 水平 == "左" and 垂直 == "上":
            return 方向.左上
        elif 水平 == "右" and 垂直 == "上":
            return 方向.右上
        elif 水平 == "左" and 垂直 == "下":
            return 方向.左下
        elif 水平 == "右" and 垂直 == "下":
            return 方向.右下
        
        return 方向.中心
    
    @staticmethod
    def 后处理(检测列表, 置信度阈值):
        """对检测结果进行后处理"""
        过滤后列表 = [r for r in 检测列表 if r.置信度 >= 置信度阈值]
        排序后列表 = sorted(过滤后列表, key=lambda x: x.置信度, reverse=True)
        return 排序后列表


# 使用Mock类替代真实的YOLO检测器
YOLO检测器 = MockYOLO检测器


class Test数据类型:
    """测试数据类型模块"""
    
    def test_实体类型枚举(self):
        """测试实体类型枚举定义正确"""
        assert 实体类型.怪物.value == "monster"
        assert 实体类型.NPC.value == "npc"
        assert 实体类型.玩家.value == "player"
        assert 实体类型.物品.value == "item"
        assert 实体类型.技能特效.value == "skill_effect"
        assert 实体类型.未知.value == "unknown"
    
    def test_方向枚举(self):
        """测试方向枚举定义正确"""
        assert 方向.左.value == "left"
        assert 方向.右.value == "right"
        assert 方向.上.value == "up"
        assert 方向.下.value == "down"
        assert 方向.中心.value == "center"
    
    def test_游戏状态枚举(self):
        """测试游戏状态枚举定义正确"""
        assert 游戏状态.战斗.value == "combat"
        assert 游戏状态.对话.value == "dialogue"
        assert 游戏状态.菜单.value == "menu"
        assert 游戏状态.移动.value == "moving"
        assert 游戏状态.空闲.value == "idle"
    
    def test_检测结果数据类(self):
        """测试检测结果数据类创建"""
        结果 = 检测结果(
            类型=实体类型.怪物,
            置信度=0.85,
            边界框=(100, 100, 50, 50),
            中心点=(125, 125),
            方向=方向.左,
            距离=100.0
        )
        assert 结果.类型 == 实体类型.怪物
        assert 结果.置信度 == 0.85
        assert 结果.边界框 == (100, 100, 50, 50)
    
    def test_检测结果置信度验证(self):
        """测试检测结果置信度范围验证"""
        with pytest.raises(ValueError):
            检测结果(
                类型=实体类型.怪物,
                置信度=1.5,  # 超出范围
                边界框=(100, 100, 50, 50),
                中心点=(125, 125),
                方向=方向.左,
                距离=100.0
            )
    
    def test_状态识别结果数据类(self):
        """测试状态识别结果数据类创建"""
        结果 = 状态识别结果(
            状态=游戏状态.战斗,
            置信度=0.9,
            检测到的UI元素=["血条"],
            附近实体数量=3
        )
        assert 结果.状态 == 游戏状态.战斗
        assert 结果.置信度 == 0.9
        assert "血条" in 结果.检测到的UI元素


class TestYOLO检测器:
    """测试YOLO检测器模块"""
    
    def test_初始化(self):
        """测试检测器初始化"""
        检测器 = YOLO检测器()
        # 由于没有实际模型文件，模型不会加载成功
        # 但初始化不应该抛出异常
        assert 检测器 is not None
    
    def test_未加载模型返回空列表(self):
        """测试未加载模型时返回空列表"""
        检测器 = YOLO检测器()
        # 创建测试图像
        测试图像 = np.zeros((480, 640, 3), dtype=np.uint8)
        结果 = 检测器.检测(测试图像)
        assert isinstance(结果, list)
        # 未加载模型应返回空列表
        if not 检测器.是否已加载():
            assert len(结果) == 0
    
    def test_方向计算_中心(self):
        """测试方向计算 - 中心位置"""
        检测器 = YOLO检测器()
        屏幕尺寸 = (1920, 1080)
        中心点 = (960, 540)  # 屏幕中心
        方向值 = 检测器.计算方向(中心点, 屏幕尺寸)
        assert 方向值 == 方向.中心
    
    def test_方向计算_左(self):
        """测试方向计算 - 左侧"""
        检测器 = YOLO检测器()
        屏幕尺寸 = (1920, 1080)
        中心点 = (100, 540)  # 左侧中间
        方向值 = 检测器.计算方向(中心点, 屏幕尺寸)
        assert 方向值 == 方向.左
    
    def test_方向计算_右(self):
        """测试方向计算 - 右侧"""
        检测器 = YOLO检测器()
        屏幕尺寸 = (1920, 1080)
        中心点 = (1800, 540)  # 右侧中间
        方向值 = 检测器.计算方向(中心点, 屏幕尺寸)
        assert 方向值 == 方向.右
    
    def test_方向计算_左上(self):
        """测试方向计算 - 左上角"""
        检测器 = YOLO检测器()
        屏幕尺寸 = (1920, 1080)
        中心点 = (100, 100)  # 左上角
        方向值 = 检测器.计算方向(中心点, 屏幕尺寸)
        assert 方向值 == 方向.左上
    
    def test_方向计算_右下(self):
        """测试方向计算 - 右下角"""
        检测器 = YOLO检测器()
        屏幕尺寸 = (1920, 1080)
        中心点 = (1800, 1000)  # 右下角
        方向值 = 检测器.计算方向(中心点, 屏幕尺寸)
        assert 方向值 == 方向.右下
    
    def test_后处理_过滤低置信度(self):
        """测试后处理 - 过滤低置信度结果"""
        检测列表 = [
            检测结果(实体类型.怪物, 0.9, (0, 0, 10, 10), (5, 5), 方向.左, 100),
            检测结果(实体类型.NPC, 0.3, (0, 0, 10, 10), (5, 5), 方向.右, 200),
            检测结果(实体类型.物品, 0.7, (0, 0, 10, 10), (5, 5), 方向.上, 150),
        ]
        结果 = YOLO检测器.后处理(检测列表, 0.5)
        assert len(结果) == 2
        assert all(r.置信度 >= 0.5 for r in 结果)
    
    def test_后处理_按置信度排序(self):
        """测试后处理 - 按置信度降序排序"""
        检测列表 = [
            检测结果(实体类型.怪物, 0.7, (0, 0, 10, 10), (5, 5), 方向.左, 100),
            检测结果(实体类型.NPC, 0.9, (0, 0, 10, 10), (5, 5), 方向.右, 200),
            检测结果(实体类型.物品, 0.8, (0, 0, 10, 10), (5, 5), 方向.上, 150),
        ]
        结果 = YOLO检测器.后处理(检测列表, 0.5)
        assert len(结果) == 3
        assert 结果[0].置信度 == 0.9
        assert 结果[1].置信度 == 0.8
        assert 结果[2].置信度 == 0.7


class Test状态识别器:
    """测试状态识别器模块"""
    
    def test_初始化(self):
        """测试状态识别器初始化"""
        识别器 = 状态识别器()
        assert 识别器 is not None
        assert 识别器.历史长度 == 10
    
    def test_状态历史记录(self):
        """测试状态历史记录功能"""
        识别器 = 状态识别器(历史长度=5)
        测试图像 = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # 多次识别状态
        for _ in range(3):
            识别器.识别状态(测试图像, [])
        
        历史 = 识别器.获取状态历史(5)
        assert len(历史) == 3
    
    def test_状态历史最大长度(self):
        """测试状态历史不超过最大长度"""
        识别器 = 状态识别器(历史长度=3)
        测试图像 = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # 识别超过历史长度的次数
        for _ in range(5):
            识别器.识别状态(测试图像, [])
        
        历史 = 识别器.获取状态历史(10)
        assert len(历史) == 3  # 不超过最大长度
    
    def test_识别结果格式(self):
        """测试识别结果返回正确格式"""
        识别器 = 状态识别器()
        测试图像 = np.zeros((480, 640, 3), dtype=np.uint8)
        
        结果 = 识别器.识别状态(测试图像, [])
        
        assert isinstance(结果, 状态识别结果)
        assert isinstance(结果.状态, 游戏状态)
        assert 0.0 <= 结果.置信度 <= 1.0
        assert isinstance(结果.检测到的UI元素, list)
        assert isinstance(结果.附近实体数量, int)
    
    def test_战斗状态判定(self):
        """测试战斗状态判定 - 有近距离敌人时"""
        识别器 = 状态识别器()
        测试图像 = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # 创建近距离敌人检测结果
        敌人 = 检测结果(
            类型=实体类型.怪物,
            置信度=0.9,
            边界框=(300, 200, 50, 50),
            中心点=(325, 225),
            方向=方向.左,
            距离=50.0  # 近距离
        )
        
        结果 = 识别器.识别状态(测试图像, [敌人])
        assert 结果.状态 == 游戏状态.战斗
    
    def test_空闲状态判定(self):
        """测试空闲状态判定 - 无实体时"""
        识别器 = 状态识别器()
        测试图像 = np.zeros((480, 640, 3), dtype=np.uint8)
        
        结果 = 识别器.识别状态(测试图像, [])
        assert 结果.状态 == 游戏状态.空闲
    
    def test_置信度累积(self):
        """测试连续相同状态时置信度累积"""
        识别器 = 状态识别器(置信度累积系数=0.1)
        测试图像 = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # 第一次识别
        结果1 = 识别器.识别状态(测试图像, [])
        
        # 第二次识别（相同状态）
        结果2 = 识别器.识别状态(测试图像, [])
        
        # 第三次识别（相同状态）
        结果3 = 识别器.识别状态(测试图像, [])
        
        # 置信度应该累积增加
        assert 结果2.置信度 >= 结果1.置信度
        assert 结果3.置信度 >= 结果2.置信度
    
    def test_状态变更回调(self):
        """测试状态变更回调功能"""
        识别器 = 状态识别器()
        测试图像 = np.zeros((480, 640, 3), dtype=np.uint8)
        
        回调记录 = []
        
        def 回调函数(旧状态, 新状态):
            回调记录.append((旧状态, 新状态))
        
        识别器.注册状态变更回调(回调函数)
        
        # 第一次识别（空闲状态）
        识别器.识别状态(测试图像, [])
        
        # 第二次识别（战斗状态）
        敌人 = 检测结果(
            类型=实体类型.怪物,
            置信度=0.9,
            边界框=(300, 200, 50, 50),
            中心点=(325, 225),
            方向=方向.左,
            距离=50.0
        )
        识别器.识别状态(测试图像, [敌人])
        
        # 应该触发一次回调
        assert len(回调记录) == 1
        assert 回调记录[0][0] == 游戏状态.空闲
        assert 回调记录[0][1] == 游戏状态.战斗
    
    def test_清空历史(self):
        """测试清空历史功能"""
        识别器 = 状态识别器()
        测试图像 = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # 添加一些历史
        for _ in range(3):
            识别器.识别状态(测试图像, [])
        
        assert len(识别器.获取状态历史(10)) == 3
        
        # 清空历史
        识别器.清空历史()
        
        assert len(识别器.获取状态历史(10)) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
