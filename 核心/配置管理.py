"""
配置管理模块
定义游戏配置档案、窗口配置、按键映射、UI区域等数据结构
"""

from dataclasses import dataclass, field
from typing import Dict, Tuple, List, Optional, Any
from datetime import datetime
import json
import os


# ==================== 窗口配置数据类 ====================
@dataclass
class WindowConfig:
    """窗口配置"""
    x: int = 0  # 窗口X坐标
    y: int = 0  # 窗口Y坐标
    width: int = 1920  # 窗口宽度
    height: int = 1080  # 窗口高度

    def __post_init__(self):
        """验证数据有效性"""
        if self.width <= 0:
            raise ValueError(f"窗口宽度必须为正数，当前值: {self.width}")
        if self.height <= 0:
            raise ValueError(f"窗口高度必须为正数，当前值: {self.height}")

    def to_dict(self) -> Dict[str, int]:
        """转换为字典"""
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height
        }

    @classmethod
    def from_dict(cls, data: Dict[str, int]) -> 'WindowConfig':
        """从字典创建"""
        return cls(
            x=data.get("x", 0),
            y=data.get("y", 0),
            width=data.get("width", 1920),
            height=data.get("height", 1080)
        )


# ==================== 按键映射数据类 ====================
@dataclass
class KeyMapping:
    """按键映射配置"""
    move_keys: Dict[str, str] = field(default_factory=lambda: {
        "W": "up", "S": "down", "A": "left", "D": "right"
    })  # 移动键映射
    skill_keys: Dict[str, str] = field(default_factory=lambda: {
        "1": "skill1", "2": "skill2", "3": "skill3", "4": "skill4"
    })  # 技能键映射
    interact_key: str = "F"  # 交互键

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "move_keys": self.move_keys.copy(),
            "skill_keys": self.skill_keys.copy(),
            "interact_key": self.interact_key
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KeyMapping':
        """从字典创建"""
        return cls(
            move_keys=data.get("move_keys", {"W": "up", "S": "down", "A": "left", "D": "right"}),
            skill_keys=data.get("skill_keys", {"1": "skill1", "2": "skill2", "3": "skill3", "4": "skill4"}),
            interact_key=data.get("interact_key", "F")
        )



# ==================== UI区域配置数据类 ====================
@dataclass
class UIRegions:
    """UI区域配置"""
    health_bar: Tuple[int, int, int, int] = (0, 0, 200, 20)  # 血条区域 (x, y, w, h)
    skill_bar: Tuple[int, int, int, int] = (0, 0, 400, 50)  # 技能栏区域
    dialog_area: Tuple[int, int, int, int] = (0, 0, 800, 200)  # 对话框区域
    minimap: Tuple[int, int, int, int] = (0, 0, 200, 200)  # 小地图区域

    def __post_init__(self):
        """验证数据有效性"""
        for name, region in [
            ("health_bar", self.health_bar),
            ("skill_bar", self.skill_bar),
            ("dialog_area", self.dialog_area),
            ("minimap", self.minimap)
        ]:
            if len(region) != 4:
                raise ValueError(f"{name} 必须是4元组 (x, y, w, h)，当前值: {region}")
            if region[2] <= 0 or region[3] <= 0:
                raise ValueError(f"{name} 的宽度和高度必须为正数，当前值: {region}")

    def to_dict(self) -> Dict[str, List[int]]:
        """转换为字典"""
        return {
            "health_bar": list(self.health_bar),
            "skill_bar": list(self.skill_bar),
            "dialog_area": list(self.dialog_area),
            "minimap": list(self.minimap)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, List[int]]) -> 'UIRegions':
        """从字典创建"""
        return cls(
            health_bar=tuple(data.get("health_bar", [0, 0, 200, 20])),
            skill_bar=tuple(data.get("skill_bar", [0, 0, 400, 50])),
            dialog_area=tuple(data.get("dialog_area", [0, 0, 800, 200])),
            minimap=tuple(data.get("minimap", [0, 0, 200, 200]))
        )


