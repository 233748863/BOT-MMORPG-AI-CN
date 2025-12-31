# -*- coding: utf-8 -*-
"""
MMORPG游戏AI助手 - GUI启动器

直接启动图形用户界面，无需通过命令行菜单。
"""

import os
import sys

# 设置工作目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


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


def 主程序():
    """启动GUI主程序"""
    print()
    print("=" * 50)
    print("🎮 MMORPG游戏AI助手 - 图形界面")
    print("=" * 50)
    print()
    print("正在启动图形界面...")
    
    # 检查依赖
    if not 检查依赖():
        input("按回车键退出...")
        return 1
    
    try:
        from 界面.主程序 import 启动应用
        return 启动应用()
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        input("\n按回车键退出...")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(主程序())
    except KeyboardInterrupt:
        print("\n\n👋 程序已退出")
        sys.exit(0)
