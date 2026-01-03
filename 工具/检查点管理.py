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
        """
        获取训练进度最新的检查点路径
        
        "最新"定义为 epoch 和 batch 最大的检查点，而不是最后保存的检查点。
        这确保了即使乱序保存检查点，也能正确返回训练进度最新的检查点。
        """
        # 始终从元数据获取训练进度最新的检查点（按 epoch, batch 排序）
        if self._元数据缓存:
            # 按 epoch 和 batch 排序，获取训练进度最新的
            排序后 = sorted(
                self._元数据缓存,
                key=lambda x: (x.epoch, x.batch),
                reverse=True
            )
            for 元数据 in 排序后:
                if os.path.exists(元数据.文件路径):
                    return 元数据.文件路径
        
        # 如果元数据缓存为空，尝试从链接文件获取（兼容旧版本）
        链接路径 = os.path.join(self.保存目录, self.最新检查点链接名)
        if os.path.exists(链接路径):
            try:
                with open(链接路径, 'r', encoding='utf-8') as f:
                    路径 = f.read().strip()
                if os.path.exists(路径):
                    return 路径
            except Exception:
                pass
        
        return None

    def 加载检查点(self, 检查点路径: str = None, 
                   epoch: int = None, 
                   时间戳: str = None) -> Optional[dict]:
        """
        加载检查点
        
        参数:
            检查点路径: 指定检查点路径，None 则根据其他参数或加载最新
            epoch: 指定要加载的 epoch 编号
            时间戳: 指定要加载的时间戳（ISO格式字符串）
            
        返回:
            检查点数据字典，加载失败返回 None
            
        说明:
            - 如果指定了检查点路径，直接加载该路径
            - 如果指定了 epoch，加载该 epoch 的最新检查点
            - 如果指定了时间戳，加载最接近该时间戳的检查点
            - 如果都未指定，加载最新的检查点
        """
        import pickle
        
        # 确定要加载的检查点路径
        if 检查点路径 is None:
            if epoch is not None:
                检查点路径 = self._按epoch查找检查点(epoch)
            elif 时间戳 is not None:
                检查点路径 = self._按时间戳查找检查点(时间戳)
            else:
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
    
    def _按epoch查找检查点(self, 目标epoch: int) -> Optional[str]:
        """
        按 epoch 编号查找检查点
        
        参数:
            目标epoch: 要查找的 epoch 编号
            
        返回:
            检查点文件路径，未找到返回 None
        """
        # 筛选指定 epoch 的检查点
        匹配的检查点 = [
            元数据 for 元数据 in self._元数据缓存
            if 元数据.epoch == 目标epoch and os.path.exists(元数据.文件路径)
        ]
        
        if not 匹配的检查点:
            日志.warning(f"未找到 epoch {目标epoch} 的检查点")
            return None
        
        # 如果同一 epoch 有多个检查点，返回 batch 最大的（最新的）
        匹配的检查点.sort(key=lambda x: x.batch, reverse=True)
        return 匹配的检查点[0].文件路径
    
    def _按时间戳查找检查点(self, 目标时间戳: str) -> Optional[str]:
        """
        按时间戳查找最接近的检查点
        
        参数:
            目标时间戳: ISO格式的时间戳字符串
            
        返回:
            检查点文件路径，未找到返回 None
        """
        from datetime import datetime
        
        try:
            # 解析目标时间戳
            目标时间 = datetime.fromisoformat(目标时间戳)
        except ValueError as e:
            日志.error(f"无效的时间戳格式: {目标时间戳}, 错误: {e}")
            return None
        
        # 筛选有效的检查点
        有效检查点 = [
            元数据 for 元数据 in self._元数据缓存
            if os.path.exists(元数据.文件路径)
        ]
        
        if not 有效检查点:
            日志.warning("没有可用的检查点")
            return None
        
        # 计算每个检查点与目标时间的差距
        def 计算时间差(元数据):
            try:
                检查点时间 = datetime.fromisoformat(元数据.创建时间)
                return abs((检查点时间 - 目标时间).total_seconds())
            except ValueError:
                return float('inf')
        
        # 找到最接近的检查点
        最接近的 = min(有效检查点, key=计算时间差)
        return 最接近的.文件路径
    
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
    
    def 验证检查点(self, 检查点路径: str) -> '检查点验证结果':
        """
        验证检查点文件完整性
        
        参数:
            检查点路径: 检查点文件路径
            
        返回:
            检查点验证结果对象
        """
        # 检查文件是否存在
        if not os.path.exists(检查点路径):
            return 检查点验证结果(
                有效=False,
                错误类型="文件不存在",
                错误消息=f"检查点文件不存在: {检查点路径}"
            )
        
        # 检查文件大小
        try:
            文件大小 = os.path.getsize(检查点路径)
            if 文件大小 == 0:
                return 检查点验证结果(
                    有效=False,
                    错误类型="文件为空",
                    错误消息=f"检查点文件为空: {检查点路径}"
                )
        except OSError as e:
            return 检查点验证结果(
                有效=False,
                错误类型="文件访问错误",
                错误消息=f"无法访问检查点文件: {e}"
            )
        
        # 验证校验和
        元数据 = self._查找元数据(检查点路径)
        if 元数据 and 元数据.校验和:
            if not self._验证校验和(检查点路径, 元数据.校验和):
                return 检查点验证结果(
                    有效=False,
                    错误类型="校验和不匹配",
                    错误消息=f"检查点文件校验和不匹配，文件可能已损坏: {检查点路径}"
                )
        
        # 尝试加载检查点数据验证格式
        try:
            import pickle
            with open(检查点路径, 'rb') as f:
                检查点数据 = pickle.load(f)
            
            # 验证必需字段
            必需字段 = ['版本', '模型权重', '优化器状态', '训练进度', '指标', '元数据']
            缺失字段 = [字段 for 字段 in 必需字段 if 字段 not in 检查点数据]
            
            if 缺失字段:
                return 检查点验证结果(
                    有效=False,
                    错误类型="数据格式错误",
                    错误消息=f"检查点缺少必需字段: {', '.join(缺失字段)}"
                )
            
            # 验证训练进度字段
            训练进度 = 检查点数据.get('训练进度', {})
            if '当前epoch' not in 训练进度 or '当前batch' not in 训练进度:
                return 检查点验证结果(
                    有效=False,
                    错误类型="训练进度不完整",
                    错误消息="检查点训练进度缺少 epoch 或 batch 信息"
                )
            
        except pickle.UnpicklingError as e:
            return 检查点验证结果(
                有效=False,
                错误类型="反序列化错误",
                错误消息=f"检查点文件无法反序列化，可能已损坏: {e}"
            )
        except Exception as e:
            return 检查点验证结果(
                有效=False,
                错误类型="未知错误",
                错误消息=f"验证检查点时发生错误: {e}"
            )
        
        return 检查点验证结果(有效=True)
    
    def 获取建议检查点(self, 排除路径: str = None) -> Optional[str]:
        """
        获取建议使用的备用检查点路径
        
        参数:
            排除路径: 要排除的检查点路径（通常是损坏的检查点）
            
        返回:
            建议的检查点路径，如果没有可用的返回 None
        """
        # 按 epoch 和 batch 排序，获取可用的检查点
        可用检查点 = [
            元数据 for 元数据 in self._元数据缓存
            if 元数据.文件路径 != 排除路径 and os.path.exists(元数据.文件路径)
        ]
        
        if not 可用检查点:
            return None
        
        # 按 epoch 和 batch 倒序排序
        可用检查点.sort(key=lambda x: (x.epoch, x.batch), reverse=True)
        
        # 验证每个检查点，返回第一个有效的
        for 元数据 in 可用检查点:
            验证结果 = self.验证检查点(元数据.文件路径)
            if 验证结果.有效:
                return 元数据.文件路径
        
        return None
    
    def 安全加载检查点(self, 检查点路径: str = None,
                       epoch: int = None,
                       时间戳: str = None,
                       抛出异常: bool = False) -> Optional[dict]:
        """
        安全加载检查点，带完整的损坏检测和处理
        
        参数:
            检查点路径: 指定检查点路径，None 则根据其他参数或加载最新
            epoch: 指定要加载的 epoch 编号
            时间戳: 指定要加载的时间戳（ISO格式字符串）
            抛出异常: 如果为 True，损坏时抛出异常而不是返回 None
            
        返回:
            检查点数据字典，加载失败返回 None
            
        异常:
            检查点损坏错误: 当检查点损坏且 抛出异常=True 时
        """
        import pickle
        
        # 确定要加载的检查点路径
        if 检查点路径 is None:
            if epoch is not None:
                检查点路径 = self._按epoch查找检查点(epoch)
            elif 时间戳 is not None:
                检查点路径 = self._按时间戳查找检查点(时间戳)
            else:
                检查点路径 = self._获取最新检查点路径()
        
        if 检查点路径 is None:
            日志.warning("未找到可用的检查点")
            return None
        
        # 验证检查点完整性
        验证结果 = self.验证检查点(检查点路径)
        
        if not 验证结果.有效:
            日志.error(f"检查点验证失败: {验证结果.错误消息}")
            
            # 获取建议的备用检查点
            建议路径 = self.获取建议检查点(排除路径=检查点路径)
            
            if 抛出异常:
                raise 检查点损坏错误(
                    消息=验证结果.错误消息,
                    损坏路径=检查点路径,
                    建议检查点=建议路径
                )
            
            # 尝试加载备用检查点
            if 建议路径:
                日志.info(f"尝试加载备用检查点: {建议路径}")
                return self.安全加载检查点(检查点路径=建议路径, 抛出异常=抛出异常)
            
            return None
        
        # 加载检查点
        try:
            with open(检查点路径, 'rb') as f:
                检查点数据 = pickle.load(f)
            日志.info(f"检查点已安全加载: {检查点路径}")
            return 检查点数据
        except Exception as e:
            日志.error(f"加载检查点失败: {e}")
            
            建议路径 = self.获取建议检查点(排除路径=检查点路径)
            
            if 抛出异常:
                raise 检查点损坏错误(
                    消息=f"加载检查点失败: {e}",
                    损坏路径=检查点路径,
                    建议检查点=建议路径
                )
            
            if 建议路径:
                日志.info(f"尝试加载备用检查点: {建议路径}")
                return self.安全加载检查点(检查点路径=建议路径, 抛出异常=抛出异常)
            
            return None



