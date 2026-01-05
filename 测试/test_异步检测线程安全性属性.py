"""
异步检测线程安全性属性测试

属性 1: 线程安全性
*对于任意* 并发访问结果缓存的操作，不应产生数据竞争

验证: 需求 4.1, 4.2

Feature: yolo-async-detection, Property 1: 线程安全性
"""

import time
import threading
import numpy as np
import pytest
from hypothesis import given, strategies as st, settings, assume
from typing import List, Tuple, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

# 导入被测试的模块
from 核心.异步检测 import 检测队列, 结果缓存, 性能监控器


# ==================== 策略定义 ====================

@st.composite
def 随机图像(draw, 最小尺寸=32, 最大尺寸=64):
    """生成随机图像"""
    宽度 = draw(st.integers(min_value=最小尺寸, max_value=最大尺寸))
    高度 = draw(st.integers(min_value=最小尺寸, max_value=最大尺寸))
    图像 = np.random.randint(0, 256, (高度, 宽度, 3), dtype=np.uint8)
    return 图像


@st.composite
def 随机检测结果(draw):
    """生成随机检测结果列表"""
    数量 = draw(st.integers(min_value=0, max_value=10))
    结果 = []
    for i in range(数量):
        结果.append({
            'id': i,
            'x': draw(st.floats(min_value=0, max_value=100)),
            'y': draw(st.floats(min_value=0, max_value=100)),
            'confidence': draw(st.floats(min_value=0, max_value=1))
        })
    return 结果


@st.composite
def 并发参数(draw):
    """生成并发测试参数"""
    线程数 = draw(st.integers(min_value=2, max_value=8))
    操作数 = draw(st.integers(min_value=5, max_value=20))
    return 线程数, 操作数


# ==================== 属性测试 ====================

