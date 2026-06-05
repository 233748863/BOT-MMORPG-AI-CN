"""
数据收集脚本
用于录制玩家操作数据，训练AI模型

使用方法:
1. 运行脚本
2. 切换到游戏窗口
3. 4秒倒计时后开始录制
4. 按 T 暂停/继续录制
5. 按 ESC 退出并保存

支持录制:
- 键盘移动 (WASD)
- 技能按键 (1-6, Q, E, R, G, C)
- 组合键 (Shift+, Ctrl+)
- 鼠标点击 (左键, 右键, 中键)
- 鼠标滚轮 (向上, 向下)
- 特殊按键 (空格, F交互)

智能录制功能:
- 自动识别高价值训练片段
- 过滤无效数据（空闲、重复、卡住）
- 实时显示价值评分
- 生成数据质量报告
"""

import numpy as np
import cv2
import time
import os
import sys
import win32api

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from 核心.屏幕截取 import 截取屏幕
from 核心.按键检测 import 检测按键
from 配置.设置 import (
    游戏窗口区域, 模型输入宽度, 模型输入高度,
    每文件样本数, 数据保存路径, 总动作数
)

# 导入智能录制模块
try:
    from 核心.智能录制 import (
        RecordingSegment, GameEvent, RecordingStatistics,
        ValueEvaluator, DataFilter, StatisticsService, 事件类型
    )
    智能录制可用 = True
except ImportError as e:
    print(f"⚠️ 智能录制模块加载失败: {e}")
    智能录制可用 = False


# ==================== 智能录制器封装类 ====================
class SmartRecorder:
    """智能录制器
    
    封装智能录制功能，提供价值评估、数据过滤和统计服务。
    需求: 10.1 - 将智能录制模块集成到现有的数据收集流程中
    """
    
    def __init__(self, enabled: bool = True):
        """初始化智能录制器
        
        Args:
            enabled: 是否启用智能录制功能
        """
        self.enabled = enabled and 智能录制可用
        
        if self.enabled:
            self.value_evaluator = ValueEvaluator()
            self.data_filter = DataFilter()
            self.statistics_service = StatisticsService()
            self.current_segment = None
            self.segment_frames = []
            self.segment_actions = []
            self.segment_start_time = 0.0
        
        # 过滤选项
        self.filter_options = {
            "保留全部": "all",
            "仅保留高价值": "high_only",
            "自动过滤低价值": "auto_filter"
        }
        self.current_filter = "all"
    
    def start_segment(self) -> None:
        """开始新的录制片段"""
        if not self.enabled:
            return
        
        self.segment_frames = []
        self.segment_actions = []
        self.segment_start_time = time.time()
        self.current_segment = RecordingSegment(
            start_time=self.segment_start_time
        )
    
    def add_frame(self, frame: np.ndarray, action: int) -> None:
        """添加帧和动作到当前片段
        
        Args:
            frame: 画面帧
            action: 动作编码
        """
        if not self.enabled:
            return
        
        self.segment_frames.append(frame.copy())
        self.segment_actions.append(action)
    
    def end_segment(self) -> tuple:
        """结束当前片段并评估
        
        Returns:
            (价值评分, 价值等级, 是否应过滤, 过滤原因)
        """
        if not self.enabled or self.current_segment is None:
            return (50.0, "medium", False, [])
        
        # 更新片段数据
        self.current_segment.end_time = time.time()
        self.current_segment.frames = self.segment_frames
        self.current_segment.actions = self.segment_actions
        
        # 检测游戏事件（简化版本，基于动作序列分析）
        self._detect_events()
        
        # 评估价值
        score = self.value_evaluator.evaluate_segment(self.current_segment)
        level = self.current_segment.value_level
        
        # 检查是否应该过滤
        should_filter, reasons = self.data_filter.filter_segment(self.current_segment)
        
        # 添加到统计
        self.statistics_service.add_segment(self.current_segment)
        
        return (score, level, should_filter, reasons)

    def _detect_events(self) -> None:
        """检测游戏事件（基于动作序列分析）"""
        if not self.current_segment:
            return
        
        actions = self.current_segment.actions
        if not actions:
            return
        
        # 检测技能连招（连续使用多个技能）
        skill_actions = [9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]  # 技能动作ID (包括新增的G和C)
        consecutive_skills = 0
        for action in actions:
            if action in skill_actions:
                consecutive_skills += 1
                if consecutive_skills >= 3:
                    # 检测到技能连招
                    event = GameEvent(
                        event_type=事件类型.技能连招.value,
                        timestamp=time.time(),
                        confidence=0.8,
                        data={"combo_length": consecutive_skills}
                    )
                    self.current_segment.add_event(event)
                    break
            else:
                consecutive_skills = 0
        
        # 检测空闲状态
        no_action_count = sum(1 for a in actions if a == 8)  # 8是无操作
        if len(actions) > 0 and no_action_count / len(actions) > 0.8:
            event = GameEvent(
                event_type=事件类型.空闲.value,
                timestamp=time.time(),
                confidence=0.9,
                data={"idle_ratio": no_action_count / len(actions)}
            )
            self.current_segment.add_event(event)
    
    def get_current_score(self) -> float:
        """获取当前片段的价值评分"""
        if not self.enabled:
            return 50.0
        return self.statistics_service.get_current_value_score()
    
    def get_statistics(self) -> dict:
        """获取录制统计"""
        if not self.enabled:
            return {"total": 0, "high": 0, "medium": 0, "low": 0}
        return self.statistics_service.get_value_counts()
    
    def generate_report(self) -> str:
        """生成数据质量报告"""
        if not self.enabled:
            return "智能录制功能未启用"
        
        report = self.statistics_service.generate_quality_report()
        return self.statistics_service.format_report_as_text(report)
    
    def should_save_segment(self, score: float, level: str, should_filter: bool) -> bool:
        """根据过滤选项判断是否应该保存片段
        
        Args:
            score: 价值评分
            level: 价值等级
            should_filter: 是否被标记为应过滤
            
        Returns:
            是否应该保存
        """
        if self.current_filter == "all":
            return True
        elif self.current_filter == "high_only":
            return level == "high"
        elif self.current_filter == "auto_filter":
            return not should_filter and level != "low"
        return True
    
    def set_filter_option(self, option: str) -> None:
        """设置过滤选项
        
        Args:
            option: 过滤选项 ("all", "high_only", "auto_filter")
        """
        if option in ["all", "high_only", "auto_filter"]:
            self.current_filter = option


