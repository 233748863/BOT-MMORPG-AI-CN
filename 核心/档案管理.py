"""
档案管理模块
管理多个配置档案的CRUD操作

需求: 3.3
"""

import os
import json
import shutil
from typing import List, Optional, Dict, Any
from datetime import datetime


class 档案管理器:
    """管理多个配置档案
    
    提供配置档案的完整生命周期管理，包括：
    - 获取档案列表
    - 创建新档案
    - 加载档案
    - 删除档案
    - 重命名档案
    - 复制档案
    
    存储结构:
        配置/profiles/           # 配置档案目录
        ├── default.json        # 默认配置
        ├── game1.json          # 游戏1配置
        └── game2.json          # 游戏2配置
    
    需求: 3.3
    """
    
    # 默认档案目录
    DEFAULT_PROFILES_DIR = "配置/profiles"
    
    def __init__(self, 档案目录: str = None):
        """初始化档案管理器
        
        Args:
            档案目录: 配置档案存储目录，默认为 "配置/profiles"
            
        需求: 3.3
        """
        self._档案目录 = 档案目录 or self.DEFAULT_PROFILES_DIR
        
        # 确保档案目录存在
        self._确保目录存在()
    
    def _确保目录存在(self) -> None:
        """确保档案目录存在"""
        if not os.path.exists(self._档案目录):
            os.makedirs(self._档案目录)
    
    def _获取档案路径(self, 档案名: str) -> str:
        """获取档案文件的完整路径
        
        Args:
            档案名: 档案名称
            
        Returns:
            档案文件的完整路径
        """
        # 清理文件名，移除不安全字符
        安全名称 = self._清理文件名(档案名)
        return os.path.join(self._档案目录, f"{安全名称}.json")
    
    def _清理文件名(self, 名称: str) -> str:
        """清理文件名，移除不安全字符
        
        Args:
            名称: 原始名称
            
        Returns:
            安全的文件名
        """
        if not 名称:
            return "unnamed"
        
        # 保留字母、数字、下划线、连字符、空格和中文字符
        安全字符 = []
        for c in 名称:
            if c.isalnum() or c in ('_', '-', ' ') or '\u4e00' <= c <= '\u9fff':
                安全字符.append(c)
        
        结果 = "".join(安全字符).strip()
        return 结果 if 结果 else "unnamed"
    
    @property
    def 档案目录(self) -> str:
        """获取档案目录路径"""
        return self._档案目录
    
    # ==================== 档案列表操作 ====================
    
    def 获取档案列表(self) -> List[str]:
        """获取所有配置档案名称
        
        Returns:
            档案名称列表（按字母顺序排序）
            
        需求: 3.3
        """
        self._确保目录存在()
        
        档案列表 = []
        try:
            for 文件名 in os.listdir(self._档案目录):
                if 文件名.endswith('.json'):
                    # 移除 .json 后缀获取档案名
                    档案名 = 文件名[:-5]
                    档案列表.append(档案名)
        except (IOError, OSError):
            # 如果目录读取失败，返回空列表
            pass
        
        return sorted(档案列表)
    
    def 档案存在(self, 档案名: str) -> bool:
        """检查档案是否存在
        
        Args:
            档案名: 档案名称
            
        Returns:
            档案是否存在
        """
        if not 档案名 or not 档案名.strip():
            return False
        
        档案路径 = self._获取档案路径(档案名)
        return os.path.exists(档案路径)
    
    def 获取档案数量(self) -> int:
        """获取档案总数
        
        Returns:
            档案数量
        """
        return len(self.获取档案列表())
    
    # ==================== 档案CRUD操作 ====================
    
    def 创建档案(self, 档案名: str, 配置: Dict[str, Any]) -> bool:
        """创建新档案
        
        Args:
            档案名: 档案名称
            配置: 配置字典
            
        Returns:
            创建是否成功
            
        Raises:
            ValueError: 如果档案名为空
            FileExistsError: 如果同名档案已存在
            IOError: 如果文件写入失败
            
        需求: 3.3
        """
        if not 档案名 or not 档案名.strip():
            raise ValueError("档案名称不能为空")
        
        档案名 = 档案名.strip()
        
        # 检查是否已存在同名档案
        if self.档案存在(档案名):
            raise FileExistsError(f"档案 '{档案名}' 已存在")
        
        # 添加元数据
        保存数据 = {
            "_元数据": {
                "创建时间": datetime.now().isoformat(),
                "更新时间": datetime.now().isoformat(),
                "版本": "1.0"
            },
            "名称": 档案名,
            "配置": 配置 or {}
        }
        
        档案路径 = self._获取档案路径(档案名)
        
        try:
            self._确保目录存在()
            with open(档案路径, 'w', encoding='utf-8') as f:
                json.dump(保存数据, f, ensure_ascii=False, indent=2)
            return True
        except (IOError, OSError) as e:
            raise IOError(f"创建档案失败: {e}")
    
    def 加载档案(self, 档案名: str) -> Dict[str, Any]:
        """加载指定档案
        
        Args:
            档案名: 档案名称
            
        Returns:
            档案配置字典
            
        Raises:
            ValueError: 如果档案名为空
            FileNotFoundError: 如果档案不存在
            ValueError: 如果档案格式无效
            IOError: 如果文件读取失败
            
        需求: 3.3
        """
        if not 档案名 or not 档案名.strip():
            raise ValueError("档案名称不能为空")
        
        档案路径 = self._获取档案路径(档案名)
        
        if not os.path.exists(档案路径):
            raise FileNotFoundError(f"档案 '{档案名}' 不存在")
        
        try:
            with open(档案路径, 'r', encoding='utf-8') as f:
                数据 = json.load(f)
            
            # 检查是否是新格式（带元数据）
            if "配置" in 数据:
                return 数据["配置"]
            
            # 兼容旧格式（直接是配置字典）
            # 移除元数据字段
            if "_元数据" in 数据:
                数据 = {k: v for k, v in 数据.items() if k != "_元数据"}
            
            return 数据
            
        except json.JSONDecodeError as e:
            raise ValueError(f"档案格式无效: {e}")
        except (IOError, OSError) as e:
            raise IOError(f"读取档案失败: {e}")
    
    def 保存档案(self, 档案名: str, 配置: Dict[str, Any]) -> bool:
        """保存档案（覆盖已存在的档案）
        
        Args:
            档案名: 档案名称
            配置: 配置字典
            
        Returns:
            保存是否成功
            
        Raises:
            ValueError: 如果档案名为空
            IOError: 如果文件写入失败
        """
        if not 档案名 or not 档案名.strip():
            raise ValueError("档案名称不能为空")
        
        档案名 = 档案名.strip()
        档案路径 = self._获取档案路径(档案名)
        
        # 读取现有元数据（如果存在）
        创建时间 = datetime.now().isoformat()
        if os.path.exists(档案路径):
            try:
                with open(档案路径, 'r', encoding='utf-8') as f:
                    现有数据 = json.load(f)
                if "_元数据" in 现有数据 and "创建时间" in 现有数据["_元数据"]:
                    创建时间 = 现有数据["_元数据"]["创建时间"]
            except (json.JSONDecodeError, IOError, OSError):
                pass
        
        # 构建保存数据
        保存数据 = {
            "_元数据": {
                "创建时间": 创建时间,
                "更新时间": datetime.now().isoformat(),
                "版本": "1.0"
            },
            "名称": 档案名,
            "配置": 配置 or {}
        }
        
        try:
            self._确保目录存在()
            with open(档案路径, 'w', encoding='utf-8') as f:
                json.dump(保存数据, f, ensure_ascii=False, indent=2)
            return True
        except (IOError, OSError) as e:
            raise IOError(f"保存档案失败: {e}")
    
    def 删除档案(self, 档案名: str) -> bool:
        """删除指定档案
        
        Args:
            档案名: 档案名称
            
        Returns:
            删除是否成功
            
        Raises:
            ValueError: 如果档案名为空
            FileNotFoundError: 如果档案不存在
            IOError: 如果文件删除失败
            
        需求: 3.3
        """
        if not 档案名 or not 档案名.strip():
            raise ValueError("档案名称不能为空")
        
        档案路径 = self._获取档案路径(档案名)
        
        if not os.path.exists(档案路径):
            raise FileNotFoundError(f"档案 '{档案名}' 不存在")
        
        try:
            os.remove(档案路径)
            return True
        except (IOError, OSError) as e:
            raise IOError(f"删除档案失败: {e}")

    # ==================== 档案操作 ====================
    # 需求: 3.3
    
    def 重命名档案(self, 旧名称: str, 新名称: str) -> bool:
        """重命名档案
        
        Args:
            旧名称: 原档案名称
            新名称: 新档案名称
            
        Returns:
            重命名是否成功
            
        Raises:
            ValueError: 如果名称为空或新旧名称相同
            FileNotFoundError: 如果原档案不存在
            FileExistsError: 如果新名称的档案已存在
            IOError: 如果文件操作失败
            
        需求: 3.3
        """
        if not 旧名称 or not 旧名称.strip():
            raise ValueError("原档案名称不能为空")
        if not 新名称 or not 新名称.strip():
            raise ValueError("新档案名称不能为空")
        
        旧名称 = 旧名称.strip()
        新名称 = 新名称.strip()
        
        # 检查新旧名称是否相同
        if self._清理文件名(旧名称) == self._清理文件名(新名称):
            raise ValueError("新名称与原名称相同")
        
        # 检查原档案是否存在
        if not self.档案存在(旧名称):
            raise FileNotFoundError(f"档案 '{旧名称}' 不存在")
        
        # 检查新名称是否已被使用
        if self.档案存在(新名称):
            raise FileExistsError(f"档案 '{新名称}' 已存在")
        
        旧路径 = self._获取档案路径(旧名称)
        新路径 = self._获取档案路径(新名称)
        
        try:
            # 读取原档案内容
            with open(旧路径, 'r', encoding='utf-8') as f:
                数据 = json.load(f)
            
            # 更新档案名称
            数据["名称"] = 新名称
            if "_元数据" in 数据:
                数据["_元数据"]["更新时间"] = datetime.now().isoformat()
            
            # 写入新文件
            with open(新路径, 'w', encoding='utf-8') as f:
                json.dump(数据, f, ensure_ascii=False, indent=2)
            
            # 删除原文件
            os.remove(旧路径)
            
            return True
        except (IOError, OSError) as e:
            # 如果新文件已创建但删除原文件失败，尝试清理
            if os.path.exists(新路径) and os.path.exists(旧路径):
                try:
                    os.remove(新路径)
                except:
                    pass
            raise IOError(f"重命名档案失败: {e}")
    
    def 复制档案(self, 源档案: str, 目标档案: str) -> bool:
        """复制档案
        
        Args:
            源档案: 源档案名称
            目标档案: 目标档案名称
            
        Returns:
            复制是否成功
            
        Raises:
            ValueError: 如果名称为空或源目标名称相同
            FileNotFoundError: 如果源档案不存在
            FileExistsError: 如果目标档案已存在
            IOError: 如果文件操作失败
            
        需求: 3.3
        """
        if not 源档案 or not 源档案.strip():
            raise ValueError("源档案名称不能为空")
        if not 目标档案 or not 目标档案.strip():
            raise ValueError("目标档案名称不能为空")
        
        源档案 = 源档案.strip()
        目标档案 = 目标档案.strip()
        
        # 检查源目标名称是否相同
        if self._清理文件名(源档案) == self._清理文件名(目标档案):
            raise ValueError("目标档案名称与源档案名称相同")
        
        # 检查源档案是否存在
        if not self.档案存在(源档案):
            raise FileNotFoundError(f"源档案 '{源档案}' 不存在")
        
        # 检查目标档案是否已存在
        if self.档案存在(目标档案):
            raise FileExistsError(f"目标档案 '{目标档案}' 已存在")
        
        源路径 = self._获取档案路径(源档案)
        目标路径 = self._获取档案路径(目标档案)
        
        try:
            # 读取源档案内容
            with open(源路径, 'r', encoding='utf-8') as f:
                数据 = json.load(f)
            
            # 更新档案名称和元数据
            数据["名称"] = 目标档案
            数据["_元数据"] = {
                "创建时间": datetime.now().isoformat(),
                "更新时间": datetime.now().isoformat(),
                "版本": "1.0",
                "复制自": 源档案
            }
            
            # 写入目标文件
            with open(目标路径, 'w', encoding='utf-8') as f:
                json.dump(数据, f, ensure_ascii=False, indent=2)
            
            return True
        except (IOError, OSError) as e:
            raise IOError(f"复制档案失败: {e}")
    
    # ==================== 档案信息查询 ====================
    
    def 获取档案信息(self, 档案名: str) -> Dict[str, Any]:
        """获取档案的元数据信息
        
        Args:
            档案名: 档案名称
            
        Returns:
            档案元数据字典，包含创建时间、更新时间等
            
        Raises:
            ValueError: 如果档案名为空
            FileNotFoundError: 如果档案不存在
        """
        if not 档案名 or not 档案名.strip():
            raise ValueError("档案名称不能为空")
        
        档案路径 = self._获取档案路径(档案名)
        
        if not os.path.exists(档案路径):
            raise FileNotFoundError(f"档案 '{档案名}' 不存在")
        
        try:
            with open(档案路径, 'r', encoding='utf-8') as f:
                数据 = json.load(f)
            
            # 获取文件信息
            文件信息 = os.stat(档案路径)
            
            信息 = {
                "名称": 数据.get("名称", 档案名),
                "文件路径": 档案路径,
                "文件大小": 文件信息.st_size,
                "修改时间": datetime.fromtimestamp(文件信息.st_mtime).isoformat()
            }
            
            # 添加元数据（如果存在）
            if "_元数据" in 数据:
                信息.update({
                    "创建时间": 数据["_元数据"].get("创建时间"),
                    "更新时间": 数据["_元数据"].get("更新时间"),
                    "版本": 数据["_元数据"].get("版本"),
                    "复制自": 数据["_元数据"].get("复制自")
                })
            
            return 信息
            
        except json.JSONDecodeError:
            # 如果JSON解析失败，返回基本文件信息
            文件信息 = os.stat(档案路径)
            return {
                "名称": 档案名,
                "文件路径": 档案路径,
                "文件大小": 文件信息.st_size,
                "修改时间": datetime.fromtimestamp(文件信息.st_mtime).isoformat(),
                "错误": "档案格式无效"
            }
        except (IOError, OSError) as e:
            raise IOError(f"获取档案信息失败: {e}")
    
    def 获取所有档案信息(self) -> List[Dict[str, Any]]:
        """获取所有档案的元数据信息
        
        Returns:
            档案信息列表
        """
        档案列表 = self.获取档案列表()
        信息列表 = []
        
        for 档案名 in 档案列表:
            try:
                信息 = self.获取档案信息(档案名)
                信息列表.append(信息)
            except (FileNotFoundError, IOError, ValueError):
                # 跳过无法读取的档案
                continue
        
        return 信息列表