class 检查点损坏错误(Exception):
    """检查点文件损坏异常"""
    
    def __init__(self, 消息: str, 损坏路径: str = None, 建议检查点: str = None):
        """
        初始化检查点损坏错误
        
        参数:
            消息: 错误消息
            损坏路径: 损坏的检查点文件路径
            建议检查点: 建议使用的备用检查点路径
        """
        super().__init__(消息)
        self.损坏路径 = 损坏路径
        self.建议检查点 = 建议检查点
    
    def __str__(self):
        基本消息 = super().__str__()
        if self.建议检查点:
            return f"{基本消息}\n建议使用更早的检查点: {self.建议检查点}"
        return 基本消息


class 模型不匹配错误(Exception):
    """模型结构不匹配异常"""
    pass


class 检查点验证结果:
    """检查点验证结果"""
    
    def __init__(self, 有效: bool, 错误类型: str = None, 错误消息: str = None):
        """
        初始化验证结果
        
        参数:
            有效: 检查点是否有效
            错误类型: 错误类型（如果无效）
            错误消息: 错误消息（如果无效）
        """
        self.有效 = 有效
        self.错误类型 = 错误类型
        self.错误消息 = 错误消息
    
    def __bool__(self):
        return self.有效


def 恢复训练状态(模型, 检查点数据: dict) -> dict:
    """
    从检查点恢复训练状态
    
    参数:
        模型: 训练模型对象
        检查点数据: 检查点数据字典
    
    返回:
        恢复信息字典，包含恢复的epoch和batch，以及下一个batch信息
    
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


def 计算恢复起点(检查点数据: dict, 每epoch批次数: int = None) -> dict:
    """
    计算训练恢复的起点，确保从中断处的下一个 batch 继续
    
    参数:
        检查点数据: 检查点数据字典
        每epoch批次数: 每个 epoch 的批次数（用于判断是否需要进入下一个 epoch）
    
    返回:
        恢复起点信息字典，包含:
        - 起始epoch: 恢复训练应从哪个 epoch 开始
        - 起始batch: 恢复训练应从哪个 batch 开始
        - 中断epoch: 中断时的 epoch
        - 中断batch: 中断时的 batch
        - 是否新epoch: 是否需要从新的 epoch 开始
    """
    if 检查点数据 is None:
        raise ValueError("检查点数据为空")
    
    训练进度 = 检查点数据.get('训练进度', {})
    中断epoch = 训练进度.get('当前epoch', 0)
    中断batch = 训练进度.get('当前batch', 0)
    
    # 计算下一个 batch
    下一batch = 中断batch + 1
    起始epoch = 中断epoch
    是否新epoch = False
    
    # 如果提供了每 epoch 批次数，检查是否需要进入下一个 epoch
    if 每epoch批次数 is not None and 下一batch >= 每epoch批次数:
        起始epoch = 中断epoch + 1
        下一batch = 0
        是否新epoch = True
    
    恢复起点 = {
        '起始epoch': 起始epoch,
        '起始batch': 下一batch,
        '中断epoch': 中断epoch,
        '中断batch': 中断batch,
        '是否新epoch': 是否新epoch
    }
    
    日志.info(f"计算恢复起点: 从 epoch={起始epoch}, batch={下一batch} 继续 "
              f"(中断于 epoch={中断epoch}, batch={中断batch})")
    
    return 恢复起点


class 训练恢复器:
    """
    训练恢复器，封装训练恢复的完整流程
    
    确保训练从中断处的下一个 batch 继续，保证训练连续性
    """
    
    def __init__(self, 管理器: 检查点管理器):
        """
        初始化训练恢复器
        
        参数:
            管理器: 检查点管理器实例
        """
        self.管理器 = 管理器
        self._恢复信息 = None
        self._恢复起点 = None
    
    def 恢复(self, 模型, 检查点路径: str = None, 
             每epoch批次数: int = None) -> Optional[dict]:
        """
        执行完整的训练恢复流程
        
        参数:
            模型: 训练模型对象
            检查点路径: 指定检查点路径，None 则加载最新
            每epoch批次数: 每个 epoch 的批次数
        
        返回:
            恢复结果字典，包含恢复信息和起点信息，失败返回 None
        """
        # 安全加载检查点
        检查点数据 = self.管理器.安全加载检查点(检查点路径=检查点路径)
        
        if 检查点数据 is None:
            日志.warning("无法加载检查点，恢复失败")
            return None
        
        try:
            # 恢复训练状态
            self._恢复信息 = 恢复训练状态(模型, 检查点数据)
            
            # 计算恢复起点
            self._恢复起点 = 计算恢复起点(检查点数据, 每epoch批次数)
            
            结果 = {
                '恢复信息': self._恢复信息,
                '恢复起点': self._恢复起点,
                '检查点数据': 检查点数据
            }
            
            日志.info(f"训练恢复成功: 将从 epoch={self._恢复起点['起始epoch']}, "
                      f"batch={self._恢复起点['起始batch']} 继续")
            
            return 结果
            
        except Exception as e:
            日志.error(f"训练恢复失败: {e}")
            return None
    
    @property
    def 起始epoch(self) -> int:
        """获取恢复后的起始 epoch"""
        if self._恢复起点 is None:
            raise ValueError("尚未执行恢复操作")
        return self._恢复起点['起始epoch']
    
    @property
    def 起始batch(self) -> int:
        """获取恢复后的起始 batch"""
        if self._恢复起点 is None:
            raise ValueError("尚未执行恢复操作")
        return self._恢复起点['起始batch']
    
    @property
    def 优化器状态(self) -> dict:
        """获取恢复的优化器状态"""
        if self._恢复信息 is None:
            raise ValueError("尚未执行恢复操作")
        return self._恢复信息.get('优化器状态', {})


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
        print(f"  训练进度: Epoch {最新信息['epoch'] + 1}, Batch {最新信息['batch'] + 1}")
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


def 自动检测并恢复(管理器: 检查点管理器, 静默模式: bool = False) -> dict:
    """
    自动检测检查点并提示用户选择恢复方式
    
    参数:
        管理器: 检查点管理器实例
        静默模式: 如果为 True，自动选择最新检查点恢复，不提示用户
    
    返回:
        恢复信息字典，包含:
        - 需要恢复: bool，是否需要恢复训练
        - 检查点路径: str，选择的检查点路径（如果需要恢复）
        - 检查点信息: dict，检查点元数据（如果需要恢复）
    """
    结果 = {
        '需要恢复': False,
        '检查点路径': None,
        '检查点信息': None
    }
    
    # 检查是否存在检查点
    if not 管理器.检查点存在():
        if not 静默模式:
            print("📝 未发现训练检查点，将从头开始训练")
        return 结果
    
    # 获取所有检查点
    检查点列表 = 管理器.列出检查点()
    
    if not 检查点列表:
        return 结果
    
    # 静默模式：自动选择最新检查点
    if 静默模式:
        结果['需要恢复'] = True
        结果['检查点路径'] = 检查点列表[0]['文件路径']
        结果['检查点信息'] = 检查点列表[0]
        return 结果
    
    # 交互模式：显示检查点列表并让用户选择
    print("\n" + "=" * 60)
    print("🔄 发现训练检查点")
    print("=" * 60)
    
    # 显示检查点列表
    print("\n可用检查点:")
    print("-" * 60)
    print(f"{'序号':<4} {'Epoch':<8} {'Batch':<8} {'Loss':<12} {'创建时间'}")
    print("-" * 60)
    
    for i, 检查点 in enumerate(检查点列表, 1):
        loss_str = f"{检查点['loss']:.4f}" if 检查点['loss'] else "N/A"
        时间 = 检查点['创建时间'][:19].replace('T', ' ')
        print(f"{i:<4} {检查点['epoch'] + 1:<8} {检查点['batch'] + 1:<8} {loss_str:<12} {时间}")
    
    print("-" * 60)
    print(f"\n共 {len(检查点列表)} 个检查点可用")
    print()
    
    # 提示用户选择
    while True:
        print("请选择操作:")
        print("  [1] 从最新检查点恢复 (推荐)")
        print("  [2] 选择特定检查点恢复")
        print("  [3] 重新开始训练 (将覆盖现有进度)")
        print()
        
        选择 = input("请输入选项 (1/2/3): ").strip()
        
        if 选择 == '1':
            # 从最新检查点恢复
            结果['需要恢复'] = True
            结果['检查点路径'] = 检查点列表[0]['文件路径']
            结果['检查点信息'] = 检查点列表[0]
            print(f"\n✅ 将从最新检查点恢复: Epoch {检查点列表[0]['epoch'] + 1}, Batch {检查点列表[0]['batch'] + 1}")
            break
            
        elif 选择 == '2':
            # 选择特定检查点
            while True:
                序号输入 = input(f"请输入检查点序号 (1-{len(检查点列表)}): ").strip()
                try:
                    序号 = int(序号输入)
                    if 1 <= 序号 <= len(检查点列表):
                        选中检查点 = 检查点列表[序号 - 1]
                        结果['需要恢复'] = True
                        结果['检查点路径'] = 选中检查点['文件路径']
                        结果['检查点信息'] = 选中检查点
                        print(f"\n✅ 将从检查点恢复: Epoch {选中检查点['epoch'] + 1}, Batch {选中检查点['batch'] + 1}")
                        break
                    else:
                        print(f"请输入 1 到 {len(检查点列表)} 之间的数字")
                except ValueError:
                    print("请输入有效的数字")
            break
            
        elif 选择 == '3':
            # 重新开始
            确认 = input("\n⚠️  确定要重新开始训练吗？现有检查点将不会被使用 (y/n): ").strip().lower()
            if 确认 in ['y', 'yes', '是']:
                print("\n📝 将从头开始训练")
                break
            else:
                print("已取消，请重新选择\n")
                continue
        else:
            print("请输入有效的选项 (1/2/3)\n")
    
    return 结果


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