def 检测鼠标按键():
    """检测鼠标按键状态"""
    左键 = win32api.GetAsyncKeyState(0x01) & 0x8000  # VK_LBUTTON
    右键 = win32api.GetAsyncKeyState(0x02) & 0x8000  # VK_RBUTTON
    中键 = win32api.GetAsyncKeyState(0x04) & 0x8000  # VK_MBUTTON
    
    # 检测滚轮（通过检测滚轮增量）
    # 注意：滚轮需要通过事件检测，这里简化处理
    滚轮上 = False  # 需要通过其他方式检测
    滚轮下 = False  # 需要通过其他方式检测
    
    return 左键, 右键, 中键, 滚轮上, 滚轮下


def 检测修饰键():
    """检测修饰键状态"""
    shift = win32api.GetAsyncKeyState(0x10) & 0x8000  # VK_SHIFT
    ctrl = win32api.GetAsyncKeyState(0x11) & 0x8000   # VK_CONTROL
    alt = win32api.GetAsyncKeyState(0x12) & 0x8000    # VK_MENU
    return shift, ctrl, alt


def 按键转动作(按键列表, 鼠标状态, 修饰键状态):
    """
    将按键转换为动作编码 (36维one-hot)
    
    返回:
        list: 动作的one-hot编码
    """
    动作 = [0] * 总动作数
    shift, ctrl, alt = 修饰键状态
    左键, 右键, 中键, 滚轮上, 滚轮下 = 鼠标状态
    
    # ===== 检测组合键 (优先级最高) =====
    if shift:
        if '1' in 按键列表:
            动作[28] = 1  # Shift+1
            return 动作
        if '2' in 按键列表:
            动作[29] = 1  # Shift+2
            return 动作
        if 'Q' in 按键列表:
            动作[30] = 1  # Shift+Q
            return 动作
        if 'E' in 按键列表:
            动作[31] = 1  # Shift+E
            return 动作
        if 'R' in 按键列表:
            动作[32] = 1  # Shift+R
            return 动作
    
    if ctrl:
        if '1' in 按键列表:
            动作[33] = 1  # Ctrl+1
            return 动作
        if '2' in 按键列表:
            动作[34] = 1  # Ctrl+2
            return 动作
        if 'Q' in 按键列表:
            动作[35] = 1  # Ctrl+Q
            return 动作
    
    # ===== 检测鼠标 =====
    if 左键:
        动作[23] = 1  # 鼠标左键
        return 动作
    if 右键:
        动作[24] = 1  # 鼠标右键
        return 动作
    if 中键:
        动作[25] = 1  # 鼠标中键
        return 动作
    if 滚轮上:
        动作[26] = 1  # 滚轮向上
        return 动作
    if 滚轮下:
        动作[27] = 1  # 滚轮向下
        return 动作

    # ===== 检测技能键 =====
    if '1' in 按键列表:
        动作[9] = 1
        return 动作
    if '2' in 按键列表:
        动作[10] = 1
        return 动作
    if '3' in 按键列表:
        动作[11] = 1
        return 动作
    if '4' in 按键列表:
        动作[12] = 1
        return 动作
    if '5' in 按键列表:
        动作[13] = 1
        return 动作
    if '6' in 按键列表:
        动作[14] = 1
        return 动作
    if 'Q' in 按键列表:
        动作[15] = 1
        return 动作
    if 'E' in 按键列表:
        动作[16] = 1
        return 动作
    if 'R' in 按键列表:
        动作[17] = 1
        return 动作
    if 'G' in 按键列表:
        动作[18] = 1  # 技能G
        return 动作
    if 'C' in 按键列表:
        动作[19] = 1  # 技能C
        return 动作
    
    # ===== 检测特殊键 =====
    if ' ' in 按键列表:  # 空格
        动作[20] = 1  # 跳跃/闪避
        return 动作
    if 'Tab' in 按键列表:
        动作[21] = 1  # 切换目标
        return 动作
    if 'F' in 按键列表:  # F键交互
        动作[22] = 1  # 交互
        return 动作
    
    # ===== 检测移动键 =====
    W按下 = 'W' in 按键列表
    A按下 = 'A' in 按键列表
    S按下 = 'S' in 按键列表
    D按下 = 'D' in 按键列表
    
    if W按下 and A按下:
        动作[4] = 1  # 前进+左移
    elif W按下 and D按下:
        动作[5] = 1  # 前进+右移
    elif S按下 and A按下:
        动作[6] = 1  # 后退+左移
    elif S按下 and D按下:
        动作[7] = 1  # 后退+右移
    elif W按下:
        动作[0] = 1  # 前进
    elif S按下:
        动作[1] = 1  # 后退
    elif A按下:
        动作[2] = 1  # 左移
    elif D按下:
        动作[3] = 1  # 右移
    else:
        动作[8] = 1  # 无操作
    
    return 动作


