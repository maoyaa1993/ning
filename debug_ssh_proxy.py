#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
调试SSH代理连接问题
详细分析为什么SSH连接在使用代理时失败
"""
import logging
import socket
import time
import requests
from ssh_client import SSHClient
from proxy_manager_v2rayn import V2rayNStyleProxyManager

# 设置详细日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def test_proxy_working():
    """测试代理是否正常工作"""
    print("="*80)
    print("🔍 测试代理是否正常工作")
    print("="*80)
    
    # 使用当前正在运行的代理端口1082
    proxy_port = 1082
    
    print(f"\n1. 测试端口 {proxy_port} 是否可连接:")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(3)
            result = s.connect_ex(('127.0.0.1', proxy_port))
            if result == 0:
                print(f"   ✓ 端口 {proxy_port} 可连接")
            else:
                print(f"   ❌ 端口 {proxy_port} 连接失败 (错误码: {result})")
                return False
    except Exception as e:
        print(f"   ❌ 端口测试异常: {e}")
        return False

    print(f"\n2. 测试HTTP代理连接:")
    try:
        proxies = {
            'http': f'socks5://127.0.0.1:{proxy_port}',
            'https': f'socks5://127.0.0.1:{proxy_port}'
        }
        
        response = requests.get('http://httpbin.org/ip', proxies=proxies, timeout=15)
        if response.status_code == 200:
            ip_info = response.json()
            print(f"   ✓ HTTP代理连接成功")
            print(f"   出口IP: {ip_info.get('origin', '未知')}")
            return True
        else:
            print(f"   ❌ HTTP请求失败，状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ HTTP代理测试失败: {e}")
        return False

def test_ssh_direct_connection():
    """测试直连SSH连接"""
    print("\n3. 测试直连SSH连接:")
    
    # 使用一个公开的SSH测试服务器或者用户提供的IP
    test_ips = [
        '8.8.8.8',  # Google DNS (通常可达但不提供SSH)
        '67.220.72.156',  # 从截图中看到的一个IP
    ]
    
    for ip in test_ips:
        print(f"   测试直连: {ip}")
        ssh_client = SSHClient(
            host=ip,
            port=22,
            username='root',
            password='test123',
            proxy_host=None,
            proxy_port=None
        )
        
        success, error = ssh_client.test_connection()
        if success:
            print(f"   ✓ 直连成功: {ip}")
        else:
            print(f"   ❌ 直连失败: {ip} - {error}")

def test_ssh_proxy_connection():
    """测试通过代理的SSH连接"""
    print("\n4. 测试通过代理的SSH连接:")
    
    proxy_port = 1082
    
    # 使用截图中看到的IP进行测试
    test_ips = [
        '67.220.72.156',  # 从截图中看到的一个成功的IP
        '38.110.1.132',   # 从截图中看到的一个失败的IP
    ]
    
    for ip in test_ips:
        print(f"   测试代理连接: {ip} (通过 127.0.0.1:{proxy_port})")
        ssh_client = SSHClient(
            host=ip,
            port=22,
            username='root',
            password='test123',  # 这个密码是假的，但可以测试连接性
            proxy_host='127.0.0.1',
            proxy_port=proxy_port
        )
        
        success, error = ssh_client.test_connection()
        if success:
            print(f"   ✓ 代理连接成功: {ip}")
        else:
            print(f"   ❌ 代理连接失败: {ip} - {error}")

def test_socks_connectivity():
    """测试SOCKS连接性"""
    print("\n5. 测试SOCKS连接性:")
    
    try:
        import socks
        proxy_port = 1082
        
        # 创建SOCKS代理socket
        sock = socks.socksocket()
        sock.set_proxy(socks.SOCKS5, '127.0.0.1', proxy_port)
        sock.settimeout(10)
        
        # 尝试连接到一个已知的服务器
        test_host = '8.8.8.8'
        test_port = 53  # DNS端口，通常开放
        
        print(f"   尝试通过代理连接到 {test_host}:{test_port}")
        sock.connect((test_host, test_port))
        sock.close()
        print(f"   ✓ SOCKS代理连接成功")
        return True
        
    except Exception as e:
        print(f"   ❌ SOCKS代理连接失败: {e}")
        return False

def main():
    """主函数"""
    print("="*80)
    print("🚀 SSH代理连接问题诊断")
    print("="*80)
    
    # 测试1: 代理是否正常工作
    if not test_proxy_working():
        print("\n❌ 代理不工作，无法继续测试")
        return
    
    # 测试2: 直连SSH
    test_ssh_direct_connection()
    
    # 测试3: SOCKS连接性
    if not test_socks_connectivity():
        print("\n❌ SOCKS连接有问题")
        return
    
    # 测试4: 代理SSH连接
    test_ssh_proxy_connection()
    
    print("\n" + "="*80)
    print("🎉 诊断完成！")
    print("="*80)

if __name__ == "__main__":
    main() 