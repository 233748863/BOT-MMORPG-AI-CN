"""
模型管理模块
支持运行时模型热切换

功能:
- 多模型加载管理
- 运行时模型切换
- 自动切换规则
- 快捷键支持
"""

import os
import time
import json
import threading
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
import numpy as np
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
日志 = logging.getLogger(__name__)


@dataclass
class 模型槽位:
    """模型槽位信息"""
    名称: str
    路径: str
    描述: str = ""
    模型实例: Any = None
    已加载: bool = False
    内存占用: int = 0  # 字节
    加载时间: float = 0.0
    适用状态: List[str] = field(default_factory=list)
    快捷键: str = ""
    
    def to_dict(self) -> dict:
        return {
            '名称': self.名称,
            '路径': self.路径,
            '描述': self.描述,
            '已加载': self.已加载,
            '内存占用': self.内存占用,
            '加载时间': round(self.加载时间, 3),
            '适用状态': self.适用状态,
            '快捷键': self.快捷键
        }


@dataclass
class 切换事件:
    """切换事件记录"""
    时间戳: float
    原模型: str
    新模型: str
    触发方式: str  # "manual", "auto", "hotkey"
    触发原因: str = ""
    耗时: float = 0.0  # 毫秒


@dataclass
class 自动切换规则:
    """自动切换规则"""
    名称: str
    触发状态: List[str]  # 触发切换的游戏状态
    目标模型: str
    优先级: int = 0
    冷却时间: float = 5.0  # 秒