class Test结果缓存线程安全性属性:
    """
    属性测试: 结果缓存线程安全性
    
    Feature: yolo-async-detection, Property 1: 线程安全性
    Validates: Requirements 4.1, 4.2
    """
    
    @settings(max_examples=100, deadline=30000)
    @given(参数=并发参数())
    def test_并发更新不产生数据竞争(self, 参数: Tuple[int, int]):
        """
        属性测试: 并发更新结果缓存不应产生数据竞争
        
        *对于任意* 并发更新操作，结果缓存应保持数据一致性
        
        Feature: yolo-async-detection, Property 1: 线程安全性
        Validates: Requirements 4.1
        """
        线程数, 操作数 = 参数
        缓存 = 结果缓存()
        错误列表 = []
        
        def 更新操作(线程id: int):
            """执行更新操作"""
            try:
                for i in range(操作数):
                    结果 = [{'线程': 线程id, '操作': i}]
                    缓存.更新(结果, 帧编号=线程id * 1000 + i)
                    # 短暂延迟增加竞争概率
                    time.sleep(0.001)
            except Exception as e:
                错误列表.append(f"线程 {线程id} 更新错误: {e}")
        
        # 启动多个线程并发更新
        线程列表 = []
        for i in range(线程数):
            线程 = threading.Thread(target=更新操作, args=(i,))
            线程列表.append(线程)
            线程.start()
        
        # 等待所有线程完成
        for 线程 in 线程列表:
            线程.join(timeout=10)
        
        # 验证没有错误
        assert len(错误列表) == 0, f"并发更新产生错误: {错误列表}"
        
        # 验证缓存状态一致
        结果, 时间戳, 帧编号 = 缓存.获取()
        assert isinstance(结果, list), "结果应为列表"
        assert 时间戳 > 0, "时间戳应大于 0"
    
    @settings(max_examples=100, deadline=30000)
    @given(参数=并发参数())
    def test_并发读写不产生数据竞争(self, 参数: Tuple[int, int]):
        """
        属性测试: 并发读写结果缓存不应产生数据竞争
        
        *对于任意* 并发读写操作，结果缓存应保持数据一致性
        
        Feature: yolo-async-detection, Property 1: 线程安全性
        Validates: Requirements 4.1, 4.2
        """
        线程数, 操作数 = 参数
        缓存 = 结果缓存()
        错误列表 = []
        读取结果 = []
        
        def 写入操作(线程id: int):
            """执行写入操作"""
            try:
                for i in range(操作数):
                    结果 = [{'线程': 线程id, '操作': i, '数据': list(range(10))}]
                    缓存.更新(结果, 帧编号=线程id * 1000 + i)
                    time.sleep(0.001)
            except Exception as e:
                错误列表.append(f"线程 {线程id} 写入错误: {e}")
        
        def 读取操作(线程id: int):
            """执行读取操作"""
            try:
                for i in range(操作数):
                    结果, 时间戳, 帧编号 = 缓存.获取()
                    读取结果.append((线程id, i, 结果))
                    _ = 缓存.获取年龄()
                    time.sleep(0.001)
            except Exception as e:
                错误列表.append(f"线程 {线程id} 读取错误: {e}")
        
        # 启动写入和读取线程
        线程列表 = []
        写入线程数 = 线程数 // 2
        读取线程数 = 线程数 - 写入线程数
        
        for i in range(写入线程数):
            线程 = threading.Thread(target=写入操作, args=(i,))
            线程列表.append(线程)
        
        for i in range(读取线程数):
            线程 = threading.Thread(target=读取操作, args=(i + 写入线程数,))
            线程列表.append(线程)
        
        # 启动所有线程
        for 线程 in 线程列表:
            线程.start()
        
        # 等待所有线程完成
        for 线程 in 线程列表:
            线程.join(timeout=10)
        
        # 验证没有错误
        assert len(错误列表) == 0, f"并发读写产生错误: {错误列表}"
        
        # 验证所有读取结果都是有效的列表
        for 线程id, 操作id, 结果 in 读取结果:
            assert isinstance(结果, list), f"线程 {线程id} 操作 {操作id} 读取结果应为列表"
    
    @settings(max_examples=100, deadline=30000)
    @given(结果=随机检测结果())
    def test_更新后获取数据一致(self, 结果: List[dict]):
        """
        属性测试: 更新后获取的数据应与更新的数据一致
        
        *对于任意* 检测结果，更新后立即获取应返回相同数据
        
        Feature: yolo-async-detection, Property 1: 线程安全性
        Validates: Requirements 4.1
        """
        缓存 = 结果缓存()
        帧编号 = 42
        
        # 更新缓存
        缓存.更新(结果, 帧编号=帧编号)
        
        # 获取缓存
        获取结果, 时间戳, 获取帧编号 = 缓存.获取()
        
        # 验证数据一致性
        assert 获取结果 == 结果, "获取的结果应与更新的结果一致"
        assert 获取帧编号 == 帧编号, "获取的帧编号应与更新的帧编号一致"
        assert 时间戳 > 0, "时间戳应大于 0"


