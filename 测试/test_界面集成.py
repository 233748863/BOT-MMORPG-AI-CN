"""
界面集成测试
测试模块管理器的错误降级机制

需求: 10.4 - WHEN 任一新模块出错 THEN 系统 SHALL 降级到基础功能继续运行
"""

import pytest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from 核心.模块管理 import 模块管理器, 模块状态, 获取模块管理器, 重置模块管理器


class Test模块管理器:
    """模块管理器测试类"""
    
    def setup_method(self):
        """每个测试前重置模块管理器"""
        重置模块管理器()
    
    def test_初始化所有模块(self):
        """测试模块管理器能正确初始化所有模块"""
        manager = 获取模块管理器()
        
        # 检查所有模块都已初始化
        状态 = manager.获取所有模块状态()
        assert "智能录制" in 状态
        assert "配置管理" in 状态
        assert "自动调参" in 状态
        
        # 检查模块状态
        for 模块名, 模块状态信息 in 状态.items():
            assert 模块状态信息["存在"] == True
            # 模块应该是正常或禁用状态（取决于依赖是否可用）
            assert 模块状态信息["状态"] in ["normal", "disabled", "degraded"]
    
    def test_模块可用性检查(self):
        """测试模块可用性检查功能"""
        manager = 获取模块管理器()
        
        # 检查智能录制模块
        if manager.智能录制可用:
            assert manager.获取模块实例("智能录制") is not None
        else:
            assert manager.获取模块实例("智能录制") is None

    def test_错误降级机制(self):
        """测试错误降级机制"""
        manager = 模块管理器()
        
        # 模拟错误
        def 会出错的操作():
            raise ValueError("测试错误")
        
        # 执行会出错的操作
        result = manager.安全执行("智能录制", 会出错的操作)
        
        # 应该返回None而不是抛出异常
        assert result is None
        
        # 检查模块状态应该是降级
        状态 = manager.获取模块状态("智能录制")
        assert 状态["状态"] in ["degraded", "disabled"]
        assert 状态["错误次数"] >= 1
    
    def test_连续错误导致禁用(self):
        """测试连续错误导致模块禁用"""
        manager = 模块管理器()
        
        def 会出错的操作():
            raise ValueError("测试错误")
        
        # 连续执行多次错误操作
        for _ in range(manager.MAX_ERROR_COUNT + 1):
            manager.安全执行("智能录制", 会出错的操作)
        
        # 检查模块应该被禁用
        状态 = manager.获取模块状态("智能录制")
        assert 状态["状态"] == "disabled"
    
    def test_模块恢复(self):
        """测试模块恢复功能"""
        manager = 模块管理器()
        
        # 先禁用模块
        manager.禁用模块("智能录制")
        assert not manager.模块可用("智能录制")
        
        # 尝试恢复
        成功 = manager.尝试恢复模块("智能录制")
        
        # 恢复后应该可用（如果依赖可用的话）
        # 注意：恢复是否成功取决于模块依赖是否可用
        状态 = manager.获取模块状态("智能录制")
        assert 状态["错误次数"] == 0
    
    def test_安全执行成功操作(self):
        """测试安全执行成功的操作"""
        manager = 模块管理器()
        
        def 成功的操作():
            return "成功"
        
        result = manager.安全执行("智能录制", 成功的操作)
        
        # 如果模块可用，应该返回结果
        if manager.模块可用("智能录制"):
            assert result == "成功"
    
    def test_手动禁用和启用(self):
        """测试手动禁用和启用模块"""
        manager = 模块管理器()
        
        # 手动禁用
        manager.禁用模块("配置管理")
        assert not manager.模块可用("配置管理")
        
        状态 = manager.获取模块状态("配置管理")
        assert 状态["降级原因"] == "手动禁用"
        
        # 手动启用
        manager.启用模块("配置管理")
        # 启用后状态取决于模块是否能正常初始化


class Test配置集成:
    """配置系统集成测试"""
    
    def test_配置管理模块加载(self):
        """测试配置管理模块能正确加载"""
        try:
            from 配置.设置 import 配置管理可用, 获取配置管理器
            
            if 配置管理可用:
                manager = 获取配置管理器()
                assert manager is not None
        except ImportError:
            pytest.skip("配置管理模块不可用")
    
    def test_配置迁移功能(self):
        """测试配置迁移功能"""
        try:
            from 配置.设置 import 配置管理可用, 迁移旧配置到档案
            
            if not 配置管理可用:
                pytest.skip("配置管理模块不可用")
            
            # 尝试迁移（可能因为档案已存在而失败，这是正常的）
            result = 迁移旧配置到档案("test_migration", "测试游戏")
            # 结果可以是True或False，取决于档案是否已存在
            assert isinstance(result, bool)
        except ImportError:
            pytest.skip("配置管理模块不可用")


class Test决策引擎集成:
    """决策引擎集成测试"""
    
    def test_自动调参集成(self):
        """测试决策引擎的自动调参集成"""
        try:
            from 核心.决策引擎 import 决策引擎, 自动调参可用
            
            # 创建启用自动调参的决策引擎
            engine = 决策引擎(启用自动调参=自动调参可用)
            
            # 检查自动调参状态
            状态 = engine.获取自动调参状态()
            assert "可用" in 状态
            assert "启用" in 状态
        except ImportError as e:
            pytest.skip(f"决策引擎模块不可用: {e}")
    
    def test_记录执行结果(self):
        """测试记录执行结果功能"""
        try:
            from 核心.决策引擎 import 决策引擎
            
            engine = 决策引擎(启用自动调参=True)
            
            # 记录一些执行结果
            engine.记录执行结果(成功=True, 卡住=False)
            engine.记录执行结果(成功=True, 卡住=False)
            engine.记录执行结果(成功=False, 卡住=True)
            
            # 不应该抛出异常
        except ImportError as e:
            pytest.skip(f"决策引擎模块不可用: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
