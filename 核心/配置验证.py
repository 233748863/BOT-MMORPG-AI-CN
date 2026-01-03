"""
配置验证模块
提供配置验证、默认值管理和档案管理功能

功能:
- 配置模式定义
- 类型和范围验证
- 默认值管理
- 配置档案管理
"""

import os
import json
import shutil
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
日志 = logging.getLogger(__name__)


@dataclass
class 验证错误:
    """验证错误信息"""
    参数名: str
    错误类型: str  # type / range / required / custom
    错误信息: str
    当前值: Any = None
    期望值: str = ""


# 默认配置模式定义
默认配置模式 = {
    "窗口设置": {
        "窗口X": {"类型": "int", "默认值": 0, "最小值": 0, "描述": "窗口左上角X坐标"},
        "窗口Y": {"类型": "int", "默认值": 0, "最小值": 0, "描述": "窗口左上角Y坐标"},
        "窗口宽度": {"类型": "int", "默认值": 1920, "最小值": 100, "最大值": 4096, "描述": "窗口宽度"},
        "窗口高度": {"类型": "int", "默认值": 1080, "最小值": 100, "最大值": 2160, "描述": "窗口高度"}
    },
    "模型设置": {
        "模型路径": {"类型": "path", "默认值": "模型/决策模型.h5", "必需": True, "描述": "决策模型路径"},
        "YOLO模型": {"类型": "path", "默认值": "模型/yolo.pt", "描述": "YOLO模型路径"},
        "置信度阈值": {"类型": "float", "默认值": 0.5, "最小值": 0.0, "最大值": 1.0, "描述": "检测置信度阈值"}
    },
    "训练设置": {
        "批次大小": {"类型": "int", "默认值": 32, "最小值": 1, "最大值": 256, "描述": "训练批次大小"},
        "学习率": {"类型": "float", "默认值": 0.001, "最小值": 0.0001, "最大值": 0.1, "描述": "学习率"},
        "训练轮次": {"类型": "int", "默认值": 100, "最小值": 1, "描述": "训练轮次数"}
    },
    "运行设置": {
        "启用YOLO": {"类型": "bool", "默认值": True, "描述": "是否启用YOLO检测"},
        "显示调试": {"类型": "bool", "默认值": False, "描述": "是否显示调试信息"},
        "日志级别": {"类型": "choice", "默认值": "INFO", "选项": ["DEBUG", "INFO", "WARNING", "ERROR"], "描述": "日志级别"}
    }
}


class 配置验证器:
    """验证配置值的有效性"""
    
    def __init__(self, 模式定义: Dict = None):
        """
        初始化验证器
        
        参数:
            模式定义: 配置模式定义
        """
        self._模式 = 模式定义 or 默认配置模式
        self._扁平模式 = self._扁平化模式()
    
    def _扁平化模式(self) -> Dict:
        """将嵌套模式扁平化"""
        扁平 = {}
        for 分区, 参数列表 in self._模式.items():
            for 参数名, 定义 in 参数列表.items():
                扁平[参数名] = {**定义, "分区": 分区}
        return 扁平
    
    def 验证值(self, 参数名: str, 值: Any) -> Tuple[bool, Optional[str]]:
        """
        验证单个参数值
        
        返回:
            (是否有效, 错误信息)
        """
        if 参数名 not in self._扁平模式:
            return True, None  # 未知参数，跳过验证
        
        定义 = self._扁平模式[参数名]
        类型 = 定义.get("类型", "str")
        
        # 类型验证
        if not self.验证类型(值, 类型):
            return False, f"类型错误: 期望 {类型}，实际 {type(值).__name__}"
        
        # 范围验证
        最小值 = 定义.get("最小值")
        最大值 = 定义.get("最大值")
        if 最小值 is not None or 最大值 is not None:
            if not self.验证范围(值, 最小值, 最大值):
                return False, f"范围错误: 值应在 {最小值} 到 {最大值} 之间"
        
        # 选项验证
        选项 = 定义.get("选项")
        if 选项 and 值 not in 选项:
            return False, f"选项错误: 值应为 {选项} 之一"
        
        return True, None
    
    def 验证类型(self, 值: Any, 期望类型: str) -> bool:
        """验证值类型"""
        类型映射 = {
            "int": (int,),
            "float": (int, float),
            "str": (str,),
            "bool": (bool,),
            "path": (str,),
            "choice": (str,),
            "list": (list,)
        }
        
        期望类型列表 = 类型映射.get(期望类型, (str,))
        return isinstance(值, 期望类型列表)
    
    def 验证范围(self, 值: Any, 最小值: Any, 最大值: Any) -> bool:
        """验证值范围"""
        if 最小值 is not None and 值 < 最小值:
            return False
        if 最大值 is not None and 值 > 最大值:
            return False
        return True
    
    def 验证必需(self, 配置: Dict, 必需参数: List[str] = None) -> List[验证错误]:
        """验证必需参数是否存在"""
        错误列表 = []
        
        if 必需参数 is None:
            必需参数 = [名 for 名, 定义 in self._扁平模式.items() if 定义.get("必需")]
        
        for 参数名 in 必需参数:
            if 参数名 not in 配置 or 配置[参数名] is None:
                错误列表.append(验证错误(
                    参数名=参数名,
                    错误类型="required",
                    错误信息=f"缺少必需参数: {参数名}"
                ))
        
        return 错误列表
    
    def 验证配置(self, 配置: Dict) -> Tuple[bool, List[验证错误]]:
        """
        验证整个配置
        
        返回:
            (是否有效, 错误列表)
        """
        错误列表 = []
        
        # 验证必需参数
        错误列表.extend(self.验证必需(配置))
        
        # 验证每个参数
        for 参数名, 值 in 配置.items():
            有效, 错误信息 = self.验证值(参数名, 值)
            if not 有效:
                错误列表.append(验证错误(
                    参数名=参数名,
                    错误类型="validation",
                    错误信息=错误信息,
                    当前值=值
                ))
        
        return len(错误列表) == 0, 错误列表


