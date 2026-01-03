"""
窗口配置管理器测试
测试配置保存、加载、多配置支持等功能
"""

import os
import tempfile
import pytest
from 核心.窗口检测 import 窗口配置管理器, 窗口信息, 窗口配置项


class Test窗口配置管理器:
    """窗口配置管理器单元测试"""
    
    @pytest.fixture
    def 临时配置文件(self):
        """创建临时配置文件"""
        fd, 路径 = tempfile.mkstemp(suffix='.json')
        os.close(fd)
        yield 路径
        # 清理
        if os.path.exists(路径):
            os.remove(路径)
    
    @pytest.fixture
    def 测试窗口信息(self):
        """创建测试用窗口信息"""
        return 窗口信息(
            句柄=12345,
            标题='测试游戏',
            进程名='test.exe',
            进程ID=1000,
            位置=(100, 200),
            大小=(800, 600)
        )
    
    @pytest.fixture
    def 管理器(self, 临时配置文件):
        """创建配置管理器实例"""
        return 窗口配置管理器(临时配置文件)
    
    def test_创建配置管理器(self, 临时配置文件):
        """测试创建配置管理器"""
        管理器 = 窗口配置管理器(临时配置文件)
        assert 管理器 is not None
        assert 管理器.获取配置数量() == 0
    
    def test_保存配置(self, 管理器, 测试窗口信息):
        """测试保存窗口配置 - 需求 4.1"""
        结果 = 管理器.保存配置('test.exe', 测试窗口信息)
        assert 结果 is True
        assert 管理器.配置是否存在('test.exe')
    
    def test_保存配置带别名和备注(self, 管理器, 测试窗口信息):
        """测试保存配置时添加别名和备注"""
        结果 = 管理器.保存配置(
            'test.exe', 
            测试窗口信息, 
            别名='我的游戏', 
            备注='这是测试备注'
        )
        assert 结果 is True
        
        配置 = 管理器.加载配置('test.exe')
        assert 配置['别名'] == '我的游戏'
        assert 配置['备注'] == '这是测试备注'
    
    def test_加载配置(self, 管理器, 测试窗口信息):
        """测试加载窗口配置 - 需求 4.2"""
        管理器.保存配置('test.exe', 测试窗口信息)
        
        配置 = 管理器.加载配置('test.exe')
        assert 配置 is not None
        assert 配置['标识类型'] == 'process'
        assert 配置['标识值'] == 'test.exe'
        assert 配置['进程名'] == 'test.exe'
        assert 配置['标题'] == '测试游戏'
    
    def test_加载不存在的配置(self, 管理器):
        """测试加载不存在的配置"""
        配置 = 管理器.加载配置('不存在.exe')
        assert 配置 is None
    
    def test_加载默认配置(self, 管理器, 测试窗口信息):
        """测试加载默认配置"""
        管理器.保存配置('test.exe', 测试窗口信息)
        管理器.设置默认('test.exe')
        
        # 不指定标识时加载默认配置
        配置 = 管理器.加载配置()
        assert 配置 is not None
        assert 配置['标识值'] == 'test.exe'
    
    def test_设置默认配置(self, 管理器, 测试窗口信息):
        """测试设置默认配置 - 需求 4.4"""
        管理器.保存配置('test.exe', 测试窗口信息)
        
        结果 = 管理器.设置默认('test.exe')
        assert 结果 is True
        assert 管理器.获取默认配置() == 'test.exe'
    
    def test_设置不存在的配置为默认(self, 管理器):
        """测试设置不存在的配置为默认"""
        结果 = 管理器.设置默认('不存在.exe')
        assert 结果 is False
    
    def test_多配置支持(self, 管理器):
        """测试多配置支持 - 需求 4.3"""
        # 创建多个窗口配置
        窗口1 = 窗口信息(
            句柄=1, 标题='游戏1', 进程名='game1.exe',
            进程ID=100, 位置=(0, 0), 大小=(800, 600)
        )
        窗口2 = 窗口信息(
            句柄=2, 标题='游戏2', 进程名='game2.exe',
            进程ID=200, 位置=(100, 100), 大小=(1024, 768)
        )
        窗口3 = 窗口信息(
            句柄=3, 标题='游戏3', 进程名='game3.exe',
            进程ID=300, 位置=(200, 200), 大小=(1920, 1080)
        )
        
        管理器.保存配置('game1.exe', 窗口1)
        管理器.保存配置('game2.exe', 窗口2)
        管理器.保存配置('game3.exe', 窗口3)
        
        assert 管理器.获取配置数量() == 3
        
        所有配置 = 管理器.获取所有配置()
        assert len(所有配置) == 3
    
    def test_删除配置(self, 管理器, 测试窗口信息):
        """测试删除配置"""
        管理器.保存配置('test.exe', 测试窗口信息)
        assert 管理器.配置是否存在('test.exe')
        
        结果 = 管理器.删除配置('test.exe')
        assert 结果 is True
        assert not 管理器.配置是否存在('test.exe')
    
    def test_删除默认配置时清除默认设置(self, 管理器, 测试窗口信息):
        """测试删除默认配置时自动清除默认设置"""
        管理器.保存配置('test.exe', 测试窗口信息)
        管理器.设置默认('test.exe')
        
        管理器.删除配置('test.exe')
        assert 管理器.获取默认配置() is None
    
    def test_更新配置(self, 管理器, 测试窗口信息):
        """测试更新配置"""
        管理器.保存配置('test.exe', 测试窗口信息)
        
        结果 = 管理器.更新配置('test.exe', {'别名': '新别名', '备注': '新备注'})
        assert 结果 is True
        
        配置 = 管理器.加载配置('test.exe')
        assert 配置['别名'] == '新别名'
        assert 配置['备注'] == '新备注'
    
    def test_按游戏名查找配置(self, 管理器):
        """测试按游戏名查找配置 - 需求 4.3"""
        窗口1 = 窗口信息(
            句柄=1, 标题='王者荣耀', 进程名='wzry.exe',
            进程ID=100, 位置=(0, 0), 大小=(800, 600)
        )
        窗口2 = 窗口信息(
            句柄=2, 标题='和平精英', 进程名='pubg.exe',
            进程ID=200, 位置=(100, 100), 大小=(1024, 768)
        )
        
        管理器.保存配置('wzry.exe', 窗口1, 别名='王者')
        管理器.保存配置('pubg.exe', 窗口2, 别名='吃鸡')
        
        # 按进程名查找
        匹配 = 管理器.按游戏名查找配置('wzry')
        assert len(匹配) == 1
        
        # 按标题查找
        匹配 = 管理器.按游戏名查找配置('荣耀')
        assert len(匹配) == 1
        
        # 按别名查找
        匹配 = 管理器.按游戏名查找配置('王者')
        assert len(匹配) == 1
    
    def test_配置持久化(self, 临时配置文件, 测试窗口信息):
        """测试配置持久化 - 保存后重新加载"""
        # 第一个管理器保存配置
        管理器1 = 窗口配置管理器(临时配置文件)
        管理器1.保存配置('test.exe', 测试窗口信息, 别名='测试')
        管理器1.设置默认('test.exe')
        
        # 创建新的管理器，应该能加载之前保存的配置
        管理器2 = 窗口配置管理器(临时配置文件)
        
        assert 管理器2.配置是否存在('test.exe')
        assert 管理器2.获取默认配置() == 'test.exe'
        
        配置 = 管理器2.加载配置('test.exe')
        assert 配置['别名'] == '测试'
        assert 配置['进程名'] == 'test.exe'
    
    def test_导出导入配置(self, 管理器, 测试窗口信息):
        """测试导出和导入配置"""
        管理器.保存配置('test.exe', 测试窗口信息)
        
        # 导出
        导出路径 = tempfile.mktemp(suffix='.json')
        try:
            结果路径 = 管理器.导出配置(导出路径)
            assert 结果路径 == 导出路径
            assert os.path.exists(导出路径)
            
            # 清空配置
            管理器.清空所有配置()
            assert 管理器.获取配置数量() == 0
            
            # 导入
            结果 = 管理器.导入配置(导出路径)
            assert 结果 is True
            assert 管理器.配置是否存在('test.exe')
        finally:
            if os.path.exists(导出路径):
                os.remove(导出路径)
    
    def test_重命名配置(self, 管理器, 测试窗口信息):
        """测试重命名配置"""
        管理器.保存配置('old.exe', 测试窗口信息)
        管理器.设置默认('old.exe')
        
        结果 = 管理器.重命名配置('old.exe', 'new.exe')
        assert 结果 is True
        
        assert not 管理器.配置是否存在('old.exe')
        assert 管理器.配置是否存在('new.exe')
        assert 管理器.获取默认配置() == 'new.exe'


