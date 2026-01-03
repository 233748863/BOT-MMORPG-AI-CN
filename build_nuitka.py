# -*- coding: utf-8 -*-
"""
Nuitka 打包脚本
每次运行前自动清理上次构建的文件

使用方法:
    python build_nuitka.py          # 打包 GUI 版本
    python build_nuitka.py --cli    # 打包命令行版本
    python build_nuitka.py --all    # 打包两个版本
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# ============== 配置区域 ==============

# 项目根目录
项目根目录 = Path(__file__).parent.absolute()

# 输出目录
输出目录 = 项目根目录 / "dist"
构建缓存目录 = 项目根目录 / "build"

# 入口文件配置
GUI入口文件 = "启动GUI.py"
CLI入口文件 = "启动.py"

# 输出程序名称
GUI程序名 = "MMORPG游戏AI助手"
CLI程序名 = "MMORPG游戏AI助手_CLI"

# 需要包含的数据文件夹
数据文件夹 = [
    "配置",
    "模型",
    "数据",
    "日志",
]

# 需要排除的模块（减小体积，避免打包未使用的库）
排除模块 = [
    # 测试相关
    "tkinter",
    "unittest",
    "test",
    "tests",
    "pytest",
    "hypothesis",
    "_pytest",
    
    # 开发工具
    "pip",
    "setuptools",
    "wheel",
    "distutils",
    "pkg_resources",
    
    # 文档和调试
    "pdb",
    "doctest",
    "pydoc",
    "pydoc_data",
    
    # 不需要的标准库
    "lib2to3",
    "idlelib",
    "turtle",
    "turtledemo",
    "curses",
    "ensurepip",
    "venv",
    
    # 不需要的网络库
    "ftplib",
    "smtplib",
    "poplib",
    "imaplib",
    "nntplib",
    "telnetlib",
    "xmlrpc",
    "http.server",
    "socketserver",
    
    # 不需要的数据库
    "sqlite3",
    "dbm",
    
    # 不需要的音频
    "audioop",
    "wave",
    "sndhdr",
    "sunau",
    "aifc",
    
    # 不需要的编码
    "encodings.cp1250",
    "encodings.cp1251",
    "encodings.cp1252",
    "encodings.cp1253",
    "encodings.cp1254",
    "encodings.cp1255",
    "encodings.cp1256",
    "encodings.cp1257",
    "encodings.cp1258",
    "encodings.iso8859_1",
    "encodings.iso8859_2",
    "encodings.iso8859_3",
    "encodings.iso8859_4",
    "encodings.iso8859_5",
    "encodings.iso8859_6",
    "encodings.iso8859_7",
    "encodings.iso8859_8",
    "encodings.iso8859_9",
    "encodings.iso8859_10",
    "encodings.iso8859_13",
    "encodings.iso8859_14",
    "encodings.iso8859_15",
    "encodings.koi8_r",
    "encodings.koi8_u",
    
    # TensorFlow 不需要的组件
    "tensorboard",
    "tensorflow.python.debug",
    "tensorflow.python.profiler",
    "tensorflow.python.tools",
    "tensorflow.python.saved_model.model_utils",
    "tensorflow_estimator",
    
    # 其他不需要的
    "IPython",
    "jupyter",
    "notebook",
    "nbformat",
    "nbconvert",
]

# ============== 清理函数 ==============

def 清理构建文件():
    """清理上次构建产生的文件"""
    print()
    print("=" * 50)
    print("🧹 清理上次构建文件...")
    print("=" * 50)
    
    清理项目 = [
        输出目录,
        构建缓存目录,
        项目根目录 / f"{GUI程序名}.build",
        项目根目录 / f"{GUI程序名}.dist",
        项目根目录 / f"{GUI程序名}.onefile-build",
        项目根目录 / f"{CLI程序名}.build",
        项目根目录 / f"{CLI程序名}.dist",
        项目根目录 / f"{CLI程序名}.onefile-build",
    ]
    
    # 清理 .pyd 和 .exe 文件
    for 文件 in 项目根目录.glob("*.pyd"):
        清理项目.append(文件)
    for 文件 in 项目根目录.glob("*.exe"):
        if 文件.name not in ["python.exe", "pythonw.exe"]:
            清理项目.append(文件)
    
    已清理 = 0
    for 路径 in 清理项目:
        if 路径.exists():
            try:
                if 路径.is_dir():
                    shutil.rmtree(路径)
                    print(f"  ✓ 删除目录: {路径.name}")
                else:
                    路径.unlink()
                    print(f"  ✓ 删除文件: {路径.name}")
                已清理 += 1
            except Exception as e:
                print(f"  ✗ 删除失败 {路径.name}: {e}")
    
    if 已清理 == 0:
        print("  (没有需要清理的文件)")
    else:
        print(f"\n  共清理 {已清理} 个项目")
    
    print()


def 检查nuitka():
    """检查 Nuitka 是否已安装"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "nuitka", "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            版本 = result.stdout.strip().split('\n')[0]
            print(f"✓ Nuitka 已安装: {版本}")
            return True
    except Exception:
        pass
    
    print("✗ Nuitka 未安装")
    print("  请运行: pip install nuitka")
    return False