def 获取动作名称(动作):
    """根据动作编码获取动作名称"""
    from 配置.设置 import 动作定义
    索引 = 动作.index(1) if 1 in 动作 else 8
    return 动作定义.get(索引, {}).get("名称", "未知")


def 获取动作索引(动作):
    """根据动作编码获取动作索引"""
    return 动作.index(1) if 1 in 动作 else 8


def 获取起始文件编号(数据目录):
    """获取下一个可用的文件编号"""
    编号 = 1
    while True:
        文件名 = os.path.join(数据目录, f'训练数据-{编号}.npy')
        if os.path.isfile(文件名):
            编号 += 1
        else:
            print(f'将从编号 {编号} 开始保存')
            break
    return 编号


def 显示训练模式菜单():
    """显示训练模式选择菜单"""
    print("\n" + "=" * 50)
    print("🎮 MMORPG游戏AI - 数据收集工具")
    print("=" * 50)
    print("\n请选择训练模式:")
    print("  1. 主线任务练级 - 侧重移动和交互")
    print("  2. 自动战斗训练 - 侧重技能和走位")
    print("  3. 通用模式 - 记录所有操作")
    print()
    
    while True:
        选择 = input("请输入选项 (1/2/3): ").strip()
        if 选择 in ['1', '2', '3']:
            模式名称 = {'1': '主线任务', '2': '自动战斗', '3': '通用模式'}
            print(f"\n✅ 已选择: {模式名称[选择]}")
            return 选择
        print("❌ 无效选项，请重新输入")


