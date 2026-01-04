"""
YOLO目标检测器模块
实现基于YOLO的游戏实体检测功能

集成智能缓存和异步检测功能，提升检测性能。

需求: 2.1, 2.2 - 智能缓存集成
"""

import logging
import math
from typing import List, Optional, Tuple, Dict, Any

import numpy as np

from 核心.数据类型 import 实体类型, 方向, 检测结果
from 配置.增强设置 import YOLO配置, 实体类型映射, 实体类型枚举

# 尝试导入缓存配置
try:
    from 配置.增强设置 import 缓存配置 as 增强设置缓存配置
except ImportError:
    增强设置缓存配置 = None

# 尝试导入智能缓存模块
try:
    from 核心.智能缓存 import 智能检测缓存, 智能缓存
    from 核心.缓存策略 import 缓存策略, 优先区域, 获取默认缓存策略
    智能缓存可用 = True
except ImportError:
    智能缓存可用 = False

# 尝试导入异步检测模块
try:
    from 核心.异步检测 import 异步检测器
    异步检测可用 = True
except ImportError:
    异步检测可用 = False

# 配置日志
logger = logging.getLogger(__name__)


# ==================== 缓存配置 ====================
# 默认缓存配置，可通过配置文件覆盖
# 需求: 2.1, 2.2, 2.3, 3.4
缓存配置 = {
    "启用": True,  # 是否启用智能缓存
    "全局相似度阈值": 0.95,  # 使用缓存的相似度阈值
    "过期时间": 0.5,  # 缓存过期时间（秒）
    "启用时间过期": True,  # 是否启用基于时间的过期
    "比较方法": "histogram",  # 帧比较方法: "histogram", "ssim", "mse", "hash"
    "预热帧数": 1,  # 预热帧数
    "优先区域": [
        # 示例优先区域配置（屏幕中心区域，更严格的阈值）
        # {
        #     "名称": "屏幕中心",
        #     "区域": [0.3, 0.3, 0.4, 0.4],  # 相对坐标 (x, y, w, h)
        #     "阈值": 0.9
        # }
    ]
}

# 如果增强设置中有缓存配置，则使用增强设置的配置
if 增强设置缓存配置 is not None:
    缓存配置.update(增强设置缓存配置)


