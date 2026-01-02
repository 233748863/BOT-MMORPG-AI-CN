"""
自动调参模块
定义性能指标、参数空间、调参记录等数据结构
以及自动调参器接口
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, List, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
import json
import os
import logging

# 配置日志
logger = logging.getLogger(__name__)


# ==================== 枚举类型 ====================
class AggressivenessLevel(Enum):
    """调参激进程度"""
    CONSERVATIVE = "conservative"  # 保守：每次调整1个步长
    BALANCED = "balanced"  # 平衡：每次调整2个步长
    AGGRESSIVE = "aggressive"  # 激进：每次调整3个步长

    def get_step_multiplier(self) -> int:
        """获取步长倍数"""
        if self == AggressivenessLevel.CONSERVATIVE:
            return 1
        elif self == AggressivenessLevel.BALANCED:
            return 2
        else:
            return 3


# ==================== 性能指标数据类 ====================
@dataclass
class PerformanceMetric:
    """性能指标数据结构"""
    timestamp: datetime = field(default_factory=datetime.now)  # 时间戳
    action_success_rate: float = 0.0  # 动作执行成功率 (0.0 - 1.0)
    state_accuracy: float = 0.0  # 状态识别准确率 (0.0 - 1.0)
    stuck_count: int = 0  # 卡住次数
    task_efficiency: float = 0.0  # 任务完成效率 (0.0 - 1.0)

    def __post_init__(self):
        """验证数据有效性"""
        if not 0.0 <= self.action_success_rate <= 1.0:
            raise ValueError(f"动作执行成功率必须在0-1范围内，当前值: {self.action_success_rate}")
        if not 0.0 <= self.state_accuracy <= 1.0:
            raise ValueError(f"状态识别准确率必须在0-1范围内，当前值: {self.state_accuracy}")
        if self.stuck_count < 0:
            raise ValueError(f"卡住次数不能为负数，当前值: {self.stuck_count}")
        if not 0.0 <= self.task_efficiency <= 1.0:
            raise ValueError(f"任务完成效率必须在0-1范围内，当前值: {self.task_efficiency}")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "action_success_rate": self.action_success_rate,
            "state_accuracy": self.state_accuracy,
            "stuck_count": self.stuck_count,
            "task_efficiency": self.task_efficiency
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PerformanceMetric':
        """从字典创建"""
        return cls(
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat())),
            action_success_rate=data.get("action_success_rate", 0.0),
            state_accuracy=data.get("state_accuracy", 0.0),
            stuck_count=data.get("stuck_count", 0),
            task_efficiency=data.get("task_efficiency", 0.0)
        )

    def get_overall_score(self) -> float:
        """计算综合性能分数 (0.0 - 1.0)"""
        # 卡住次数转换为惩罚因子 (每次卡住扣0.05，最多扣0.5)
        stuck_penalty = min(self.stuck_count * 0.05, 0.5)
        # 综合评分 = 各指标加权平均 - 卡住惩罚
        score = (
            self.action_success_rate * 0.3 +
            self.state_accuracy * 0.3 +
            self.task_efficiency * 0.4
        ) - stuck_penalty
        return max(0.0, min(1.0, score))



# ==================== 参数空间数据类 ====================
@dataclass
class ParameterSpace:
    """参数空间定义"""
    name: str  # 参数名称
    min_value: float  # 最小值
    max_value: float  # 最大值
    step: float  # 调整步长
    current_value: float  # 当前值
    default_value: float  # 默认值
    locked: bool = False  # 是否锁定

    def __post_init__(self):
        """验证数据有效性"""
        if not self.name or not self.name.strip():
            raise ValueError("参数名称不能为空")
        if self.min_value > self.max_value:
            raise ValueError(f"最小值不能大于最大值: min={self.min_value}, max={self.max_value}")
        if self.step <= 0:
            raise ValueError(f"步长必须为正数，当前值: {self.step}")
        if not self.min_value <= self.current_value <= self.max_value:
            raise ValueError(f"当前值必须在[{self.min_value}, {self.max_value}]范围内，当前值: {self.current_value}")
        if not self.min_value <= self.default_value <= self.max_value:
            raise ValueError(f"默认值必须在[{self.min_value}, {self.max_value}]范围内，当前值: {self.default_value}")

    def adjust(self, delta: float) -> float:
        """调整参数值，返回调整后的值
        
        Args:
            delta: 调整量（可正可负）
            
        Returns:
            调整后的值（已限制在范围内）
        """
        if self.locked:
            return self.current_value
        
        new_value = self.current_value + delta
        # 限制在范围内
        new_value = max(self.min_value, min(self.max_value, new_value))
        self.current_value = new_value
        return new_value

    def reset(self) -> None:
        """重置为默认值"""
        if not self.locked:
            self.current_value = self.default_value

    def get_diff(self) -> float:
        """获取当前值与默认值的差异"""
        return self.current_value - self.default_value

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "step": self.step,
            "current_value": self.current_value,
            "default_value": self.default_value,
            "locked": self.locked
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ParameterSpace':
        """从字典创建"""
        return cls(
            name=data["name"],
            min_value=data["min_value"],
            max_value=data["max_value"],
            step=data["step"],
            current_value=data["current_value"],
            default_value=data["default_value"],
            locked=data.get("locked", False)
        )



# ==================== 调参记录数据类 ====================
@dataclass
class TuningRecord:
    """调参记录"""
    timestamp: datetime = field(default_factory=datetime.now)  # 时间戳
    parameter_name: str = ""  # 参数名称
    old_value: float = 0.0  # 调整前的值
    new_value: float = 0.0  # 调整后的值
    reason: str = ""  # 调整原因
    performance_before: Optional[PerformanceMetric] = None  # 调整前的性能指标
    performance_after: Optional[PerformanceMetric] = None  # 调整后的性能指标

    def __post_init__(self):
        """验证数据有效性"""
        if not self.parameter_name:
            raise ValueError("参数名称不能为空")

    @property
    def adjustment_delta(self) -> float:
        """获取调整幅度"""
        return self.new_value - self.old_value

    @property
    def is_improvement(self) -> Optional[bool]:
        """判断是否为改进（需要有调整后的性能数据）
        
        Returns:
            True: 性能提升
            False: 性能下降
            None: 无法判断（缺少数据）
        """
        if self.performance_before is None or self.performance_after is None:
            return None
        return self.performance_after.get_overall_score() >= self.performance_before.get_overall_score()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "parameter_name": self.parameter_name,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "reason": self.reason,
            "performance_before": self.performance_before.to_dict() if self.performance_before else None,
            "performance_after": self.performance_after.to_dict() if self.performance_after else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TuningRecord':
        """从字典创建"""
        return cls(
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat())),
            parameter_name=data["parameter_name"],
            old_value=data["old_value"],
            new_value=data["new_value"],
            reason=data.get("reason", ""),
            performance_before=PerformanceMetric.from_dict(data["performance_before"]) if data.get("performance_before") else None,
            performance_after=PerformanceMetric.from_dict(data["performance_after"]) if data.get("performance_after") else None
        )


# ==================== 默认参数空间定义 ====================
def get_default_parameter_spaces() -> Dict[str, ParameterSpace]:
    """获取默认的参数空间定义
    
    Returns:
        参数名称 -> ParameterSpace 的字典
    """
    return {
        "action_cooldown": ParameterSpace(
            name="action_cooldown",
            min_value=0.1,
            max_value=2.0,
            step=0.1,
            current_value=0.5,
            default_value=0.5
        ),
        "state_switch_threshold": ParameterSpace(
            name="state_switch_threshold",
            min_value=0.3,
            max_value=0.9,
            step=0.05,
            current_value=0.6,
            default_value=0.6
        ),
        "rule_priority_weight": ParameterSpace(
            name="rule_priority_weight",
            min_value=0.0,
            max_value=1.0,
            step=0.1,
            current_value=0.7,
            default_value=0.7
        ),
        "detection_confidence_threshold": ParameterSpace(
            name="detection_confidence_threshold",
            min_value=0.3,
            max_value=0.9,
            step=0.05,
            current_value=0.5,
            default_value=0.5
        )
    }


# ==================== 自动调参器类 ====================
class AutoTuner:
    """自动调参器
    
    负责收集性能指标、汇总分析、参数优化等功能
    """
    
    # 默认存储目录
    DEFAULT_TUNING_DIR = "配置/tuning"
    METRICS_FILE = "metrics.json"
    RECORDS_FILE = "records.json"
    PARAMETERS_FILE = "parameters.json"
    
    def __init__(
        self, 
        enabled: bool = False, 
        aggressiveness: AggressivenessLevel = AggressivenessLevel.BALANCED,
        tuning_dir: Optional[str] = None
    ):
        """初始化自动调参器
        
        Args:
            enabled: 是否启用自动调参
            aggressiveness: 调参激进程度
            tuning_dir: 调参数据存储目录，默认为 配置/tuning
        """
        self.enabled = enabled
        self.aggressiveness = aggressiveness
        self.tuning_dir = tuning_dir or self.DEFAULT_TUNING_DIR
        
        # 内存中的指标列表
        self._metrics: List[PerformanceMetric] = []
        # 调参记录列表
        self._records: List[TuningRecord] = []
        # 参数空间
        self._parameters: Dict[str, ParameterSpace] = get_default_parameter_spaces()
        
        # 确保存储目录存在
        self._ensure_dir_exists()
        # 加载持久化数据
        self._load_persisted_data()
    
    def _ensure_dir_exists(self) -> None:
        """确保存储目录存在"""
        if not os.path.exists(self.tuning_dir):
            os.makedirs(self.tuning_dir, exist_ok=True)
    
    def _get_metrics_path(self) -> str:
        """获取指标文件路径"""
        return os.path.join(self.tuning_dir, self.METRICS_FILE)
    
    def _get_records_path(self) -> str:
        """获取记录文件路径"""
        return os.path.join(self.tuning_dir, self.RECORDS_FILE)
    
    def _get_parameters_path(self) -> str:
        """获取参数文件路径"""
        return os.path.join(self.tuning_dir, self.PARAMETERS_FILE)
    
    def _load_persisted_data(self) -> None:
        """加载持久化的数据"""
        # 加载指标数据
        metrics_path = self._get_metrics_path()
        if os.path.exists(metrics_path):
            try:
                with open(metrics_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._metrics = [PerformanceMetric.from_dict(m) for m in data]
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.warning(f"加载指标数据失败: {e}")
                self._metrics = []
        
        # 加载调参记录
        records_path = self._get_records_path()
        if os.path.exists(records_path):
            try:
                with open(records_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._records = [TuningRecord.from_dict(r) for r in data]
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.warning(f"加载调参记录失败: {e}")
                self._records = []
        
        # 加载参数数据
        params_path = self._get_parameters_path()
        if os.path.exists(params_path):
            try:
                with open(params_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for name, param_data in data.items():
                        if name in self._parameters:
                            # 更新现有参数
                            self._parameters[name] = ParameterSpace.from_dict(param_data)
                        else:
                            # 添加新参数
                            self._parameters[name] = ParameterSpace.from_dict(param_data)
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.warning(f"加载参数数据失败: {e}")
    
    def _save_metrics(self) -> bool:
        """保存指标数据到文件
        
        Returns:
            是否保存成功
        """
        try:
            self._ensure_dir_exists()
            metrics_path = self._get_metrics_path()
            with open(metrics_path, 'w', encoding='utf-8') as f:
                data = [m.to_dict() for m in self._metrics]
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except (IOError, OSError) as e:
            logger.error(f"保存指标数据失败: {e}")
            return False
    
    def _save_records(self) -> bool:
        """保存调参记录到文件
        
        Returns:
            是否保存成功
        """
        try:
            self._ensure_dir_exists()
            records_path = self._get_records_path()
            with open(records_path, 'w', encoding='utf-8') as f:
                data = [r.to_dict() for r in self._records]
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except (IOError, OSError) as e:
            logger.error(f"保存调参记录失败: {e}")
            return False
    
    def _save_parameters(self) -> bool:
        """保存参数数据到文件
        
        Returns:
            是否保存成功
        """
        try:
            self._ensure_dir_exists()
            params_path = self._get_parameters_path()
            with open(params_path, 'w', encoding='utf-8') as f:
                data = {name: p.to_dict() for name, p in self._parameters.items()}
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except (IOError, OSError) as e:
            logger.error(f"保存参数数据失败: {e}")
            return False
    
    # ==================== 指标收集功能 ====================
    
    def collect_metric(self, metric: PerformanceMetric) -> None:
        """收集性能指标
        
        将指标添加到内存列表并持久化存储
        
        Args:
            metric: 性能指标对象
        """
        self._metrics.append(metric)
        # 立即持久化
        self._save_metrics()
    
    def get_metrics(self) -> List[PerformanceMetric]:
        """获取所有收集的指标
        
        Returns:
            指标列表
        """
        return self._metrics.copy()
    
    def get_metrics_in_window(self, window_minutes: int = 5) -> List[PerformanceMetric]:
        """获取指定时间窗口内的指标
        
        Args:
            window_minutes: 时间窗口大小（分钟）
            
        Returns:
            时间窗口内的指标列表
        """
        if window_minutes <= 0:
            return []
        
        cutoff_time = datetime.now() - timedelta(minutes=window_minutes)
        return [m for m in self._metrics if m.timestamp >= cutoff_time]
    
    def get_aggregated_metrics(self, window_minutes: int = 5) -> PerformanceMetric:
        """获取时间窗口内的汇总指标
        
        对时间窗口内的所有指标进行聚合：
        - action_success_rate: 平均值
        - state_accuracy: 平均值
        - stuck_count: 累加值
        - task_efficiency: 平均值
        
        Args:
            window_minutes: 时间窗口大小（分钟），默认5分钟
            
        Returns:
            汇总后的性能指标，如果窗口内无数据则返回默认值
        """
        metrics_in_window = self.get_metrics_in_window(window_minutes)
        
        if not metrics_in_window:
            # 无数据时返回默认指标
            return PerformanceMetric()
        
        # 计算平均值和累加值
        total_action_success = sum(m.action_success_rate for m in metrics_in_window)
        total_state_accuracy = sum(m.state_accuracy for m in metrics_in_window)
        total_stuck_count = sum(m.stuck_count for m in metrics_in_window)
        total_task_efficiency = sum(m.task_efficiency for m in metrics_in_window)
        
        count = len(metrics_in_window)
        
        return PerformanceMetric(
            timestamp=datetime.now(),
            action_success_rate=total_action_success / count,
            state_accuracy=total_state_accuracy / count,
            stuck_count=total_stuck_count,  # 累加值
            task_efficiency=total_task_efficiency / count
        )
    
    def clear_metrics(self) -> None:
        """清空所有指标数据"""
        self._metrics = []
        self._save_metrics()
    
    def get_metrics_count(self) -> int:
        """获取指标数量
        
        Returns:
            指标数量
        """
        return len(self._metrics)
    
    # ==================== 调参记录功能 ====================
    
    def add_record(self, record: TuningRecord) -> None:
        """添加调参记录
        
        Args:
            record: 调参记录对象
        """
        self._records.append(record)
        self._save_records()
    
    def get_records(self) -> List[TuningRecord]:
        """获取所有调参记录
        
        Returns:
            调参记录列表
        """
        return self._records.copy()
    
    def get_records_for_parameter(self, param_name: str) -> List[TuningRecord]:
        """获取指定参数的调参记录
        
        Args:
            param_name: 参数名称
            
        Returns:
            该参数的调参记录列表
        """
        return [r for r in self._records if r.parameter_name == param_name]
    
    # ==================== 参数管理功能 ====================
    
    def get_parameter(self, name: str) -> Optional[ParameterSpace]:
        """获取指定参数
        
        Args:
            name: 参数名称
            
        Returns:
            参数空间对象，不存在则返回None
        """
        return self._parameters.get(name)
    
    def get_all_parameters(self) -> Dict[str, ParameterSpace]:
        """获取所有参数
        
        Returns:
            参数名称 -> ParameterSpace 的字典
        """
        return self._parameters.copy()
    
    def set_parameter_value(self, name: str, value: float) -> bool:
        """设置参数值
        
        Args:
            name: 参数名称
            value: 新值
            
        Returns:
            是否设置成功
        """
        if name not in self._parameters:
            return False
        
        param = self._parameters[name]
        if param.locked:
            return False
        
        # 限制在范围内
        value = max(param.min_value, min(param.max_value, value))
        param.current_value = value
        self._save_parameters()
        return True
    
    # ==================== 参数锁定和重置功能 ====================
    
    def lock_parameter(self, param_name: str) -> None:
        """锁定参数，防止自动调参修改
        
        锁定后的参数在自动调参过程中将保持不变。
        
        Args:
            param_name: 要锁定的参数名称
            
        Raises:
            ValueError: 参数不存在
        """
        if param_name not in self._parameters:
            raise ValueError(f"参数不存在: {param_name}")
        
        self._parameters[param_name].locked = True
        self._save_parameters()
        logger.info(f"参数已锁定: {param_name}")
    
    def unlock_parameter(self, param_name: str) -> None:
        """解锁参数，允许自动调参修改
        
        解锁后的参数可以被自动调参过程修改。
        
        Args:
            param_name: 要解锁的参数名称
            
        Raises:
            ValueError: 参数不存在
        """
        if param_name not in self._parameters:
            raise ValueError(f"参数不存在: {param_name}")
        
        self._parameters[param_name].locked = False
        self._save_parameters()
        logger.info(f"参数已解锁: {param_name}")
    
    def is_parameter_locked(self, param_name: str) -> bool:
        """检查参数是否被锁定
        
        Args:
            param_name: 参数名称
            
        Returns:
            True: 参数已锁定
            False: 参数未锁定
            
        Raises:
            ValueError: 参数不存在
        """
        if param_name not in self._parameters:
            raise ValueError(f"参数不存在: {param_name}")
        
        return self._parameters[param_name].locked
    
    def reset_to_defaults(self) -> None:
        """重置所有参数为默认值
        
        将所有未锁定的参数重置为其默认值。
        锁定的参数不会被重置。
        """
        reset_count = 0
        skipped_count = 0
        
        for name, param in self._parameters.items():
            if param.locked:
                # 锁定的参数不重置
                skipped_count += 1
                logger.debug(f"参数 {name} 已锁定，跳过重置")
            else:
                param.current_value = param.default_value
                reset_count += 1
        
        self._save_parameters()
        logger.info(f"参数重置完成: 重置 {reset_count} 个参数，跳过 {skipped_count} 个锁定参数")
    
    def reset_parameter_to_default(self, param_name: str) -> bool:
        """重置单个参数为默认值
        
        Args:
            param_name: 参数名称
            
        Returns:
            是否重置成功（锁定的参数返回False）
            
        Raises:
            ValueError: 参数不存在
        """
        if param_name not in self._parameters:
            raise ValueError(f"参数不存在: {param_name}")
        
        param = self._parameters[param_name]
        
        if param.locked:
            logger.warning(f"参数 {param_name} 已锁定，无法重置")
            return False
        
        param.current_value = param.default_value
        self._save_parameters()
        logger.info(f"参数 {param_name} 已重置为默认值: {param.default_value}")
        return True
    
    def get_parameter_diff(self) -> Dict[str, Tuple[float, float]]:
        """获取当前参数与默认值的差异
        
        返回所有参数的当前值与默认值的差异对比。
        
        Returns:
            字典，键为参数名称，值为元组 (当前值, 默认值)
            只返回当前值与默认值不同的参数
        """
        diff = {}
        for name, param in self._parameters.items():
            if param.current_value != param.default_value:
                diff[name] = (param.current_value, param.default_value)
        return diff
    
    def get_all_parameter_diff(self) -> Dict[str, Tuple[float, float, float]]:
        """获取所有参数的详细差异信息
        
        返回所有参数的当前值、默认值和差值。
        
        Returns:
            字典，键为参数名称，值为元组 (当前值, 默认值, 差值)
        """
        diff = {}
        for name, param in self._parameters.items():
            diff[name] = (
                param.current_value, 
                param.default_value, 
                param.current_value - param.default_value
            )
        return diff
    
    def get_locked_parameters(self) -> List[str]:
        """获取所有被锁定的参数名称
        
        Returns:
            被锁定的参数名称列表
        """
        return [name for name, param in self._parameters.items() if param.locked]
    
    def get_unlocked_parameters(self) -> List[str]:
        """获取所有未锁定的参数名称
        
        Returns:
            未锁定的参数名称列表
        """
        return [name for name, param in self._parameters.items() if not param.locked]
    
    # ==================== 参数调整核心逻辑 ====================
    
    def is_performance_degraded(self, current: PerformanceMetric, baseline: PerformanceMetric) -> bool:
        """判断性能是否下降
        
        通过比较当前性能指标与基准性能指标的综合分数来判断。
        如果当前分数低于基准分数，则认为性能下降。
        
        Args:
            current: 当前性能指标
            baseline: 基准性能指标
            
        Returns:
            True: 性能下降
            False: 性能未下降（持平或提升）
        """
        current_score = current.get_overall_score()
        baseline_score = baseline.get_overall_score()
        return current_score < baseline_score
    
    def should_tune(self) -> bool:
        """判断是否应该进行调参
        
        满足以下条件时应该进行调参：
        1. 自动调参已启用
        2. 有足够的性能指标数据（至少5个）
        
        Returns:
            是否应该进行调参
        """
        if not self.enabled:
            return False
        
        # 需要至少5个指标数据才能进行调参
        if len(self._metrics) < 5:
            return False
        
        return True
    
    def _calculate_adjustment_delta(self, param: ParameterSpace, direction: int = 1) -> float:
        """计算参数调整量
        
        根据激进程度计算调整量：
        - 保守(CONSERVATIVE): 1个步长
        - 平衡(BALANCED): 2个步长
        - 激进(AGGRESSIVE): 3个步长
        
        Args:
            param: 参数空间对象
            direction: 调整方向，1为增加，-1为减少
            
        Returns:
            调整量（带符号）
        """
        step_multiplier = self.aggressiveness.get_step_multiplier()
        return direction * param.step * step_multiplier
    
    def _determine_adjustment_direction(self, param_name: str) -> int:
        """确定参数调整方向
        
        基于最近的调参记录和性能变化来确定调整方向：
        - 如果上次调整该参数后性能提升，继续同方向调整
        - 如果上次调整该参数后性能下降，反向调整
        - 如果没有历史记录，默认向上调整
        
        Args:
            param_name: 参数名称
            
        Returns:
            调整方向：1为增加，-1为减少
        """
        # 获取该参数的历史调参记录
        records = self.get_records_for_parameter(param_name)
        
        if not records:
            # 没有历史记录，默认向上调整
            return 1
        
        # 获取最近一次调参记录
        last_record = records[-1]
        
        # 判断上次调整的方向
        last_direction = 1 if last_record.new_value > last_record.old_value else -1
        
        # 判断上次调整是否带来改进
        if last_record.is_improvement is True:
            # 性能提升，继续同方向
            return last_direction
        elif last_record.is_improvement is False:
            # 性能下降，反向调整
            return -last_direction
        else:
            # 无法判断，默认向上调整
            return 1
    
    def tune_parameter(self, param_name: str) -> TuningRecord:
        """调整指定参数
        
        根据当前性能指标和激进程度，对指定参数进行渐进式调整。
        调整后会记录调参信息，包括调整前后的值和性能指标。
        
        调整策略：
        1. 获取当前性能指标作为基准
        2. 根据历史记录确定调整方向
        3. 根据激进程度计算调整量
        4. 在参数范围内进行调整
        5. 记录调参信息
        
        Args:
            param_name: 要调整的参数名称
            
        Returns:
            调参记录对象
            
        Raises:
            ValueError: 参数不存在或参数被锁定
        """
        # 检查参数是否存在
        if param_name not in self._parameters:
            raise ValueError(f"参数不存在: {param_name}")
        
        param = self._parameters[param_name]
        
        # 检查参数是否被锁定
        if param.locked:
            raise ValueError(f"参数已被锁定，无法调整: {param_name}")
        
        # 获取当前性能指标作为基准
        performance_before = self.get_aggregated_metrics(window_minutes=5)
        
        # 记录调整前的值
        old_value = param.current_value
        
        # 确定调整方向
        direction = self._determine_adjustment_direction(param_name)
        
        # 计算调整量
        delta = self._calculate_adjustment_delta(param, direction)
        
        # 执行调整（ParameterSpace.adjust 会自动限制在范围内）
        new_value = param.adjust(delta)
        
        # 如果调整后值没有变化（已达到边界），尝试反向调整
        if new_value == old_value:
            delta = self._calculate_adjustment_delta(param, -direction)
            new_value = param.adjust(delta)
        
        # 保存参数
        self._save_parameters()
        
        # 生成调整原因
        reason = self._generate_tuning_reason(param_name, old_value, new_value, direction)
        
        # 创建调参记录
        record = TuningRecord(
            timestamp=datetime.now(),
            parameter_name=param_name,
            old_value=old_value,
            new_value=new_value,
            reason=reason,
            performance_before=performance_before,
            performance_after=None  # 调整后的性能需要后续收集
        )
        
        # 保存记录
        self.add_record(record)
        
        # 记录日志
        logger.info(f"参数调整: {param_name} {old_value} -> {new_value}, 原因: {reason}")
        
        return record
    
    def _generate_tuning_reason(self, param_name: str, old_value: float, new_value: float, direction: int) -> str:
        """生成调参原因说明
        
        Args:
            param_name: 参数名称
            old_value: 调整前的值
            new_value: 调整后的值
            direction: 调整方向
            
        Returns:
            调参原因说明字符串
        """
        direction_str = "增加" if new_value > old_value else "减少"
        delta = abs(new_value - old_value)
        aggressiveness_str = {
            AggressivenessLevel.CONSERVATIVE: "保守",
            AggressivenessLevel.BALANCED: "平衡",
            AggressivenessLevel.AGGRESSIVE: "激进"
        }.get(self.aggressiveness, "未知")
        
        return f"自动调参({aggressiveness_str}模式): {direction_str} {delta:.4f}"
    
    def rollback(self, record: TuningRecord) -> bool:
        """回滚参数调整
        
        将参数恢复到调整前的值。
        
        Args:
            record: 要回滚的调参记录
            
        Returns:
            是否回滚成功
        """
        param_name = record.parameter_name
        
        if param_name not in self._parameters:
            logger.error(f"回滚失败: 参数不存在 {param_name}")
            return False
        
        param = self._parameters[param_name]
        
        if param.locked:
            logger.warning(f"回滚失败: 参数已锁定 {param_name}")
            return False
        
        # 恢复到调整前的值
        param.current_value = record.old_value
        self._save_parameters()
        
        logger.info(f"参数回滚: {param_name} {record.new_value} -> {record.old_value}")
        
        return True
    
    def update_record_performance_after(self, record: TuningRecord, performance_after: PerformanceMetric) -> None:
        """更新调参记录的调整后性能指标
        
        在收集到调整后的性能数据后，更新对应的调参记录。
        
        Args:
            record: 调参记录
            performance_after: 调整后的性能指标
        """
        record.performance_after = performance_after
        self._save_records()
    
    def auto_tune_cycle(self) -> Optional[TuningRecord]:
        """执行一次自动调参循环
        
        自动选择一个参数进行调整，并在后续检查性能变化。
        如果性能下降，自动回滚。
        
        Returns:
            调参记录，如果未进行调参则返回None
        """
        if not self.should_tune():
            return None
        
        # 选择一个未锁定的参数进行调整
        unlocked_params = [
            name for name, param in self._parameters.items() 
            if not param.locked
        ]
        
        if not unlocked_params:
            logger.info("所有参数都已锁定，跳过自动调参")
            return None
        
        # 选择最近调整次数最少的参数
        param_tune_counts = {
            name: len(self.get_records_for_parameter(name)) 
            for name in unlocked_params
        }
        param_name = min(param_tune_counts, key=param_tune_counts.get)
        
        # 执行调参
        try:
            record = self.tune_parameter(param_name)
            return record
        except ValueError as e:
            logger.error(f"自动调参失败: {e}")
            return None
    
    def evaluate_and_rollback_if_needed(self, record: TuningRecord) -> bool:
        """评估调参效果，如果性能下降则回滚
        
        Args:
            record: 要评估的调参记录
            
        Returns:
            True: 保留调整（性能未下降）
            False: 已回滚（性能下降）
        """
        if record.performance_before is None:
            logger.warning("无法评估: 缺少调整前的性能数据")
            return True
        
        # 获取当前性能指标
        current_performance = self.get_aggregated_metrics(window_minutes=5)
        
        # 更新记录中的调整后性能
        self.update_record_performance_after(record, current_performance)
        
        # 判断性能是否下降
        if self.is_performance_degraded(current_performance, record.performance_before):
            # 性能下降，回滚
            logger.info(f"性能下降，回滚参数 {record.parameter_name}")
            self.rollback(record)
            return False
        else:
            # 性能未下降，保留调整
            logger.info(f"性能未下降，保留参数调整 {record.parameter_name}")
            return True
