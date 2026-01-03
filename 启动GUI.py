# -*- coding: utf-8 -*-
"""
MMORPG游戏AI助手 - GUI启动器

直接启动图形用户界面，无需通过命令行菜单。
集成配置界面功能。
"""

import os
import sys

# 设置工作目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 抑制 TensorFlow 警告信息，避免启动时卡顿
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # 0=全部, 1=INFO, 2=WARNING, 3=ERROR
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'  # 禁用 oneDNN 优化警告

# 抑制 Keras/TensorFlow 弃用警告
import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', module='tensorflow')
warnings.filterwarnings('ignore', module='keras')

# 抑制 TensorFlow 的 absl 日志
import logging
logging.getLogger('tensorflow').setLevel(logging.ERROR)
logging.getLogger('absl').setLevel(logging.ERROR)

# 尝试导入配置界面模块
try:
    from 界面.配置界面 import 配置界面
    配置界面可用 = True
except ImportError:
    配置界面可用 = False


def 检查依赖():
    """检查必要的依赖是否已安装"""
    缺失依赖 = []
    
    try:
        import PySide6
    except ImportError:
        缺失依赖.append("PySide6")
    
    try:
        import pyqtgraph
    except ImportError:
        缺失依赖.append("pyqtgraph")
    
    if 缺失依赖:
        print("❌ 缺少必要的依赖:")
        for 依赖 in 缺失依赖:
            print(f"   - {依赖}")
        print()
        print("请运行以下命令安装依赖:")
        print(f"   pip install {' '.join(缺失依赖)}")
        print()
        return False
    
    return True


def 显示启动菜单():
    """显示启动菜单"""
    print()
    print("=" * 50)
    print("🎮 MMORPG游戏AI助手 - 启动菜单")
    print("=" * 50)
    print()
    print("请选择启动模式:")
    print("  1. 启动主界面")
    print("  2. 打开配置界面" + (" ✅" if 配置界面可用 else " ❌ (不可用)"))
    print("  3. 退出")
    print()
    return input("请输入选项 (1-3, 默认1): ").strip() or "1"


def 启动配置界面():
    """启动配置界面"""
    if not 配置界面可用:
        print("❌ 配置界面模块不可用")
        return 1
    
    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication(sys.argv)
        窗口 = 配置界面()
        窗口.show()
        return app.exec()
    except Exception as e:
        print(f"❌ 启动配置界面失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


def 主程序():
    """启动GUI主程序"""
    print()
    print("=" * 50)
    print("🎮 MMORPG游戏AI助手 - 图形界面")
    print("=" * 50)
    print()
    
    # 检查依赖
    if not 检查依赖():
        input("按回车键退出...")
        return 1
    
    # 显示可用模块状态
    print("可用功能模块:")
    print(f"  - 配置界面: {'✅ 可用' if 配置界面可用 else '❌ 不可用'}")
    
    # 显示启动菜单
    选项 = 显示启动菜单()
    
    if 选项 == "1":
        print("正在启动主界面...")
        try:
            from 界面.主程序 import 启动应用
            return 启动应用()
        except Exception as e:
            print(f"\n❌ 启动失败: {e}")
            import traceback
            traceback.print_exc()
            input("\n按回车键退出...")
            return 1
    
    elif 选项 == "2":
        print("正在启动配置界面...")
        return 启动配置界面()
    
    elif 选项 == "3":
        print("👋 再见!")
        return 0
    
    else:
        print("❌ 无效选项")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(主程序())
    except KeyboardInterrupt:
        print("\n\n👋 程序已退出")
        sys.exit(0)