class 模型管理器:
    """管理多个模型的加载和切换"""
    
    def __init__(self, 配置路径: str = None, 模型加载器: Callable = None):
        """
        初始化模型管理器
        
        参数:
            配置路径: 模型配置文件路径
            模型加载器: 自定义模型加载函数
        """
        self._槽位字典: Dict[str, 模型槽位] = {}
        self._活动模型: str = ""
        self._默认模型: str = ""
        self._模型加载器 = 模型加载器
        self._切换锁 = threading.Lock()
        self._切换历史: List[切换事件] = []
        self._最大历史数 = 100
        
        if 配置路径 and os.path.exists(配置路径):
            self.从配置加载(配置路径)
    
    def 从配置加载(self, 配置路径: str):
        """从配置文件加载模型配置"""
        try:
            with open(配置路径, 'r', encoding='utf-8') as f:
                配置 = json.load(f)
            
            # 加载模型列表
            for 模型配置 in 配置.get('模型列表', []):
                槽位 = 模型槽位(
                    名称=模型配置['名称'],
                    路径=模型配置['路径'],
                    描述=模型配置.get('描述', ''),
                    适用状态=模型配置.get('适用状态', []),
                    快捷键=模型配置.get('快捷键', '')
                )
                self._槽位字典[槽位.名称] = 槽位
            
            # 设置默认模型
            self._默认模型 = 配置.get('默认模型', '')
            
            日志.info(f"已加载 {len(self._槽位字典)} 个模型配置")
            
        except Exception as e:
            日志.error(f"加载配置失败: {e}")
    
    def 保存配置(self, 配置路径: str):
        """保存模型配置到文件"""
        配置 = {
            '模型列表': [
                {
                    '名称': 槽位.名称,
                    '路径': 槽位.路径,
                    '描述': 槽位.描述,
                    '适用状态': 槽位.适用状态,
                    '快捷键': 槽位.快捷键
                }
                for 槽位 in self._槽位字典.values()
            ],
            '默认模型': self._默认模型
        }
        
        os.makedirs(os.path.dirname(配置路径) or '.', exist_ok=True)
        with open(配置路径, 'w', encoding='utf-8') as f:
            json.dump(配置, f, ensure_ascii=False, indent=2)
    
    def 注册模型(self, 名称: str, 路径: str, 描述: str = "",
                 适用状态: List[str] = None, 快捷键: str = ""):
        """
        注册模型槽位
        
        参数:
            名称: 模型名称
            路径: 模型文件路径
            描述: 模型描述
            适用状态: 适用的游戏状态列表
            快捷键: 切换快捷键
        """
        槽位 = 模型槽位(
            名称=名称,
            路径=路径,
            描述=描述,
            适用状态=适用状态 or [],
            快捷键=快捷键
        )
        self._槽位字典[名称] = 槽位
        日志.info(f"已注册模型: {名称}")
    
    def 加载模型(self, 名称: str) -> bool:
        """
        加载模型到内存
        
        参数:
            名称: 模型名称
            
        返回:
            是否加载成功
        """
        if 名称 not in self._槽位字典:
            日志.error(f"模型不存在: {名称}")
            return False
        
        槽位 = self._槽位字典[名称]
        
        if 槽位.已加载:
            日志.info(f"模型已加载: {名称}")
            return True
        
        开始时间 = time.time()
        
        try:
            if self._模型加载器:
                槽位.模型实例 = self._模型加载器(槽位.路径)
            else:
                槽位.模型实例 = self._默认加载模型(槽位.路径)
            
            槽位.已加载 = True
            槽位.加载时间 = time.time() - 开始时间
            
            日志.info(f"模型加载成功: {名称}，耗时 {槽位.加载时间:.2f}s")
            return True
            
        except Exception as e:
            日志.error(f"模型加载失败: {名称}, 错误: {e}")
            return False
    
    def _默认加载模型(self, 路径: str):
        """默认模型加载方法"""
        # 尝试使用统一推理引擎
        try:
            from 核心.ONNX推理 import 统一推理引擎
            return 统一推理引擎(路径)
        except ImportError:
            pass
        
        # 尝试使用 TFLearn
        try:
            from 核心.模型定义 import inception_v3
            from 配置.设置 import 模型输入宽度, 模型输入高度, 学习率, 总动作数
            
            模型 = inception_v3(
                模型输入宽度, 模型输入高度, 3, 学习率,
                输出类别=总动作数, 模型名称=路径
            )
            模型.load(路径)
            return 模型
        except Exception as e:
            raise RuntimeError(f"无法加载模型: {e}")
    
    def 卸载模型(self, 名称: str) -> bool:
        """
        卸载指定模型
        
        参数:
            名称: 模型名称
            
        返回:
            是否卸载成功
        """
        if 名称 not in self._槽位字典:
            return False
        
        槽位 = self._槽位字典[名称]
        
        if not 槽位.已加载:
            return True
        
        # 不能卸载活动模型
        if 名称 == self._活动模型:
            日志.warning(f"不能卸载活动模型: {名称}")
            return False
        
        槽位.模型实例 = None
        槽位.已加载 = False
        槽位.内存占用 = 0
        
        日志.info(f"模型已卸载: {名称}")
        return True

    def 切换模型(self, 名称: str, 触发方式: str = "manual", 
                 触发原因: str = "") -> bool:
        """
        切换活动模型
        
        参数:
            名称: 目标模型名称
            触发方式: 触发方式 ("manual", "auto", "hotkey")
            触发原因: 触发原因描述
            
        返回:
            是否切换成功
        """
        if 名称 not in self._槽位字典:
            日志.error(f"模型不存在: {名称}")
            return False
        
        if 名称 == self._活动模型:
            return True
        
        开始时间 = time.time()
        原模型 = self._活动模型
        
        with self._切换锁:
            槽位 = self._槽位字典[名称]
            
            # 确保模型已加载
            if not 槽位.已加载:
                if not self.加载模型(名称):
                    return False
            
            # 切换活动模型
            self._活动模型 = 名称
        
        耗时 = (time.time() - 开始时间) * 1000
        
        # 记录切换事件
        事件 = 切换事件(
            时间戳=time.time(),
            原模型=原模型,
            新模型=名称,
            触发方式=触发方式,
            触发原因=触发原因,
            耗时=耗时
        )
        self._记录切换事件(事件)
        
        日志.info(f"模型已切换: {原模型} -> {名称}，耗时 {耗时:.1f}ms")
        return True
    
    def _记录切换事件(self, 事件: 切换事件):
        """记录切换事件"""
        self._切换历史.append(事件)
        if len(self._切换历史) > self._最大历史数:
            self._切换历史.pop(0)
    
    def 获取活动模型(self) -> str:
        """获取当前活动模型名称"""
        return self._活动模型
    
    def 获取活动模型实例(self):
        """获取当前活动模型实例"""
        if not self._活动模型:
            return None
        return self._槽位字典[self._活动模型].模型实例
    
    def 预测(self, 图像: np.ndarray) -> List[float]:
        """
        使用活动模型进行预测
        
        参数:
            图像: 输入图像
            
        返回:
            预测结果
        """
        with self._切换锁:
            if not self._活动模型:
                日志.warning("没有活动模型")
                return []
            
            模型 = self._槽位字典[self._活动模型].模型实例
            
            if 模型 is None:
                日志.warning("活动模型未加载")
                return []
        
        try:
            # 支持不同类型的模型接口
            if hasattr(模型, '预测'):
                return 模型.预测(图像)
            elif hasattr(模型, 'predict'):
                结果 = 模型.predict(np.expand_dims(图像, axis=0))
                return 结果[0].tolist() if hasattr(结果[0], 'tolist') else list(结果[0])
            else:
                日志.error("模型没有预测方法")
                return []
        except Exception as e:
            日志.error(f"预测失败: {e}")
            return []
    
    def 获取模型列表(self) -> List[dict]:
        """获取所有模型信息"""
        return [槽位.to_dict() for 槽位 in self._槽位字典.values()]
    
    def 获取切换历史(self, 数量: int = 10) -> List[dict]:
        """获取最近的切换历史"""
        历史 = self._切换历史[-数量:]
        return [
            {
                '时间': 事件.时间戳,
                '原模型': 事件.原模型,
                '新模型': 事件.新模型,
                '触发方式': 事件.触发方式,
                '触发原因': 事件.触发原因,
                '耗时': 事件.耗时
            }
            for 事件 in 历史
        ]
    
    def 循环切换(self) -> str:
        """
        循环切换到下一个模型
        
        返回:
            新的活动模型名称
        """
        模型名列表 = list(self._槽位字典.keys())
        if not 模型名列表:
            return ""
        
        if not self._活动模型:
            下一个 = 模型名列表[0]
        else:
            当前索引 = 模型名列表.index(self._活动模型) if self._活动模型 in 模型名列表 else -1
            下一个索引 = (当前索引 + 1) % len(模型名列表)
            下一个 = 模型名列表[下一个索引]
        
        self.切换模型(下一个, "hotkey", "循环切换")
        return 下一个


