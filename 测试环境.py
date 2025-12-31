"""
环境测试脚本
用于验证所有依赖是否正确安装
"""

import sys
import os

# 设置路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def 测试依赖():
    """测试所有依赖是否可用"""
    
    print("=" * 60)
    print("🔍 MMORPG游戏AI - 环境测试")
    print("=" * 60)
    print()
    
    测试结果 = []
    
    # 测试 NumPy
    try:
        import numpy as np
        测试结果.append(("NumPy", True, np.__version__))
    except ImportError as e:
        测试结果.append(("NumPy", False, str(e)))
    
    # 测试 OpenCV
    try:
        import cv2
        测试结果.append(("OpenCV", True, cv2.__version__))
    except ImportError as e:
        测试结果.append(("OpenCV", False, str(e)))
    
    # 测试 TensorFlow
    try:
        import tensorflow as tf
        测试结果.append(("TensorFlow", True, tf.__version__))
    except ImportError as e:
        测试结果.append(("TensorFlow", False, str(e)))
    
    # 测试 TFLearn
    try:
        import tflearn
        测试结果.append(("TFLearn", True, "已安装"))
    except ImportError as e:
        测试结果.append(("TFLearn", False, "未安装 - 见下方安装说明"))
    
    # 测试 pywin32
    try:
        import win32api
        import win32gui
        import win32ui
        import win32con
        测试结果.append(("pywin32", True, "已安装"))
    except ImportError as e:
        测试结果.append(("pywin32", False, str(e)))
    
    # 显示结果
    print("📦 依赖检测结果:")
    print("-" * 60)
    
    全部通过 = True
    for 名称, 状态, 信息 in 测试结果:
        if 状态:
            print(f"  ✅ {名称}: {信息}")
        else:
            print(f"  ❌ {名称}: {信息}")
            全部通过 = False
    
    print("-" * 60)
    
    # 测试核心模块
    print("\n📁 核心模块检测:")
    print("-" * 60)
    
    模块列表 = [
        ("配置.设置", "配置模块"),
        ("核心.屏幕截取", "屏幕截取"),
        ("核心.键盘控制", "键盘控制"),
        ("核心.按键检测", "按键检测"),
        ("核心.动作检测", "动作检测"),
        ("核心.模型定义", "模型定义"),
    ]
    
    for 模块名, 描述 in 模块列表:
        try:
            __import__(模块名)
            print(f"  ✅ {描述}: 正常")
        except Exception as e:
            print(f"  ❌ {描述}: {e}")
            全部通过 = False
    
    print("-" * 60)
    
    # 检测预训练模型
    print("\n🧠 模型文件检测:")
    print("-" * 60)
    
    基础路径 = os.path.dirname(os.path.abspath(__file__))
    模型文件 = [
        os.path.join(基础路径, "模型/预训练模型/test.index"),
        os.path.join(基础路径, "模型/预训练模型/test.meta"),
        os.path.join(基础路径, "模型/预训练模型/test.data-00000-of-00001"),
    ]
    
    for 文件 in 模型文件:
        文件名 = os.path.basename(文件)
        if os.path.exists(文件):
            print(f"  ✅ {文件名}")
        else:
            print(f"  ❌ {文件名} (未找到)")
    
    print("-" * 60)
    
    # 总结
    print()
    if 全部通过:
        print("🎉 所有检测通过! 可以开始使用了")
        print()
        print("下一步:")
        print("  运行 'python 启动.py' 开始使用")
    else:
        print("⚠️  部分检测未通过，请安装缺失的依赖:")
        print()
        print("【TFLearn 安装方法】")
        print()
        print("方案1: TensorFlow 2.15 + 官方TFLearn")
        print("  pip install tensorflow==2.15.0")
        print("  pip install tflearn==0.5.0")
        print()
        print("方案2: TensorFlow 2.16+ + 修复版TFLearn (推荐)")
        print("  pip install tensorflow")
        print("  pip install git+https://github.com/MihaMarkic/tflearn.git@fix/is_sequence_missing")
    
    print()
    return 全部通过


if __name__ == "__main__":
    测试依赖()
    input("\n按回车键退出...")
