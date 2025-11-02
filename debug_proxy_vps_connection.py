#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试VPS代理连接问题
"""

import logging
import socket
import time
from ssh_client import SSHClient
from proxy_manager_v2rayn import V2rayNStyleProxyManager

# 配置详细日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def test_proxy_status():
    """检查代理状态"""
    print("=" * 60)
    print("🔍 检查代理状态")
    print("=" * 60)
    
    # 检查端口1081是否可连接
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('127.0.0.1', 1081))
        sock.close()
        
        if result == 0:
            print("✅ 端口1081可连接")
        else:
            print("❌ 端口1081不可连接")
            return False
    except Exception as e:
        print(f"❌ 端口测试失败: {e}")
        return False
    
    # 测试SOCKS5协议
    try:
        import requests
        proxies = {
            'http': 'socks5://127.0.0.1:1081',
            'https': 'socks5://127.0.0.1:1081'
        }
        
        response = requests.get('http://httpbin.org/ip', proxies=proxies, timeout=10)
        if response.status_code == 200:
            result_data = response.json()
            print(f"✅ SOCKS5代理可用，出口IP: {result_data.get('origin', 'N/A')}")
            return True
        else:
            print(f"❌ SOCKS5测试失败，状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ SOCKS5测试异常: {e}")
        return False

def test_ssh_direct_connection():
    """测试SSH直连"""
    print("\n" + "=" * 60)
    print("🔍 测试SSH直连")
    print("=" * 60)
    
    # 使用一个已知可直连的IP
    ssh_client = SSHClient(
        host='67.220.72.156',
        port=22,
        username='root',
        password='ASAasal92.0'
    )
    
    print("测试直连到 67.220.72.156...")
    success = ssh_client.connect(timeout=30)
    
    if success:
        print("✅ 直连成功")
        ssh_client.disconnect()
        return True
    else:
        print(f"❌ 直连失败: {ssh_client.last_error}")
        return False

def test_ssh_proxy_connection():
    """测试SSH代理连接"""
    print("\n" + "=" * 60)
    print("🔍 测试SSH代理连接")
    print("=" * 60)
    
    # 使用一个可能被封的IP
    ssh_client = SSHClient(
        host='38.110.1.13',
        port=22,
        username='root',
        password='ASAasal92.0',
        proxy_host='127.0.0.1',
        proxy_port=1081
    )
    
    print("测试代理连接到 38.110.1.13...")
    success = ssh_client.connect(timeout=45)
    
    if success:
        print("✅ 代理连接成功")
        ssh_client.disconnect()
        return True
    else:
        print(f"❌ 代理连接失败: {ssh_client.last_error}")
        return False

def test_different_vps():
    """测试不同的VPS"""
    print("\n" + "=" * 60)
    print("🔍 测试不同VPS的代理连接")
    print("=" * 60)
    
    test_cases = [
        {
            'name': '可直连IP',
            'ip': '67.220.72.156',
            'password': 'ASAasal92.0'
        },
        {
            'name': '可能被封IP',
            'ip': '38.110.1.13', 
            'password': 'ASAasal92.0'
        },
        {
            'name': '另一个IP',
            'ip': '67.220.73.228',
            'password': 'ASAasal92.0'
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\n测试 {test_case['name']} ({test_case['ip']})...")
        
        # 直连测试
        ssh_direct = SSHClient(
            host=test_case['ip'],
            port=22,
            username='root',
            password=test_case['password']
        )
        
        direct_success = ssh_direct.connect(timeout=20)
        if direct_success:
            ssh_direct.disconnect()
        
        # 代理测试
        ssh_proxy = SSHClient(
            host=test_case['ip'],
            port=22,
            username='root',
            password=test_case['password'],
            proxy_host='127.0.0.1',
            proxy_port=1081
        )
        
        proxy_success = ssh_proxy.connect(timeout=30)
        if proxy_success:
            ssh_proxy.disconnect()
        
        result = {
            'name': test_case['name'],
            'ip': test_case['ip'],
            'direct': direct_success,
            'proxy': proxy_success,
            'direct_error': ssh_direct.last_error if not direct_success else '',
            'proxy_error': ssh_proxy.last_error if not proxy_success else ''
        }
        results.append(result)
        
        print(f"  直连: {'✅' if direct_success else '❌'} {ssh_direct.last_error if not direct_success else ''}")
        print(f"  代理: {'✅' if proxy_success else '❌'} {ssh_proxy.last_error if not proxy_success else ''}")
    
    return results

def main():
    """主函数"""
    print("🔍 VPS代理连接问题诊断")
    print("=" * 60)
    
    # 检查代理状态
    if not test_proxy_status():
        print("\n❌ 代理不可用，请先启动代理")
        return
    
    # 测试SSH连接
    print("\n📊 SSH连接测试结果:")
    
    direct_ok = test_ssh_direct_connection()
    proxy_ok = test_ssh_proxy_connection()
    
    print(f"\n总结:")
    print(f"直连测试: {'✅ 成功' if direct_ok else '❌ 失败'}")
    print(f"代理测试: {'✅ 成功' if proxy_ok else '❌ 失败'}")
    
    if not proxy_ok:
        print("\n🔧 代理连接失败的可能原因:")
        print("1. 代理服务器配置问题")
        print("2. SOCKS5协议实现问题")
        print("3. SSH客户端代理设置问题")
        print("4. 网络超时设置问题")
        
        # 详细测试
        print("\n" + "=" * 60)
        print("🔬 详细VPS测试")
        print("=" * 60)
        
        results = test_different_vps()
        
        print(f"\n📋 测试总结:")
        for result in results:
            print(f"\n{result['name']} ({result['ip']}):")
            print(f"  直连: {'✅' if result['direct'] else '❌'} {result['direct_error']}")
            print(f"  代理: {'✅' if result['proxy'] else '❌'} {result['proxy_error']}")

if __name__ == "__main__":
    main() 