def 构建命令(入口文件: str, 程序名: str, 是GUI: bool = True) -> list:
    """生成 Nuitka 构建命令"""
    命令 = [
        sys.executable, "-m", "nuitka",
        
        # 基本选项
        "--standalone",                    # 独立打包
        "--onefile",                       # 单文件模式
        f"--output-filename={程序名}.exe", # 输出文件名
        f"--output-dir={输出目录}",        # 输出目录
        
        # 编译优化
        "--assume-yes-for-downloads",      # 自动下载依赖
        "--remove-output",                 # 移除旧输出
        
        # 重要：只跟踪实际导入的模块，不打包未使用的库
        "--follow-imports",                # 只跟踪实际导入
        "--no-prefer-source-code",         # 优先使用编译后的模块
        
        # 插件
        "--enable-plugin=pyside6",         # PySide6 支持
        "--enable-plugin=numpy",           # NumPy 支持
        # 注意：tensorflow2 插件在新版 Nuitka 中已移除，TensorFlow 会自动处理
        
        # 包含整个包
        "--include-package=核心",
        "--include-package=界面",
        "--include-package=训练",
        "--include-package=运行",
        "--include-package=工具",
        "--include-package=配置",
    ]
    
    # GUI 模式禁用控制台窗口
    if 是GUI:
        命令.append("--windows-disable-console")
        命令.append("--windows-icon-from-ico=icon.ico")  # 如果有图标的话
    
    # 排除不需要的模块（关键：减小体积）
    for 模块 in 排除模块:
        命令.append(f"--nofollow-import-to={模块}")
    
    # 包含数据文件夹
    for 文件夹 in 数据文件夹:
        文件夹路径 = 项目根目录 / 文件夹
        if 文件夹路径.exists():
            命令.append(f"--include-data-dir={文件夹}={文件夹}")
    
    # 入口文件
    命令.append(str(项目根目录 / 入口文件))
    
    return 命令


def 执行打包(入口文件: str, 程序名: str, 是GUI: bool = True):
    """执行打包过程"""
    print()
    print("=" * 50)
    print(f"📦 开始打包: {程序名}")
    print("=" * 50)
    print(f"  入口文件: {入口文件}")
    print(f"  输出目录: {输出目录}")
    print()
    
    # 确保输出目录存在
    输出目录.mkdir(parents=True, exist_ok=True)
    
    # 生成命令
    命令 = 构建命令(入口文件, 程序名, 是GUI)
    
    # 移除不存在的图标参数
    图标文件 = 项目根目录 / "icon.ico"
    if not 图标文件.exists():
        命令 = [c for c in 命令 if "--windows-icon-from-ico" not in c]
    
    print("执行命令:")
    print("  " + " ".join(命令[:5]) + " ...")
    print()
    
    # 执行打包
    try:
        process = subprocess.Popen(
            命令,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        # 实时输出
        for line in process.stdout:
            print(line, end='')
        
        process.wait()
        
        if process.returncode == 0:
            print()
            print("=" * 50)
            print(f"✅ 打包成功: {程序名}.exe")
            print(f"   位置: {输出目录 / f'{程序名}.exe'}")
            print("=" * 50)
            return True
        else:
            print()
            print(f"❌ 打包失败，返回码: {process.returncode}")
            return False
            
    except Exception as e:
        print(f"❌ 打包出错: {e}")
        return False


def 显示帮助():
    """显示帮助信息"""
    print(__doc__)


def 主程序():
    """主程序入口"""
    print()
    print("=" * 50)
    print("🔨 Nuitka 打包工具")
    print("=" * 50)
    
    # 解析参数
    打包GUI = True
    打包CLI = False
    
    if len(sys.argv) > 1:
        参数 = sys.argv[1].lower()
        if 参数 in ['--help', '-h', 'help']:
            显示帮助()
            return 0
        elif 参数 in ['--cli', '-c', 'cli']:
            打包GUI = False
            打包CLI = True
        elif 参数 in ['--all', '-a', 'all']:
            打包GUI = True
            打包CLI = True
        elif 参数 in ['--gui', '-g', 'gui']:
            打包GUI = True
            打包CLI = False
        else:
            print(f"未知参数: {参数}")
            显示帮助()
            return 1
    
    # 检查 Nuitka
    if not 检查nuitka():
        return 1
    
    # 清理上次构建
    清理构建文件()
    
    # 执行打包
    成功 = True
    
    if 打包GUI:
        if not 执行打包(GUI入口文件, GUI程序名, 是GUI=True):
            成功 = False
    
    if 打包CLI:
        if not 执行打包(CLI入口文件, CLI程序名, 是GUI=False):
            成功 = False
    
    # 最终清理临时文件
    print()
    print("🧹 清理临时构建文件...")
    临时目录 = [
        项目根目录 / f"{GUI程序名}.build",
        项目根目录 / f"{GUI程序名}.onefile-build",
        项目根目录 / f"{CLI程序名}.build",
        项目根目录 / f"{CLI程序名}.onefile-build",
    ]
    for 目录 in 临时目录:
        if 目录.exists():
            try:
                shutil.rmtree(目录)
            except Exception:
                pass
    
    print()
    if 成功:
        print("=" * 50)
        print("🎉 所有打包任务完成!")
        print(f"   输出目录: {输出目录}")
        print("=" * 50)
        return 0
    else:
        print("⚠️ 部分打包任务失败")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(主程序())
    except KeyboardInterrupt:
        print("\n\n👋 打包已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
