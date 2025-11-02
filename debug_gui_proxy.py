#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试版本的代理配置GUI
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
from proxy_manager import ProxyManager

class DebugProxyConfigWindow:
    def __init__(self):
        self.window = tk.Toplevel()
        self.window.title("🌐 VMESS代理配置 (调试版)")
        self.window.geometry("800x700")
        self.window.resizable(True, True)
        
        # 初始化变量
        self.proxy_manager = None
        self.proxy_var = tk.StringVar(value="no_proxy")
        
        print("创建调试版代理配置窗口...")
        self.create_widgets()
        
        # 显示窗口
        self.window.deiconify()
        self.window.lift()
        self.window.focus_force()
        
    def create_widgets(self):
        """创建界面控件"""
        print("开始创建界面控件...")
        
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        print("创建标题...")
        title_label = ttk.Label(main_frame, text="VMESS代理配置 (调试版)", font=('微软雅黑', 14, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # 代理选择
        print("创建代理选择区域...")
        self.create_proxy_selection(main_frame)
        
        # 代理链接输入
        print("创建代理链接输入区域...")
        self.create_proxy_input(main_frame)
        
        # 代理状态显示
        print("创建代理状态显示区域...")
        self.create_proxy_status(main_frame)
        
        # 操作按钮
        print("创建操作按钮...")
        self.create_action_buttons(main_frame)
        
        print("所有控件创建完成！")
        
        # 初始化状态
        self.window.after(100, self.initialize_state)
        
    def create_proxy_selection(self, parent):
        """创建代理选择区域"""
        print("  - 创建代理选择框架...")
        selection_frame = ttk.LabelFrame(parent, text="代理选择", padding="10")
        selection_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 不使用代理
        no_proxy_radio = ttk.Radiobutton(
            selection_frame, 
            text="不使用代理 (直连)", 
            variable=self.proxy_var, 
            value="no_proxy",
            command=self.on_proxy_selection_change
        )
        no_proxy_radio.pack(anchor=tk.W, pady=2)
        
        # 使用VMESS代理
        vmess_radio = ttk.Radiobutton(
            selection_frame, 
            text="使用VMESS代理 (适用于IP被风控)", 
            variable=self.proxy_var, 
            value="vmess_proxy",
            command=self.on_proxy_selection_change
        )
        vmess_radio.pack(anchor=tk.W, pady=2)
        print("  - 代理选择区域创建完成")
        
    def create_proxy_input(self, parent):
        """创建代理链接输入区域"""
        print("  - 创建输入框架...")
        self.input_frame = ttk.LabelFrame(parent, text="VMESS代理链接", padding="10")
        self.input_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 说明文字
        info_label = ttk.Label(
            self.input_frame, 
            text="请输入完整的VMESS链接，格式: vmess://xxxxxxx...",
            font=('微软雅黑', 9),
            foreground='gray'
        )
        info_label.pack(anchor=tk.W, pady=(0, 5))
        
        # 输入框
        self.vmess_entry = tk.Text(self.input_frame, height=4, wrap=tk.WORD, font=('Consolas', 9))
        self.vmess_entry.pack(fill=tk.X, pady=(0, 10))
        
        # 按钮框架
        button_frame = ttk.Frame(self.input_frame)
        button_frame.pack(fill=tk.X)
        
        # 解析按钮
        print("  - 创建解析按钮...")
        self.parse_btn = ttk.Button(
            button_frame, 
            text="🔍 解析链接", 
            command=self.parse_vmess_link
        )
        self.parse_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 测试按钮
        print("  - 创建测试按钮...")
        self.test_btn = ttk.Button(
            button_frame, 
            text="🧪 测试连接", 
            command=self.test_proxy_connection,
            state=tk.DISABLED
        )
        self.test_btn.pack(side=tk.LEFT)
        print("  - 输入区域创建完成")
        
    def create_proxy_status(self, parent):
        """创建代理状态显示区域"""
        print("  - 创建状态显示框架...")
        self.status_frame = ttk.LabelFrame(parent, text="代理状态", padding="10")
        self.status_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # 状态显示
        self.status_text = scrolledtext.ScrolledText(
            self.status_frame, 
            height=8, 
            wrap=tk.WORD, 
            font=('Consolas', 9),
            state=tk.DISABLED
        )
        self.status_text.pack(fill=tk.BOTH, expand=True)
        print("  - 状态显示区域创建完成")
        
    def create_action_buttons(self, parent):
        """创建操作按钮"""
        print("  - 创建操作按钮框架...")
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 确保框架可见
        button_frame.configure(relief="solid", borderwidth=1)  # 调试用边框
        
        # 启动代理按钮
        print("  - 创建启动代理按钮...")
        self.start_proxy_btn = ttk.Button(
            button_frame, 
            text="🚀 启动代理", 
            command=self.start_proxy,
            state=tk.DISABLED
        )
        self.start_proxy_btn.pack(side=tk.LEFT, padx=(0, 10))
        print(f"    启动按钮已创建: {self.start_proxy_btn}")
        
        # 停止代理按钮
        print("  - 创建停止代理按钮...")
        self.stop_proxy_btn = ttk.Button(
            button_frame, 
            text="⏹ 停止代理", 
            command=self.stop_proxy,
            state=tk.DISABLED
        )
        self.stop_proxy_btn.pack(side=tk.LEFT, padx=(0, 10))
        print(f"    停止按钮已创建: {self.stop_proxy_btn}")
        
        # 测试连接按钮（额外的）
        test_conn_btn = ttk.Button(
            button_frame, 
            text="🔧 连接测试", 
            command=self.quick_test
        )
        test_conn_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 关闭按钮
        close_btn = ttk.Button(button_frame, text="关闭", command=self.close_window)
        close_btn.pack(side=tk.RIGHT)
        
        print("  - 操作按钮创建完成")
        
    def initialize_state(self):
        """初始化界面状态"""
        print("初始化界面状态...")
        try:
            self.add_status_message("=== 调试版代理配置窗口已就绪 ===")
            self.add_status_message("✓ 所有按钮组件已创建")
            
            # 检查按钮是否存在
            if hasattr(self, 'start_proxy_btn'):
                self.add_status_message("✓ 启动代理按钮: 存在")
            else:
                self.add_status_message("❌ 启动代理按钮: 不存在")
                
            if hasattr(self, 'stop_proxy_btn'):
                self.add_status_message("✓ 停止代理按钮: 存在")
            else:
                self.add_status_message("❌ 停止代理按钮: 不存在")
                
            # 根据当前代理选择设置输入状态
            use_proxy = self.proxy_var.get() == "vmess_proxy"
            self.add_status_message(f"当前代理模式: {'启用' if use_proxy else '禁用'}")
            
        except Exception as e:
            print(f"初始化状态失败: {e}")
            self.add_status_message(f"❌ 初始化失败: {e}")
        
    def on_proxy_selection_change(self):
        """代理选择改变时的处理"""
        use_proxy = self.proxy_var.get() == "vmess_proxy"
        self.add_status_message(f"代理模式切换为: {'启用' if use_proxy else '禁用'}")
        
    def parse_vmess_link(self):
        """解析VMESS链接"""
        vmess_link = self.vmess_entry.get('1.0', tk.END).strip()
        
        if not vmess_link:
            self.add_status_message("⚠️ 请输入VMESS链接")
            return
            
        if not vmess_link.startswith('vmess://'):
            self.add_status_message("❌ 无效的VMESS链接格式")
            return
            
        try:
            self.add_status_message("正在解析VMESS链接...")
            
            # 创建代理管理器
            self.proxy_manager = ProxyManager()
            
            # 解析链接
            config = self.proxy_manager.parse_vmess_link(vmess_link)
            
            if config:
                self.add_status_message("✓ VMESS链接解析成功")
                self.add_status_message(f"  服务器: {config.get('add', 'N/A')}:{config.get('port', 'N/A')}")
                self.add_status_message(f"  传输协议: {config.get('net', 'N/A')} + {config.get('type', 'none')}")
                self.add_status_message(f"  节点名称: {config.get('ps', '未知')}")
                
                # 启用按钮
                if hasattr(self, 'test_btn'):
                    self.test_btn.config(state=tk.NORMAL)
                if hasattr(self, 'start_proxy_btn'):
                    self.start_proxy_btn.config(state=tk.NORMAL)
                    self.add_status_message("✓ 启动代理按钮已启用")
            else:
                self.add_status_message("❌ VMESS链接解析失败")
                
        except Exception as e:
            self.add_status_message(f"❌ 解析出错: {str(e)}")
    
    def test_proxy_connection(self):
        """测试代理连接"""
        if not self.proxy_manager:
            self.add_status_message("❌ 请先解析VMESS链接")
            return
            
        self.add_status_message("开始测试代理连接...")
        self.add_status_message("使用代理管理器内置测试功能...")
        
        try:
            if self.proxy_manager.test_proxy():
                self.add_status_message("✅ 代理连接测试成功！")
            else:
                self.add_status_message("❌ 代理连接测试失败")
        except Exception as e:
            self.add_status_message(f"❌ 测试异常: {e}")
    
    def start_proxy(self):
        """启动代理"""
        if not self.proxy_manager:
            self.add_status_message("❌ 请先解析VMESS链接")
            return
            
        try:
            self.add_status_message("正在启动代理服务...")
            self.add_status_message("使用Xray核心启动代理...")
            
            if self.proxy_manager.start_proxy():
                self.add_status_message("✅ 代理服务启动成功！")
                self.add_status_message(f"本地SOCKS代理: 127.0.0.1:{self.proxy_manager.local_socks_port}")
                
                # 更新按钮状态
                self.start_proxy_btn.config(state=tk.DISABLED)
                if hasattr(self, 'stop_proxy_btn'):
                    self.stop_proxy_btn.config(state=tk.NORMAL)
            else:
                self.add_status_message("❌ 代理服务启动失败")
                
        except Exception as e:
            self.add_status_message(f"❌ 启动异常: {str(e)}")
    
    def stop_proxy(self):
        """停止代理"""
        if self.proxy_manager:
            try:
                self.proxy_manager.stop_proxy()
                self.add_status_message("代理服务已停止")
                
                # 更新按钮状态
                self.start_proxy_btn.config(state=tk.NORMAL)
                self.stop_proxy_btn.config(state=tk.DISABLED)
                
            except Exception as e:
                self.add_status_message(f"❌ 停止异常: {str(e)}")
    
    def quick_test(self):
        """快速测试"""
        self.add_status_message("=== 快速测试 ===")
        
        # 测试VMESS链接
        test_vmess = "vmess://ewogICJ2IjogIjIiLAogICJwcyI6ICJ2bXNlZStrY3B8YUhURS5sb3ZlQHhyYXkuY29tIiwKICAiYWRkIjogIjM4LjExNC4xMjIuMzkiLAogICJwb3J0IjogMTc4MzYsCiAgImlkIjogIjU2MTZmYTlmLTY3MDYtNGY5Ny1lNzA0LWVjYzQwMDFhOGQzOCIsCiAgImFpZCI6IDAsCiAgIm5ldCI6ICJrY3AiLAogICJ0eXBlIjogImR0bHMiLAogICJob3N0IjogIiIsCiAgInBhdGgiOiAiekVBQkx3a2xoZSIsCiAgInRscyI6ICJub25lIgp9"
        
        # 自动填入链接
        self.vmess_entry.delete('1.0', tk.END)
        self.vmess_entry.insert('1.0', test_vmess)
        self.add_status_message("已自动填入测试VMESS链接")
        
        # 自动解析
        self.parse_vmess_link()
        
    def add_status_message(self, message):
        """添加状态消息"""
        try:
            import datetime
            self.status_text.config(state=tk.NORMAL)
            timestamp = datetime.datetime.now().strftime('%H:%M:%S')
            self.status_text.insert(tk.END, f"[{timestamp}] {message}\n")
            self.status_text.see(tk.END)
            self.status_text.config(state=tk.DISABLED)
            print(f"[GUI] {message}")  # 同时输出到控制台
        except Exception as e:
            print(f"状态消息添加失败: {e}")
    
    def close_window(self):
        """关闭窗口"""
        if self.proxy_manager:
            try:
                self.proxy_manager.stop_proxy()
            except:
                pass
        self.window.destroy()

if __name__ == "__main__":
    print("启动调试版GUI...")
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    
    app = DebugProxyConfigWindow()
    
    print("进入GUI主循环...")
    root.mainloop() 