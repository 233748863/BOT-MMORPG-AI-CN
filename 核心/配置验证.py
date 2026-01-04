"""
配置验证模块

提供配置值的验证功能，包括类型验证、范围验证、必需参数验证等。
支持详细的错误信息生成。

需求: 4.1, 4.2, 4.3, 4.4, 4.5
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union
import os


@dataclass
class 验证错误:
    """验证错误信息
    
    Attributes:
        参数名: 出错的参数名称
        错误类型: 错误类型 (type / range / required / custom)
        错误信息: 详细的错误描述
        当前值: 当前的参数值
        期望值: 期望的值或范围描述
    """
    参数名: str
    错误类型: str  # type / range / required / custom
    错误信息: str
    当前值: Any
    期望值: str


class 配置验证器:
    """配置验证器
    
    验证配置值的有效性，支持：
    - 类型验证 (int, float, str, bool, path, choice)
    - 范围验证 (最小值、最大值)
    - 必需参数验证
    - 选项验证 (choice 类型)
    
    需求: 4.1, 4.2, 4.3, 4.4
    """
    
    # 支持的类型映射
    类型映射 = {
        "int": int,
        "float": (int, float),  # float 也接受 int
        "str": str,
        "bool": bool,
        "path": str,
        "choice": str,
    }
    
    def __init__(self, 模式定义: Dict[str, Dict[str, Any]] = None):
        """初始化验证器
        
        Args:
            模式定义: 配置模式定义，格式为:
                {
                    "分区名": {
                        "参数名": {
                            "类型": "int/float/str/bool/path/choice",
                            "默认值": ...,
                            "最小值": ...,  # 可选
                            "最大值": ...,  # 可选
                            "必需": True/False,  # 可选
                            "选项": [...],  # choice 类型必需
                            "描述": "..."  # 可选
                        }
                    }
                }
        """
        self._模式定义 = 模式定义 or {}
    
    @property
    def 模式定义(self) -> Dict[str, Dict[str, Any]]:
        """获取模式定义"""
        return self._模式定义
    
    @模式定义.setter
    def 模式定义(self, 值: Dict[str, Dict[str, Any]]):
        """设置模式定义"""
        self._模式定义 = 值 or {}
    
    def 验证值(self, 参数名: str, 值: Any, 参数定义: Dict[str, Any] = None) -> Tuple[bool, Optional[验证错误]]:
        """验证单个参数值
        
        Args:
            参数名: 参数名称
            值: 要验证的值
            参数定义: 参数定义字典，如果为 None 则从模式定义中查找
            
        Returns:
            (是否有效, 验证错误对象或None)
            
        需求: 4.3, 4.4
        """
        # 查找参数定义
        if 参数定义 is None:
            参数定义 = self._查找参数定义(参数名)
            if 参数定义 is None:
                # 未定义的参数，默认通过
                return True, None
        
        期望类型 = 参数定义.get("类型", "str")
        
        # 类型验证
        类型有效, 类型错误 = self._验证类型(参数名, 值, 期望类型)
        if not 类型有效:
            return False, 类型错误
        
        # 范围验证 (仅对数值类型)
        if 期望类型 in ("int", "float"):
            最小值 = 参数定义.get("最小值")
            最大值 = 参数定义.get("最大值")
            范围有效, 范围错误 = self._验证范围(参数名, 值, 最小值, 最大值)
            if not 范围有效:
                return False, 范围错误
        
        # 选项验证 (choice 类型)
        if 期望类型 == "choice":
            选项列表 = 参数定义.get("选项", [])
            选项有效, 选项错误 = self._验证选项(参数名, 值, 选项列表)
            if not 选项有效:
                return False, 选项错误
        
        # 路径验证 (path 类型，可选检查文件是否存在)
        if 期望类型 == "path":
            # 路径类型只验证是否为字符串，不强制检查文件存在
            pass
        
        return True, None
    
    def _验证类型(self, 参数名: str, 值: Any, 期望类型: str) -> Tuple[bool, Optional[验证错误]]:
        """验证值类型
        
        Args:
            参数名: 参数名称
            值: 要验证的值
            期望类型: 期望的类型字符串
            
        Returns:
            (是否有效, 验证错误对象或None)
            
        需求: 4.3
        """
        if 值 is None:
            return True, None  # None 值在必需验证中处理
        
        python类型 = self.类型映射.get(期望类型)
        if python类型 is None:
            # 未知类型，默认通过
            return True, None
        
        if not isinstance(值, python类型):
            实际类型 = type(值).__name__
            return False, 验证错误(
                参数名=参数名,
                错误类型="type",
                错误信息=self._生成类型错误信息(参数名, 期望类型, 实际类型),
                当前值=值,
                期望值=期望类型
            )
        
        return True, None
    
    def 验证类型(self, 值: Any, 期望类型: str) -> bool:
        """验证值类型（简化版本）
        
        Args:
            值: 要验证的值
            期望类型: 期望的类型字符串
            
        Returns:
            是否类型匹配
            
        需求: 4.3
        """
        if 值 is None:
            return True
        
        python类型 = self.类型映射.get(期望类型)
        if python类型 is None:
            return True
        
        return isinstance(值, python类型)
    
    def _验证范围(self, 参数名: str, 值: Any, 最小值: Any, 最大值: Any) -> Tuple[bool, Optional[验证错误]]:
        """验证值范围
        
        Args:
            参数名: 参数名称
            值: 要验证的值
            最小值: 最小值限制
            最大值: 最大值限制
            
        Returns:
            (是否有效, 验证错误对象或None)
            
        需求: 4.4
        """
        if 值 is None:
            return True, None
        
        if 最小值 is not None and 值 < 最小值:
            return False, 验证错误(
                参数名=参数名,
                错误类型="range",
                错误信息=self._生成范围错误信息(参数名, 值, 最小值, 最大值, "小于最小值"),
                当前值=值,
                期望值=f">= {最小值}"
            )
        
        if 最大值 is not None and 值 > 最大值:
            return False, 验证错误(
                参数名=参数名,
                错误类型="range",
                错误信息=self._生成范围错误信息(参数名, 值, 最小值, 最大值, "大于最大值"),
                当前值=值,
                期望值=f"<= {最大值}"
            )
        
        return True, None
    
    def 验证范围(self, 值: Any, 最小值: Any, 最大值: Any) -> bool:
        """验证值范围（简化版本）
        
        Args:
            值: 要验证的值
            最小值: 最小值限制
            最大值: 最大值限制
            
        Returns:
            是否在范围内
            
        需求: 4.4
        """
        if 值 is None:
            return True
        
        if 最小值 is not None and 值 < 最小值:
            return False
        
        if 最大值 is not None and 值 > 最大值:
            return False
        
        return True
    
    def _验证选项(self, 参数名: str, 值: Any, 选项列表: List[Any]) -> Tuple[bool, Optional[验证错误]]:
        """验证值是否在选项列表中
        
        Args:
            参数名: 参数名称
            值: 要验证的值
            选项列表: 有效选项列表
            
        Returns:
            (是否有效, 验证错误对象或None)
        """
        if 值 is None:
            return True, None
        
        if not 选项列表:
            return True, None
        
        if 值 not in 选项列表:
            return False, 验证错误(
                参数名=参数名,
                错误类型="choice",
                错误信息=self._生成选项错误信息(参数名, 值, 选项列表),
                当前值=值,
                期望值=f"其中之一: {选项列表}"
            )
        
        return True, None
    
    def 验证必需(self, 配置: Dict[str, Any], 必需参数: List[str]) -> List[验证错误]:
        """验证必需参数是否存在
        
        Args:
            配置: 配置字典
            必需参数: 必需参数名称列表
            
        Returns:
            验证错误列表
            
        需求: 4.2
        """
        错误列表 = []
        
        for 参数名 in 必需参数:
            if 参数名 not in 配置 or 配置[参数名] is None:
                错误列表.append(验证错误(
                    参数名=参数名,
                    错误类型="required",
                    错误信息=self._生成必需错误信息(参数名),
                    当前值=None,
                    期望值="非空值"
                ))
        
        return 错误列表
    
    def 验证配置(self, 配置: Dict[str, Any]) -> Tuple[bool, List[验证错误]]:
        """验证完整配置
        
        根据模式定义验证整个配置字典。
        
        Args:
            配置: 要验证的配置字典
            
        Returns:
            (是否有效, 验证错误列表)
            
        需求: 4.1
        """
        错误列表 = []
        
        # 收集所有必需参数
        必需参数 = []
        
        for 分区名, 分区定义 in self._模式定义.items():
            分区配置 = 配置.get(分区名, {})
            
            for 参数名, 参数定义 in 分区定义.items():
                完整参数名 = f"{分区名}.{参数名}"
                
                # 检查是否必需
                if 参数定义.get("必需", False):
                    必需参数.append(完整参数名)
                
                # 获取参数值
                值 = 分区配置.get(参数名) if isinstance(分区配置, dict) else None
                
                # 验证值
                有效, 错误 = self.验证值(完整参数名, 值, 参数定义)
                if not 有效 and 错误:
                    错误列表.append(错误)
        
        # 验证必需参数
        for 完整参数名 in 必需参数:
            分区名, 参数名 = 完整参数名.split(".", 1)
            分区配置 = 配置.get(分区名, {})
            值 = 分区配置.get(参数名) if isinstance(分区配置, dict) else None
            
            if 值 is None:
                错误列表.append(验证错误(
                    参数名=完整参数名,
                    错误类型="required",
                    错误信息=self._生成必需错误信息(完整参数名),
                    当前值=None,
                    期望值="非空值"
                ))
        
        return len(错误列表) == 0, 错误列表
    
    def _查找参数定义(self, 参数名: str) -> Optional[Dict[str, Any]]:
        """从模式定义中查找参数定义
        
        Args:
            参数名: 参数名称，可以是 "分区.参数" 格式或单独的参数名
            
        Returns:
            参数定义字典或 None
        """
        # 尝试解析 "分区.参数" 格式
        if "." in 参数名:
            分区名, 实际参数名 = 参数名.split(".", 1)
            分区定义 = self._模式定义.get(分区名, {})
            return 分区定义.get(实际参数名)
        
        # 在所有分区中查找
        for 分区定义 in self._模式定义.values():
            if 参数名 in 分区定义:
                return 分区定义[参数名]
        
        return None
    
    # ==================== 错误信息生成 ====================
    # 需求: 4.5
    
    def _生成类型错误信息(self, 参数名: str, 期望类型: str, 实际类型: str) -> str:
        """生成类型错误信息
        
        Args:
            参数名: 参数名称
            期望类型: 期望的类型
            实际类型: 实际的类型
            
        Returns:
            错误信息字符串
            
        需求: 4.5
        """
        类型名称映射 = {
            "int": "整数",
            "float": "浮点数",
            "str": "字符串",
            "bool": "布尔值",
            "path": "路径",
            "choice": "选项",
        }
        
        期望名称 = 类型名称映射.get(期望类型, 期望类型)
        实际名称 = 类型名称映射.get(实际类型, 实际类型)
        
        return f"参数 '{参数名}' 类型错误: 期望 {期望名称}，实际为 {实际名称}"
    
    def _生成范围错误信息(self, 参数名: str, 值: Any, 最小值: Any, 最大值: Any, 原因: str) -> str:
        """生成范围错误信息
        
        Args:
            参数名: 参数名称
            值: 当前值
            最小值: 最小值限制
            最大值: 最大值限制
            原因: 错误原因
            
        Returns:
            错误信息字符串
            
        需求: 4.5
        """
        范围描述 = ""
        if 最小值 is not None and 最大值 is not None:
            范围描述 = f"{最小值} 到 {最大值}"
        elif 最小值 is not None:
            范围描述 = f">= {最小值}"
        elif 最大值 is not None:
            范围描述 = f"<= {最大值}"
        
        return f"参数 '{参数名}' 值 {值} {原因}，有效范围: {范围描述}"
    
    def _生成必需错误信息(self, 参数名: str) -> str:
        """生成必需参数错误信息
        
        Args:
            参数名: 参数名称
            
        Returns:
            错误信息字符串
            
        需求: 4.5
        """
        return f"参数 '{参数名}' 是必需的，但未提供值"
    
    def _生成选项错误信息(self, 参数名: str, 值: Any, 选项列表: List[Any]) -> str:
        """生成选项错误信息
        
        Args:
            参数名: 参数名称
            值: 当前值
            选项列表: 有效选项列表
            
        Returns:
            错误信息字符串
            
        需求: 4.5
        """
        选项字符串 = ", ".join(str(选项) for 选项 in 选项列表)
        return f"参数 '{参数名}' 值 '{值}' 不在有效选项中，可选值: {选项字符串}"
    
    def 生成错误摘要(self, 错误列表: List[验证错误]) -> str:
        """生成错误摘要信息
        
        Args:
            错误列表: 验证错误列表
            
        Returns:
            格式化的错误摘要字符串
            
        需求: 4.5
        """
        if not 错误列表:
            return "配置验证通过"
        
        摘要行 = [f"配置验证失败，共 {len(错误列表)} 个错误:"]
        
        for i, 错误 in enumerate(错误列表, 1):
            摘要行.append(f"  {i}. [{错误.错误类型}] {错误.错误信息}")
        
        return "\n".join(摘要行)


# ==================== 默认配置模式 ====================
默认配置模式 = {
    "窗口设置": {
        "窗口X": {"类型": "int", "默认值": 0, "最小值": 0, "描述": "窗口左上角X坐标"},
        "窗口Y": {"类型": "int", "默认值": 0, "最小值": 0, "描述": "窗口左上角Y坐标"},
        "窗口宽度": {"类型": "int", "默认值": 1920, "最小值": 100, "最大值": 7680, "描述": "窗口宽度"},
        "窗口高度": {"类型": "int", "默认值": 1080, "最小值": 100, "最大值": 4320, "描述": "窗口高度"},
    },
    "模型设置": {
        "模型路径": {"类型": "path", "默认值": "模型/决策模型.pth", "必需": True, "描述": "决策模型文件路径"},
        "YOLO模型": {"类型": "path", "默认值": "模型/yolo.pt", "描述": "YOLO检测模型路径"},
        "置信度阈值": {"类型": "float", "默认值": 0.5, "最小值": 0.0, "最大值": 1.0, "描述": "检测置信度阈值"},
    },
    "训练设置": {
        "批次大小": {"类型": "int", "默认值": 32, "最小值": 1, "最大值": 256, "描述": "训练批次大小"},
        "学习率": {"类型": "float", "默认值": 0.001, "最小值": 0.0001, "最大值": 0.1, "描述": "学习率"},
        "训练轮次": {"类型": "int", "默认值": 100, "最小值": 1, "描述": "训练轮次数"},
    },
    "运行设置": {
        "启用YOLO": {"类型": "bool", "默认值": True, "描述": "是否启用YOLO检测"},
        "显示调试": {"类型": "bool", "默认值": False, "描述": "是否显示调试信息"},
        "日志级别": {"类型": "choice", "默认值": "INFO", "选项": ["DEBUG", "INFO", "WARNING", "ERROR"], "描述": "日志级别"},
    },
}


def 创建默认验证器() -> 配置验证器:
    """创建使用默认模式的验证器
    
    Returns:
        配置验证器实例
    """
    return 配置验证器(默认配置模式)