class Test检测队列线程安全性属性:
    """
    属性测试: 检测队列线程安全性
    
    Feature: yolo-async-detection, Property 1: 线程安全性
    Validates: Requirements 4.2
    """
    
    @settings(max_examples=100, deadline=30000)
    @given(参数=并发参数())
    def test_并发放入不产生数据竞争(self, 参数: Tuple[int, int]):
        """
        属性测试: 并发放入检测队列不应产生数据竞争
        
        *对于任意* 并发放入操作，检测队列应正确处理
        
        Feature: yolo-async-detection, Property 1: 线程安全性
        Validates: Requirements 4.2
        """
        线程数, 操作数 = 参数
        队列 = 检测队列(最大大小=100)  # 使用较大队列避免溢出
        错误列表 = []
        成功计数 = [0]  # 使用列表以便在闭包中修改
        计数锁 = threading.Lock()
        
        def 放入操作(线程id: int):
            """执行放入操作"""
            try:
                for i in range(操作数):
                    图像 = np.random.randint(0, 256, (32, 32, 3), dtype=np.uint8)
                    成功 = 队列.放入(图像)
                    if 成功:
                        with 计数锁:
                            成功计数[0] += 1
                    time.sleep(0.001)
            except Exception as e:
                错误列表.append(f"线程 {线程id} 放入错误: {e}")
        
        # 启动多个线程并发放入
        线程列表 = []
        for i in range(线程数):
            线程 = threading.Thread(target=放入操作, args=(i,))
            线程列表.append(线程)
            线程.start()
        
        # 等待所有线程完成
        for 线程 in 线程列表:
            线程.join(timeout=10)
        
        # 验证没有错误
        assert len(错误列表) == 0, f"并发放入产生错误: {错误列表}"
        
        # 验证队列状态一致
        队列深度 = 队列.获取深度()
        溢出计数 = 队列.获取溢出计数()
        
        # 成功放入数 + 溢出数 应等于总操作数
        总操作数 = 线程数 * 操作数
        assert 成功计数[0] + 溢出计数 == 总操作数, \
            f"成功数 {成功计数[0]} + 溢出数 {溢出计数} 应等于总操作数 {总操作数}"
    
    @settings(max_examples=100, deadline=30000)
    @given(参数=并发参数())
    def test_并发放入取出不产生数据竞争(self, 参数: Tuple[int, int]):
        """
        属性测试: 并发放入和取出检测队列不应产生数据竞争
        
        *对于任意* 并发放入和取出操作，检测队列应正确处理
        
        Feature: yolo-async-detection, Property 1: 线程安全性
        Validates: Requirements 4.2
        """
        线程数, 操作数 = 参数
        队列 = 检测队列(最大大小=50)
        错误列表 = []
        取出计数 = [0]
        计数锁 = threading.Lock()
        停止标志 = threading.Event()
        
        def 放入操作(线程id: int):
            """执行放入操作"""
            try:
                for i in range(操作数):
                    if 停止标志.is_set():
                        break
                    图像 = np.random.randint(0, 256, (32, 32, 3), dtype=np.uint8)
                    队列.放入(图像)
                    time.sleep(0.002)
            except Exception as e:
                错误列表.append(f"线程 {线程id} 放入错误: {e}")
        
        def 取出操作(线程id: int):
            """执行取出操作"""
            try:
                for i in range(操作数):
                    if 停止标志.is_set():
                        break
                    任务 = 队列.取出(超时=0.1)
                    if 任务 is not None:
                        with 计数锁:
                            取出计数[0] += 1
                    time.sleep(0.001)
            except Exception as e:
                错误列表.append(f"线程 {线程id} 取出错误: {e}")
        
        # 启动放入和取出线程
        线程列表 = []
        放入线程数 = 线程数 // 2
        取出线程数 = 线程数 - 放入线程数
        
        for i in range(放入线程数):
            线程 = threading.Thread(target=放入操作, args=(i,))
            线程列表.append(线程)
        
        for i in range(取出线程数):
            线程 = threading.Thread(target=取出操作, args=(i + 放入线程数,))
            线程列表.append(线程)
        
        # 启动所有线程
        for 线程 in 线程列表:
            线程.start()
        
        # 等待所有线程完成
        for 线程 in 线程列表:
            线程.join(timeout=15)
        
        停止标志.set()
        
        # 验证没有错误
        assert len(错误列表) == 0, f"并发放入取出产生错误: {错误列表}"
    
    @settings(max_examples=100, deadline=10000)
    @given(队列大小=st.integers(min_value=1, max_value=10))
    def test_溢出计数正确(self, 队列大小: int):
        """
        属性测试: 队列溢出计数应正确
        
        *对于任意* 队列大小，溢出计数应正确反映溢出次数
        
        Feature: yolo-async-detection, Property 1: 线程安全性
        Validates: Requirements 4.2
        """
        队列 = 检测队列(最大大小=队列大小)
        
        # 放入超过队列大小的图像
        放入次数 = 队列大小 + 5
        成功次数 = 0
        
        for i in range(放入次数):
            图像 = np.random.randint(0, 256, (32, 32, 3), dtype=np.uint8)
            if 队列.放入(图像):
                成功次数 += 1
        
        溢出计数 = 队列.获取溢出计数()
        
        # 成功次数应等于队列大小
        assert 成功次数 == 队列大小, f"成功次数 {成功次数} 应等于队列大小 {队列大小}"
        
        # 溢出次数应等于放入次数减去队列大小
        期望溢出 = 放入次数 - 队列大小
        assert 溢出计数 == 期望溢出, f"溢出计数 {溢出计数} 应等于 {期望溢出}"


