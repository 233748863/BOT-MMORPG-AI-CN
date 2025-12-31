"""
MMORPG游戏AI助手 - 主启动器
中文汉化版

功能:
- 主线任务自动化
- 自动战斗训练
- 增强模式 (YOLO检测 + 状态识别 + 智能决策)
"""

import os
import sys

# 设置工作目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def 显示主菜单():
    """显示主菜单"""
    print()
    print("=" * 60)
    print("🎮 MMORPG游戏AI助手 - 中文版")
    print("=" * 60)
    print()
    print("📋 请选择功能:")
    print("  1. 🎥 数据收集 (录制游戏操作)")
    print("  2. 🧠 训练模型 (训练AI大脑)")
    print("  3. 🤖 运行机器人 (基础模式)")
    print("  4. 🚀 运行增强机器人 (智能模式)")
    print("  5. 🔧 数据工具 (预处理/清洗/权重)")
    print("  6. ⚙️  增强模块配置")
    print("  7. ❓ 查看帮助")
    print("  0. 🚪 退出程序")
    print()


def 显示帮助():
    """显示帮助信息"""
    print()
    print("=" * 60)
    print("📖 使用帮助")
    print("=" * 60)
    print()
    print("【快速开始】")
    print()
    print("1️⃣  数据收集:")
    print("   - 运行数据收集功能")
    print("   - 切换到游戏窗口")
    print("   - 正常玩游戏，AI会记录你的操作")
    print("   - 按 T 暂停/继续，按 Q 退出")
    print()
    print("2️⃣  训练模型:")
    print("   - 收集足够数据后运行训练")
    print("   - 建议至少收集10个数据文件")
    print("   - 训练时间取决于数据量和硬件")
    print()
    print("3️⃣  运行机器人:")
    print("   - 基础模式: 使用模仿学习模型")
    print("   - 增强模式: 集成YOLO检测+状态识别+智能决策")
    print("   - 按 T 暂停/继续，按 ESC 退出")
    print()
    print("【运行模式说明】")
    print()
    print("🤖 基础模式:")
    print("   使用训练好的模仿学习模型")
    print("   适合已有训练数据的用户")
    print()
    print("🚀 增强模式:")
    print("   - YOLO目标检测: 识别怪物、NPC、物品等")
    print("   - 状态识别: 判断战斗、对话、菜单等状态")
    print("   - 智能决策: 结合规则和模型做出决策")
    print("   - 自动降级: 模块失败时自动切换到基础模式")
    print()
    print("【训练模式说明】")
    print()
    print("🎯 主线任务模式:")
    print("   专注于学习做主线任务的操作")
    print("   包括: NPC对话、任务寻路、物品拾取等")
    print()
    print("⚔️  自动战斗模式:")
    print("   专注于学习战斗技能释放")
    print("   包括: 技能释放、走位躲避、目标选择等")
    print()
    print("【系统要求】")
    print()
    print("   - Windows 10/11")
    print("   - Python 3.8+")
    print("   - 8GB+ 内存")
    print("   - NVIDIA GPU (推荐，CPU也可运行)")
    print("   - ultralytics库 (增强模式需要)")
    print()
    input("按回车键返回主菜单...")


def 运行数据收集():
    """运行数据收集脚本"""
    print("\n🎥 启动数据收集...")
    from 训练.收集数据 import 主程序
    主程序()


def 运行训练模型():
    """运行模型训练脚本"""
    print("\n🧠 启动模型训练...")
    from 训练.训练模型 import 主程序
    主程序()


def 运行机器人():
    """运行基础游戏机器人"""
    print("\n🤖 启动基础游戏机器人...")
    from 运行.运行机器人 import 主程序
    主程序()


def 运行增强机器人():
    """运行增强版游戏机器人"""
    print("\n🚀 启动增强版游戏机器人...")
    from 运行.增强机器人 import 主程序
    主程序()


