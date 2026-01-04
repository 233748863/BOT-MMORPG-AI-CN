#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
推理性能基准测试脚本

对比 TFLearn 和 ONNX 后端的推理性能，生成详细的性能报告。

使用方法:
    python 运行基准测试.py --onnx 模型/model.onnx
    python 运行基准测试.py --onnx 模型/model.onnx --tflearn 模型/预训练模型/test
    python 运行基准测试.py --onnx 模型/model.onnx --iterations 200 --no-gpu

需求: 3.1, 3.2, 3.3
"""

import os
import sys
import argparse
from datetime import datetime

# 添加项目根目录到路径
项目根目录 = os.path.dirname(os.path.abspath(__file__))
if 项目根目录 not in sys.path:
    sys.path.insert(0, 项目根目录)


def 解析参数():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="推理性能基准测试 - 对比 TFLearn 和 ONNX 后端性能",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python 运行基准测试.py --onnx 模型/model.onnx
  python 运行基准测试.py --onnx 模型/model.onnx --tflearn 模型/预训练模型/test
  python 运行基准测试.py --onnx 模型/model.onnx --iterations 200 --no-gpu
  python 运行基准测试.py --onnx 模型/model.onnx --output 日志/我的测试
        """
    )
    
    parser.add_argument(
        "--onnx", 
        type=str, 
        help="ONNX 模型文件路径 (.onnx)"
    )
    parser.add_argument(
        "--tflearn", 
        type=str, 
        help="TFLearn 模型文件路径 (不含扩展名)"
    )
    parser.add_argument(
        "--iterations", "-n",
        type=int, 
        default=100, 
        help="测试迭代次数 (默认: 100)"
    )
    parser.add_argument(
        "--warmup", "-w",
        type=int, 
        default=10, 
        help="预热迭代次数 (默认: 10)"
    )
    parser.add_argument(
        "--no-gpu", 
        action="store_true", 
        help="禁用 GPU 加速"
    )
    parser.add_argument(
        "--width",
        type=int,
        default=480,
        help="输入图像宽度 (默认: 480)"
    )
    parser.add_argument(
        "--height",
        type=int,
        default=270,
        help="输入图像高度 (默认: 270)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str, 
        default="日志/基准测试", 
        help="报告输出目录 (默认: 日志/基准测试)"
    )
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="只输出 JSON 格式报告"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="安静模式，减少输出"
    )
    
    return parser.parse_args()


def 检查模型文件(onnx路径: str, tflearn路径: str) -> bool:
    """检查模型文件是否存在"""
    有效 = False
    
    if onnx路径:
        if os.path.exists(onnx路径):
            print(f"✓ ONNX 模型: {onnx路径}")
            有效 = True
        else:
            print(f"✗ ONNX 模型不存在: {onnx路径}")
    
    if tflearn路径:
        # TFLearn 模型检查 .index 文件
        index文件 = tflearn路径 + ".index"
        if os.path.exists(index文件):
            print(f"✓ TFLearn 模型: {tflearn路径}")
            有效 = True
        else:
            print(f"✗ TFLearn 模型不存在: {tflearn路径}")
    
    return 有效


def 主函数():
    """主函数"""
    args = 解析参数()
    
    # 检查是否指定了模型
    if not args.onnx and not args.tflearn:
        print("错误: 请至少指定一个模型路径 (--onnx 或 --tflearn)")
        print("使用 --help 查看帮助信息")
        return 1
    
    print("=" * 60)
    print("推理性能基准测试")
    print("=" * 60)
    print()
    
    # 检查模型文件
    print("检查模型文件...")
    if not 检查模型文件(args.onnx, args.tflearn):
        print("\n错误: 没有找到有效的模型文件")
        return 1
    print()
    
    # 显示测试配置
    print("测试配置:")
    print(f"  迭代次数: {args.iterations}")
    print(f"  预热次数: {args.warmup}")
    print(f"  输入尺寸: {args.width} x {args.height}")
    print(f"  使用 GPU: {'否' if args.no_gpu else '是'}")
    print(f"  输出目录: {args.output}")
    print()
    
    # 导入测试模块
    try:
        from 工具.性能基准测试 import 性能基准测试器
    except ImportError as e:
        print(f"错误: 无法导入测试模块: {e}")
        return 1
    
    # 创建测试器
    测试器 = 性能基准测试器(
        测试次数=args.iterations,
        预热次数=args.warmup,
        输入形状=(args.width, args.height, 3)
    )
    
    # 运行对比测试
    print("开始基准测试...")
    print()
    
    报告 = 测试器.对比测试(
        onnx模型路径=args.onnx,
        tflearn模型路径=args.tflearn,
        使用GPU=not args.no_gpu
    )
    
    # 生成报告
    时间戳 = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if args.output:
        os.makedirs(args.output, exist_ok=True)
        
        # JSON 报告
        json报告路径 = os.path.join(args.output, f"基准测试报告_{时间戳}.json")
        测试器.保存JSON报告(报告, json报告路径)
        
        # 文本报告
        if not args.json_only:
            文本报告路径 = os.path.join(args.output, f"基准测试报告_{时间戳}.txt")
            测试器.生成报告(报告, 文本报告路径)
    
    # 打印报告
    if not args.quiet:
        print()
        测试器.打印报告(报告)
    
    # 打印总结
    print()
    print("=" * 60)
    print("测试完成!")
    print("=" * 60)
    
    if 报告.结果列表:
        for 结果 in 报告.结果列表:
            状态 = "✓" if 结果.满足延迟要求 else "✗"
            print(f"  {状态} {结果.后端名称}: {结果.延迟统计.平均延迟:.2f} ms (FPS: {结果.延迟统计.理论FPS:.1f})")
    
    if 报告.加速比 > 0:
        print(f"\n  加速比: {报告.加速比:.2f}x")
        print(f"  推荐后端: {报告.推荐后端}")
    
    if args.output:
        print(f"\n报告已保存到: {args.output}")
    
    return 0


if __name__ == "__main__":
    sys.exit(主函数())