def 显示过滤选项菜单():
    """显示智能录制过滤选项菜单"""
    if not 智能录制可用:
        return "all"
    
    print("\n" + "-" * 50)
    print("🧠 智能录制 - 数据过滤选项")
    print("-" * 50)
    print("  1. 保留全部 - 保存所有录制数据")
    print("  2. 仅保留高价值 - 只保存高价值片段")
    print("  3. 自动过滤 - 过滤低价值和无效数据")
    print()
    
    while True:
        选择 = input("请选择过滤选项 (1/2/3) [默认1]: ").strip()
        if 选择 == '' or 选择 == '1':
            print("✅ 已选择: 保留全部")
            return "all"
        elif 选择 == '2':
            print("✅ 已选择: 仅保留高价值")
            return "high_only"
        elif 选择 == '3':
            print("✅ 已选择: 自动过滤")
            return "auto_filter"
        print("❌ 无效选项，请重新输入")


def 主程序():
    """主数据收集程序"""
    
    # 选择训练模式
    训练模式 = 显示训练模式菜单()
    
    # 选择过滤选项（智能录制功能）
    过滤选项 = 显示过滤选项菜单()
    
    # 初始化智能录制器
    smart_recorder = SmartRecorder(enabled=智能录制可用)
    smart_recorder.set_filter_option(过滤选项)
    
    # 确保数据目录存在
    数据目录 = 数据保存路径
    os.makedirs(数据目录, exist_ok=True)
    
    # 获取起始文件编号
    文件编号 = 获取起始文件编号(数据目录)
    文件名 = os.path.join(数据目录, f'训练数据-{文件编号}.npy')
    
    # 初始化
    训练数据 = []
    已暂停 = False
    片段帧数 = 0
    片段评估间隔 = 100  # 每100帧评估一次片段
    过滤计数 = 0
    保存计数 = 0
    总片段数 = 0
    
    # 临时缓冲区：存储当前片段的帧数据，等待评估后决定是否保存
    片段缓冲区 = []
    
    print("\n" + "=" * 50)
    print("📋 操作说明:")
    print("  - 按 T 暂停/继续录制")
    print("  - 按 ESC 退出并保存")
    print(f"  - 每 {每文件样本数} 帧自动保存一次")
    if 智能录制可用:
        print("  - 🧠 智能录制已启用")
        print(f"  - 过滤模式: {过滤选项}")
    print()
    print("📊 支持录制的操作:")
    print("  - 移动: W A S D 及组合")
    print("  - 技能: 1-6, Q, E, R, G, C")
    print("  - 组合: Shift+键, Ctrl+键")
    print("  - 鼠标: 左键, 右键, 中键, 滚轮上下")
    print("  - 特殊: 空格(跳跃/闪避), F(交互)")
    print("=" * 50)
    
    # 倒计时
    print("\n⏱️  准备开始录制...")
    for i in range(4, 0, -1):
        print(f"   {i}...")
        time.sleep(1)
    
    print("\n🎬 开始录制! 请切换到游戏窗口")
    print("-" * 50)
    
    上次时间 = time.time()
    上次动作 = ""
    
    # 开始第一个片段
    smart_recorder.start_segment()

    try:
        while True:
            # 检查控制按键
            按键 = 检测按键()
            
            # 暂停/继续
            if 'T' in 按键:
                已暂停 = not 已暂停
                if 已暂停:
                    print("\n⏸️  已暂停录制")
                else:
                    print("\n▶️  继续录制")
                    smart_recorder.start_segment()  # 继续时开始新片段
                time.sleep(0.5)
            
            # ESC退出
            if win32api.GetAsyncKeyState(0x1B) & 0x8000:  # VK_ESCAPE
                print("\n🛑 正在退出...")
                break
            
            if not 已暂停:
                # 截取屏幕
                屏幕 = 截取屏幕(region=游戏窗口区域)
                屏幕 = cv2.resize(屏幕, (模型输入宽度, 模型输入高度))
                屏幕 = cv2.cvtColor(屏幕, cv2.COLOR_BGR2RGB)
                
                # 获取输入状态
                鼠标状态 = 检测鼠标按键()
                修饰键状态 = 检测修饰键()
                
                # 转换为动作编码
                动作 = 按键转动作(按键, 鼠标状态, 修饰键状态)
                动作索引 = 获取动作索引(动作)
                
                # 添加到智能录制器
                smart_recorder.add_frame(屏幕, 动作索引)
                片段帧数 += 1
                
                # 将当前帧数据添加到片段缓冲区（等待评估后决定是否保存）
                片段缓冲区.append([屏幕, 动作])
                
                # 每隔一定帧数评估片段
                if 片段帧数 >= 片段评估间隔:
                    score, level, should_filter, reasons = smart_recorder.end_segment()
                    总片段数 += 1
                    
                    # 根据过滤选项决定是否保存
                    if smart_recorder.should_save_segment(score, level, should_filter):
                        # 将缓冲区数据添加到训练数据列表
                        训练数据.extend(片段缓冲区)
                        保存计数 += 1
                    else:
                        过滤计数 += 1
                    
                    # 清空缓冲区，开始新片段
                    片段缓冲区 = []
                    smart_recorder.start_segment()
                    片段帧数 = 0
                
                # 显示预览窗口
                预览图 = cv2.resize(屏幕, (640, 360))
                cv2.imshow('录制预览 (ESC退出)', cv2.cvtColor(预览图, cv2.COLOR_RGB2BGR))
                
                if cv2.waitKey(25) & 0xFF == 27:  # ESC
                    break

                # 显示进度（包含智能录制信息）
                if len(训练数据) % 50 == 0 or (len(片段缓冲区) + len(训练数据)) % 50 == 0:
                    当前时间 = time.time()
                    总帧数 = len(训练数据) + len(片段缓冲区)
                    帧率 = 50 / (当前时间 - 上次时间) if 当前时间 > 上次时间 else 0
                    当前动作 = 获取动作名称(动作)
                    
                    # 获取智能录制统计
                    if 智能录制可用:
                        stats = smart_recorder.get_statistics()
                        current_score = smart_recorder.get_current_score()
                        print(f"📊 帧数: {总帧数:4d} | FPS: {帧率:5.1f} | "
                              f"动作: {当前动作} | 评分: {current_score:.1f} | "
                              f"片段-保存:{保存计数} 过滤:{过滤计数} | "
                              f"高:{stats['high']} 中:{stats['medium']} 低:{stats['low']}")
                    else:
                        print(f"📊 帧数: {总帧数:4d} | FPS: {帧率:5.1f} | 动作: {当前动作}")
                    
                    上次时间 = 当前时间
                
                # 自动保存
                if len(训练数据) >= 每文件样本数:
                    np.save(文件名, 训练数据)
                    print(f"\n💾 已保存: {文件名} ({len(训练数据)} 帧)")
                    print(f"   📈 过滤统计: 总片段 {总片段数}, 保存 {保存计数}, 过滤 {过滤计数}")
                    训练数据 = []
                    文件编号 += 1
                    文件名 = os.path.join(数据目录, f'训练数据-{文件编号}.npy')
    
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
    
    finally:
        cv2.destroyAllWindows()
        
        # 处理缓冲区中剩余的数据（最后一个未完成的片段）
        if 片段缓冲区:
            # 评估最后一个片段
            score, level, should_filter, reasons = smart_recorder.end_segment()
            总片段数 += 1
            if smart_recorder.should_save_segment(score, level, should_filter):
                训练数据.extend(片段缓冲区)
                保存计数 += 1
            else:
                过滤计数 += 1
        
        if 训练数据:
            np.save(文件名, 训练数据)
            print(f"\n💾 已保存剩余数据: {文件名} ({len(训练数据)} 帧)")
        
        print("\n" + "=" * 50)
        print("✅ 数据收集完成!")
        print(f"📁 数据保存在: {数据目录}")
        
        # 显示过滤统计
        if 智能录制可用 and 总片段数 > 0:
            过滤率 = (过滤计数 / 总片段数) * 100 if 总片段数 > 0 else 0
            print(f"\n📊 过滤统计:")
            print(f"   总片段数: {总片段数}")
            print(f"   保存片段: {保存计数} ({(保存计数/总片段数)*100:.1f}%)")
            print(f"   过滤片段: {过滤计数} ({过滤率:.1f}%)")
        
        # 显示智能录制报告
        if 智能录制可用:
            print("\n" + smart_recorder.generate_report())
        
        print("=" * 50)


if __name__ == "__main__":
    主程序()
