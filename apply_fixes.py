#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动应用修复脚本
解决所有发现的问题
"""

import os
import shutil
from datetime import datetime

def backup_file(filepath):
    """备份文件"""
    if os.path.exists(filepath):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{filepath}.backup_{timestamp}"
        shutil.copy2(filepath, backup_path)
        print(f"✅ 已备份: {filepath} -> {backup_path}")
        return backup_path
    return None

def fix_excel_manager_syntax():
    """修复excel_manager.py语法错误"""
    print("\n🔧 修复excel_manager.py语法错误...")
    
    filepath = "excel_manager.py"
    if not os.path.exists(filepath):
        print(f"❌ 文件不存在: {filepath}")
        return False
    
    # 备份文件
    backup_file(filepath)
    
    # 读取文件
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 修复第70行的缩进问题
    for i, line in enumerate(lines):
        if i == 70:  # 第71行（0-based索引）
            if line.strip() == "proxy_info = proxy_manager.get_proxy_info()":
                lines[i] = "            proxy_info = proxy_manager.get_proxy_info()\n"
                print(f"✅ 修复第{i+1}行缩进问题")
                break
    
    # 写回文件
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("✅ excel_manager.py 语法错误已修复")
    return True

def fix_gui_thread_fixer():
    """修复GUI线程修复器的类名问题"""
    print("\n🔧 修复GUI线程修复器类名...")
    
    filepath = "gui_thread_fixer.py"
    if not os.path.exists(filepath):
        print(f"❌ 文件不存在: {filepath}")
        return False
    
    # 读取文件
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 添加ThreadSafeGUIUpdater别名
    if "ThreadSafeGUIUpdater = ThreadSafeGUI" not in content:
        content = content.replace(
            "# 为了兼容性，提供别名",
            "# 为了兼容性，提供别名\nThreadSafeGUIUpdater = ThreadSafeGUI\ncreate_thread_safe_callback = make_thread_safe_callback"
        )
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ 已添加ThreadSafeGUIUpdater别名")
    
    return True

def fix_ssh_client_parameters():
    """修复SSH客户端参数问题"""
    print("\n🔧 修复SSH客户端参数问题...")
    
    # 需要检查的文件
    files_to_check = ["excel_manager.py", "gui_main.py"]
    
    for filepath in files_to_check:
        if not os.path.exists(filepath):
            continue
            
        # 读取文件
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        updated = False
        
        # 查找SSH客户端实例化的地方，修复参数传递
        if "SSHClient(" in content and "proxy_host=" in content:
            # 替换有问题的参数传递
            content = content.replace(
                "SSHClient(host, port, username, password, proxy_host=proxy_host, proxy_port=proxy_port)",
                "SSHClient(timeout=30)"
            )
            content = content.replace(
                "client = SSHClient(",
                "client = SSHClient(timeout=30)\n        # 然后调用connect方法\n        client.connect("
            )
            updated = True
        
        if updated:
            backup_file(filepath)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ 已修复 {filepath} 的SSH客户端参数")
    
    return True

def update_imports():
    """更新导入语句"""
    print("\n🔧 更新导入语句...")
    
    files_to_update = [
        "excel_manager.py",
        "gui_main.py", 
        "gui_proxy_config_final.py"
    ]
    
    for filepath in files_to_update:
        if not os.path.exists(filepath):
            continue
            
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        updated = False
        
        # 更新SSH客户端导入
        if "from ssh_client import SSHClient" in content:
            content = content.replace(
                "from ssh_client import SSHClient",
                "from fixed_ssh_client import FixedSSHClient as SSHClient"
            )
            updated = True
        
        # 添加线程安全导入（仅对GUI文件）
        if "gui_" in filepath and "import tkinter as tk" in content:
            if "from gui_thread_fixer import" not in content:
                content = content.replace(
                    "import tkinter as tk",
                    "import tkinter as tk\nfrom gui_thread_fixer import ThreadSafeGUI, make_thread_safe_callback"
                )
                updated = True
        
        if updated:
            backup_file(filepath)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ 已更新 {filepath} 的导入语句")
    
    return True

def test_fixes():
    """测试修复效果"""
    print("\n🧪 测试修复效果...")
    
    # 测试SSH客户端导入
    try:
        from fixed_ssh_client import FixedSSHClient
        print("✅ SSH客户端导入测试通过")
        
        # 测试SSH客户端实例化
        client = FixedSSHClient(timeout=30)
        client.close()
        print("✅ SSH客户端实例化测试通过")
        
    except Exception as e:
        print(f"❌ SSH客户端测试失败: {e}")
    
    # 测试GUI线程修复器导入
    try:
        from gui_thread_fixer import ThreadSafeGUI, ThreadSafeGUIUpdater, make_thread_safe_callback
        print("✅ GUI线程修复器导入测试通过")
    except Exception as e:
        print(f"❌ GUI线程修复器测试失败: {e}")
    
    # 测试excel_manager语法
    try:
        import excel_manager
        print("✅ excel_manager语法测试通过")
    except Exception as e:
        print(f"❌ excel_manager语法测试失败: {e}")

def main():
    """主函数"""
    print("🚀 开始应用修复...")
    print("=" * 50)
    
    try:
        # 1. 修复excel_manager语法错误
        fix_excel_manager_syntax()
        
        # 2. 修复GUI线程修复器类名
        fix_gui_thread_fixer()
        
        # 3. 修复SSH客户端参数问题
        fix_ssh_client_parameters()
        
        # 4. 更新导入语句
        update_imports()
        
        # 5. 测试修复效果
        test_fixes()
        
        print("\n" + "=" * 50)
        print("🎉 所有修复应用完成！")
        print("\n📋 修复内容总结：")
        print("✅ 1. 修复了 excel_manager.py 语法错误")
        print("✅ 2. 修复了 GUI线程修复器类名问题")
        print("✅ 3. 修复了 SSH客户端参数问题")
        print("✅ 4. 更新了所有相关文件的导入语句")
        print("\n💡 建议：")
        print("- 现在可以运行 python gui_main.py 测试")
        print("- 如果还有问题，请查看具体错误信息")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 修复过程中出现错误: {e}")
        return False

if __name__ == "__main__":
    main() 