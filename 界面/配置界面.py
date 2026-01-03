"""
配置界面模块
提供图形化配置编辑界面

功能:
- 分区配置编辑
- 实时验证
- 档案管理
- 窗口区域预览
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, List, Optional, Any, Callable
import logging

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from 核心.配置验证 import 配置管理器, 档案管理器, 默认配置模式

# 配置日志
logging.basicConfig(level=logging.INFO)
日志 = logging.getLogger(__name__)


class 配置界面:
    """图形化配置编辑界面"""
    
    def __init__(self, 配置管理器实例: 配置管理器 = None):
        self._配置管理器 = 配置管理器实例 or 配置管理器()
        self._档案管理器 = 档案管理器()
        self._控件字典: Dict[str, tk.Widget] = {}
        self._变量字典: Dict[str, tk.Variable] = {}
        self._已修改 = False
        self._窗口: Optional[tk.Tk] = None
    
    def 显示(self):
        """显示配置界面"""
        self._窗口 = tk.Tk()
        self._窗口.title("配置管理")
        self._窗口.geometry("800x600")
        self._窗口.minsize(600, 400)
        
        # 创建主框架
        主框架 = ttk.Frame(self._窗口, padding="10")
        主框架.pack(fill=tk.BOTH, expand=True)
        
        # 创建工具栏
        self._创建工具栏(主框架)
        
        # 创建笔记本（选项卡）
        self._笔记本 = ttk.Notebook(主框架)
        self._笔记本.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # 创建配置分区
        模式 = self._配置管理器.获取模式()
        for 分区名, 参数列表 in 模式.items():
            self._创建分区(分区名, 参数列表)
        
        # 创建状态栏
        self._创建状态栏(主框架)
        
        # 加载当前配置
        self._加载配置到界面()
        
        # 绑定关闭事件
        self._窗口.protocol("WM_DELETE_WINDOW", self._关闭窗口)
        
        self._窗口.mainloop()

    def _创建工具栏(self, 父容器):
        """创建工具栏"""
        工具栏 = ttk.Frame(父容器)
        工具栏.pack(fill=tk.X)
        
        # 档案选择
        ttk.Label(工具栏, text="档案:").pack(side=tk.LEFT)
        
        self._档案变量 = tk.StringVar()
        self._档案下拉 = ttk.Combobox(工具栏, textvariable=self._档案变量, width=15, state="readonly")
        self._档案下拉.pack(side=tk.LEFT, padx=(5, 10))
        self._档案下拉.bind("<<ComboboxSelected>>", self._切换档案)
        self._刷新档案列表()
        
        # 按钮
        ttk.Button(工具栏, text="新建档案", command=self._新建档案).pack(side=tk.LEFT, padx=2)
        ttk.Button(工具栏, text="删除档案", command=self._删除档案).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(工具栏, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        ttk.Button(工具栏, text="导入", command=self._导入配置).pack(side=tk.LEFT, padx=2)
        ttk.Button(工具栏, text="导出", command=self._导出配置).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(工具栏, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        ttk.Button(工具栏, text="重置", command=self._重置配置).pack(side=tk.LEFT, padx=2)
        ttk.Button(工具栏, text="保存", command=self._保存配置).pack(side=tk.LEFT, padx=2)
    
    def _创建分区(self, 分区名: str, 参数列表: Dict):
        """创建配置分区"""
        框架 = ttk.Frame(self._笔记本, padding="10")
        self._笔记本.add(框架, text=分区名)
        
        # 创建滚动区域
        画布 = tk.Canvas(框架)
        滚动条 = ttk.Scrollbar(框架, orient=tk.VERTICAL, command=画布.yview)
        内容框架 = ttk.Frame(画布)
        
        画布.configure(yscrollcommand=滚动条.set)
        
        滚动条.pack(side=tk.RIGHT, fill=tk.Y)
        画布.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        画布.create_window((0, 0), window=内容框架, anchor=tk.NW)
        
        # 创建参数控件
        行号 = 0
        for 参数名, 定义 in 参数列表.items():
            self._创建参数控件(内容框架, 参数名, 定义, 行号)
            行号 += 1
        
        # 更新滚动区域
        内容框架.update_idletasks()
        画布.configure(scrollregion=画布.bbox("all"))
    
    def _创建参数控件(self, 父容器, 参数名: str, 定义: Dict, 行号: int):
        """创建单个参数的控件"""
        类型 = 定义.get("类型", "str")
        默认值 = 定义.get("默认值", "")
        描述 = 定义.get("描述", "")
        
        # 标签
        标签 = ttk.Label(父容器, text=f"{参数名}:")
        标签.grid(row=行号, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        
        # 根据类型创建控件
        if 类型 == "bool":
            变量 = tk.BooleanVar(value=默认值)
            控件 = ttk.Checkbutton(父容器, variable=变量)
        elif 类型 == "choice":
            变量 = tk.StringVar(value=默认值)
            选项 = 定义.get("选项", [])
            控件 = ttk.Combobox(父容器, textvariable=变量, values=选项, state="readonly", width=20)
        elif 类型 == "int":
            变量 = tk.IntVar(value=默认值)
            最小值 = 定义.get("最小值", 0)
            最大值 = 定义.get("最大值", 10000)
            控件 = ttk.Spinbox(父容器, textvariable=变量, from_=最小值, to=最大值, width=20)
        elif 类型 == "float":
            变量 = tk.DoubleVar(value=默认值)
            控件 = ttk.Entry(父容器, textvariable=变量, width=22)
        elif 类型 == "path":
            变量 = tk.StringVar(value=默认值)
            框架 = ttk.Frame(父容器)
            控件 = ttk.Entry(框架, textvariable=变量, width=30)
            控件.pack(side=tk.LEFT)
            ttk.Button(框架, text="浏览", width=6,
                      command=lambda v=变量: self._浏览文件(v)).pack(side=tk.LEFT, padx=5)
            框架.grid(row=行号, column=1, sticky=tk.W, pady=5)
            self._控件字典[参数名] = 控件
            self._变量字典[参数名] = 变量
            变量.trace_add("write", lambda *args: self._标记已修改())
            
            # 描述
            if 描述:
                描述标签 = ttk.Label(父容器, text=描述, foreground="gray")
                描述标签.grid(row=行号, column=2, sticky=tk.W, padx=10)
            return
        else:
            变量 = tk.StringVar(value=默认值)
            控件 = ttk.Entry(父容器, textvariable=变量, width=22)
        
        控件.grid(row=行号, column=1, sticky=tk.W, pady=5)
        
        # 描述
        if 描述:
            描述标签 = ttk.Label(父容器, text=描述, foreground="gray")
            描述标签.grid(row=行号, column=2, sticky=tk.W, padx=10)
        
        self._控件字典[参数名] = 控件
        self._变量字典[参数名] = 变量
        变量.trace_add("write", lambda *args: self._标记已修改())

    def _创建状态栏(self, 父容器):
        """创建状态栏"""
        状态栏 = ttk.Frame(父容器)
        状态栏.pack(fill=tk.X, pady=(10, 0))
        
        self._状态标签 = ttk.Label(状态栏, text="就绪")
        self._状态标签.pack(side=tk.LEFT)
        
        self._修改标签 = ttk.Label(状态栏, text="", foreground="orange")
        self._修改标签.pack(side=tk.RIGHT)
    
    def _浏览文件(self, 变量: tk.StringVar):
        """浏览文件"""
        文件路径 = filedialog.askopenfilename(
            title="选择文件",
            filetypes=[("所有文件", "*.*"), ("模型文件", "*.h5 *.pt *.onnx")]
        )
        if 文件路径:
            变量.set(文件路径)
    
    def _标记已修改(self):
        """标记配置已修改"""
        self._已修改 = True
        self._修改标签.config(text="● 未保存")
    
    def _刷新档案列表(self):
        """刷新档案列表"""
        档案列表 = self._档案管理器.获取档案列表()
        档案名列表 = ["默认"] + [d["名称"] for d in 档案列表]
        self._档案下拉["values"] = 档案名列表
        if not self._档案变量.get():
            self._档案变量.set("默认")
    
    def _切换档案(self, event=None):
        """切换档案"""
        if self._已修改:
            if not messagebox.askyesno("确认", "当前配置未保存，是否继续切换？"):
                return
        
        档案名 = self._档案变量.get()
        if 档案名 == "默认":
            self._配置管理器.加载配置()
        else:
            配置 = self._档案管理器.加载档案(档案名)
            if 配置:
                for 参数名, 值 in 配置.items():
                    if 参数名 in self._变量字典:
                        self._变量字典[参数名].set(值)
        
        self._已修改 = False
        self._修改标签.config(text="")
        self._状态标签.config(text=f"已加载档案: {档案名}")
    
    def _新建档案(self):
        """新建档案"""
        档案名 = tk.simpledialog.askstring("新建档案", "请输入档案名称:")
        if 档案名:
            配置 = self.获取当前值()
            if self._档案管理器.创建档案(档案名, 配置):
                self._刷新档案列表()
                self._档案变量.set(档案名)
                messagebox.showinfo("成功", f"档案 '{档案名}' 已创建")
            else:
                messagebox.showerror("错误", "创建档案失败")
    
    def _删除档案(self):
        """删除档案"""
        档案名 = self._档案变量.get()
        if 档案名 == "默认":
            messagebox.showwarning("警告", "不能删除默认配置")
            return
        
        if messagebox.askyesno("确认", f"确定要删除档案 '{档案名}' 吗？"):
            if self._档案管理器.删除档案(档案名):
                self._刷新档案列表()
                self._档案变量.set("默认")
                messagebox.showinfo("成功", "档案已删除")
    
    def _导入配置(self):
        """导入配置"""
        文件路径 = filedialog.askopenfilename(
            title="导入配置",
            filetypes=[("JSON文件", "*.json")]
        )
        if 文件路径:
            配置 = self._配置管理器.导入配置(文件路径)
            if 配置:
                self.设置值(配置)
                messagebox.showinfo("成功", "配置已导入")
    
    def _导出配置(self):
        """导出配置"""
        文件路径 = filedialog.asksaveasfilename(
            title="导出配置",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json")]
        )
        if 文件路径:
            配置 = self.获取当前值()
            self._配置管理器.导出配置(配置, 文件路径)
            messagebox.showinfo("成功", "配置已导出")
    
    def _重置配置(self):
        """重置配置"""
        if messagebox.askyesno("确认", "确定要重置为默认配置吗？"):
            默认配置 = self._配置管理器.获取默认值()
            self.设置值(默认配置)
            self._状态标签.config(text="已重置为默认配置")

    def _保存配置(self):
        """保存配置"""
        配置 = self.获取当前值()
        
        # 验证配置
        有效, 错误列表 = self._配置管理器.验证配置(配置)
        if not 有效:
            错误信息 = "\n".join([f"• {e.参数名}: {e.错误信息}" for e in 错误列表])
            messagebox.showerror("验证失败", f"配置验证失败:\n{错误信息}")
            return
        
        档案名 = self._档案变量.get()
        if 档案名 == "默认":
            if self._配置管理器.保存配置(配置):
                self._已修改 = False
                self._修改标签.config(text="")
                self._状态标签.config(text="配置已保存")
                messagebox.showinfo("成功", "配置已保存")
        else:
            if self._档案管理器.保存档案(档案名, 配置):
                self._已修改 = False
                self._修改标签.config(text="")
                self._状态标签.config(text=f"档案 '{档案名}' 已保存")
                messagebox.showinfo("成功", "档案已保存")
    
    def _加载配置到界面(self):
        """加载配置到界面"""
        self._配置管理器.加载配置()
        配置 = self._配置管理器.获取当前配置()
        
        # 合并默认值
        默认配置 = self._配置管理器.获取默认值()
        完整配置 = {**默认配置, **配置}
        
        self.设置值(完整配置)
        self._已修改 = False
        self._修改标签.config(text="")
    
    def _关闭窗口(self):
        """关闭窗口"""
        if self._已修改:
            结果 = messagebox.askyesnocancel("确认", "配置已修改，是否保存？")
            if 结果 is None:  # 取消
                return
            if 结果:  # 是
                self._保存配置()
        
        self._窗口.destroy()
    
    def 获取当前值(self) -> Dict:
        """获取界面上的当前配置值"""
        配置 = {}
        for 参数名, 变量 in self._变量字典.items():
            try:
                配置[参数名] = 变量.get()
            except:
                配置[参数名] = ""
        return 配置
    
    def 设置值(self, 配置: Dict):
        """设置界面上的配置值"""
        for 参数名, 值 in 配置.items():
            if 参数名 in self._变量字典:
                try:
                    self._变量字典[参数名].set(值)
                except:
                    pass
    
    def 显示错误(self, 参数名: str, 错误信息: str):
        """显示参数错误信息"""
        if 参数名 in self._控件字典:
            控件 = self._控件字典[参数名]
            # 可以添加红色边框等视觉提示
            self._状态标签.config(text=f"错误: {参数名} - {错误信息}", foreground="red")


def 启动配置界面():
    """启动配置界面"""
    try:
        import tkinter.simpledialog
    except ImportError:
        日志.error("tkinter 未安装，无法启动图形界面")
        return
    
    界面 = 配置界面()
    界面.显示()


if __name__ == "__main__":
    启动配置界面()