class Test性能监控器线程安全性属性:
    """
    属性测试: 性能监控器线程安全性
    
    Feature: yolo-async-detection, Property 1: 线程安全性
    Validates: Requirements 4.1, 4.2
    """
    
    @settings(max_examples=100, deadline=30000)
    @given(参数=并发参数())
    def test_并发记录延迟不产生数据竞争(self, 参数: Tuple[int, int]):
        """
        属性测试: 并发记录延迟不应产生数据竞争
        
        *对于任意* 并发记录操作，性能监控器应正确处理
        
        Feature: yolo-async-detection, Property 1: 线程安全性
        Validates: Requirements 4.1, 4.2
        """
        线程数, 操作数 = 参数
        监控器 = 性能监控器(窗口大小=1000)
        错误列表 = []
        
        def 记录操作(线程id: int):
            """执行记录操作"""
            try:
                for i in range(操作数):
                    延迟 = float(线程id * 100 + i)
                    监控器.记录延迟(延迟)
                    time.sleep(0.001)
            except Exception as e:
                错误列表.append(f"线程 {线程id} 记录错误: {e}")
        
        # 启动多个线程并发记录
        线程列表 = []
        for i in range(线程数):
            线程 = threading.Thread(target=记录操作, args=(i,))
            线程列表.append(线程)
            线程.start()
        
        # 等待所有线程完成
        for 线程 in 线程列表:
            线程.join(timeout=10)
        
        # 验证没有错误
        assert len(错误列表) == 0, f"并发记录产生错误: {错误列表}"
        
        # 验证统计数据
        统计 = 监控器.获取统计()
        期望检测次数 = 线程数 * 操作数
        assert 统计['检测次数'] == 期望检测次数, \
            f"检测次数 {统计['检测次数']} 应等于 {期望检测次数}"
    
    @settings(max_examples=100, deadline=30000)
    @given(参数=并发参数())
    def test_并发记录和获取统计不产生数据竞争(self, 参数: Tuple[int, int]):
        """
        属性测试: 并发记录和获取统计不应产生数据竞争
        
        *对于任意* 并发记录和获取操作，性能监控器应正确处理
        
        Feature: yolo-async-detection, Property 1: 线程安全性
        Validates: Requirements 4.1, 4.2
        """
        线程数, 操作数 = 参数
        监控器 = 性能监控器(窗口大小=1000)
        错误列表 = []
        统计结果 = []
        
        def 记录操作(线程id: int):
            """执行记录操作"""
            try:
                for i in range(操作数):
                    延迟 = float(线程id * 100 + i)
                    监控器.记录延迟(延迟)
                    time.sleep(0.001)
            except Exception as e:
                错误列表.append(f"线程 {线程id} 记录错误: {e}")
        
        def 获取操作(线程id: int):
            """执行获取统计操作"""
            try:
                for i in range(操作数):
                    统计 = 监控器.获取统计()
                    统计结果.append(统计)
                    time.sleep(0.001)
            except Exception as e:
                错误列表.append(f"线程 {线程id} 获取错误: {e}")
        
        # 启动记录和获取线程
        线程列表 = []
        记录线程数 = 线程数 // 2
        获取线程数 = 线程数 - 记录线程数
        
        for i in range(记录线程数):
            线程 = threading.Thread(target=记录操作, args=(i,))
            线程列表.append(线程)
        
        for i in range(获取线程数):
            线程 = threading.Thread(target=获取操作, args=(i + 记录线程数,))
            线程列表.append(线程)
        
        # 启动所有线程
        for 线程 in 线程列表:
            线程.start()
        
        # 等待所有线程完成
        for 线程 in 线程列表:
            线程.join(timeout=10)
        
        # 验证没有错误
        assert len(错误列表) == 0, f"并发记录和获取产生错误: {错误列表}"
        
        # 验证所有统计结果都是有效的字典
        for 统计 in 统计结果:
            assert isinstance(统计, dict), "统计结果应为字典"
            assert '检测次数' in 统计, "统计结果应包含检测次数"


