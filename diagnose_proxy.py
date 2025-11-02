#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
代理问题诊断脚本
检查端口占用、V2Ray核心、配置文件等
"""
import os
import socket
import subprocess
import json
from proxy_manager import ProxyManager

def check_port_usage(port_range=(1080, 1180)):
    """检查端口占用情况"""
    print(f"\n🔍 检查端口 {port_range[0]}-{port_range[1]} 占用情况:")
    available_ports = []
    occupied_ports = []
    
    for port in range(port_range[0], port_range[1] + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', port))
                available_ports.append(port)
                if len(available_ports) <= 5:  # 只显示前5个
                    print(f"  ✓ 端口 {port} 可用")
            except OSError:
                occupied_ports.append(port)
                if len(occupied_ports) <= 5:  # 只显示前5个
                    print(f"  ❌ 端口 {port} 被占用")
    
    print(f"\n📊 端口统计:")
    print(f"  可用端口: {len(available_ports)} 个")
    print(f"  被占用端口: {len(occupied_ports)} 个")
    
    if available_ports:
        print(f"  推荐使用端口: {available_ports[0]}")
        return available_ports[0]
    else:
        print("  ⚠️ 警告: 指定范围内无可用端口")
        return None

def check_v2ray_core():
    """检查V2Ray核心程序"""
    print(f"\n🔧 检查V2Ray核心程序:")
    
    # 检查本地V2Ray
    local_v2ray = os.path.join(os.path.dirname(__file__), 'v2ray_core', 'v2ray.exe')
    if os.path.exists(local_v2ray):
        print(f"  ✓ 本地V2Ray核心: {local_v2ray}")
        try:
            result = subprocess.run([local_v2ray, 'version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version_info = result.stdout.split('\n')[0] if result.stdout else "未知版本"
                print(f"  ✓ 版本信息: {version_info}")
                return True
            else:
                print(f"  ❌ 版本检查失败: {result.stderr}")
        except Exception as e:
            print(f"  ❌ 运行失败: {e}")
    else:
        print(f"  ❌ 本地V2Ray核心未找到: {local_v2ray}")
    
    # 检查系统V2Ray
    try:
        result = subprocess.run(['v2ray', 'version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"  ✓ 系统V2Ray可用")
            return True
    except:
        pass
    
    print(f"  ❌ 系统V2Ray不可用")
    return False

def check_proxy_manager():
    """检查代理管理器"""
    print(f"\n⚙️ 检查代理管理器:")
    
    try:
        pm = ProxyManager()
        print(f"  ✓ 代理管理器初始化成功")
        print(f"  ✓ 分配端口: {pm.local_socks_port}")
        print(f"  ✓ 配置文件路径: {pm.temp_config_file}")
        
        # 检查配置文件目录
        config_dir = os.path.dirname(pm.temp_config_file)
        if os.path.exists(config_dir):
            print(f"  ✓ 配置文件目录存在: {config_dir}")
        else:
            print(f"  ❌ 配置文件目录不存在: {config_dir}")
            
        return pm
        
    except Exception as e:
        print(f"  ❌ 代理管理器初始化失败: {e}")
        return None

def test_config_generation():
    """测试配置生成"""
    print(f"\n📄 测试配置生成:")
    
    # 创建测试用的VMESS配置
    test_vmess = {
        "add": "example.com",
        "port": "443",
        "id": "12345678-1234-1234-1234-123456789abc", 
        "aid": "0",
        "net": "ws",
        "type": "none",
        "host": "example.com",
        "path": "/",
        "tls": "tls",
        "ps": "测试节点",
        "scy": "auto"
    }
    
    try:
        pm = ProxyManager()
        if pm:
            v2ray_config = pm.generate_v2ray_config(test_vmess)
            print(f"  ✓ V2Ray配置生成成功")
            
            # 尝试保存配置
            test_config_file = "test_config.json"
            with open(test_config_file, 'w', encoding='utf-8') as f:
                json.dump(v2ray_config, f, indent=2, ensure_ascii=False)
            print(f"  ✓ 配置文件保存成功: {test_config_file}")
            
            # 清理测试文件
            os.remove(test_config_file)
            print(f"  ✓ 测试文件已清理")
            
            return True
        else:
            print(f"  ❌ 代理管理器不可用")
            return False
            
    except Exception as e:
        print(f"  ❌ 配置生成测试失败: {e}")
        return False

def main():
    """主诊断流程"""
    print("="*80)
    print("🔍 VPS代理系统诊断工具")
    print("="*80)
    
    # 1. 检查端口
    available_port = check_port_usage()
    
    # 2. 检查V2Ray核心
    v2ray_ok = check_v2ray_core()
    
    # 3. 检查代理管理器
    pm = check_proxy_manager()
    
    # 4. 测试配置生成
    config_ok = test_config_generation()
    
    # 总结
    print(f"\n📋 诊断总结:")
    print(f"  端口检查: {'✓ 通过' if available_port else '❌ 失败'}")
    print(f"  V2Ray核心: {'✓ 通过' if v2ray_ok else '❌ 失败'}")
    print(f"  代理管理器: {'✓ 通过' if pm else '❌ 失败'}")
    print(f"  配置生成: {'✓ 通过' if config_ok else '❌ 失败'}")
    
    if all([available_port, v2ray_ok, pm, config_ok]):
        print(f"\n🎉 所有检查通过！代理系统应该可以正常工作")
        if available_port != 1080:
            print(f"💡 建议: 使用端口 {available_port} 而不是默认的 1080")
    else:
        print(f"\n⚠️ 发现问题，请根据上述信息进行修复")
    
    print("="*80)

if __name__ == "__main__":
    main() 