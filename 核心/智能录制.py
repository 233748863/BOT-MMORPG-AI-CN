"""
智能录制模块
定义录制片段、游戏事件、录制统计等数据结构
以及价值评估器和数据过滤器接口
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import time
import uuid


# ==================== 枚举类型 ====================
class 事件类型(Enum):
    """游戏事件类型"""
    击杀 = "kill"
    任务完成 = "quest_complete"
    拾取 = "pickup"
    技能连招 = "combo"
    空闲 = "idle"
    重复 = "repeat"
    卡住 = "stuck"
    加载 = "loading"
    菜单 = "menu"
    普通 = "normal"


class 价值等级(Enum):
    """片段价值等级"""
    高 = "high"
    中 = "medium"
    低 = "low"


# ==================== 游戏事件数据类 ====================
@dataclass
class GameEvent:
    """游戏事件数据结构"""
    event_type: str  # 事件类型
    timestamp: float  # 发生时间
    confidence: float  # 置信度 (0.0 - 1.0)
    data: Dict[str, Any] = field(default_factory=dict)  # 附加数据

    def __post_init__(self):
        """验证数据有效性"""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"置信度必须在0-1范围内，当前值: {self.confidence}")
        if self.timestamp < 0:
            raise ValueError(f"时间戳不能为负数，当前值: {self.timestamp}")



# ==================== 录制片段数据类 ====================
@dataclass
class RecordingSegment:
    """录制片段数据结构"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))  # 片段唯一标识
    start_time: float = 0.0  # 开始时间戳
    end_time: float = 0.0  # 结束时间戳
    frames: List[Any] = field(default_factory=list)  # 画面帧列表 (np.ndarray)
    actions: List[int] = field(default_factory=list)  # 动作序列
    events: List[GameEvent] = field(default_factory=list)  # 检测到的游戏事件
    _value_score: float = field(default=50.0, repr=False)  # 内部价值评分存储
    value_level: str = "medium"  # 价值等级: "high", "medium", "low"
    tags: List[str] = field(default_factory=list)  # 标签列表

    @property
    def value_score(self) -> float:
        """获取价值评分"""
        return self._value_score

    @value_score.setter
    def value_score(self, value: float) -> None:
        """设置价值评分，确保在0-100范围内"""
        if not 0.0 <= value <= 100.0:
            raise ValueError(f"价值评分必须在0-100范围内，当前值: {value}")
        self._value_score = value
        # 自动更新价值等级
        if value >= 70:
            self.value_level = "high"
        elif value >= 40:
            self.value_level = "medium"
        else:
            self.value_level = "low"

    def __post_init__(self):
        """验证数据有效性"""
        # 验证初始value_score
        if not 0.0 <= self._value_score <= 100.0:
            raise ValueError(f"价值评分必须在0-100范围内，当前值: {self._value_score}")
        # 验证时间戳
        if self.start_time < 0:
            raise ValueError(f"开始时间不能为负数，当前值: {self.start_time}")
        if self.end_time < 0:
            raise ValueError(f"结束时间不能为负数，当前值: {self.end_time}")
        # 验证价值等级
        if self.value_level not in ("high", "medium", "low"):
            raise ValueError(f"价值等级必须是 'high', 'medium' 或 'low'，当前值: {self.value_level}")

    @property
    def duration(self) -> float:
        """获取片段时长（秒）"""
        return self.end_time - self.start_time

    def add_event(self, event: GameEvent) -> None:
        """添加游戏事件"""
        self.events.append(event)

    def add_tag(self, tag: str) -> None:
        """添加标签（避免重复）"""
        if tag not in self.tags:
            self.tags.append(tag)



