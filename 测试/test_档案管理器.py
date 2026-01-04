"""
档案管理器测试模块

测试档案管理器的CRUD操作和档案操作功能
需求: 3.3
"""

import os
import json
import pytest
import tempfile
import shutil
from 核心.档案管理 import 档案管理器


class Test档案管理器基础功能:
    """测试档案管理器的基础功能"""
    
    @pytest.fixture
    def 临时目录(self):
        """创建临时测试目录"""
        目录 = tempfile.mkdtemp()
        yield 目录
        # 清理
        if os.path.exists(目录):
            shutil.rmtree(目录)
    
    @pytest.fixture
    def 管理器(self, 临时目录):
        """创建测试用的档案管理器"""
        return 档案管理器(档案目录=临时目录)
    
    def test_初始化创建目录(self, 临时目录):
        """测试初始化时创建档案目录"""
        新目录 = os.path.join(临时目录, "新档案目录")
        管理器 = 档案管理器(档案目录=新目录)
        assert os.path.exists(新目录)
    
    def test_获取空档案列表(self, 管理器):
        """测试获取空档案列表"""
        列表 = 管理器.获取档案列表()
        assert isinstance(列表, list)
        assert len(列表) == 0
    
    def test_档案不存在(self, 管理器):
        """测试检查不存在的档案"""
        assert not 管理器.档案存在("不存在的档案")
    
    def test_获取档案数量(self, 管理器):
        """测试获取档案数量"""
        assert 管理器.获取档案数量() == 0


class Test档案CRUD操作:
    """测试档案的创建、读取、更新、删除操作"""
    
    @pytest.fixture
    def 临时目录(self):
        """创建临时测试目录"""
        目录 = tempfile.mkdtemp()
        yield 目录
        if os.path.exists(目录):
            shutil.rmtree(目录)
    
    @pytest.fixture
    def 管理器(self, 临时目录):
        """创建测试用的档案管理器"""
        return 档案管理器(档案目录=临时目录)
    
    def test_创建档案(self, 管理器):
        """测试创建新档案"""
        配置 = {"测试键": "测试值"}
        结果 = 管理器.创建档案("测试档案", 配置)
        
        assert 结果 is True
        assert 管理器.档案存在("测试档案")
        assert 管理器.获取档案数量() == 1
    
    def test_创建档案_空名称(self, 管理器):
        """测试创建空名称档案应抛出异常"""
        with pytest.raises(ValueError, match="档案名称不能为空"):
            管理器.创建档案("", {})
    
    def test_创建档案_重复名称(self, 管理器):
        """测试创建重复名称档案应抛出异常"""
        管理器.创建档案("测试档案", {})
        
        with pytest.raises(FileExistsError, match="已存在"):
            管理器.创建档案("测试档案", {})
    
    def test_加载档案(self, 管理器):
        """测试加载档案"""
        原始配置 = {"键1": "值1", "键2": 123}
        管理器.创建档案("测试档案", 原始配置)
        
        加载配置 = 管理器.加载档案("测试档案")
        
        assert 加载配置 == 原始配置
    
    def test_加载档案_不存在(self, 管理器):
        """测试加载不存在的档案应抛出异常"""
        with pytest.raises(FileNotFoundError, match="不存在"):
            管理器.加载档案("不存在的档案")
    
    def test_保存档案_更新(self, 管理器):
        """测试保存档案（更新已存在的档案）"""
        管理器.创建档案("测试档案", {"原始": True})
        
        新配置 = {"更新": True, "新键": "新值"}
        管理器.保存档案("测试档案", 新配置)
        
        加载配置 = 管理器.加载档案("测试档案")
        assert 加载配置 == 新配置
    
    def test_删除档案(self, 管理器):
        """测试删除档案"""
        管理器.创建档案("测试档案", {})
        assert 管理器.档案存在("测试档案")
        
        结果 = 管理器.删除档案("测试档案")
        
        assert 结果 is True
        assert not 管理器.档案存在("测试档案")
    
    def test_删除档案_不存在(self, 管理器):
        """测试删除不存在的档案应抛出异常"""
        with pytest.raises(FileNotFoundError, match="不存在"):
            管理器.删除档案("不存在的档案")