class Test线程安全性单元测试:
    """线程安全性单元测试"""
    
    def test_结果缓存初始状态(self):
        """测试结果缓存初始状态"""
        缓存 = 结果缓存()
        结果, 时间戳, 帧编号 = 缓存.获取()
        
        assert 结果 == [], "初始结果应为空列表"
        assert 时间戳 == 0.0, "初始时间戳应为 0"
        assert 帧编号 == 0, "初始帧编号应为 0"
    
    def test_结果缓存更新和获取(self):
        """测试结果缓存更新和获取"""
        缓存 = 结果缓存()
        测试结果 = [{'id': 1}, {'id': 2}]
        
        缓存.更新(测试结果, 帧编号=100)
        获取结果, 时间戳, 帧编号 = 缓存.获取()
        
        assert 获取结果 == 测试结果, "获取结果应与更新结果一致"
        assert 帧编号 == 100, "帧编号应为 100"
        assert 时间戳 > 0, "时间戳应大于 0"
    
    def test_结果缓存年龄计算(self):
        """测试结果缓存年龄计算"""
        缓存 = 结果缓存()
        
        # 初始年龄应为无穷大
        assert 缓存.获取年龄() == float('inf'), "初始年龄应为无穷大"
        
        # 更新后年龄应接近 0
        缓存.更新([], 帧编号=1)
        年龄 = 缓存.获取年龄()
        assert 年龄 < 0.1, f"刚更新后年龄 {年龄} 应接近 0"
    
    def test_检测队列基本操作(self):
        """测试检测队列基本操作"""
        队列 = 检测队列(最大大小=3)
        图像 = np.zeros((32, 32, 3), dtype=np.uint8)
        
        # 放入
        assert 队列.放入(图像) == True, "放入应成功"
        assert 队列.获取深度() == 1, "队列深度应为 1"
        
        # 取出
        任务 = 队列.取出(超时=1.0)
        assert 任务 is not None, "取出应成功"
        assert 队列.获取深度() == 0, "队列深度应为 0"
    
    def test_检测队列溢出(self):
        """测试检测队列溢出"""
        队列 = 检测队列(最大大小=2)
        图像 = np.zeros((32, 32, 3), dtype=np.uint8)
        
        # 放入直到溢出
        assert 队列.放入(图像) == True
        assert 队列.放入(图像) == True
        assert 队列.放入(图像) == False, "队列满时放入应失败"
        
        assert 队列.获取溢出计数() == 1, "溢出计数应为 1"
    
    def test_性能监控器基本操作(self):
        """测试性能监控器基本操作"""
        监控器 = 性能监控器(窗口大小=10)
        
        # 记录延迟
        for i in range(5):
            监控器.记录延迟(float(i * 10))
        
        统计 = 监控器.获取统计()
        
        assert 统计['检测次数'] == 5, "检测次数应为 5"
        assert 统计['平均延迟'] == 20.0, "平均延迟应为 20.0"
        assert 统计['最小延迟'] == 0.0, "最小延迟应为 0.0"
        assert 统计['最大延迟'] == 40.0, "最大延迟应为 40.0"
    
    def test_性能监控器重置(self):
        """测试性能监控器重置"""
        监控器 = 性能监控器()
        
        监控器.记录延迟(100.0)
        监控器.重置()
        
        统计 = 监控器.获取统计()
        assert 统计['检测次数'] == 0, "重置后检测次数应为 0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
