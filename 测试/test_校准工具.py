"""
校准工具测试脚本
测试校准工具和配置管理器的基本功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from 核心.状态检测 import 校准工具, 状态检测配置管理器, 状态检测器


def test_校准工具初始化():
    """测试校准工具初始化"""
    print('测试校准工具初始化...')
    工具 = 校准工具()
    assert 工具.获取配置目录() == "配置/状态检测"
    print(f'  配置目录: {工具.获取配置目录()}')
    print('  ✓ 初始化成功')
    return 工具


def test_配置保存(工具):
    """测试配置保存"""
    print('\n测试配置保存...')
    路径 = 工具.保存配置(
        配置名称='测试游戏',
        游戏名称='Test Game',
        血条区域=(100, 50, 200, 20),
        蓝条区域=(100, 75, 200, 15)
    )
    assert 路径 is not None
    print(f'  保存路径: {路径}')
    print('  ✓ 配置保存成功')


def test_配置加载(工具):
    """测试配置加载"""
    print('\n测试配置加载...')
    配置 = 工具.加载配置('测试游戏')
    assert 配置 is not None
    assert 配置.get('游戏名称') == 'Test Game'
    assert 配置.get('血条', {}).get('区域') == [100, 50, 200, 20]
    assert 配置.get('蓝条', {}).get('区域') == [100, 75, 200, 15]
    print(f'  游戏名称: {配置.get("游戏名称")}')
    print(f'  血条区域: {配置.get("血条", {}).get("区域")}')
    print(f'  蓝条区域: {配置.get("蓝条", {}).get("区域")}')
    print('  ✓ 配置加载成功')
    return 配置


def test_列出配置(工具):
    """测试列出配置"""
    print('\n测试列出配置...')
    配置列表 = 工具.列出配置()
    assert '测试游戏' in 配置列表
    print(f'  可用配置: {配置列表}')
    print('  ✓ 列出配置成功')


def test_配置管理器():
    """测试配置管理器"""
    print('\n测试配置管理器...')
    管理器 = 状态检测配置管理器()
    所有配置 = 管理器.列出所有配置()
    print(f'  所有配置数量: {len(所有配置)}')
    for 配置信息 in 所有配置:
        print(f'    - {配置信息["name"]}: {配置信息["game_name"]}')
    print('  ✓ 配置管理器测试成功')
    return 管理器


def test_切换配置(管理器):
    """测试切换配置"""
    print('\n测试切换配置...')
    结果 = 管理器.切换配置('测试游戏')
    assert 结果 == True
    assert 管理器.获取当前配置名() == '测试游戏'
    当前配置 = 管理器.获取当前配置()
    assert 当前配置 is not None
    print(f'  当前配置: {管理器.获取当前配置名()}')
    print('  ✓ 切换配置成功')


def test_预览区域(工具):
    """测试预览区域"""
    print('\n测试预览区域...')
    测试图像 = np.zeros((480, 640, 3), dtype=np.uint8)
    预览图 = 工具.预览区域(测试图像, (100, 50, 200, 20), '血条', 显示检测结果=False)
    assert 预览图.shape == (480, 640, 3)
    print(f'  预览图尺寸: {预览图.shape}')
    print('  ✓ 预览区域成功')


def test_预览多区域(工具):
    """测试同时预览多个区域"""
    print('\n测试预览多区域...')
    测试图像 = np.zeros((480, 640, 3), dtype=np.uint8)
    预览图 = 工具.预览多区域(
        测试图像, 
        血条区域=(100, 50, 200, 20),
        蓝条区域=(100, 75, 200, 15)
    )
    assert 预览图.shape == (480, 640, 3)
    print(f'  预览图尺寸: {预览图.shape}')
    print('  ✓ 预览多区域成功')


def test_应用配置到检测器(管理器):
    """测试将配置应用到检测器"""
    print('\n测试应用配置到检测器...')
    检测器 = 状态检测器()
    结果 = 管理器.应用到检测器(检测器)
    assert 结果 == True
    assert 检测器._血量检测器.区域 == (100, 50, 200, 20)
    assert 检测器._蓝量检测器.区域 == (100, 75, 200, 15)
    print(f'  血条区域: {检测器._血量检测器.区域}')
    print(f'  蓝条区域: {检测器._蓝量检测器.区域}')
    print('  ✓ 应用配置成功')


def test_清理(工具):
    """清理测试配置"""
    print('\n清理测试配置...')
    结果 = 工具.删除配置('测试游戏')
    assert 结果 == True
    assert '测试游戏' not in 工具.列出配置()
    print('  ✓ 清理成功')


def main():
    """运行所有测试"""
    print('=' * 50)
    print('校准工具测试')
    print('=' * 50)
    
    try:
        # 测试校准工具
        工具 = test_校准工具初始化()
        test_配置保存(工具)
        test_配置加载(工具)
        test_列出配置(工具)
        
        # 测试配置管理器
        管理器 = test_配置管理器()
        test_切换配置(管理器)
        
        # 测试预览功能
        test_预览区域(工具)
        test_预览多区域(工具)
        
        # 测试应用配置
        test_应用配置到检测器(管理器)
        
        # 清理
        test_清理(工具)
        
        print('\n' + '=' * 50)
        print('✅ 所有测试通过!')
        print('=' * 50)
        return 0
        
    except Exception as e:
        print(f'\n❌ 测试失败: {e}')
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