class Test档案操作:
    """测试档案的重命名和复制操作"""
    
    @pytest.fixture
    def 临时目录(self):
        """创建临时测试目录"""
        目录 = tempfile.mkdtemp()
        yield 目录
        if os.path.exists(目录):
            shutil.rmtree(目录)
    
    @pytest.fixture
    def 管理器(self, 临时目录):
        """创建测试用的档案管理器"""
        return 档案管理器(档案目录=临时目录)
    
    def test_重命名档案(self, 管理器):
        """测试重命名档案"""
        管理器.创建档案("原名称", {"数据": "测试"})
        
        结果 = 管理器.重命名档案("原名称", "新名称")
        
        assert 结果 is True
        assert not 管理器.档案存在("原名称")
        assert 管理器.档案存在("新名称")
        
        # 验证数据保持不变
        配置 = 管理器.加载档案("新名称")
        assert 配置 == {"数据": "测试"}
    
    def test_重命名档案_源不存在(self, 管理器):
        """测试重命名不存在的档案应抛出异常"""
        with pytest.raises(FileNotFoundError, match="不存在"):
            管理器.重命名档案("不存在", "新名称")
    
    def test_重命名档案_目标已存在(self, 管理器):
        """测试重命名到已存在的名称应抛出异常"""
        管理器.创建档案("档案1", {})
        管理器.创建档案("档案2", {})
        
        with pytest.raises(FileExistsError, match="已存在"):
            管理器.重命名档案("档案1", "档案2")
    
    def test_重命名档案_相同名称(self, 管理器):
        """测试重命名为相同名称应抛出异常"""
        管理器.创建档案("测试档案", {})
        
        with pytest.raises(ValueError, match="相同"):
            管理器.重命名档案("测试档案", "测试档案")
    
    def test_复制档案(self, 管理器):
        """测试复制档案"""
        原始配置 = {"数据": "测试", "数值": 42}
        管理器.创建档案("源档案", 原始配置)
        
        结果 = 管理器.复制档案("源档案", "目标档案")
        
        assert 结果 is True
        assert 管理器.档案存在("源档案")
        assert 管理器.档案存在("目标档案")
        
        # 验证两个档案的配置相同
        源配置 = 管理器.加载档案("源档案")
        目标配置 = 管理器.加载档案("目标档案")
        assert 源配置 == 目标配置 == 原始配置
    
    def test_复制档案_源不存在(self, 管理器):
        """测试复制不存在的档案应抛出异常"""
        with pytest.raises(FileNotFoundError, match="不存在"):
            管理器.复制档案("不存在", "目标档案")
    
    def test_复制档案_目标已存在(self, 管理器):
        """测试复制到已存在的名称应抛出异常"""
        管理器.创建档案("档案1", {})
        管理器.创建档案("档案2", {})
        
        with pytest.raises(FileExistsError, match="已存在"):
            管理器.复制档案("档案1", "档案2")


class Test档案信息查询:
    """测试档案信息查询功能"""
    
    @pytest.fixture
    def 临时目录(self):
        """创建临时测试目录"""
        目录 = tempfile.mkdtemp()
        yield 目录
        if os.path.exists(目录):
            shutil.rmtree(目录)
    
    @pytest.fixture
    def 管理器(self, 临时目录):
        """创建测试用的档案管理器"""
        return 档案管理器(档案目录=临时目录)
    
    def test_获取档案信息(self, 管理器):
        """测试获取档案信息"""
        管理器.创建档案("测试档案", {"数据": "测试"})
        
        信息 = 管理器.获取档案信息("测试档案")
        
        assert 信息["名称"] == "测试档案"
        assert "文件路径" in 信息
        assert "文件大小" in 信息
        assert 信息["文件大小"] > 0
        assert "创建时间" in 信息
        assert "更新时间" in 信息
    
    def test_获取档案信息_不存在(self, 管理器):
        """测试获取不存在档案的信息应抛出异常"""
        with pytest.raises(FileNotFoundError, match="不存在"):
            管理器.获取档案信息("不存在的档案")
    
    def test_获取所有档案信息(self, 管理器):
        """测试获取所有档案信息"""
        管理器.创建档案("档案1", {})
        管理器.创建档案("档案2", {})
        管理器.创建档案("档案3", {})
        
        信息列表 = 管理器.获取所有档案信息()
        
        assert len(信息列表) == 3
        名称列表 = [信息["名称"] for 信息 in 信息列表]
        assert "档案1" in 名称列表
        assert "档案2" in 名称列表
        assert "档案3" in 名称列表


class Test中文档案名:
    """测试中文档案名支持"""
    
    @pytest.fixture
    def 临时目录(self):
        """创建临时测试目录"""
        目录 = tempfile.mkdtemp()
        yield 目录
        if os.path.exists(目录):
            shutil.rmtree(目录)
    
    @pytest.fixture
    def 管理器(self, 临时目录):
        """创建测试用的档案管理器"""
        return 档案管理器(档案目录=临时目录)
    
    def test_中文档案名创建(self, 管理器):
        """测试创建中文名称的档案"""
        管理器.创建档案("游戏配置", {"游戏": "测试游戏"})
        
        assert 管理器.档案存在("游戏配置")
        配置 = 管理器.加载档案("游戏配置")
        assert 配置 == {"游戏": "测试游戏"}
    
    def test_中文档案名重命名(self, 管理器):
        """测试重命名中文名称的档案"""
        管理器.创建档案("原始配置", {})
        管理器.重命名档案("原始配置", "新配置名称")
        
        assert not 管理器.档案存在("原始配置")
        assert 管理器.档案存在("新配置名称")
    
    def test_中文档案名复制(self, 管理器):
        """测试复制中文名称的档案"""
        管理器.创建档案("源配置", {"数据": 123})
        管理器.复制档案("源配置", "配置副本")
        
        assert 管理器.档案存在("源配置")
        assert 管理器.档案存在("配置副本")
