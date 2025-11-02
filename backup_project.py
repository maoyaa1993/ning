#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VPS自动部署工具 - 项目备份脚本
自动备份所有重要文件，确保项目安全
"""
import os
import shutil
import zipfile
import time
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProjectBackup:
    def __init__(self):
        self.project_root = os.getcwd()
        self.backup_dir = os.path.join(self.project_root, 'backups')
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 确保备份目录存在
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
            
        # 定义需要备份的文件和目录
        self.backup_items = {
            'core_files': [
                'main.py',
                'gui_main.py',
                'gui_backend.py',
                'gui_vps_config.py',
                'gui_proxy_config_final.py',
                'start_gui.py'
            ],
            'modules': [
                'v2ray_deployer.py',
                'vmess_creator.py',
                'socks5_creator.py',
                'ssh_client.py',
                'proxy_manager.py',
                'proxy_manager_v2rayn.py',
                'result_collector.py',
                'word_generator.py',
                'input_handler.py'
            ],
            'config_files': [
                'requirements.txt',
                'proxy_config.json',
                'test_kcp_config.json',
                'test_xray_config.json'
            ],
            'documentation': [
                'README.md',
                'GUI使用说明.md',
                '修复问题总结.md'
            ],
            'utilities': [
                'install_deps.py',
                'quick_deploy.py',
                'diagnose_proxy.py',
                'debug_gui_proxy.py',
                'debug_proxy_startup.py'
            ],
            'test_files': [
                'test_buttons.py',
                'test_final_integration.py',
                'test_gui_integration.py',
                'test_proxy_connection.py',
                'test_proxy_fix.py',
                'test_proxy_quick.py',
                'test_proxy_simple.py'
            ],
            'directories': [
                'config',
                'v2ray_core',
                'reports'
            ]
        }
        
        # 排除的文件模式
        self.exclude_patterns = [
            '*.pyc',
            '__pycache__',
            '*.log',
            '.git',
            '.gitignore',
            'backups',
            '*.tmp',
            '*.temp'
        ]

    def create_backup(self):
        """创建完整项目备份"""
        logger.info("开始创建项目备份...")
        
        # 创建备份文件名
        backup_filename = f'vmess_project_backup_{self.timestamp}.zip'
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        try:
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 备份所有分类的文件
                for category, items in self.backup_items.items():
                    logger.info(f"备份 {category} 类别文件...")
                    
                    if category == 'directories':
                        self._backup_directories(zipf, items)
                    else:
                        self._backup_files(zipf, items, category)
                
                # 添加备份信息文件
                self._create_backup_info(zipf)
            
            # 验证备份文件
            if self._verify_backup(backup_path):
                logger.info(f"✅ 项目备份成功创建: {backup_path}")
                self._print_backup_summary(backup_path)
                return backup_path
            else:
                logger.error("❌ 备份文件验证失败")
                return None
                
        except Exception as e:
            logger.error(f"❌ 创建备份失败: {str(e)}")
            return None

    def _backup_files(self, zipf, file_list, category):
        """备份指定的文件列表"""
        backed_up = 0
        for filename in file_list:
            file_path = os.path.join(self.project_root, filename)
            if os.path.exists(file_path):
                # 在zip中创建分类目录
                archive_name = f"{category}/{filename}"
                zipf.write(file_path, archive_name)
                backed_up += 1
                logger.debug(f"  已备份: {filename}")
            else:
                logger.warning(f"  文件不存在: {filename}")
        
        logger.info(f"  {category}: 成功备份 {backed_up}/{len(file_list)} 个文件")

    def _backup_directories(self, zipf, dir_list):
        """备份指定的目录"""
        backed_up = 0
        for dirname in dir_list:
            dir_path = os.path.join(self.project_root, dirname)
            if os.path.exists(dir_path):
                self._add_directory_to_zip(zipf, dir_path, f"directories/{dirname}")
                backed_up += 1
                logger.debug(f"  已备份目录: {dirname}")
            else:
                logger.warning(f"  目录不存在: {dirname}")
        
        logger.info(f"  directories: 成功备份 {backed_up}/{len(dir_list)} 个目录")

    def _add_directory_to_zip(self, zipf, dir_path, archive_dir):
        """递归添加目录到zip文件"""
        for root, dirs, files in os.walk(dir_path):
            # 过滤排除的目录
            dirs[:] = [d for d in dirs if not self._should_exclude(d)]
            
            for file in files:
                if not self._should_exclude(file):
                    file_path = os.path.join(root, file)
                    # 计算在zip中的相对路径
                    rel_path = os.path.relpath(file_path, dir_path)
                    archive_path = os.path.join(archive_dir, rel_path).replace('\\', '/')
                    zipf.write(file_path, archive_path)

    def _should_exclude(self, item_name):
        """检查文件或目录是否应该被排除"""
        for pattern in self.exclude_patterns:
            if pattern.startswith('*'):
                if item_name.endswith(pattern[1:]):
                    return True
            else:
                if pattern in item_name:
                    return True
        return False

    def _create_backup_info(self, zipf):
        """创建备份信息文件"""
        backup_info = f"""VPS自动部署工具 - 项目备份信息
=====================================

备份时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}
项目版本: v2.0 (美化版)
备份类型: 完整项目备份

