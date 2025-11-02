#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Excel模板生成器
用于创建VPS批量导入的Excel模板文件
"""
import pandas as pd
import os
from datetime import datetime

def create_vps_template():
    """创建VPS配置Excel模板"""
    
    # 示例数据
    template_data = {
        'VPS名称': [
            '示例VPS-1',
            '示例VPS-2', 
            '示例VPS-3',
            '生产环境-VPS1',
            '测试环境-VPS1'
        ],
        'IP地址': [
            '192.168.1.100',
            '192.168.1.101',
            '192.168.1.102', 
            '45.76.123.45',
            '10.0.0.50'
        ],
        'SSH端口': [
            22,
            22,
            2222,
            22,
            22
        ],
        '用户名': [
            'root',
            'root',
            'root',
            'root', 
            'admin'
        ],
        '密码': [
            'your_password_here',
            'another_password',
            'complex_password_123',
            'production_password',
            'test_password'
        ],
        '备注': [
            '测试服务器，可以删除',
            '示例数据，请替换为真实信息',
            '使用非标准SSH端口',
            '生产环境，请谨慎操作',
            '测试环境，用于功能验证'
        ]
    }
    
    # 创建DataFrame
    df = pd.DataFrame(template_data)
    
    # 确保templates目录存在
    template_dir = 'templates'
    if not os.path.exists(template_dir):
        os.makedirs(template_dir)
    
    # 生成带时间戳的文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    template_path = os.path.join(template_dir, f'VPS批量导入模板_{timestamp}.xlsx')
    
    # 保存Excel文件
    with pd.ExcelWriter(template_path, engine='openpyxl') as writer:
        # 写入主表
        df.to_excel(writer, sheet_name='VPS配置清单', index=False)
        
        # 获取工作表对象
        worksheet = writer.sheets['VPS配置清单']
        
        # 设置列宽
        column_widths = {
            'A': 15,  # VPS名称
            'B': 18,  # IP地址  
            'C': 10,  # SSH端口
            'D': 12,  # 用户名
            'E': 20,  # 密码
            'F': 30   # 备注
        }
        
        for col, width in column_widths.items():
            worksheet.column_dimensions[col].width = width
        
        # 添加说明表
        instructions = pd.DataFrame({
            '字段名称': ['VPS名称', 'IP地址', 'SSH端口', '用户名', '密码', '备注'],
            '必填': ['是', '是', '是', '是', '是', '否'],
            '说明': [
                '给VPS起个容易识别的名字，如：生产环境-Web服务器',
                'VPS的公网IP地址，如：45.76.123.45',
                'SSH连接端口，通常是22，部分VPS可能使用其他端口',
                'SSH登录用户名，通常是root',
                'SSH登录密码，请确保密码正确',
                '可选的备注信息，用于记录VPS用途等'
            ],
            '示例': [
                '生产环境-VPS1',
                '45.76.123.45', 
                '22',
                'root',
                'your_strong_password',
                '用于Web服务部署'
            ]
        })
        
        instructions.to_excel(writer, sheet_name='填写说明', index=False)
        
        # 设置说明表列宽
        worksheet2 = writer.sheets['填写说明']
        worksheet2.column_dimensions['A'].width = 12
        worksheet2.column_dimensions['B'].width = 8
        worksheet2.column_dimensions['C'].width = 35
        worksheet2.column_dimensions['D'].width = 20
    
    print(f"✅ Excel模板已生成: {template_path}")
    print(f"📋 包含 {len(df)} 个示例VPS配置")
    print("📝 请根据'填写说明'表格填写您的真实VPS信息")
    print("⚠️  注意：请删除示例数据，填入真实的VPS配置信息")
    
    return template_path

def create_standard_template():
    """创建标准空白模板"""
    template_data = {
        'VPS名称': [''],
        'IP地址': [''],
        'SSH端口': [22],
        '用户名': ['root'],
        '密码': [''],
        '备注': ['']
    }
    
    df = pd.DataFrame(template_data)
    
    template_dir = 'templates'
    if not os.path.exists(template_dir):
        os.makedirs(template_dir)
    
    template_path = os.path.join(template_dir, 'VPS批量导入模板_空白.xlsx')
    
    with pd.ExcelWriter(template_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='VPS配置清单', index=False)
        
        worksheet = writer.sheets['VPS配置清单']
        # 设置列宽
        worksheet.column_dimensions['A'].width = 15
        worksheet.column_dimensions['B'].width = 18
        worksheet.column_dimensions['C'].width = 10
        worksheet.column_dimensions['D'].width = 12
        worksheet.column_dimensions['E'].width = 20
        worksheet.column_dimensions['F'].width = 30
    
    print(f"✅ 空白模板已生成: {template_path}")
    return template_path

if __name__ == "__main__":
    print("🚀 生成VPS批量导入Excel模板...")
    print()
    
    # 生成示例模板
    example_template = create_vps_template()
    
    # 生成空白模板  
    blank_template = create_standard_template()
    
    print()
    print("📁 模板文件位置:")
    print(f"  示例模板: {example_template}")
    print(f"  空白模板: {blank_template}")
    print()
    print("🎯 使用步骤:")
    print("  1. 选择一个模板文件")
    print("  2. 填入您的真实VPS信息")
    print("  3. 保存文件")
    print("  4. 在GUI中点击'导入Excel'导入配置")
    print("  5. 使用'批量检测'验证VPS连接")
    print("  6. 对验证成功的VPS执行批量部署") 