# ==================== 录制统计数据类 ====================
@dataclass
class RecordingStatistics:
    """录制统计数据结构"""
    total_segments: int = 0  # 总片段数
    high_value_count: int = 0  # 高价值片段数
    medium_value_count: int = 0  # 中等价值片段数
    low_value_count: int = 0  # 低价值片段数
    action_distribution: Dict[int, int] = field(default_factory=dict)  # 动作ID -> 样本数量
    total_duration: float = 0.0  # 总时长（秒）
    average_value_score: float = 0.0  # 平均价值评分

    def __post_init__(self):
        """验证数据有效性"""
        if self.total_segments < 0:
            raise ValueError(f"总片段数不能为负数，当前值: {self.total_segments}")
        if self.high_value_count < 0:
            raise ValueError(f"高价值片段数不能为负数，当前值: {self.high_value_count}")
        if self.medium_value_count < 0:
            raise ValueError(f"中等价值片段数不能为负数，当前值: {self.medium_value_count}")
        if self.low_value_count < 0:
            raise ValueError(f"低价值片段数不能为负数，当前值: {self.low_value_count}")
        if self.total_duration < 0:
            raise ValueError(f"总时长不能为负数，当前值: {self.total_duration}")
        if not 0.0 <= self.average_value_score <= 100.0:
            # 允许初始值为0
            if self.average_value_score != 0.0:
                raise ValueError(f"平均价值评分必须在0-100范围内，当前值: {self.average_value_score}")

    def update_from_segments(self, segments: List[RecordingSegment]) -> None:
        """从片段列表更新统计数据"""
        self.total_segments = len(segments)
        self.high_value_count = 0
        self.medium_value_count = 0
        self.low_value_count = 0
        self.action_distribution = {}
        self.total_duration = 0.0
        total_score = 0.0

        for segment in segments:
            # 统计价值等级
            if segment.value_level == "high":
                self.high_value_count += 1
            elif segment.value_level == "medium":
                self.medium_value_count += 1
            else:
                self.low_value_count += 1

            # 统计动作分布
            for action in segment.actions:
                self.action_distribution[action] = self.action_distribution.get(action, 0) + 1

            # 累计时长和评分
            self.total_duration += segment.duration
            total_score += segment.value_score

        # 计算平均评分
        if self.total_segments > 0:
            self.average_value_score = total_score / self.total_segments
        else:
            self.average_value_score = 0.0

    def get_action_suggestions(self, min_samples: int = 100) -> List[Tuple[int, int]]:
        """获取需要更多样本的动作建议
        
        Args:
            min_samples: 最小样本数阈值
            
        Returns:
            需要更多样本的动作列表，格式为 [(动作ID, 当前样本数), ...]
        """
        suggestions = []
        for action_id, count in self.action_distribution.items():
            if count < min_samples:
                suggestions.append((action_id, count))
        # 按样本数升序排序
        suggestions.sort(key=lambda x: x[1])
        return suggestions

    def get_quality_score(self) -> float:
        """计算数据质量评分
        
        基于高价值片段比例、动作分布均衡度等因素计算综合质量评分。
        
        Returns:
            质量评分 (0-100)
        """
        if self.total_segments == 0:
            return 0.0
        
        # 因素1: 高价值片段比例 (权重40%)
        high_value_ratio = self.high_value_count / self.total_segments
        high_value_score = high_value_ratio * 100 * 0.4
        
        # 因素2: 平均价值评分 (权重30%)
        avg_score_component = self.average_value_score * 0.3
        
        # 因素3: 动作分布均衡度 (权重30%)
        # 使用变异系数的倒数来衡量均衡度
        if self.action_distribution:
            counts = list(self.action_distribution.values())
            if len(counts) > 1:
                mean_count = sum(counts) / len(counts)
                if mean_count > 0:
                    variance = sum((c - mean_count) ** 2 for c in counts) / len(counts)
                    std_dev = variance ** 0.5
                    cv = std_dev / mean_count  # 变异系数
                    # 变异系数越小，分布越均衡，得分越高
                    balance_score = max(0, (1 - cv)) * 100 * 0.3
                else:
                    balance_score = 0
            else:
                # 只有一种动作，均衡度为0
                balance_score = 0
        else:
            balance_score = 0
        
        total_score = high_value_score + avg_score_component + balance_score
        return min(100.0, max(0.0, total_score))

    def get_value_distribution_ratio(self) -> Dict[str, float]:
        """获取价值等级分布比例
        
        Returns:
            字典，包含各价值等级的比例
        """
        if self.total_segments == 0:
            return {"high": 0.0, "medium": 0.0, "low": 0.0}
        
        return {
            "high": self.high_value_count / self.total_segments,
            "medium": self.medium_value_count / self.total_segments,
            "low": self.low_value_count / self.total_segments
        }