# ==================== 检测参数数据类 ====================
@dataclass
class DetectionParams:
    """检测参数配置"""
    yolo_model_path: str = "模型/预训练模型/yolo.pt"  # YOLO模型路径
    confidence_threshold: float = 0.5  # 置信度阈值

    def __post_init__(self):
        """验证数据有效性"""
        if not 0.0 <= self.confidence_threshold <= 1.0:
            raise ValueError(f"置信度阈值必须在0-1范围内，当前值: {self.confidence_threshold}")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "yolo_model_path": self.yolo_model_path,
            "confidence_threshold": self.confidence_threshold
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DetectionParams':
        """从字典创建"""
        return cls(
            yolo_model_path=data.get("yolo_model_path", "模型/预训练模型/yolo.pt"),
            confidence_threshold=data.get("confidence_threshold", 0.5)
        )


# ==================== 决策规则配置数据类 ====================
@dataclass
class DecisionRules:
    """决策规则配置"""
    state_priorities: Dict[str, int] = field(default_factory=lambda: {
        "combat": 1, "dialog": 2, "looting": 3, "moving": 4, "idle": 5
    })  # 状态优先级
    action_weights: Dict[str, float] = field(default_factory=lambda: {
        "skill": 1.0, "move": 0.8, "interact": 0.9, "wait": 0.3
    })  # 动作权重

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "state_priorities": self.state_priorities.copy(),
            "action_weights": self.action_weights.copy()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DecisionRules':
        """从字典创建"""
        return cls(
            state_priorities=data.get("state_priorities", {
                "combat": 1, "dialog": 2, "looting": 3, "moving": 4, "idle": 5
            }),
            action_weights=data.get("action_weights", {
                "skill": 1.0, "move": 0.8, "interact": 0.9, "wait": 0.3
            })
        )