class 配置管理器:
    """管理配置的加载、保存和验证"""
    
    def __init__(self, 模式定义: Dict = None, 配置路径: str = "配置/设置.json"):
        """
        初始化配置管理器
        
        参数:
            模式定义: 配置模式定义
            配置路径: 默认配置文件路径
        """
        self._模式 = 模式定义 or 默认配置模式
        self._验证器 = 配置验证器(self._模式)
        self._配置路径 = 配置路径
        self._当前配置: Dict = {}
    
    def 加载配置(self, 配置路径: str = None) -> Dict:
        """
        从文件加载配置
        
        参数:
            配置路径: 配置文件路径
            
        返回:
            配置字典
        """
        路径 = 配置路径 or self._配置路径
        
        if not os.path.exists(路径):
            日志.warning(f"配置文件不存在: {路径}，使用默认配置")
            self._当前配置 = self.获取默认值()
            return self._当前配置
        
        try:
            with open(路径, 'r', encoding='utf-8') as f:
                self._当前配置 = json.load(f)
            日志.info(f"配置已加载: {路径}")
        except Exception as e:
            日志.error(f"加载配置失败: {e}，使用默认配置")
            self._当前配置 = self.获取默认值()
        
        return self._当前配置
    
    def 保存配置(self, 配置: Dict = None, 配置路径: str = None) -> bool:
        """
        保存配置到文件
        
        参数:
            配置: 配置字典
            配置路径: 配置文件路径
            
        返回:
            是否保存成功
        """
        配置 = 配置 or self._当前配置
        路径 = 配置路径 or self._配置路径
        
        # 验证配置
        有效, 错误列表 = self._验证器.验证配置(配置)
        if not 有效:
            日志.error(f"配置验证失败: {[e.错误信息 for e in 错误列表]}")
            return False
        
        try:
            os.makedirs(os.path.dirname(路径), exist_ok=True)
            with open(路径, 'w', encoding='utf-8') as f:
                json.dump(配置, f, ensure_ascii=False, indent=2)
            日志.info(f"配置已保存: {路径}")
            return True
        except Exception as e:
            日志.error(f"保存配置失败: {e}")
            return False
    
    def 验证配置(self, 配置: Dict = None) -> Tuple[bool, List[验证错误]]:
        """验证配置有效性"""
        配置 = 配置 or self._当前配置
        return self._验证器.验证配置(配置)
    
    def 获取默认值(self, 参数名: str = None) -> Any:
        """
        获取参数默认值
        
        参数:
            参数名: 参数名称，None 表示获取所有默认值
        """
        if 参数名:
            for 分区, 参数列表 in self._模式.items():
                if 参数名 in 参数列表:
                    return 参数列表[参数名].get("默认值")
            return None
        
        # 获取所有默认值
        默认配置 = {}
        for 分区, 参数列表 in self._模式.items():
            for 名称, 定义 in 参数列表.items():
                默认配置[名称] = 定义.get("默认值")
        return 默认配置
    
    def 重置为默认(self, 分区: str = None) -> Dict:
        """
        重置配置为默认值
        
        参数:
            分区: 分区名称，None 表示重置所有
        """
        if 分区 is None:
            self._当前配置 = self.获取默认值()
        elif 分区 in self._模式:
            for 名称, 定义 in self._模式[分区].items():
                self._当前配置[名称] = 定义.get("默认值")
        
        return self._当前配置
    
    def 导出配置(self, 配置: Dict, 导出路径: str):
        """导出配置到文件"""
        try:
            with open(导出路径, 'w', encoding='utf-8') as f:
                json.dump(配置, f, ensure_ascii=False, indent=2)
            日志.info(f"配置已导出: {导出路径}")
        except Exception as e:
            日志.error(f"导出配置失败: {e}")
    
    def 导入配置(self, 导入路径: str) -> Optional[Dict]:
        """从文件导入配置"""
        try:
            with open(导入路径, 'r', encoding='utf-8') as f:
                配置 = json.load(f)
            日志.info(f"配置已导入: {导入路径}")
            return 配置
        except Exception as e:
            日志.error(f"导入配置失败: {e}")
            return None
    
    def 获取模式(self) -> Dict:
        """获取配置模式定义"""
        return self._模式
    
    def 获取当前配置(self) -> Dict:
        """获取当前配置"""
        return self._当前配置.copy()
    
    def 设置值(self, 参数名: str, 值: Any) -> bool:
        """设置单个参数值"""
        有效, 错误 = self._验证器.验证值(参数名, 值)
        if 有效:
            self._当前配置[参数名] = 值
            return True
        日志.warning(f"设置值失败: {错误}")
        return False


