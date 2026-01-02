"""
配置导入导出功能测试
测试 ConfigManager 的 export_profile 和 import_profile 方法
"""

import sys
import os
import tempfile
import shutil

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from 核心.配置管理 import ConfigManager, GameProfile


def test_export_import_basic():
    """测试基本的导出导入功能"""
    test_dir = tempfile.mkdtemp()
    profiles_dir = os.path.join(test_dir, 'profiles')
    export_dir = os.path.join(test_dir, 'exports')
    
    try:
        manager = ConfigManager(profiles_dir=profiles_dir)
        
        # 创建并保存一个测试档案
        profile = manager.create_profile('测试档案', '测试游戏')
        manager.save_profile(profile)
        
        # 测试导出功能
        export_path = os.path.join(export_dir, 'exported_profile.json')
        result = manager.export_profile('测试档案', export_path)
        assert result == True, '导出应该返回True'
        assert os.path.exists(export_path), '导出文件应该存在'
        
        # 测试导入功能 - 使用原名称
        imported_profile = manager.import_profile(export_path)
        assert imported_profile.name == '测试档案'
        assert imported_profile.game_name == '测试游戏'
        
        # 测试导入功能 - 使用新名称
        imported_profile2 = manager.import_profile(export_path, new_name='新档案名')
        assert imported_profile2.name == '新档案名'
        
        print('test_export_import_basic: PASSED')
        
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_round_trip():
    """测试Round-Trip: 导出后再导入应该得到等价的数据"""
    test_dir = tempfile.mkdtemp()
    profiles_dir = os.path.join(test_dir, 'profiles')
    
    try:
        manager = ConfigManager(profiles_dir=profiles_dir)
        
        # 创建并保存档案
        profile = manager.create_profile('测试档案', '测试游戏')
        manager.save_profile(profile)
        
        # 导出
        export_path = os.path.join(test_dir, 'export.json')
        manager.export_profile('测试档案', export_path)
        
        # 导入
        imported_profile = manager.import_profile(export_path)
        
        # 比较关键字段
        original_dict = profile.to_dict()
        imported_dict = imported_profile.to_dict()
        
        for key in ['name', 'game_name', 'window_config', 'key_mapping', 
                    'ui_regions', 'detection_params', 'decision_rules']:
            assert original_dict[key] == imported_dict[key], f'{key} 不匹配'
        
        print('test_round_trip: PASSED')
        
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_export_errors():
    """测试导出错误处理"""
    test_dir = tempfile.mkdtemp()
    profiles_dir = os.path.join(test_dir, 'profiles')
    
    try:
        manager = ConfigManager(profiles_dir=profiles_dir)
        
        # 导出不存在的档案
        try:
            manager.export_profile('不存在的档案', 'test.json')
            assert False, '应该抛出FileNotFoundError'
        except FileNotFoundError:
            pass
        
        # 导出空名称
        try:
            manager.export_profile('', 'test.json')
            assert False, '应该抛出ValueError'
        except ValueError:
            pass
        
        # 导出空路径
        profile = manager.create_profile('测试', '游戏')
        manager.save_profile(profile)
        try:
            manager.export_profile('测试', '')
            assert False, '应该抛出ValueError'
        except ValueError:
            pass
        
        print('test_export_errors: PASSED')
        
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_import_errors():
    """测试导入错误处理"""
    test_dir = tempfile.mkdtemp()
    profiles_dir = os.path.join(test_dir, 'profiles')
    
    try:
        manager = ConfigManager(profiles_dir=profiles_dir)
        
        # 导入不存在的文件
        try:
            manager.import_profile('不存在的文件.json')
            assert False, '应该抛出FileNotFoundError'
        except FileNotFoundError:
            pass
        
        # 导入空路径
        try:
            manager.import_profile('')
            assert False, '应该抛出ValueError'
        except ValueError:
            pass
        
        # 导入无效JSON文件
        invalid_json_path = os.path.join(test_dir, 'invalid.json')
        with open(invalid_json_path, 'w') as f:
            f.write('这不是有效的JSON')
        try:
            manager.import_profile(invalid_json_path)
            assert False, '应该抛出ValueError'
        except ValueError:
            pass
        
        # 导入缺少必要字段的JSON
        incomplete_json_path = os.path.join(test_dir, 'incomplete.json')
        with open(incomplete_json_path, 'w', encoding='utf-8') as f:
            f.write('{"some_field": "value"}')
        try:
            manager.import_profile(incomplete_json_path)
            assert False, '应该抛出ValueError'
        except ValueError:
            pass
        
        print('test_import_errors: PASSED')
        
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


if __name__ == '__main__':
    test_export_import_basic()
    test_round_trip()
    test_export_errors()
    test_import_errors()
    print('\n所有测试通过！')