# ==================== 游戏配置档案数据类 ====================
@dataclass
class GameProfile:
    """游戏配置档案数据结构"""
    name: str  # 档案名称
    game_name: str  # 游戏名称
    created_at: datetime = field(default_factory=datetime.now)  # 创建时间
    updated_at: datetime = field(default_factory=datetime.now)  # 更新时间
    
    # 窗口配置
    window_config: WindowConfig = field(default_factory=WindowConfig)
    # 按键映射
    key_mapping: KeyMapping = field(default_factory=KeyMapping)
    # UI区域配置
    ui_regions: UIRegions = field(default_factory=UIRegions)
    # 检测参数
    detection_params: DetectionParams = field(default_factory=DetectionParams)
    # 决策规则
    decision_rules: DecisionRules = field(default_factory=DecisionRules)

    def __post_init__(self):
        """验证数据有效性"""
        if not self.name or not self.name.strip():
            raise ValueError("档案名称不能为空")
        if not self.game_name or not self.game_name.strip():
            raise ValueError("游戏名称不能为空")

    def validate_completeness(self) -> Tuple[bool, List[str]]:
        """验证配置档案完整性
        
        Returns:
            (是否完整, 缺失字段列表)
        """
        missing_fields = []
        
        # 检查必要字段
        if self.window_config is None:
            missing_fields.append("window_config")
        if self.key_mapping is None:
            missing_fields.append("key_mapping")
        if self.ui_regions is None:
            missing_fields.append("ui_regions")
        if self.detection_params is None:
            missing_fields.append("detection_params")
        if self.decision_rules is None:
            missing_fields.append("decision_rules")
        
        return len(missing_fields) == 0, missing_fields

    def update_timestamp(self) -> None:
        """更新修改时间"""
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于JSON序列化）"""
        return {
            "name": self.name,
            "game_name": self.game_name,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "window_config": self.window_config.to_dict(),
            "key_mapping": self.key_mapping.to_dict(),
            "ui_regions": self.ui_regions.to_dict(),
            "detection_params": self.detection_params.to_dict(),
            "decision_rules": self.decision_rules.to_dict()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GameProfile':
        """从字典创建（用于JSON反序列化）"""
        return cls(
            name=data["name"],
            game_name=data["game_name"],
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat())),
            window_config=WindowConfig.from_dict(data.get("window_config", {})),
            key_mapping=KeyMapping.from_dict(data.get("key_mapping", {})),
            ui_regions=UIRegions.from_dict(data.get("ui_regions", {})),
            detection_params=DetectionParams.from_dict(data.get("detection_params", {})),
            decision_rules=DecisionRules.from_dict(data.get("decision_rules", {}))
        )

    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> 'GameProfile':
        """从JSON字符串创建"""
        data = json.loads(json_str)
        return cls.from_dict(data)


# ==================== 配置管理器类 ====================
class ConfigManager:
    """配置管理器
    
    负责游戏配置档案的CRUD操作，包括：
    - 创建新配置档案
    - 保存配置档案
    - 加载配置档案
    - 删除配置档案
    - 列出所有档案
    
    存储结构:
        配置/profiles/           # 游戏配置档案目录
        ├── default.json        # 默认配置
        ├── game1.json          # 游戏1配置
        └── game2.json          # 游戏2配置
        配置/last_profile.txt   # 上次使用的档案名
    """
    
    # 默认配置目录
    DEFAULT_PROFILES_DIR = "配置/profiles"
    # 上次使用档案记录文件
    LAST_PROFILE_FILE = "配置/last_profile.txt"
    
    def __init__(self, profiles_dir: Optional[str] = None, last_profile_file: Optional[str] = None, auto_load_last: bool = True):
        """初始化配置管理器
        
        Args:
            profiles_dir: 配置档案存储目录，默认为 "配置/profiles"
            last_profile_file: 上次使用档案记录文件路径，默认为 "配置/last_profile.txt"
            auto_load_last: 是否自动加载上次使用的档案，默认为 True
        """
        self._profiles_dir = profiles_dir or self.DEFAULT_PROFILES_DIR
        self._last_profile_file = last_profile_file or self.LAST_PROFILE_FILE
        self._current_profile: Optional[GameProfile] = None
        self._has_unsaved_changes: bool = False
        
        # 确保配置目录存在
        self._ensure_profiles_dir()
        
        # 自动加载上次使用的档案
        if auto_load_last:
            self._auto_load_last_profile()
    
    def _ensure_profiles_dir(self) -> None:
        """确保配置档案目录存在"""
        if not os.path.exists(self._profiles_dir):
            os.makedirs(self._profiles_dir)
    
    def _auto_load_last_profile(self) -> None:
        """自动加载上次使用的档案
        
        如果上次使用的档案记录存在且档案有效，则自动加载。
        加载失败时静默处理，不抛出异常。
        """
        try:
            last_name = self._load_last_profile_name()
            if last_name and self.profile_exists(last_name):
                profile = self.load_profile(last_name)
                self._current_profile = profile
                self._has_unsaved_changes = False
        except (FileNotFoundError, ValueError, IOError):
            # 加载失败时静默处理
            pass
    
    def _load_last_profile_name(self) -> Optional[str]:
        """读取上次使用的档案名称
        
        Returns:
            上次使用的档案名称，如果不存在则返回 None
        """
        if not os.path.exists(self._last_profile_file):
            return None
        
        try:
            with open(self._last_profile_file, 'r', encoding='utf-8') as f:
                name = f.read().strip()
                return name if name else None
        except (IOError, OSError):
            return None
    
    def _save_last_profile_name(self, name: str) -> bool:
        """保存上次使用的档案名称
        
        Args:
            name: 档案名称
            
        Returns:
            保存是否成功
        """
        try:
            # 确保目录存在
            last_profile_dir = os.path.dirname(self._last_profile_file)
            if last_profile_dir and not os.path.exists(last_profile_dir):
                os.makedirs(last_profile_dir)
            
            with open(self._last_profile_file, 'w', encoding='utf-8') as f:
                f.write(name)
            return True
        except (IOError, OSError):
            return False
    
    def switch_profile(self, name: str) -> bool:
        """切换当前使用的档案
        
        热加载新配置，切换成功后会持久化记录上次使用的档案。
        
        Args:
            name: 要切换到的档案名称
            
        Returns:
            切换是否成功
            
        Raises:
            FileNotFoundError: 如果档案不存在
            ValueError: 如果档案名称为空或档案格式无效
        """
        if not name or not name.strip():
            raise ValueError("档案名称不能为空")
        
        # 加载目标档案
        profile = self.load_profile(name)
        
        # 设置为当前档案
        self._current_profile = profile
        self._has_unsaved_changes = False
        
        # 持久化记录上次使用的档案
        self._save_last_profile_name(name)
        
        return True
    
    def _get_profile_path(self, name: str) -> str:
        """获取配置档案文件路径
        
        Args:
            name: 档案名称
            
        Returns:
            档案文件的完整路径
        """
        # 清理文件名，移除不安全字符
        safe_name = "".join(c for c in name if c.isalnum() or c in ('_', '-', ' ', '中', '文'))
        if not safe_name:
            safe_name = "unnamed"
        return os.path.join(self._profiles_dir, f"{safe_name}.json")
    
    def create_profile(self, name: str, game_name: str) -> GameProfile:
        """创建新配置档案
        
        Args:
            name: 档案名称
            game_name: 游戏名称
            
        Returns:
            新创建的 GameProfile 实例
            
        Raises:
            ValueError: 如果档案名称或游戏名称为空
            FileExistsError: 如果同名档案已存在
        """
        if not name or not name.strip():
            raise ValueError("档案名称不能为空")
        if not game_name or not game_name.strip():
            raise ValueError("游戏名称不能为空")
        
        # 检查是否已存在同名档案
        profile_path = self._get_profile_path(name)
        if os.path.exists(profile_path):
            raise FileExistsError(f"档案 '{name}' 已存在")
        
        # 创建新档案
        profile = GameProfile(
            name=name.strip(),
            game_name=game_name.strip()
        )
        
        return profile
    
    def save_profile(self, profile: GameProfile) -> bool:
        """保存配置档案
        
        Args:
            profile: 要保存的配置档案
            
        Returns:
            保存是否成功
            
        Raises:
            ValueError: 如果配置档案无效
        """
        if profile is None:
            raise ValueError("配置档案不能为空")
        
        # 验证档案完整性
        is_complete, missing = profile.validate_completeness()
        if not is_complete:
            raise ValueError(f"配置档案不完整，缺少字段: {missing}")
        
        # 更新时间戳
        profile.update_timestamp()
        
        # 获取保存路径
        profile_path = self._get_profile_path(profile.name)
        
        try:
            # 写入JSON文件
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(profile.to_dict(), f, ensure_ascii=False, indent=2)
            
            # 如果是当前档案，清除未保存标记
            if self._current_profile and self._current_profile.name == profile.name:
                self._has_unsaved_changes = False
            
            return True
        except (IOError, OSError) as e:
            raise IOError(f"保存配置档案失败: {e}")
    
    def load_profile(self, name: str) -> GameProfile:
        """加载配置档案
        
        Args:
            name: 档案名称
            
        Returns:
            加载的 GameProfile 实例
            
        Raises:
            FileNotFoundError: 如果档案不存在
            ValueError: 如果档案格式无效
        """
        if not name or not name.strip():
            raise ValueError("档案名称不能为空")
        
        profile_path = self._get_profile_path(name)
        
        if not os.path.exists(profile_path):
            raise FileNotFoundError(f"档案 '{name}' 不存在")
        
        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            profile = GameProfile.from_dict(data)
            return profile
        except json.JSONDecodeError as e:
            raise ValueError(f"档案格式无效: {e}")
        except (IOError, OSError) as e:
            raise IOError(f"读取配置档案失败: {e}")
    
    def delete_profile(self, name: str) -> bool:
        """删除配置档案
        
        Args:
            name: 档案名称
            
        Returns:
            删除是否成功
            
        Raises:
            FileNotFoundError: 如果档案不存在
        """
        if not name or not name.strip():
            raise ValueError("档案名称不能为空")
        
        profile_path = self._get_profile_path(name)
        
        if not os.path.exists(profile_path):
            raise FileNotFoundError(f"档案 '{name}' 不存在")
        
        try:
            os.remove(profile_path)
            
            # 如果删除的是当前档案，清除当前档案引用
            if self._current_profile and self._current_profile.name == name:
                self._current_profile = None
                self._has_unsaved_changes = False
            
            return True
        except (IOError, OSError) as e:
            raise IOError(f"删除配置档案失败: {e}")
    
    def list_profiles(self) -> List[str]:
        """列出所有档案名称
        
        Returns:
            档案名称列表
        """
        self._ensure_profiles_dir()
        
        profiles = []
        try:
            for filename in os.listdir(self._profiles_dir):
                if filename.endswith('.json'):
                    # 移除 .json 后缀获取档案名
                    profile_name = filename[:-5]
                    profiles.append(profile_name)
        except (IOError, OSError):
            # 如果目录读取失败，返回空列表
            pass
        
        return sorted(profiles)
    
    def profile_exists(self, name: str) -> bool:
        """检查档案是否存在
        
        Args:
            name: 档案名称
            
        Returns:
            档案是否存在
        """
        if not name or not name.strip():
            return False
        
        profile_path = self._get_profile_path(name)
        return os.path.exists(profile_path)
    
    def get_current_profile(self) -> Optional[GameProfile]:
        """获取当前档案
        
        Returns:
            当前使用的配置档案，如果没有则返回 None
        """
        return self._current_profile
    
    def set_current_profile(self, profile: GameProfile) -> None:
        """设置当前档案
        
        Args:
            profile: 要设置为当前的配置档案
        """
        self._current_profile = profile
        self._has_unsaved_changes = False
    
    def has_unsaved_changes(self) -> bool:
        """检查是否有未保存的更改
        
        Returns:
            是否有未保存的更改
        """
        return self._has_unsaved_changes
    
    def mark_as_modified(self) -> None:
        """标记当前档案已修改"""
        self._has_unsaved_changes = True
    
    @property
    def profiles_dir(self) -> str:
        """获取配置档案目录路径"""
        return self._profiles_dir
    
    @property
    def last_profile_file(self) -> str:
        """获取上次使用档案记录文件路径"""
        return self._last_profile_file
    
    def export_profile(self, name: str, filepath: str) -> bool:
        """导出档案为JSON文件
        
        将指定的配置档案导出到用户指定的文件路径。
        
        Args:
            name: 要导出的档案名称
            filepath: 导出文件的目标路径
            
        Returns:
            导出是否成功
            
        Raises:
            FileNotFoundError: 如果档案不存在
            ValueError: 如果参数无效
            IOError: 如果文件写入失败
        """
        if not name or not name.strip():
            raise ValueError("档案名称不能为空")
        if not filepath or not filepath.strip():
            raise ValueError("导出路径不能为空")
        
        # 加载档案
        profile = self.load_profile(name)
        
        # 确保目标目录存在
        target_dir = os.path.dirname(filepath)
        if target_dir and not os.path.exists(target_dir):
            os.makedirs(target_dir)
        
        try:
            # 写入JSON文件
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(profile.to_dict(), f, ensure_ascii=False, indent=2)
            return True
        except (IOError, OSError) as e:
            raise IOError(f"导出配置档案失败: {e}")
    
    def import_profile(self, filepath: str, new_name: Optional[str] = None) -> GameProfile:
        """从JSON文件导入档案
        
        从用户指定的JSON文件导入配置档案。
        
        Args:
            filepath: 要导入的JSON文件路径
            new_name: 可选，导入后使用的新档案名称。如果不指定，使用文件中的原名称。
            
        Returns:
            导入的 GameProfile 实例
            
        Raises:
            FileNotFoundError: 如果文件不存在
            ValueError: 如果文件格式无效
            IOError: 如果文件读取失败
        """
        if not filepath or not filepath.strip():
            raise ValueError("导入路径不能为空")
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"文件 '{filepath}' 不存在")
        
        try:
            # 读取JSON文件
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 验证必要字段
            if "name" not in data:
                raise ValueError("导入文件缺少必要字段: name")
            if "game_name" not in data:
                raise ValueError("导入文件缺少必要字段: game_name")
            
            # 如果指定了新名称，使用新名称
            if new_name and new_name.strip():
                data["name"] = new_name.strip()
                # 更新时间戳为当前时间
                data["updated_at"] = datetime.now().isoformat()
            
            # 创建 GameProfile 实例
            profile = GameProfile.from_dict(data)
            
            # 验证档案完整性
            is_complete, missing = profile.validate_completeness()
            if not is_complete:
                raise ValueError(f"导入的配置档案不完整，缺少字段: {missing}")
            
            return profile
            
        except json.JSONDecodeError as e:
            raise ValueError(f"文件格式无效，不是有效的JSON: {e}")
        except KeyError as e:
            raise ValueError(f"导入文件缺少必要字段: {e}")
        except (IOError, OSError) as e:
            raise IOError(f"读取导入文件失败: {e}")