class YOLO检测器:
    """
    YOLO目标检测器
    
    用于检测游戏画面中的实体（怪物、NPC、玩家、物品、技能特效等）
    
    支持智能缓存功能，根据画面变化程度决定是否重新执行检测
    需求: 2.1, 2.2
    """
    
    def __init__(
        self, 
        模型路径: Optional[str] = None, 
        置信度阈值: Optional[float] = None,
        NMS阈值: Optional[float] = None,
        输入尺寸: Optional[Tuple[int, int]] = None,
        启用缓存: bool = True,
        启用异步: bool = False,
        缓存配置项: Optional[Dict[str, Any]] = None
    ):
        """
        初始化YOLO检测器
        
        Args:
            模型路径: YOLO模型文件路径，默认使用配置文件中的路径
            置信度阈值: 检测置信度阈值，低于此值的结果将被过滤
            NMS阈值: 非极大值抑制阈值
            输入尺寸: 模型输入图像尺寸
            启用缓存: 是否启用智能缓存
            启用异步: 是否启用异步检测
            缓存配置项: 缓存配置字典，覆盖默认配置
            
        需求: 2.1, 2.2
        """
        self.模型路径 = 模型路径 or YOLO配置["模型路径"]
        self.置信度阈值 = 置信度阈值 if 置信度阈值 is not None else YOLO配置["置信度阈值"]
        self.NMS阈值 = NMS阈值 if NMS阈值 is not None else YOLO配置["NMS阈值"]
        self.输入尺寸 = 输入尺寸 or YOLO配置["输入尺寸"]
        
        self._模型 = None
        self._已加载 = False
        self._上次检测结果: List[检测结果] = []
        
        # 合并缓存配置
        self._缓存配置 = 缓存配置.copy()
        if 缓存配置项:
            self._缓存配置.update(缓存配置项)
        
        # 智能缓存集成
        self._智能缓存: Optional['智能缓存'] = None
        self._启用缓存 = 启用缓存 and 智能缓存可用 and self._缓存配置.get("启用", True)
        if self._启用缓存:
            self._初始化缓存()
        
        # 异步检测集成
        self._异步检测器: Optional['异步检测器'] = None
        self._启用异步 = 启用异步 and 异步检测可用
        if self._启用异步:
            self._初始化异步检测()
        
        # 尝试加载模型
        self._加载模型()
        
        logger.info(f"YOLO检测器初始化完成，缓存: {self._启用缓存}, 异步: {self._启用异步}")
    
    def _加载模型(self) -> bool:
        """
        加载YOLO模型
        
        Returns:
            是否加载成功
        """
        try:
            # 尝试导入ultralytics库
            from ultralytics import YOLO
            self._模型 = YOLO(self.模型路径)
            self._已加载 = True
            logger.info(f"YOLO模型加载成功: {self.模型路径}")
            return True
        except ImportError:
            logger.warning("未安装ultralytics库，YOLO检测器将返回空结果")
            self._已加载 = False
            return False
        except Exception as e:
            logger.warning(f"YOLO模型加载失败: {e}，检测器将返回空结果")
            self._已加载 = False
            return False
    
    def 是否已加载(self) -> bool:
        """
        检查模型是否已加载
        
        Returns:
            模型是否已加载
        """
        return self._已加载
    
    def 检测(self, 图像: np.ndarray, 使用缓存: bool = True) -> List[检测结果]:
        """
        执行目标检测
        
        Args:
            图像: 输入图像 (BGR格式的numpy数组)
            使用缓存: 是否使用缓存（如果启用）
            
        Returns:
            检测结果列表，按置信度降序排列
        """
        # 如果模型未加载，返回空列表
        if not self._已加载:
            logger.warning("模型未加载，返回空检测结果")
            return []
        
        # 验证图像
        if 图像 is None or 图像.size == 0:
            logger.warning("输入图像无效，返回空检测结果")
            return []
        
        # 尝试使用缓存
        if self._启用缓存 and self._智能缓存 and 使用缓存:
            缓存结果 = self._智能缓存.获取(图像)
            if 缓存结果 is not None:
                logger.debug("使用缓存的检测结果")
                return 缓存结果
        
        try:
            # 获取屏幕尺寸
            屏幕高度, 屏幕宽度 = 图像.shape[:2]
            屏幕尺寸 = (屏幕宽度, 屏幕高度)
            
            # 执行检测
            结果 = self._模型(图像, conf=self.置信度阈值, iou=self.NMS阈值, verbose=False)
            
            # 解析检测结果
            检测列表 = self._解析检测结果(结果, 屏幕尺寸)
            
            # 后处理：过滤和排序
            检测列表 = self.后处理(检测列表, self.置信度阈值)
            
            # 缓存结果
            self._上次检测结果 = 检测列表
            
            # 更新智能缓存
            if self._启用缓存 and self._智能缓存:
                self._智能缓存.存储(图像, 检测列表)
            
            return 检测列表
            
        except Exception as e:
            logger.error(f"检测过程出错: {e}")
            return self._上次检测结果  # 返回上一帧结果
    
    def _解析检测结果(
        self, 
        原始结果, 
        屏幕尺寸: Tuple[int, int]
    ) -> List[检测结果]:
        """
        解析YOLO原始检测结果
        
        Args:
            原始结果: YOLO模型返回的原始结果
            屏幕尺寸: 屏幕尺寸 (宽度, 高度)
            
        Returns:
            解析后的检测结果列表
        """
        检测列表 = []
        
        for result in 原始结果:
            boxes = result.boxes
            if boxes is None:
                continue
                
            for i in range(len(boxes)):
                # 获取边界框坐标 (x1, y1, x2, y2)
                box = boxes.xyxy[i].cpu().numpy()
                x1, y1, x2, y2 = map(int, box)
                
                # 计算边界框 (x, y, width, height)
                宽度 = x2 - x1
                高度 = y2 - y1
                边界框 = (x1, y1, 宽度, 高度)
                
                # 计算中心点
                中心x = x1 + 宽度 // 2
                中心y = y1 + 高度 // 2
                中心点 = (中心x, 中心y)
                
                # 获取置信度
                置信度 = float(boxes.conf[i].cpu().numpy())
                
                # 获取类别
                类别id = int(boxes.cls[i].cpu().numpy())
                实体 = self._映射实体类型(类别id)
                
                # 计算方向和距离
                方向值 = self.计算方向(中心点, 屏幕尺寸)
                距离值 = self._计算距离(中心点, 屏幕尺寸)
                
                检测列表.append(检测结果(
                    类型=实体,
                    置信度=置信度,
                    边界框=边界框,
                    中心点=中心点,
                    方向=方向值,
                    距离=距离值
                ))
        
        return 检测列表
    
    def _映射实体类型(self, 类别id: int) -> 实体类型:
        """
        将YOLO类别ID映射为实体类型
        
        Args:
            类别id: YOLO检测的类别ID
            
        Returns:
            对应的实体类型
        """
        映射结果 = 实体类型映射.get(类别id)
        if 映射结果 is None:
            return 实体类型.未知
        
        # 将配置中的枚举转换为数据类型中的枚举
        类型映射 = {
            实体类型枚举.怪物: 实体类型.怪物,
            实体类型枚举.NPC: 实体类型.NPC,
            实体类型枚举.玩家: 实体类型.玩家,
            实体类型枚举.物品: 实体类型.物品,
            实体类型枚举.技能特效: 实体类型.技能特效,
            实体类型枚举.未知: 实体类型.未知,
        }
        return 类型映射.get(映射结果, 实体类型.未知)
    
    def 计算方向(self, 中心点: Tuple[int, int], 屏幕尺寸: Tuple[int, int]) -> 方向:
        """
        计算实体相对于屏幕中心的方向
        
        Args:
            中心点: 实体中心点坐标 (x, y)
            屏幕尺寸: 屏幕尺寸 (宽度, 高度)
            
        Returns:
            相对于屏幕中心的方向
        """
        屏幕宽度, 屏幕高度 = 屏幕尺寸
        屏幕中心x = 屏幕宽度 // 2
        屏幕中心y = 屏幕高度 // 2
        
        实体x, 实体y = 中心点
        
        # 计算相对位置
        dx = 实体x - 屏幕中心x
        dy = 实体y - 屏幕中心y
        
        # 定义中心区域阈值（屏幕尺寸的10%）
        中心阈值x = 屏幕宽度 * 0.1
        中心阈值y = 屏幕高度 * 0.1
        
        # 判断是否在中心区域
        在中心x = abs(dx) < 中心阈值x
        在中心y = abs(dy) < 中心阈值y
        
        if 在中心x and 在中心y:
            return 方向.中心
        
        # 判断水平方向
        if 在中心x:
            水平 = None
        elif dx < 0:
            水平 = "左"
        else:
            水平 = "右"
        
        # 判断垂直方向
        if 在中心y:
            垂直 = None
        elif dy < 0:
            垂直 = "上"
        else:
            垂直 = "下"
        
        # 组合方向
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
    
    def _计算距离(self, 中心点: Tuple[int, int], 屏幕尺寸: Tuple[int, int]) -> float:
        """
        计算实体中心点到屏幕中心的距离
        
        Args:
            中心点: 实体中心点坐标 (x, y)
            屏幕尺寸: 屏幕尺寸 (宽度, 高度)
            
        Returns:
            到屏幕中心的欧几里得距离
        """
        屏幕宽度, 屏幕高度 = 屏幕尺寸
        屏幕中心x = 屏幕宽度 // 2
        屏幕中心y = 屏幕高度 // 2
        
        实体x, 实体y = 中心点
        
        dx = 实体x - 屏幕中心x
        dy = 实体y - 屏幕中心y
        
        return math.sqrt(dx * dx + dy * dy)
    
    @staticmethod
    def 后处理(检测列表: List[检测结果], 置信度阈值: float) -> List[检测结果]:
        """
        对检测结果进行后处理：过滤低置信度结果并按置信度降序排序
        
        Args:
            检测列表: 原始检测结果列表
            置信度阈值: 置信度阈值，低于此值的结果将被过滤
            
        Returns:
            处理后的检测结果列表，按置信度降序排列
        """
        # 过滤低置信度结果
        过滤后列表 = [r for r in 检测列表 if r.置信度 >= 置信度阈值]
        
        # 按置信度降序排序
        排序后列表 = sorted(过滤后列表, key=lambda x: x.置信度, reverse=True)
        
        return 排序后列表
    
    def 获取上次检测结果(self) -> List[检测结果]:
        """
        获取上一次检测的结果（用于检测超时时的降级）
        
        Returns:
            上一次的检测结果列表
        """
        return self._上次检测结果.copy()
    
    def 按类型过滤(self, 检测列表: List[检测结果], 类型: 实体类型) -> List[检测结果]:
        """
        按实体类型过滤检测结果
        
        Args:
            检测列表: 检测结果列表
            类型: 要过滤的实体类型
            
        Returns:
            指定类型的检测结果列表
        """
        return [r for r in 检测列表 if r.类型 == 类型]
    
    def 获取最近实体(
        self, 
        检测列表: List[检测结果], 
        类型: Optional[实体类型] = None
    ) -> Optional[检测结果]:
        """
        获取距离屏幕中心最近的实体
        
        Args:
            检测列表: 检测结果列表
            类型: 可选的实体类型过滤
            
        Returns:
            最近的实体，如果没有则返回None
        """
        if not 检测列表:
            return None
        
        候选列表 = 检测列表
        if 类型 is not None:
            候选列表 = self.按类型过滤(检测列表, 类型)
        
        if not 候选列表:
            return None
        
        return min(候选列表, key=lambda x: x.距离)
    
    # ==================== 智能缓存集成方法 ====================
    
    def _初始化缓存(self) -> None:
        """
        初始化智能缓存
        
        根据缓存配置创建智能缓存实例
        需求: 2.1, 2.2, 3.4
        """
        if not 智能缓存可用:
            logger.warning("智能缓存模块不可用")
            return
        
        try:
            # 创建缓存策略
            策略 = 缓存策略(
                全局阈值=self._缓存配置.get("全局相似度阈值", 0.95),
                过期时间=self._缓存配置.get("过期时间", 0.5),
                启用时间过期=self._缓存配置.get("启用时间过期", True),
                比较方法=self._缓存配置.get("比较方法", "histogram"),
                预热帧数=self._缓存配置.get("预热帧数", 1)
            )
            
            # 添加优先区域
            优先区域配置 = self._缓存配置.get("优先区域", [])
            for 区域配置 in 优先区域配置:
                try:
                    策略.添加优先区域(
                        名称=区域配置.get("名称", "未命名区域"),
                        区域=tuple(区域配置.get("区域", [0.0, 0.0, 1.0, 1.0])),
                        阈值=区域配置.get("阈值", 0.9)
                    )
                except (ValueError, KeyError) as e:
                    logger.warning(f"添加优先区域失败: {e}")
            
            # 创建智能缓存实例
            self._智能缓存 = 智能缓存(策略=策略)
            
            logger.info(f"智能缓存初始化成功: 阈值={策略.全局阈值}, "
                       f"过期时间={策略.过期时间}s, "
                       f"优先区域数={len(策略.优先区域列表)}")
            
        except Exception as e:
            logger.error(f"智能缓存初始化失败: {e}")
            self._智能缓存 = None
            self._启用缓存 = False
    
    def 启用缓存(self, 启用: bool = True) -> None:
        """启用或禁用智能缓存
        
        Args:
            启用: 是否启用
        """
        if not 智能缓存可用:
            logger.warning("智能缓存模块不可用")
            return
        
        self._启用缓存 = 启用
        
        if 启用 and self._智能缓存 is None:
            self._初始化缓存()
        
        logger.info(f"智能缓存已{'启用' if 启用 else '禁用'}")
    
    def 清空缓存(self) -> None:
        """清空检测缓存"""
        if self._智能缓存:
            self._智能缓存.清空()
            logger.debug("已清空检测缓存")
    
    def 获取缓存统计(self) -> dict:
        """获取缓存统计信息"""
        if not self._智能缓存:
            return {"可用": False, "启用": False}
        
        try:
            统计 = self._智能缓存.获取统计()
            统计["可用"] = True
            统计["启用"] = self._启用缓存
            return 统计
        except Exception as e:
            logger.warning(f"获取缓存统计失败: {e}")
            return {"可用": True, "启用": self._启用缓存, "错误": str(e)}
    
    def 设置缓存相似度阈值(self, 阈值: float) -> None:
        """
        设置缓存相似度阈值
        
        Args:
            阈值: 新的相似度阈值 (0.0-1.0)
            
        需求: 2.3
        """
        if self._智能缓存:
            self._智能缓存.设置相似度阈值(阈值)
            self._缓存配置["全局相似度阈值"] = 阈值
    
    def 设置缓存过期时间(self, 过期时间: float) -> None:
        """
        设置缓存过期时间
        
        Args:
            过期时间: 新的过期时间（秒）
        """
        if self._智能缓存:
            self._智能缓存.设置过期时间(过期时间)
            self._缓存配置["过期时间"] = 过期时间
    
    def 添加缓存优先区域(self, 名称: str, 区域: Tuple[float, float, float, float], 
                         阈值: float = 0.9) -> None:
        """
        添加缓存优先区域
        
        Args:
            名称: 区域名称
            区域: 相对坐标 (x, y, w, h)，范围 0.0-1.0
            阈值: 该区域的相似度阈值
            
        需求: 3.1
        """
        if self._智能缓存 and self._智能缓存.策略:
            self._智能缓存.策略.添加优先区域(名称, 区域, 阈值)
            # 更新配置
            优先区域列表 = self._缓存配置.get("优先区域", [])
            优先区域列表.append({
                "名称": 名称,
                "区域": list(区域),
                "阈值": 阈值
            })
            self._缓存配置["优先区域"] = 优先区域列表
    
    def 移除缓存优先区域(self, 名称: str) -> bool:
        """
        移除缓存优先区域
        
        Args:
            名称: 要移除的区域名称
            
        Returns:
            是否成功移除
        """
        if self._智能缓存 and self._智能缓存.策略:
            结果 = self._智能缓存.策略.移除优先区域(名称)
            if 结果:
                # 更新配置
                优先区域列表 = self._缓存配置.get("优先区域", [])
                self._缓存配置["优先区域"] = [
                    区域 for 区域 in 优先区域列表 if 区域.get("名称") != 名称
                ]
            return 结果
        return False
    
    def 获取缓存配置(self) -> Dict[str, Any]:
        """
        获取当前缓存配置
        
        Returns:
            缓存配置字典
        """
        return self._缓存配置.copy()
    
    def 更新缓存配置(self, 新配置: Dict[str, Any]) -> None:
        """
        更新缓存配置
        
        Args:
            新配置: 新的缓存配置字典
            
        需求: 3.4
        """
        self._缓存配置.update(新配置)
        
        # 重新初始化缓存以应用新配置
        if self._启用缓存:
            self._初始化缓存()
            logger.info("缓存配置已更新并重新初始化")
    
    def 从配置文件加载缓存配置(self, 配置路径: str) -> bool:
        """
        从配置文件加载缓存配置
        
        Args:
            配置路径: JSON 配置文件路径
            
        Returns:
            加载是否成功
            
        需求: 3.4
        """
        if not 智能缓存可用:
            logger.warning("智能缓存模块不可用")
            return False
        
        try:
            策略 = 缓存策略.从配置文件创建(配置路径)
            
            # 更新内部配置
            self._缓存配置.update(策略.to_dict())
            
            # 更新智能缓存的策略
            if self._智能缓存:
                self._智能缓存.策略 = 策略
            
            logger.info(f"从 {配置路径} 加载缓存配置成功")
            return True
            
        except Exception as e:
            logger.error(f"加载缓存配置失败: {e}")
            return False
    
    def 保存缓存配置到文件(self, 配置路径: str) -> bool:
        """
        保存当前缓存配置到文件
        
        Args:
            配置路径: JSON 配置文件路径
            
        Returns:
            保存是否成功
        """
        if not 智能缓存可用:
            logger.warning("智能缓存模块不可用")
            return False
        
        try:
            if self._智能缓存 and self._智能缓存.策略:
                return self._智能缓存.策略.保存到配置(配置路径)
            else:
                # 创建临时策略保存配置
                策略 = 缓存策略.from_dict(self._缓存配置)
                return 策略.保存到配置(配置路径)
                
        except Exception as e:
            logger.error(f"保存缓存配置失败: {e}")
            return False
    
    def 预热缓存(self, 图像: np.ndarray) -> bool:
        """
        预热缓存
        
        在启动时执行初始检测以填充缓存
        
        Args:
            图像: 用于预热的初始图像
            
        Returns:
            预热是否成功
            
        需求: 5.1, 5.2
        """
        if not self._智能缓存:
            logger.warning("智能缓存未初始化，无法预热")
            return False
        
        # 设置检测器到智能缓存
        self._智能缓存.设置检测器(self)
        
        return self._智能缓存.预热(图像)
    
    def 获取缓存预热状态(self) -> dict:
        """
        获取缓存预热状态
        
        Returns:
            预热状态字典
            
        需求: 5.2
        """
        if not self._智能缓存:
            return {"预热完成": False, "有缓存": False}
        
        return self._智能缓存.获取预热状态()
    
    # ==================== 异步检测集成方法 ====================
    
    def _初始化异步检测(self) -> None:
        """初始化异步检测器"""
        if not 异步检测可用:
            logger.warning("异步检测模块不可用")
            return
        
        try:
            self._异步检测器 = 异步检测器(self)
            logger.info("异步检测器初始化成功")
        except Exception as e:
            logger.error(f"异步检测器初始化失败: {e}")
            self._异步检测器 = None
            self._启用异步 = False
    
    def 启用异步检测(self, 启用: bool = True) -> None:
        """启用或禁用异步检测
        
        Args:
            启用: 是否启用
        """
        if not 异步检测可用:
            logger.warning("异步检测模块不可用")
            return
        
        self._启用异步 = 启用
        
        if 启用 and self._异步检测器 is None:
            self._初始化异步检测()
        
        logger.info(f"异步检测已{'启用' if 启用 else '禁用'}")
    
    def 异步检测(self, 图像: np.ndarray) -> None:
        """提交异步检测任务
        
        Args:
            图像: 输入图像
        """
        if not self._异步检测器 or not self._启用异步:
            logger.warning("异步检测未启用")
            return
        
        try:
            self._异步检测器.提交(图像)
        except Exception as e:
            logger.error(f"提交异步检测任务失败: {e}")
    
    def 获取异步结果(self, 超时: float = 0.0) -> Optional[List[检测结果]]:
        """获取异步检测结果
        
        Args:
            超时: 等待超时时间（秒），0表示不等待
            
        Returns:
            检测结果列表，如果没有结果返回None
        """
        if not self._异步检测器 or not self._启用异步:
            return None
        
        try:
            return self._异步检测器.获取结果(超时)
        except Exception as e:
            logger.warning(f"获取异步检测结果失败: {e}")
            return None
    
    def 停止异步检测(self) -> None:
        """停止异步检测器"""
        if self._异步检测器:
            try:
                self._异步检测器.停止()
                logger.info("异步检测器已停止")
            except Exception as e:
                logger.error(f"停止异步检测器失败: {e}")
    
    def 获取异步检测状态(self) -> dict:
        """获取异步检测状态"""
        if not self._异步检测器:
            return {"可用": False, "启用": False}
        
        try:
            状态 = self._异步检测器.获取状态() if hasattr(self._异步检测器, '获取状态') else {}
            状态["可用"] = True
            状态["启用"] = self._启用异步
            return 状态
        except Exception as e:
            logger.warning(f"获取异步检测状态失败: {e}")
            return {"可用": True, "启用": self._启用异步, "错误": str(e)}
    
    # ==================== 综合状态方法 ====================
    
    def 获取检测器完整状态(self) -> dict:
        """获取检测器完整状态信息
        
        Returns:
            包含所有子模块状态的字典
        """
        缓存状态 = self.获取缓存统计()
        缓存状态["配置"] = self._缓存配置
        
        return {
            "模型": {
                "已加载": self._已加载,
                "模型路径": self.模型路径,
                "置信度阈值": self.置信度阈值,
                "NMS阈值": self.NMS阈值
            },
            "缓存": 缓存状态,
            "异步检测": self.获取异步检测状态()
        }
    
    def 释放资源(self) -> None:
        """释放检测器资源"""
        # 停止异步检测
        self.停止异步检测()
        
        # 清空缓存
        self.清空缓存()
        
        # 清空模型
        self._模型 = None
        self._已加载 = False
        
        logger.info("检测器资源已释放")