def 显示增强模块配置菜单():
    """显示增强模块配置菜单"""
    while True:
        print()
        print("=" * 60)
        print("⚙️  增强模块配置")
        print("=" * 60)
        print()
        
        # 读取当前配置
        from 配置.增强设置 import (
            YOLO配置, 状态识别配置, 决策引擎配置, 模块启用配置, 性能配置
        )
        
        print("📋 当前配置:")
        print()
        print("【模块启用状态】")
        print(f"  YOLO检测器:   {'✓ 启用' if 模块启用配置.get('YOLO检测器', True) else '✗ 禁用'}")
        print(f"  状态识别器:   {'✓ 启用' if 模块启用配置.get('状态识别器', True) else '✗ 禁用'}")
        print(f"  决策引擎:     {'✓ 启用' if 模块启用配置.get('决策引擎', True) else '✗ 禁用'}")
        print()
        print("【YOLO检测器配置】")
        print(f"  模型路径:     {YOLO配置.get('模型路径', '未设置')}")
        print(f"  置信度阈值:   {YOLO配置.get('置信度阈值', 0.5)}")
        print(f"  检测间隔:     每 {YOLO配置.get('检测间隔', 3)} 帧")
        print()
        print("【状态识别配置】")
        print(f"  历史长度:     {状态识别配置.get('历史长度', 10)}")
        print(f"  置信度累积:   {状态识别配置.get('置信度累积系数', 0.1)}")
        print()
        print("【决策引擎配置】")
        print(f"  决策策略:     {决策引擎配置.get('策略', '混合加权')}")
        print(f"  规则权重:     {决策引擎配置.get('规则权重', 0.6)}")
        print(f"  模型权重:     {决策引擎配置.get('模型权重', 0.4)}")
        print()
        print("【性能配置】")
        print(f"  帧率阈值:     {性能配置.get('帧率阈值', 15)} FPS")
        print(f"  自动降级:     {'✓ 启用' if 性能配置.get('自动降级', True) else '✗ 禁用'}")
        print()
        print("📋 操作选项:")
        print("  1. 查看详细配置说明")
        print("  2. 打开配置文件 (手动编辑)")
        print("  0. 返回主菜单")
        print()
        
        选择 = input("请输入选项 (0-2): ").strip()
        
        if 选择 == '0':
            break
        elif 选择 == '1':
            显示配置说明()
        elif 选择 == '2':
            print("\n📂 配置文件位置: 配置/增强设置.py")
            print("   请使用文本编辑器打开并修改配置")
            input("\n按回车键继续...")
        else:
            print("\n❌ 无效选项")
            input("按回车键继续...")


def 显示配置说明():
    """显示配置说明"""
    print()
    print("=" * 60)
    print("📖 配置说明")
    print("=" * 60)
    print()
    print("【YOLO检测器】")
    print("  模型路径: YOLO模型文件路径 (.pt格式)")
    print("  置信度阈值: 0.0-1.0，低于此值的检测结果会被过滤")
    print("  检测间隔: 每N帧执行一次检测，值越大性能越好但响应越慢")
    print()
    print("【状态识别器】")
    print("  历史长度: 保存的状态历史数量，用于状态稳定性判断")
    print("  置信度累积系数: 连续相同状态时置信度的增加量")
    print()
    print("【决策引擎】")
    print("  决策策略:")
    print("    - 规则优先: 优先使用规则，规则不匹配时使用模型")
    print("    - 模型优先: 优先使用模型，紧急规则可覆盖")
    print("    - 混合加权: 结合规则和模型的加权结果")
    print("  规则权重/模型权重: 混合加权时的权重分配")
    print()
    print("【性能配置】")
    print("  帧率阈值: 低于此帧率时进入低性能模式")
    print("  自动降级: 性能不足时自动降低检测频率")
    print()
    input("按回车键返回...")


def 显示数据工具菜单():
    """显示数据工具子菜单"""
    while True:
        print()
        print("=" * 60)
        print("🔧 数据工具")
        print("=" * 60)
        print()
        print("📋 请选择功能:")
        print("  1. 📊 数据预处理 (图像增强)")
        print("  2. 🧹 数据清洗 (平衡类别)")
        print("  3. ⚖️  类别权重 (优化权重)")
        print("  4. 📈 查看数据分布")
        print("  0. ↩️  返回主菜单")
        print()
        
        选择 = input("请输入选项 (0-4): ").strip()
        
        if 选择 == '0':
            break
        elif 选择 == '1':
            print("\n📊 启动数据预处理...")
            from 工具.数据预处理 import 批量预处理数据
            批量预处理数据()
        elif 选择 == '2':
            print("\n🧹 启动数据清洗...")
            from 工具.数据清洗 import 批量清洗数据
            批量清洗数据()
        elif 选择 == '3':
            print("\n⚖️  启动类别权重工具...")
            from 工具.类别权重 import 主程序 as 权重主程序
            权重主程序()
        elif 选择 == '4':
            print("\n📈 数据分布统计...")
            from 工具.类别权重 import 显示数据分布
            显示数据分布()
            input("\n按回车键继续...")
        else:
            print("\n❌ 无效选项")
            input("按回车键继续...")


def 主程序():
    """主程序入口"""
    
    while True:
        显示主菜单()
        
        选择 = input("请输入选项 (0-7): ").strip()
        
        if 选择 == '0':
            print("\n👋 再见！")
            break
        elif 选择 == '1':
            运行数据收集()
        elif 选择 == '2':
            运行训练模型()
        elif 选择 == '3':
            运行机器人()
        elif 选择 == '4':
            运行增强机器人()
        elif 选择 == '5':
            显示数据工具菜单()
        elif 选择 == '6':
            显示增强模块配置菜单()
        elif 选择 == '7':
            显示帮助()
        else:
            print("\n❌ 无效选项，请重新输入")
            input("按回车键继续...")


if __name__ == "__main__":
    try:
        主程序()
    except KeyboardInterrupt:
        print("\n\n👋 程序已退出")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        input("按回车键退出...")