备份内容统计:
- 核心文件: {len(self.backup_items['core_files'])} 个
- 功能模块: {len(self.backup_items['modules'])} 个  
- 配置文件: {len(self.backup_items['config_files'])} 个
- 文档文件: {len(self.backup_items['documentation'])} 个
- 工具文件: {len(self.backup_items['utilities'])} 个
- 测试文件: {len(self.backup_items['test_files'])} 个
- 目录数量: {len(self.backup_items['directories'])} 个

项目特性:
✅ 智能端口冲突解决
✅ VMess + SOCKS5 双协议支持
✅ 现代化GUI界面
✅ 批量VPS部署
✅ 美化版Word报告生成
✅ 完整的错误处理和恢复

技术栈:
- Python 3.x
- tkinter (GUI)
- paramiko (SSH)
- python-docx (Word生成)
- V2Ray核心

最近更新:
- 修复端口冲突问题 ✅
- 优化Word报告格式 ✅
- 修复VPS配置重复加载 ✅
- 结果收集器错误修复 ✅

开发团队: V2Ray自动化工具开发组
联系方式: 技术支持邮箱
"""
        
        # 将备份信息写入zip文件
        import io
        info_bytes = backup_info.encode('utf-8')
        zipf.writestr('BACKUP_INFO.txt', info_bytes)

    def _verify_backup(self, backup_path):
        """验证备份文件的完整性"""
        try:
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                # 检查zip文件是否损坏
                bad_file = zipf.testzip()
                if bad_file:
                    logger.error(f"备份文件中发现损坏文件: {bad_file}")
                    return False
                
                # 检查关键文件是否存在
                file_list = zipf.namelist()
                required_files = ['BACKUP_INFO.txt']
                
                for req_file in required_files:
                    if req_file not in file_list:
                        logger.error(f"缺少必要文件: {req_file}")
                        return False
                
                logger.info(f"备份文件验证通过，包含 {len(file_list)} 个文件")
                return True
                
        except Exception as e:
            logger.error(f"验证备份文件时出错: {str(e)}")
            return False

    def _print_backup_summary(self, backup_path):
        """打印备份摘要"""
        file_size = os.path.getsize(backup_path)
        size_mb = file_size / (1024 * 1024)
        
        print("\n" + "="*60)
        print("🎉 VPS自动部署工具 - 项目备份完成")
        print("="*60)
        print(f"📦 备份文件: {os.path.basename(backup_path)}")
        print(f"📍 备份路径: {backup_path}")
        print(f"📊 文件大小: {size_mb:.2f} MB")
        print(f"🕐 备份时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"✨ 项目版本: v2.0 (美化版)")
        print("\n📋 备份内容:")
        
        total_items = sum(len(items) for items in self.backup_items.values())
        print(f"  - 总计 {total_items} 个文件/目录")
        
        for category, items in self.backup_items.items():
            category_name = {
                'core_files': '核心文件',
                'modules': '功能模块', 
                'config_files': '配置文件',
                'documentation': '文档文件',
                'utilities': '工具文件',
                'test_files': '测试文件',
                'directories': '目录'
            }.get(category, category)
            print(f"  - {category_name}: {len(items)} 个")
        
        print("\n🔄 恢复说明:")
        print("  1. 解压备份文件到新目录")
        print("  2. 安装依赖: pip install -r requirements.txt")
        print("  3. 运行主程序: python start_gui.py")
        print("\n✅ 备份已安全保存，项目可随时恢复！")
        print("="*60)

    def list_backups(self):
        """列出所有现有备份"""
        if not os.path.exists(self.backup_dir):
            print("❌ 备份目录不存在")
            return
        
        backup_files = [f for f in os.listdir(self.backup_dir) if f.endswith('.zip')]
        
        if not backup_files:
            print("📁 暂无备份文件")
            return
        
        print("\n" + "="*50)
        print("📦 现有备份文件列表")
        print("="*50)
        
        backup_files.sort(reverse=True)  # 按时间倒序
        
        for i, backup_file in enumerate(backup_files, 1):
            backup_path = os.path.join(self.backup_dir, backup_file)
            file_size = os.path.getsize(backup_path) / (1024 * 1024)
            mod_time = os.path.getmtime(backup_path)
            mod_time_str = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')
            
            print(f"{i}. {backup_file}")
            print(f"   📊 大小: {file_size:.2f} MB")
            print(f"   🕐 时间: {mod_time_str}")
            print(f"   📍 路径: {backup_path}")
            print()

def main():
    """主函数"""
    print("🚀 VPS自动部署工具 - 项目备份脚本")
    print("="*50)
    
    backup = ProjectBackup()
    
    while True:
        print("\n请选择操作:")
        print("1. 创建新备份")
        print("2. 查看现有备份")
        print("3. 退出")
        
        choice = input("\n请输入选择 (1-3): ").strip()
        
        if choice == '1':
            print("\n开始创建备份...")
            result = backup.create_backup()
            if result:
                print(f"\n🎉 备份创建成功!")
            else:
                print("\n❌ 备份创建失败!")
                
        elif choice == '2':
            backup.list_backups()
            
        elif choice == '3':
            print("\n👋 感谢使用项目备份工具!")
            break
            
        else:
            print("\n❌ 无效选择，请重新输入")

if __name__ == "__main__":
    main() 