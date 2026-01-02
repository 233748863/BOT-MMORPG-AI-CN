"""
智能录制模块功能验证测试
用于检查点6：确保智能录制模块测试通过
"""

import pytest
from 核心.智能录制 import (
    RecordingSegment, GameEvent, RecordingStatistics, 
    ValueEvaluator, DataFilter, StatisticsService,
    事件类型, 价值等级
)


class Test价值评分范围约束:
    """测试 Property 1: 价值评分范围约束"""
    
    def test_有效评分范围(self):
        """价值评分在0-100范围内应该被接受"""
        segment = RecordingSegment()
        for score in [0, 25, 50, 75, 100]:
            segment.value_score = score
            assert 0 <= segment.value_score <= 100
    
    def test_拒绝负数评分(self):
        """负数评分应该被拒绝"""
        segment = RecordingSegment()
        with pytest.raises(ValueError):
            segment.value_score = -1
    
    def test_拒绝超过100的评分(self):
        """超过100的评分应该被拒绝"""
        segment = RecordingSegment()
        with pytest.raises(ValueError):
            segment.value_score = 101


class Test事件类型与价值等级映射:
    """测试 Property 2: 事件类型与价值等级映射一致性"""
    
    def test_击杀事件为高价值(self):
        """击杀事件应该映射为高价值"""
        evaluator = ValueEvaluator()
        event = GameEvent(event_type='kill', timestamp=1.0, confidence=1.0)
        level, _ = evaluator.classify_event(event)
        assert level == 'high'
    
    def test_任务完成事件为高价值(self):
        """任务完成事件应该映射为高价值"""
        evaluator = ValueEvaluator()
        event = GameEvent(event_type='quest_complete', timestamp=1.0, confidence=1.0)
        level, _ = evaluator.classify_event(event)
        assert level == 'high'
    
    def test_技能连招事件为高价值(self):
        """技能连招事件应该映射为高价值"""
        evaluator = ValueEvaluator()
        event = GameEvent(event_type='combo', timestamp=1.0, confidence=1.0)
        level, _ = evaluator.classify_event(event)
        assert level == 'high'
    
    def test_拾取事件为中等价值(self):
        """拾取事件应该映射为中等价值"""
        evaluator = ValueEvaluator()
        event = GameEvent(event_type='pickup', timestamp=1.0, confidence=1.0)
        level, _ = evaluator.classify_event(event)
        assert level == 'medium'


class Test空闲检测:
    """测试 Property 3: 空闲检测正确性"""
    
    def test_连续无操作超过5秒检测为空闲(self):
        """连续无操作超过5秒应该检测为空闲"""
        data_filter = DataFilter()
        # 全是无操作(0)的动作序列，持续6秒
        idle_actions = [0] * 60
        is_idle = data_filter.is_idle(idle_actions, 6.0)
        assert is_idle == True
    
    def test_有操作不检测为空闲(self):
        """有操作的序列不应该检测为空闲"""
        data_filter = DataFilter()
        active_actions = [1, 2, 3, 4, 5] * 10
        is_idle = data_filter.is_idle(active_actions, 5.0)
        assert is_idle == False
    
    def test_时长不足不检测为空闲(self):
        """时长不足5秒不应该检测为空闲"""
        data_filter = DataFilter()
        idle_actions = [0] * 30
        is_idle = data_filter.is_idle(idle_actions, 3.0)
        assert is_idle == False


class Test重复操作检测:
    """测试 Property 4: 重复操作检测正确性"""
    
    def test_相同动作超过10次检测为重复(self):
        """相同动作连续超过10次应该检测为重复"""
        data_filter = DataFilter()
        repetitive_actions = [1] * 15
        is_rep = data_filter.is_repetitive(repetitive_actions)
        assert is_rep == True
    
    def test_变化动作不检测为重复(self):
        """变化的动作序列不应该检测为重复"""
        data_filter = DataFilter()
        varied_actions = [1, 2, 3, 4, 5, 1, 2, 3, 4, 5]
        is_rep = data_filter.is_repetitive(varied_actions)
        assert is_rep == False
    
    def test_刚好10次不检测为重复(self):
        """刚好10次相同动作不应该检测为重复（需要超过10次）"""
        data_filter = DataFilter()
        actions = [1] * 10
        is_rep = data_filter.is_repetitive(actions)
        assert is_rep == False


class Test统计计算一致性:
    """测试 Property 5: 统计计算一致性"""
    
    def test_价值等级计数总和等于总片段数(self):
        """高/中/低价值片段计数之和应该等于总片段数"""
        stats_service = StatisticsService()
        segments = []
        for i in range(10):
            seg = RecordingSegment(start_time=i*10, end_time=(i+1)*10, actions=[i])
            if i < 3:
                seg.value_score = 80  # high
            elif i < 7:
                seg.value_score = 50  # medium
            else:
                seg.value_score = 20  # low
            segments.append(seg)
        
        stats_service.add_segments(segments)
        stats = stats_service.get_statistics()
        
        total = stats.high_value_count + stats.medium_value_count + stats.low_value_count
        assert total == stats.total_segments
    
    def test_空片段列表统计为零(self):
        """空片段列表的统计应该全为零"""
        stats_service = StatisticsService()
        stats = stats_service.get_statistics()
        
        assert stats.total_segments == 0
        assert stats.high_value_count == 0
        assert stats.medium_value_count == 0
        assert stats.low_value_count == 0


class Test质量报告生成:
    """测试质量报告生成功能"""
    
    def test_报告包含必要字段(self):
        """质量报告应该包含所有必要字段"""
        stats_service = StatisticsService()
        segments = [
            RecordingSegment(start_time=0, end_time=10, actions=[1, 2, 3])
        ]
        segments[0].value_score = 75
        stats_service.add_segments(segments)
        
        report = stats_service.generate_quality_report()
        
        assert 'summary' in report
        assert 'value_distribution' in report
        assert 'action_distribution' in report
        assert 'quality_score' in report
        assert 'suggestions' in report
        assert 'quality_level' in report


class Test片段评估:
    """测试片段评估功能"""
    
    def test_评估分数在有效范围内(self):
        """评估分数应该在0-100范围内"""
        evaluator = ValueEvaluator()
        segment = RecordingSegment()
        segment.events = [
            GameEvent(event_type='kill', timestamp=1.0, confidence=1.0),
            GameEvent(event_type='pickup', timestamp=2.0, confidence=0.8),
        ]
        score = evaluator.evaluate_segment(segment)
        assert 0 <= score <= 100
    
    def test_高价值事件提高评分(self):
        """高价值事件应该提高评分"""
        evaluator = ValueEvaluator()
        
        # 无事件的片段
        segment1 = RecordingSegment()
        score1 = evaluator.evaluate_segment(segment1)
        
        # 有击杀事件的片段
        segment2 = RecordingSegment()
        segment2.events = [
            GameEvent(event_type='kill', timestamp=1.0, confidence=1.0)
        ]
        score2 = evaluator.evaluate_segment(segment2)
        
        assert score2 > score1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
