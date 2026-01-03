"""
检查点管理模块
用于训练过程中的断点续训功能

功能:
- 保存训练检查点
- 加载检查点恢复训练
- 管理检查点数量
- 检查点元数据管理
"""

import os
import json
import hashlib
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
日志 = logging.getLogger(__name__)


@dataclass
class 训练状态:
    """训练状态数据类"""
    模型权重: Dict[str, Any]
    优化器状态: Dict[str, Any]
    当前epoch: int
    当前batch: int
    总epoch: int
    loss历史: List[float] = field(default_factory=list)
    最佳loss: float = float('inf')
    随机种子: Optional[int] = None


@dataclass
class 检查点元数据:
    """检查点元数据"""
    文件路径: str
    创建时间: str  # ISO格式字符串
    epoch: int
    batch: int
    loss值: float
    文件大小: int  # 字节
    校验和: str = ""  # MD5校验和
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, 数据: dict) -> '检查点元数据':
        """从字典创建"""
        return cls(**数据)


class 检查点管理器:
    """管理训练检查点的保存和加载"""
    
    版本号 = "1.0"
    元数据文件名 = "metadata.json"
    最新检查点链接名 = "checkpoint_latest"
    
    def __init__(self, 保存目录: str, 最大检查点数: int = 5):
        """
        初始化检查点管理器
        
        参数:
            保存目录: 检查点保存目录
            最大检查点数: 保留的最大检查点数量
        """
        self.保存目录 = 保存目录
        self.最大检查点数 = max(1, 最大检查点数)  # 至少保留1个
        self._元数据缓存: List[检查点元数据] = []
        
        # 确保目录存在
        os.makedirs(保存目录, exist_ok=True)
        
        # 加载现有元数据
        self._加载元数据()
    
    def _生成检查点文件名(self, epoch: int, batch: int) -> str:
        """生成检查点文件名"""
        return f"checkpoint_epoch_{epoch:03d}_batch_{batch:04d}.pt"
    
    def _计算校验和(self, 文件路径: str) -> str:
        """计算文件MD5校验和"""
        try:
            md5 = hashlib.md5()
            with open(文件路径, 'rb') as f:
                for 块 in iter(lambda: f.read(8192), b''):
                    md5.update(块)
            return md5.hexdigest()
        except Exception as e:
            日志.warning(f"计算校验和失败: {e}")
            return ""
    
    def _验证校验和(self, 文件路径: str, 期望校验和: str) -> bool:
        """验证文件校验和"""
        if not 期望校验和:
            return True  # 没有校验和则跳过验证
        实际校验和 = self._计算校验和(文件路径)
        return 实际校验和 == 期望校验和
    
    def _加载元数据(self):
        """从文件加载元数据"""
        元数据路径 = os.path.join(self.保存目录, self.元数据文件名)
        
        if os.path.exists(元数据路径):
            try:
                with open(元数据路径, 'r', encoding='utf-8') as f:
                    数据 = json.load(f)
                self._元数据缓存 = [
                    检查点元数据.from_dict(项) for 项 in 数据.get('检查点列表', [])
                ]
                日志.info(f"已加载 {len(self._元数据缓存)} 个检查点元数据")
            except Exception as e:
                日志.warning(f"加载元数据失败: {e}")
                self._元数据缓存 = []
        else:
            self._元数据缓存 = []
    
    def _保存元数据(self):
        """保存元数据到文件"""
        元数据路径 = os.path.join(self.保存目录, self.元数据文件名)
        
        数据 = {
            '版本': self.版本号,
            '更新时间': datetime.now().isoformat(),
            '检查点列表': [项.to_dict() for 项 in self._元数据缓存]
        }
        
        try:
            with open(元数据路径, 'w', encoding='utf-8') as f:
                json.dump(数据, f, ensure_ascii=False, indent=2)
        except Exception as e:
            日志.error(f"保存元数据失败: {e}")

    def 保存检查点(self, 模型, 优化器状态: dict, 
                   当前epoch: int, 当前batch: int,
                   loss值: float, 
                   额外数据: dict = None) -> str:
        """
        保存训练检查点
        
        参数:
            模型: 训练模型对象
            优化器状态: 优化器状态字典
            当前epoch: 当前训练轮次
            当前batch: 当前批次
            loss值: 当前loss值
            额外数据: 额外需要保存的数据
        
        返回:
            检查点文件路径
        """
        # 延迟导入，避免循环依赖
        try:
            import pickle
        except ImportError:
            日志.error("无法导入pickle模块")
            raise
        
        # 生成文件名和路径
        文件名 = self._生成检查点文件名(当前epoch, 当前batch)
        文件路径 = os.path.join(self.保存目录, 文件名)
        
        # 构建检查点数据
        检查点数据 = {
            "版本": self.版本号,
            "模型权重": self._获取模型权重(模型),
            "优化器状态": 优化器状态,
            "训练进度": {
                "当前epoch": 当前epoch,
                "当前batch": 当前batch,
            },
            "指标": {
                "loss": loss值,
            },
            "元数据": {
                "创建时间": datetime.now().isoformat(),
            }
        }
        
        # 添加额外数据
        if 额外数据:
            检查点数据["额外数据"] = 额外数据
        
        # 保存检查点文件
        try:
            with open(文件路径, 'wb') as f:
                pickle.dump(检查点数据, f)
            日志.info(f"检查点已保存: {文件路径}")
        except Exception as e:
            日志.error(f"保存检查点失败: {e}")
            raise
        
        # 获取文件大小和校验和
        文件大小 = os.path.getsize(文件路径)
        校验和 = self._计算校验和(文件路径)
        
        # 创建元数据
        新元数据 = 检查点元数据(
            文件路径=文件路径,
            创建时间=datetime.now().isoformat(),
            epoch=当前epoch,
            batch=当前batch,
            loss值=loss值,
            文件大小=文件大小,
            校验和=校验和
        )
        
        # 更新元数据缓存
        self._元数据缓存.append(新元数据)
        self._保存元数据()
        
        # 更新最新检查点链接
        self._更新最新链接(文件路径)
        
        # 清理旧检查点
        self.删除旧检查点()
        
        return 文件路径
    
    def _获取模型权重(self, 模型) -> dict:
        """获取模型权重，支持多种模型类型"""
        # TFLearn模型
        if hasattr(模型, 'get_weights'):
            return {'类型': 'tflearn', '权重': 模型.get_weights()}
        # PyTorch模型
        elif hasattr(模型, 'state_dict'):
            return {'类型': 'pytorch', '权重': 模型.state_dict()}
        # 其他情况，尝试直接保存
        else:
            return {'类型': 'unknown', '模型对象': 模型}
    
    def _更新最新链接(self, 目标路径: str):
        """更新指向最新检查点的链接文件"""
        链接路径 = os.path.join(self.保存目录, self.最新检查点链接名)
        
        try:
            # 保存最新检查点路径到文件
            with open(链接路径, 'w', encoding='utf-8') as f:
                f.write(目标路径)
        except Exception as e:
            日志.warning(f"更新最新链接失败: {e}")
    
    def _获取最新检查点路径(self) -> Optional[str]:
        """获取最新检查点的路径"""
        链接路径 = os.path.join(self.保存目录, self.最新检查点链接名)
        
        if os.path.exists(链接路径):
            try:
                with open(链接路径, 'r', encoding='utf-8') as f:
                    路径 = f.read().strip()
                if os.path.exists(路径):
                    return 路径
            except Exception:
                pass
        
        # 如果链接文件不存在或无效，从元数据获取最新的
        if self._元数据缓存:
            # 按epoch和batch排序，获取最新的
            排序后 = sorted(
                self._元数据缓存,
                key=lambda x: (x.epoch, x.batch),
                reverse=True
            )
            for 元数据 in 排序后:
                if os.path.exists(元数据.文件路径):
                    return 元数据.文件路径
        
        return None

    def 加载检查点(self, 检查点路径: str = None) -> Optional[dict]:
        """
        加载检查点
        
        参数:
            检查点路径: 指定检查点路径，None 则加载最新
            
        返回:
            检查点数据字典，加载失败返回 None
        """
        import pickle
        
        # 确定要加载的检查点路径
        if 检查点路径 is None:
            检查点路径 = self._获取最新检查点路径()
        
        if 检查点路径 is None or not os.path.exists(检查点路径):
            日志.warning("未找到可用的检查点")
            return None
        
        # 验证校验和
        元数据 = self._查找元数据(检查点路径)
        if 元数据 and 元数据.校验和:
            if not self._验证校验和(检查点路径, 元数据.校验和):
                日志.error(f"检查点文件损坏: {检查点路径}")
                # 尝试加载上一个检查点
                return self._尝试加载备用检查点(检查点路径)
        
        # 加载检查点
        try:
            with open(检查点路径, 'rb') as f:
                检查点数据 = pickle.load(f)
            日志.info(f"检查点已加载: {检查点路径}")
            return 检查点数据
        except Exception as e:
            日志.error(f"加载检查点失败: {e}")
            return self._尝试加载备用检查点(检查点路径)
    
    def _查找元数据(self, 文件路径: str) -> Optional[检查点元数据]:
        """根据文件路径查找元数据"""
        for 元数据 in self._元数据缓存:
            if 元数据.文件路径 == 文件路径:
                return 元数据
        return None
    
    def _尝试加载备用检查点(self, 排除路径: str) -> Optional[dict]:
        """尝试加载备用检查点（排除指定路径）"""
        日志.info("尝试加载备用检查点...")
        
        # 按时间排序，获取可用的检查点
        可用检查点 = [
            元数据 for 元数据 in self._元数据缓存
            if 元数据.文件路径 != 排除路径 and os.path.exists(元数据.文件路径)
        ]
        
        if not 可用检查点:
            日志.warning("没有可用的备用检查点")
            return None
        
        # 按epoch和batch排序
        可用检查点.sort(key=lambda x: (x.epoch, x.batch), reverse=True)
        
        # 尝试加载
        for 元数据 in 可用检查点:
            try:
                import pickle
                with open(元数据.文件路径, 'rb') as f:
                    检查点数据 = pickle.load(f)
                日志.info(f"已加载备用检查点: {元数据.文件路径}")
                return 检查点数据
            except Exception as e:
                日志.warning(f"加载备用检查点失败: {元数据.文件路径}, 错误: {e}")
                continue
        
        return None
    
    def 列出检查点(self) -> List[dict]:
        """
        列出所有可用检查点及其元数据
        
        返回:
            检查点信息列表，按时间倒序排列
        """
        # 刷新元数据（检查文件是否存在）
        有效检查点 = []
        
        for 元数据 in self._元数据缓存:
            if os.path.exists(元数据.文件路径):
                有效检查点.append({
                    '文件路径': 元数据.文件路径,
                    '创建时间': 元数据.创建时间,
                    'epoch': 元数据.epoch,
                    'batch': 元数据.batch,
                    'loss': 元数据.loss值,
                    '文件大小': 元数据.文件大小,
                    '文件大小_可读': self._格式化文件大小(元数据.文件大小)
                })
        
        # 按epoch和batch倒序排列
        有效检查点.sort(key=lambda x: (x['epoch'], x['batch']), reverse=True)
        
        return 有效检查点
    
    def _格式化文件大小(self, 字节数: int) -> str:
        """格式化文件大小为可读字符串"""
        for 单位 in ['B', 'KB', 'MB', 'GB']:
            if 字节数 < 1024:
                return f"{字节数:.1f} {单位}"
            字节数 /= 1024
        return f"{字节数:.1f} TB"
    
    def 删除旧检查点(self) -> int:
        """
        删除超出数量限制的旧检查点
        
        返回:
            删除的检查点数量
        """
        # 按epoch和batch排序
        self._元数据缓存.sort(key=lambda x: (x.epoch, x.batch), reverse=True)
        
        删除数量 = 0
        
        # 保留最新的N个检查点
        while len(self._元数据缓存) > self.最大检查点数:
            旧检查点 = self._元数据缓存.pop()  # 移除最旧的
            
            # 删除文件
            if os.path.exists(旧检查点.文件路径):
                try:
                    os.remove(旧检查点.文件路径)
                    日志.info(f"已删除旧检查点: {旧检查点.文件路径}")
                    删除数量 += 1
                except Exception as e:
                    日志.warning(f"删除检查点失败: {旧检查点.文件路径}, 错误: {e}")
        
        # 保存更新后的元数据
        if 删除数量 > 0:
            self._保存元数据()
        
        return 删除数量
    
    def 检查点存在(self) -> bool:
        """检查是否存在可用的检查点"""
        return self._获取最新检查点路径() is not None
    
    def 获取最新检查点信息(self) -> Optional[dict]:
        """获取最新检查点的信息"""
        检查点列表 = self.列出检查点()
        return 检查点列表[0] if 检查点列表 else None
    
    def 清空所有检查点(self):
        """清空所有检查点（谨慎使用）"""
        for 元数据 in self._元数据缓存:
            if os.path.exists(元数据.文件路径):
                try:
                    os.remove(元数据.文件路径)
                except Exception as e:
                    日志.warning(f"删除检查点失败: {元数据.文件路径}, 错误: {e}")
        
        self._元数据缓存 = []
        self._保存元数据()
        
        # 删除最新链接文件
        链接路径 = os.path.join(self.保存目录, self.最新检查点链接名)
        if os.path.exists(链接路径):
            os.remove(链接路径)
        
        日志.info("已清空所有检查点")