# ==================== 统计服务 ====================
class StatisticsService:
    """录制统计服务
    
    提供录制数据的统计分析和质量报告生成功能。
    
    需求: 3.2, 3.3, 3.4, 3.5
    """
    
    def __init__(self):
        """初始化统计服务"""
        self._current_statistics = RecordingStatistics()
        self._segments: List[RecordingSegment] = []
    
    def add_segment(self, segment: RecordingSegment) -> None:
        """添加录制片段并更新统计
        
        Args:
            segment: 录制片段
        """
        self._segments.append(segment)
        self._current_statistics.update_from_segments(self._segments)
    
    def add_segments(self, segments: List[RecordingSegment]) -> None:
        """批量添加录制片段并更新统计
        
        Args:
            segments: 录制片段列表
        """
        self._segments.extend(segments)
        self._current_statistics.update_from_segments(self._segments)
    
    def get_statistics(self) -> RecordingStatistics:
        """获取当前统计数据
        
        Returns:
            录制统计对象
        """
        return self._current_statistics
    
    def get_value_counts(self) -> Dict[str, int]:
        """获取高/中/低价值片段计数
        
        需求: 3.2 - 显示本次录制的高/中/低价值片段数量统计
        
        Returns:
            字典，包含各价值等级的片段数量
        """
        return {
            "high": self._current_statistics.high_value_count,
            "medium": self._current_statistics.medium_value_count,
            "low": self._current_statistics.low_value_count,
            "total": self._current_statistics.total_segments
        }
    
    def get_action_distribution(self) -> Dict[int, int]:
        """获取动作分布统计
        
        需求: 3.3 - 显示各动作类别的样本分布情况
        
        Returns:
            字典，动作ID -> 样本数量
        """
        return self._current_statistics.action_distribution.copy()
    
    def generate_quality_report(self, min_samples_threshold: int = 100) -> Dict[str, Any]:
        """生成数据质量报告
        
        需求: 3.4 - WHEN 录制结束 THEN THE Smart_Recorder SHALL 生成数据质量报告
        需求: 3.5 - 提供建议：哪些动作类别需要更多样本
        
        Args:
            min_samples_threshold: 最小样本数阈值，用于生成建议
            
        Returns:
            数据质量报告字典，包含：
            - summary: 摘要信息
            - value_distribution: 价值分布
            - action_distribution: 动作分布
            - quality_score: 质量评分
            - suggestions: 改进建议
        """
        stats = self._current_statistics
        
        # 摘要信息
        summary = {
            "total_segments": stats.total_segments,
            "total_duration": stats.total_duration,
            "total_duration_formatted": self._format_duration(stats.total_duration),
            "average_value_score": round(stats.average_value_score, 2),
            "average_segment_duration": round(
                stats.total_duration / stats.total_segments, 2
            ) if stats.total_segments > 0 else 0.0
        }
        
        # 价值分布
        value_distribution = {
            "counts": {
                "high": stats.high_value_count,
                "medium": stats.medium_value_count,
                "low": stats.low_value_count
            },
            "ratios": stats.get_value_distribution_ratio()
        }
        
        # 动作分布
        action_distribution = {
            "distribution": stats.action_distribution.copy(),
            "total_actions": sum(stats.action_distribution.values()),
            "unique_actions": len(stats.action_distribution)
        }
        
        # 质量评分
        quality_score = stats.get_quality_score()
        
        # 改进建议
        suggestions = self._generate_suggestions(min_samples_threshold)
        
        return {
            "summary": summary,
            "value_distribution": value_distribution,
            "action_distribution": action_distribution,
            "quality_score": round(quality_score, 2),
            "quality_level": self._get_quality_level(quality_score),
            "suggestions": suggestions,
            "generated_at": time.time()
        }
    
    def _generate_suggestions(self, min_samples_threshold: int) -> List[Dict[str, Any]]:
        """生成改进建议
        
        需求: 3.5 - 提供建议：哪些动作类别需要更多样本
        
        Args:
            min_samples_threshold: 最小样本数阈值
            
        Returns:
            建议列表
        """
        suggestions = []
        stats = self._current_statistics
        
        # 建议1: 样本不足的动作
        low_sample_actions = stats.get_action_suggestions(min_samples_threshold)
        if low_sample_actions:
            for action_id, count in low_sample_actions:
                suggestions.append({
                    "type": "low_samples",
                    "priority": "high" if count < min_samples_threshold // 2 else "medium",
                    "message": f"动作 {action_id} 样本不足，当前 {count} 个，建议至少 {min_samples_threshold} 个",
                    "action_id": action_id,
                    "current_count": count,
                    "target_count": min_samples_threshold
                })
        
        # 建议2: 高价值片段比例过低
        if stats.total_segments > 0:
            high_ratio = stats.high_value_count / stats.total_segments
            if high_ratio < 0.2:  # 高价值片段少于20%
                suggestions.append({
                    "type": "low_high_value",
                    "priority": "high",
                    "message": f"高价值片段比例过低 ({high_ratio:.1%})，建议录制更多有效操作（击杀、任务、技能连招）",
                    "current_ratio": high_ratio,
                    "target_ratio": 0.2
                })
        
        # 建议3: 低价值片段比例过高
        if stats.total_segments > 0:
            low_ratio = stats.low_value_count / stats.total_segments
            if low_ratio > 0.5:  # 低价值片段超过50%
                suggestions.append({
                    "type": "high_low_value",
                    "priority": "medium",
                    "message": f"低价值片段比例过高 ({low_ratio:.1%})，建议启用自动过滤功能",
                    "current_ratio": low_ratio,
                    "target_ratio": 0.5
                })
        
        # 建议4: 动作分布不均衡
        if stats.action_distribution:
            counts = list(stats.action_distribution.values())
            if len(counts) > 1:
                max_count = max(counts)
                min_count = min(counts)
                if max_count > min_count * 10:  # 最大最小差距超过10倍
                    suggestions.append({
                        "type": "unbalanced_actions",
                        "priority": "low",
                        "message": "动作分布不均衡，某些动作样本过多或过少，可能影响模型训练效果",
                        "max_count": max_count,
                        "min_count": min_count
                    })
        
        # 建议5: 总样本数不足
        if stats.total_segments < 50:
            suggestions.append({
                "type": "insufficient_data",
                "priority": "high",
                "message": f"总片段数不足 ({stats.total_segments})，建议至少录制50个片段",
                "current_count": stats.total_segments,
                "target_count": 50
            })
        
        # 按优先级排序
        priority_order = {"high": 0, "medium": 1, "low": 2}
        suggestions.sort(key=lambda x: priority_order.get(x["priority"], 3))
        
        return suggestions
    
    def _format_duration(self, seconds: float) -> str:
        """格式化时长为可读字符串
        
        Args:
            seconds: 秒数
            
        Returns:
            格式化的时长字符串，如 "1小时23分45秒"
        """
        if seconds < 60:
            return f"{seconds:.1f}秒"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = seconds % 60
            return f"{minutes}分{secs:.0f}秒"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = seconds % 60
            return f"{hours}小时{minutes}分{secs:.0f}秒"
    
    def _get_quality_level(self, score: float) -> str:
        """根据质量评分获取质量等级
        
        Args:
            score: 质量评分 (0-100)
            
        Returns:
            质量等级: "excellent", "good", "fair", "poor"
        """
        if score >= 80:
            return "excellent"
        elif score >= 60:
            return "good"
        elif score >= 40:
            return "fair"
        else:
            return "poor"
    
    def reset(self) -> None:
        """重置统计数据"""
        self._segments.clear()
        self._current_statistics = RecordingStatistics()
    
    def get_current_value_score(self) -> float:
        """获取当前（最新片段）的价值评分
        
        需求: 3.1 - 实时显示当前片段的Value_Score
        
        Returns:
            最新片段的价值评分，如果没有片段则返回0
        """
        if self._segments:
            return self._segments[-1].value_score
        return 0.0
    
    def format_report_as_text(self, report: Dict[str, Any]) -> str:
        """将质量报告格式化为文本
        
        Args:
            report: 质量报告字典
            
        Returns:
            格式化的文本报告
        """
        lines = []
        lines.append("=" * 50)
        lines.append("数据质量报告")
        lines.append("=" * 50)
        
        # 摘要
        summary = report["summary"]
        lines.append("\n【摘要】")
        lines.append(f"  总片段数: {summary['total_segments']}")
        lines.append(f"  总时长: {summary['total_duration_formatted']}")
        lines.append(f"  平均价值评分: {summary['average_value_score']}")
        lines.append(f"  平均片段时长: {summary['average_segment_duration']}秒")
        
        # 价值分布
        value_dist = report["value_distribution"]
        lines.append("\n【价值分布】")
        lines.append(f"  高价值: {value_dist['counts']['high']} ({value_dist['ratios']['high']:.1%})")
        lines.append(f"  中价值: {value_dist['counts']['medium']} ({value_dist['ratios']['medium']:.1%})")
        lines.append(f"  低价值: {value_dist['counts']['low']} ({value_dist['ratios']['low']:.1%})")
        
        # 动作分布
        action_dist = report["action_distribution"]
        lines.append("\n【动作分布】")
        lines.append(f"  总动作数: {action_dist['total_actions']}")
        lines.append(f"  动作类型数: {action_dist['unique_actions']}")
        if action_dist['distribution']:
            lines.append("  各动作样本数:")
            for action_id, count in sorted(action_dist['distribution'].items()):
                lines.append(f"    动作{action_id}: {count}")
        
        # 质量评分
        lines.append("\n【质量评估】")
        lines.append(f"  质量评分: {report['quality_score']}/100")
        quality_level_map = {
            "excellent": "优秀",
            "good": "良好",
            "fair": "一般",
            "poor": "较差"
        }
        lines.append(f"  质量等级: {quality_level_map.get(report['quality_level'], report['quality_level'])}")
        
        # 改进建议
        if report["suggestions"]:
            lines.append("\n【改进建议】")
            for i, suggestion in enumerate(report["suggestions"], 1):
                priority_map = {"high": "高", "medium": "中", "low": "低"}
                priority = priority_map.get(suggestion["priority"], suggestion["priority"])
                lines.append(f"  {i}. [{priority}优先级] {suggestion['message']}")
        else:
            lines.append("\n【改进建议】")
            lines.append("  数据质量良好，暂无改进建议")
        
        lines.append("\n" + "=" * 50)
        
        return "\n".join(lines)