class Test窗口配置项:
    """窗口配置项数据类测试"""
    
    def test_创建配置项(self):
        """测试创建配置项"""
        配置项 = 窗口配置项(
            标识='test.exe',
            标识类型='process',
            标识值='test.exe',
            上次位置=(100, 200, 800, 600),
            进程名='test.exe',
            标题='测试',
            上次使用='2026-01-03T10:00:00',
            别名='我的游戏',
            备注='测试备注'
        )
        
        assert 配置项.标识 == 'test.exe'
        assert 配置项.别名 == '我的游戏'
    
    def test_配置项转字典(self):
        """测试配置项转换为字典"""
        配置项 = 窗口配置项(
            标识='test.exe',
            标识类型='process',
            标识值='test.exe',
            上次位置=(100, 200, 800, 600),
            进程名='test.exe',
            标题='测试',
            上次使用='2026-01-03T10:00:00'
        )
        
        字典 = 配置项.to_dict()
        assert 字典['标识类型'] == 'process'
        assert 字典['标识值'] == 'test.exe'
    
    def test_从字典创建配置项(self):
        """测试从字典创建配置项"""
        数据 = {
            '标识类型': 'process',
            '标识值': 'test.exe',
            '上次位置': [100, 200, 800, 600],
            '进程名': 'test.exe',
            '标题': '测试',
            '上次使用': '2026-01-03T10:00:00',
            '别名': '我的游戏'
        }
        
        配置项 = 窗口配置项.from_dict('test.exe', 数据)
        assert 配置项.标识 == 'test.exe'
        assert 配置项.别名 == '我的游戏'
        assert 配置项.上次位置 == (100, 200, 800, 600)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