class 档案管理器:
    """管理多个配置档案"""
    
    def __init__(self, 档案目录: str = "配置/档案"):
        self._档案目录 = 档案目录
        os.makedirs(档案目录, exist_ok=True)
    
    def 获取档案列表(self) -> List[Dict]:
        """获取所有配置档案"""
        档案列表 = []
        
        if not os.path.exists(self._档案目录):
            return 档案列表
        
        for 文件名 in os.listdir(self._档案目录):
            if 文件名.endswith('.json'):
                档案名 = 文件名[:-5]
                文件路径 = os.path.join(self._档案目录, 文件名)
                
                try:
                    修改时间 = os.path.getmtime(文件路径)
                    档案列表.append({
                        "名称": 档案名,
                        "路径": 文件路径,
                        "修改时间": datetime.fromtimestamp(修改时间).strftime("%Y-%m-%d %H:%M")
                    })
                except:
                    pass
        
        return sorted(档案列表, key=lambda x: x["名称"])
    
    def 创建档案(self, 档案名: str, 配置: Dict) -> bool:
        """创建新档案"""
        文件路径 = os.path.join(self._档案目录, f"{档案名}.json")
        
        if os.path.exists(文件路径):
            日志.warning(f"档案已存在: {档案名}")
            return False
        
        try:
            with open(文件路径, 'w', encoding='utf-8') as f:
                json.dump(配置, f, ensure_ascii=False, indent=2)
            日志.info(f"档案已创建: {档案名}")
            return True
        except Exception as e:
            日志.error(f"创建档案失败: {e}")
            return False
    
    def 加载档案(self, 档案名: str) -> Optional[Dict]:
        """加载指定档案"""
        文件路径 = os.path.join(self._档案目录, f"{档案名}.json")
        
        if not os.path.exists(文件路径):
            日志.warning(f"档案不存在: {档案名}")
            return None
        
        try:
            with open(文件路径, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            日志.error(f"加载档案失败: {e}")
            return None
    
    def 保存档案(self, 档案名: str, 配置: Dict) -> bool:
        """保存到指定档案"""
        文件路径 = os.path.join(self._档案目录, f"{档案名}.json")
        
        try:
            with open(文件路径, 'w', encoding='utf-8') as f:
                json.dump(配置, f, ensure_ascii=False, indent=2)
            日志.info(f"档案已保存: {档案名}")
            return True
        except Exception as e:
            日志.error(f"保存档案失败: {e}")
            return False
    
    def 删除档案(self, 档案名: str) -> bool:
        """删除指定档案"""
        文件路径 = os.path.join(self._档案目录, f"{档案名}.json")
        
        if not os.path.exists(文件路径):
            return False
        
        try:
            os.remove(文件路径)
            日志.info(f"档案已删除: {档案名}")
            return True
        except Exception as e:
            日志.error(f"删除档案失败: {e}")
            return False
    
    def 重命名档案(self, 旧名称: str, 新名称: str) -> bool:
        """重命名档案"""
        旧路径 = os.path.join(self._档案目录, f"{旧名称}.json")
        新路径 = os.path.join(self._档案目录, f"{新名称}.json")
        
        if not os.path.exists(旧路径):
            return False
        
        if os.path.exists(新路径):
            日志.warning(f"目标档案名已存在: {新名称}")
            return False
        
        try:
            os.rename(旧路径, 新路径)
            日志.info(f"档案已重命名: {旧名称} -> {新名称}")
            return True
        except Exception as e:
            日志.error(f"重命名档案失败: {e}")
            return False
    
    def 复制档案(self, 源档案: str, 目标档案: str) -> bool:
        """复制档案"""
        源路径 = os.path.join(self._档案目录, f"{源档案}.json")
        目标路径 = os.path.join(self._档案目录, f"{目标档案}.json")
        
        if not os.path.exists(源路径):
            return False
        
        try:
            shutil.copy2(源路径, 目标路径)
            日志.info(f"档案已复制: {源档案} -> {目标档案}")
            return True
        except Exception as e:
            日志.error(f"复制档案失败: {e}")
            return False