# ==================== 价值评估器 ====================
class ValueEvaluator:
    """价值评估器
    
    负责评估录制片段的价值，根据游戏事件类型分类并计算价值评分。
    
    事件类型与价值等级映射规则（需求 1.2, 1.3, 1.4, 1.5）：
    - 击杀(kill)、任务完成(quest_complete)、技能连招(combo) -> 高价值
    - 拾取(pickup) -> 中等价值
    - 空闲(idle)、重复(repeat)、卡住(stuck)、加载(loading) -> 低价值
    - 普通(normal)、菜单(menu) -> 基础价值
    """
    
    # 事件类型到价值等级的映射
    EVENT_VALUE_MAPPING: Dict[str, Tuple[str, float]] = {
        # 高价值事件 (value_level="high", 分数增量)
        事件类型.击杀.value: ("high", 25.0),
        事件类型.任务完成.value: ("high", 30.0),
        事件类型.技能连招.value: ("high", 20.0),
        # 中等价值事件 (value_level="medium", 分数增量)
        事件类型.拾取.value: ("medium", 10.0),
        # 低价值事件 (value_level="low", 分数减量)
        事件类型.空闲.value: ("low", -15.0),
        事件类型.重复.value: ("low", -10.0),
        事件类型.卡住.value: ("low", -20.0),
        事件类型.加载.value: ("low", -25.0),
        # 基础价值事件
        事件类型.菜单.value: ("low", -5.0),
        事件类型.普通.value: ("medium", 0.0),
    }
    
    # 基础评分（无事件时的默认分数）
    BASE_SCORE: float = 50.0
    
    def __init__(self):
        """初始化价值评估器"""
        pass
    
    def classify_event(self, event: GameEvent) -> Tuple[str, float]:
        """分类事件并返回价值等级和分数增量
        
        根据事件类型确定其价值等级和对应的分数增量。
        
        Args:
            event: 游戏事件对象
            
        Returns:
            元组 (价值等级, 分数增量)
            - 价值等级: "high", "medium", "low"
            - 分数增量: 正数表示增加价值，负数表示降低价值
            
        需求: 1.2, 1.3, 1.4, 1.5
        """
        event_type = event.event_type
        
        # 查找事件类型对应的价值映射
        if event_type in self.EVENT_VALUE_MAPPING:
            value_level, score_delta = self.EVENT_VALUE_MAPPING[event_type]
            # 根据事件置信度调整分数增量
            adjusted_delta = score_delta * event.confidence
            return (value_level, adjusted_delta)
        
        # 未知事件类型，返回默认中等价值
        return ("medium", 0.0)
    
    def evaluate_segment(self, segment: RecordingSegment) -> float:
        """评估片段价值，返回0-100分
        
        根据片段中的所有事件计算综合价值评分。
        
        评分规则：
        1. 从基础分数(50分)开始
        2. 遍历所有事件，累加分数增量
        3. 确保最终分数在0-100范围内
        4. 更新片段的value_score和value_level
        
        Args:
            segment: 录制片段对象
            
        Returns:
            价值评分 (0-100)
            
        需求: 1.2, 1.3, 1.4, 1.5, 1.6
        """
        # 从基础分数开始
        score = self.BASE_SCORE
        
        # 记录检测到的最高价值等级
        highest_level = "low"
        level_priority = {"low": 0, "medium": 1, "high": 2}
        
        # 遍历所有事件，累加分数
        for event in segment.events:
            value_level, score_delta = self.classify_event(event)
            score += score_delta
            
            # 更新最高价值等级
            if level_priority.get(value_level, 0) > level_priority.get(highest_level, 0):
                highest_level = value_level
            
            # 根据事件类型添加标签
            if event.event_type not in [tag for tag in segment.tags]:
                segment.add_tag(event.event_type)
        
        # 确保分数在0-100范围内
        score = max(0.0, min(100.0, score))
        
        # 更新片段的价值评分（这会自动更新value_level）
        segment.value_score = score
        
        return score
    
    def get_value_level_from_score(self, score: float) -> str:
        """根据分数获取价值等级
        
        Args:
            score: 价值评分 (0-100)
            
        Returns:
            价值等级: "high", "medium", "low"
        """
        if score >= 70:
            return "high"
        elif score >= 40:
            return "medium"
        else:
            return "low"
    
    def get_dominant_value_level(self, segment: RecordingSegment) -> str:
        """获取片段中主导的价值等级
        
        根据事件类型确定片段的主导价值等级。
        如果存在高价值事件（击杀、任务完成、技能连招），则为高价值。
        如果存在中等价值事件（拾取），则为中等价值。
        否则为低价值。
        
        Args:
            segment: 录制片段对象
            
        Returns:
            主导价值等级: "high", "medium", "low"
        """
        has_high = False
        has_medium = False
        
        high_value_types = {
            事件类型.击杀.value,
            事件类型.任务完成.value,
            事件类型.技能连招.value
        }
        medium_value_types = {
            事件类型.拾取.value
        }
        
        for event in segment.events:
            if event.event_type in high_value_types:
                has_high = True
                break  # 找到高价值事件，直接返回
            elif event.event_type in medium_value_types:
                has_medium = True
        
        if has_high:
            return "high"
        elif has_medium:
            return "medium"
        else:
            return "low"


