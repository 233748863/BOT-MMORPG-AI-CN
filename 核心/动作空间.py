# -*- coding: utf-8 -*-
"""
动作空间兼容工具。

当前动作表为 36 维；旧数据/旧配置可能仍是 32 维，本模块集中处理映射。
"""

from numbers import Integral
from typing import Iterable, List, Sequence

from 配置.设置 import 总动作数


# 旧 32 维动作表:
# 0-17 与当前一致；18=F，19=空格，20=Tab，21=F交互，
# 22-24=鼠标，25-28=Shift组合，29-31=Ctrl组合。
旧32到36动作映射 = {
    **{i: i for i in range(18)},
    18: 22,
    19: 20,
    20: 21,
    21: 22,
    22: 23,
    23: 24,
    24: 25,
    25: 28,
    26: 29,
    27: 30,
    28: 31,
    29: 33,
    30: 34,
    31: 35,
}


def _转列表(值) -> List[float]:
    """将 numpy/list/tuple 等动作向量转为普通 float 列表。"""
    if hasattr(值, "tolist"):
        值 = 值.tolist()
    return [float(x) for x in 值]


def _最大索引(向量: Sequence[float]) -> int:
    if not 向量:
        return 8
    return max(range(len(向量)), key=lambda i: 向量[i])


def 标准化动作向量(向量, 默认值: float = 0.0) -> List[float]:
    """
    将动作概率/标签/权重向量转换为当前 36 维动作空间。

    32 维向量按旧动作表映射；其他短向量尾部补默认值，长向量截断。
    """
    值 = _转列表(向量)

    if len(值) == 总动作数:
        return 值

    if len(值) == 32:
        结果 = [默认值] * 总动作数
        for 旧索引, 权重 in enumerate(值):
            新索引 = 旧32到36动作映射.get(旧索引)
            if 新索引 is None:
                continue
            结果[新索引] = max(结果[新索引], 权重)
        return 结果

    if len(值) < 总动作数:
        return 值 + [默认值] * (总动作数 - len(值))

    return 值[:总动作数]


def 标准化动作权重(权重: Iterable[float]) -> List[float]:
    """将训练/推理动作权重标准化为当前 36 维。"""
    return 标准化动作向量(权重, 默认值=1.0)


def 标准化动作标签(标签) -> List[float]:
    """将标量标签、旧 32 维 one-hot 或当前 36 维 one-hot 统一为 36 维 one-hot。"""
    if isinstance(标签, Integral):
        索引 = int(标签)
    else:
        值 = _转列表(标签)
        if len(值) == 总动作数:
            return 值
        索引 = _最大索引(值)
        if len(值) == 32:
            索引 = 旧32到36动作映射.get(索引, 8)

    if 索引 < 0 or 索引 >= 总动作数:
        索引 = 8

    结果 = [0.0] * 总动作数
    结果[索引] = 1.0
    return 结果