class 检查点损坏错误(Exception):
    """检查点文件损坏异常"""
    pass


class 模型不匹配错误(Exception):
    """模型结构不匹配异常"""
    pass


def 恢复训练状态(模型, 检查点数据: dict) -> dict:
    """
    从检查点恢复训练状态
    
    参数:
        模型: 训练模型对象
        检查点数据: 检查点数据字典
    
    返回:
        恢复信息字典，包含恢复的epoch和batch
    
    异常:
        模型不匹配错误: 当模型结构与检查点不匹配时
    """
    if 检查点数据 is None:
        raise ValueError("检查点数据为空")
    
    # 恢复模型权重
    模型权重 = 检查点数据.get('模型权重', {})
    权重类型 = 模型权重.get('类型', 'unknown')
    
    try:
        if 权重类型 == 'tflearn':
            if hasattr(模型, 'set_weights'):
                模型.set_weights(模型权重['权重'])
            else:
                日志.warning("模型不支持 set_weights 方法，尝试使用 load")
        elif 权重类型 == 'pytorch':
            if hasattr(模型, 'load_state_dict'):
                模型.load_state_dict(模型权重['权重'])
            else:
                raise 模型不匹配错误("模型不支持 PyTorch 的 load_state_dict 方法")
        else:
            日志.warning(f"未知的权重类型: {权重类型}")
    except Exception as e:
        raise 模型不匹配错误(f"恢复模型权重失败: {e}")
    
    # 提取训练进度
    训练进度 = 检查点数据.get('训练进度', {})
    
    恢复信息 = {
        '当前epoch': 训练进度.get('当前epoch', 0),
        '当前batch': 训练进度.get('当前batch', 0),
        '优化器状态': 检查点数据.get('优化器状态', {}),
        'loss': 检查点数据.get('指标', {}).get('loss', None),
        '额外数据': 检查点数据.get('额外数据', {})
    }
    
    日志.info(f"训练状态已恢复: epoch={恢复信息['当前epoch']}, batch={恢复信息['当前batch']}")
    
    return 恢复信息