# ==================== 数据过滤器 ====================
class DataFilter:
    """数据过滤器
    
    负责检测和过滤无效的训练数据，包括：
    - 空闲状态检测（连续无操作）
    - 重复操作检测
    - 卡住状态检测
    - 加载画面检测
    
    需求: 2.1, 2.2, 2.3, 2.4
    """
    
    # 默认阈值配置
    DEFAULT_IDLE_THRESHOLD: float = 5.0  # 空闲检测阈值（秒）
    DEFAULT_REPETITIVE_THRESHOLD: int = 10  # 重复操作检测阈值（次数）
    DEFAULT_STUCK_THRESHOLD: float = 3.0  # 卡住检测阈值（秒）
    DEFAULT_FRAME_SIMILARITY_THRESHOLD: float = 0.95  # 帧相似度阈值
    
    # 无操作动作ID（表示没有按键）
    NO_ACTION_ID: int = 0
    
    def __init__(
        self,
        idle_threshold: float = DEFAULT_IDLE_THRESHOLD,
        repetitive_threshold: int = DEFAULT_REPETITIVE_THRESHOLD,
        stuck_threshold: float = DEFAULT_STUCK_THRESHOLD,
        frame_similarity_threshold: float = DEFAULT_FRAME_SIMILARITY_THRESHOLD
    ):
        """初始化数据过滤器
        
        Args:
            idle_threshold: 空闲检测阈值（秒），默认5秒
            repetitive_threshold: 重复操作检测阈值（次数），默认10次
            stuck_threshold: 卡住检测阈值（秒），默认3秒
            frame_similarity_threshold: 帧相似度阈值，默认0.95
        """
        self.idle_threshold = idle_threshold
        self.repetitive_threshold = repetitive_threshold
        self.stuck_threshold = stuck_threshold
        self.frame_similarity_threshold = frame_similarity_threshold
    
    def is_idle(self, actions: List[int], duration: float) -> bool:
        """检测是否为空闲状态（连续无操作）
        
        当连续无操作时间超过阈值（默认5秒）时，判定为空闲状态。
        
        Args:
            actions: 动作序列列表
            duration: 片段时长（秒）
            
        Returns:
            True 如果检测到空闲状态，否则 False
            
        需求: 2.1 - WHEN 检测到连续5秒无操作 THEN THE Smart_Recorder SHALL 标记该片段为低价值
        """
        if duration < self.idle_threshold:
            # 时长不足阈值，不可能是空闲
            return False
        
        if not actions:
            # 没有动作记录，视为空闲
            return duration >= self.idle_threshold
        
        # 计算无操作动作的比例
        # 假设动作序列是按时间均匀采样的
        no_action_count = sum(1 for action in actions if action == self.NO_ACTION_ID)
        
        if len(actions) == 0:
            return duration >= self.idle_threshold
        
        # 计算无操作的时间比例
        no_action_ratio = no_action_count / len(actions)
        estimated_idle_duration = duration * no_action_ratio
        
        # 检查是否有连续的无操作序列
        max_consecutive_idle = self._get_max_consecutive_count(actions, self.NO_ACTION_ID)
        
        # 如果有连续的无操作，估算其时长
        if len(actions) > 0:
            time_per_action = duration / len(actions)
            consecutive_idle_duration = max_consecutive_idle * time_per_action
            
            if consecutive_idle_duration >= self.idle_threshold:
                return True
        
        return False
    
    def is_repetitive(self, actions: List[int], threshold: int = None) -> bool:
        """检测是否为重复操作
        
        当相同动作连续出现超过阈值（默认10次）时，判定为重复操作。
        
        Args:
            actions: 动作序列列表
            threshold: 重复次数阈值，默认使用实例配置值
            
        Returns:
            True 如果检测到重复操作，否则 False
            
        需求: 2.2 - WHEN 检测到重复相同操作超过10次 THEN THE Smart_Recorder SHALL 标记为重复数据
        """
        if threshold is None:
            threshold = self.repetitive_threshold
        
        if not actions or len(actions) < threshold:
            return False
        
        # 检查是否有连续重复的动作
        current_action = actions[0]
        consecutive_count = 1
        
        for i in range(1, len(actions)):
            if actions[i] == current_action:
                consecutive_count += 1
                if consecutive_count > threshold:
                    return True
            else:
                current_action = actions[i]
                consecutive_count = 1
        
        return False
    
    def is_stuck(self, frames: List[Any], duration: float) -> bool:
        """检测角色是否卡住
        
        当画面几乎没有变化超过阈值（默认3秒）时，判定为卡住状态。
        通过比较连续帧的相似度来检测。
        
        Args:
            frames: 画面帧列表 (np.ndarray)
            duration: 片段时长（秒）
            
        Returns:
            True 如果检测到卡住状态，否则 False
            
        需求: 2.3 - WHEN 检测到角色卡住不动超过3秒 THEN THE Smart_Recorder SHALL 标记为异常数据
        """
        if duration < self.stuck_threshold:
            # 时长不足阈值，不可能是卡住
            return False
        
        if not frames or len(frames) < 2:
            # 帧数不足，无法判断
            return False
        
        # 计算每帧对应的时间
        time_per_frame = duration / len(frames)
        
        # 需要连续相似的帧数
        required_similar_frames = int(self.stuck_threshold / time_per_frame)
        
        if required_similar_frames < 2:
            required_similar_frames = 2
        
        # 检测连续相似帧
        consecutive_similar = 1
        
        for i in range(1, len(frames)):
            if self._frames_are_similar(frames[i-1], frames[i]):
                consecutive_similar += 1
                if consecutive_similar >= required_similar_frames:
                    return True
            else:
                consecutive_similar = 1
        
        return False
    
    def is_loading(self, frame: Any) -> bool:
        """检测是否为加载画面
        
        通过分析画面特征判断是否为游戏加载画面。
        加载画面通常具有以下特征：
        - 画面颜色单一（大面积纯色）
        - 可能有加载进度条
        - 画面变化很小
        
        Args:
            frame: 单帧画面 (np.ndarray)
            
        Returns:
            True 如果检测到加载画面，否则 False
            
        需求: 2.4 - WHEN 检测到游戏加载画面 THEN THE Smart_Recorder SHALL 暂停录制直到加载完成
        """
        if frame is None:
            return False
        
        try:
            # 尝试导入numpy进行图像分析
            import numpy as np
            
            if not isinstance(frame, np.ndarray):
                return False
            
            # 检查画面是否为空或无效
            if frame.size == 0:
                return False
            
            # 计算画面的颜色方差
            # 加载画面通常颜色单一，方差较小
            if len(frame.shape) == 3:
                # 彩色图像
                variance = np.var(frame)
            else:
                # 灰度图像
                variance = np.var(frame)
            
            # 如果方差很小，可能是加载画面（纯色或接近纯色）
            # 阈值可以根据实际情况调整
            LOADING_VARIANCE_THRESHOLD = 100.0
            
            if variance < LOADING_VARIANCE_THRESHOLD:
                return True
            
            # 检查是否大部分像素颜色相同（黑屏或纯色背景）
            if len(frame.shape) == 3:
                # 计算每个像素的平均颜色
                mean_color = np.mean(frame, axis=(0, 1))
                # 计算与平均颜色的差异
                diff = np.abs(frame.astype(float) - mean_color)
                similar_ratio = np.mean(diff < 30)  # 差异小于30的像素比例
            else:
                mean_val = np.mean(frame)
                diff = np.abs(frame.astype(float) - mean_val)
                similar_ratio = np.mean(diff < 30)
            
            # 如果超过80%的像素颜色相似，可能是加载画面
            if similar_ratio > 0.8:
                return True
            
            return False
            
        except ImportError:
            # 如果没有numpy，返回False
            return False
        except Exception:
            # 其他异常，返回False
            return False
    
    def _frames_are_similar(self, frame1: Any, frame2: Any) -> bool:
        """比较两帧是否相似
        
        Args:
            frame1: 第一帧
            frame2: 第二帧
            
        Returns:
            True 如果两帧相似，否则 False
        """
        if frame1 is None or frame2 is None:
            return False
        
        try:
            import numpy as np
            
            if not isinstance(frame1, np.ndarray) or not isinstance(frame2, np.ndarray):
                return False
            
            if frame1.shape != frame2.shape:
                return False
            
            # 计算两帧的差异
            diff = np.abs(frame1.astype(float) - frame2.astype(float))
            
            # 计算相似度（差异小的像素比例）
            similar_pixels = np.mean(diff < 10)  # 差异小于10的像素
            
            return similar_pixels >= self.frame_similarity_threshold
            
        except ImportError:
            return False
        except Exception:
            return False
    
    def _get_max_consecutive_count(self, items: List[Any], target: Any) -> int:
        """获取列表中目标元素的最大连续出现次数
        
        Args:
            items: 元素列表
            target: 目标元素
            
        Returns:
            最大连续出现次数
        """
        if not items:
            return 0
        
        max_count = 0
        current_count = 0
        
        for item in items:
            if item == target:
                current_count += 1
                max_count = max(max_count, current_count)
            else:
                current_count = 0
        
        return max_count
    
    def filter_segment(self, segment: RecordingSegment) -> Tuple[bool, List[str]]:
        """综合过滤片段，返回是否应该过滤及原因
        
        Args:
            segment: 录制片段
            
        Returns:
            元组 (是否应过滤, 过滤原因列表)
        """
        reasons = []
        
        # 检测空闲
        if self.is_idle(segment.actions, segment.duration):
            reasons.append("idle")
        
        # 检测重复
        if self.is_repetitive(segment.actions):
            reasons.append("repetitive")
        
        # 检测卡住
        if self.is_stuck(segment.frames, segment.duration):
            reasons.append("stuck")
        
        # 检测加载画面（检查最后一帧）
        if segment.frames and self.is_loading(segment.frames[-1]):
            reasons.append("loading")
        
        should_filter = len(reasons) > 0
        return (should_filter, reasons)
