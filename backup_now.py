#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VPS自动部署工具 - 快速备份脚本
直接执行项目备份，无需交互
"""
from backup_project import ProjectBackup

def main():
    """直接执行备份"""
    print("🚀 开始快速备份项目...")
    
    backup = ProjectBackup()
    result = backup.create_backup()
    
    if result:
        print("\n🎉 项目备份完成！")
        print(f"📦 备份文件已保存至: {result}")
        
        # 显示备份目录的所有文件
        backup.list_backups()
    else:
        print("\n❌ 备份失败！")

if __name__ == "__main__":
    main() 