def 提示恢复训练(管理器: 检查点管理器) -> bool:
    """
    提示用户是否恢复训练
    
    参数:
        管理器: 检查点管理器实例
    
    返回:
        True 表示用户选择恢复，False 表示重新开始
    """
    if not 管理器.检查点存在():
        return False
    
    最新信息 = 管理器.获取最新检查点信息()
    
    if 最新信息:
        print("\n" + "=" * 50)
        print("🔄 发现训练检查点")
        print("=" * 50)
        print(f"  创建时间: {最新信息['创建时间']}")
        print(f"  训练进度: Epoch {最新信息['epoch']}, Batch {最新信息['batch']}")
        print(f"  Loss: {最新信息['loss']:.4f}" if 最新信息['loss'] else "  Loss: N/A")
        print(f"  文件大小: {最新信息['文件大小_可读']}")
        print()
        
        while True:
            选择 = input("是否从检查点恢复训练? (y=恢复/n=重新开始): ").strip().lower()
            if 选择 in ['y', 'yes', '是']:
                return True
            elif 选择 in ['n', 'no', '否']:
                return False
            else:
                print("请输入 y 或 n")
    
    return False


def 显示检查点列表(管理器: 检查点管理器):
    """显示所有可用检查点"""
    检查点列表 = 管理器.列出检查点()
    
    if not 检查点列表:
        print("没有可用的检查点")
        return
    
    print("\n可用检查点:")
    print("-" * 70)
    print(f"{'序号':<4} {'Epoch':<6} {'Batch':<6} {'Loss':<10} {'大小':<10} {'创建时间'}")
    print("-" * 70)
    
    for i, 检查点 in enumerate(检查点列表, 1):
        loss_str = f"{检查点['loss']:.4f}" if 检查点['loss'] else "N/A"
        时间 = 检查点['创建时间'][:19].replace('T', ' ')
        print(f"{i:<4} {检查点['epoch']:<6} {检查点['batch']:<6} {loss_str:<10} {检查点['文件大小_可读']:<10} {时间}")
    
    print("-" * 70)