class 自动切换器:
    """根据游戏状态自动切换模型"""
    
    def __init__(self, 模型管理器: 模型管理器, 冷却时间: float = 5.0):
        """
        初始化自动切换器
        
        参数:
            模型管理器: 模型管理器实例
            冷却时间: 切换冷却时间（秒）
        """
        self._管理器 = 模型管理器
        self._规则列表: List[自动切换规则] = []
        self._冷却时间 = 冷却时间
        self._上次切换时间: float = 0.0
        self._启用 = True
    
    def 添加规则(self, 规则: 自动切换规则):
        """添加自动切换规则"""
        self._规则列表.append(规则)
        # 按优先级排序
        self._规则列表.sort(key=lambda r: r.优先级, reverse=True)
    
    def 从配置加载(self, 规则列表: List[dict]):
        """从配置加载规则"""
        for 规则配置 in 规则列表:
            规则 = 自动切换规则(
                名称=规则配置.get('名称', ''),
                触发状态=规则配置.get('触发状态', []),
                目标模型=规则配置.get('目标模型', ''),
                优先级=规则配置.get('优先级', 0),
                冷却时间=规则配置.get('冷却时间', self._冷却时间)
            )
            self.添加规则(规则)
    
    def 检查切换(self, 当前状态: str) -> Optional[str]:
        """
        检查是否需要切换
        
        参数:
            当前状态: 当前游戏状态
            
        返回:
            目标模型名称，None 表示不切换
        """
        if not self._启用:
            return None
        
        # 检查冷却时间
        if time.time() - self._上次切换时间 < self._冷却时间:
            return None
        
        # 检查规则
        for 规则 in self._规则列表:
            if 当前状态 in 规则.触发状态:
                # 检查是否需要切换
                if 规则.目标模型 != self._管理器.获取活动模型():
                    return 规则.目标模型
        
        return None
    
    def 执行切换(self, 当前状态: str) -> bool:
        """
        检查并执行切换
        
        参数:
            当前状态: 当前游戏状态
            
        返回:
            是否执行了切换
        """
        目标模型 = self.检查切换(当前状态)
        
        if 目标模型:
            成功 = self._管理器.切换模型(
                目标模型, 
                "auto", 
                f"状态触发: {当前状态}"
            )
            if 成功:
                self._上次切换时间 = time.time()
            return 成功
        
        return False
    
    def 设置启用(self, 启用: bool):
        """设置是否启用自动切换"""
        self._启用 = 启用
    
    def 是否启用(self) -> bool:
        """检查是否启用"""
        return self._启用


class 快捷键处理器:
    """处理模型切换快捷键"""
    
    def __init__(self, 模型管理器: 模型管理器):
        """
        初始化快捷键处理器
        
        参数:
            模型管理器: 模型管理器实例
        """
        self._管理器 = 模型管理器
        self._快捷键映射: Dict[str, str] = {}  # 按键 -> 模型名
        self._循环切换键: str = ""
        self._回调函数: Optional[Callable] = None
    
    def 注册快捷键(self, 按键: str, 模型名: str):
        """
        注册快捷键
        
        参数:
            按键: 按键名称（如 "F1", "F2"）
            模型名: 对应的模型名称
        """
        self._快捷键映射[按键.upper()] = 模型名
    
    def 设置循环切换键(self, 按键: str):
        """设置循环切换快捷键"""
        self._循环切换键 = 按键.upper()
    
    def 设置切换回调(self, 回调: Callable):
        """设置切换完成后的回调函数"""
        self._回调函数 = 回调
    
    def 处理按键(self, 按键: str) -> bool:
        """
        处理按键事件
        
        参数:
            按键: 按键名称
            
        返回:
            是否触发了模型切换
        """
        按键 = 按键.upper()
        
        # 检查循环切换键
        if 按键 == self._循环切换键:
            新模型 = self._管理器.循环切换()
            if 新模型 and self._回调函数:
                self._回调函数(新模型)
            return bool(新模型)
        
        # 检查直接切换键
        if 按键 in self._快捷键映射:
            模型名 = self._快捷键映射[按键]
            成功 = self._管理器.切换模型(模型名, "hotkey", f"快捷键: {按键}")
            if 成功 and self._回调函数:
                self._回调函数(模型名)
            return 成功
        
        return False
    
    def 从模型配置加载(self):
        """从模型管理器的配置加载快捷键"""
        for 槽位 in self._管理器._槽位字典.values():
            if 槽位.快捷键:
                self.注册快捷键(槽位.快捷键, 槽位.名称)
