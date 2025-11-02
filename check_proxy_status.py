#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
检查代理状态并提供解决方案
"""

import socket
import requests
import time

def check_proxy_port(host='127.0.0.1', port=1081):
    """检查代理端口是否开启"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def test_proxy_http(proxy_host='127.0.0.1', proxy_port=1081):
    """测试代理HTTP访问"""
    try:
        proxies = {
            'http': f'socks5h://{proxy_host}:{proxy_port}',
            'https': f'socks5h://{proxy_host}:{proxy_port}'
        }
        
        response = requests.get('http://ipinfo.io/ip', 
                              proxies=proxies, 
                              timeout=10)
        return True, response.text.strip()
    except Exception as e:
        return False, str(e)

def main():
    print("🔍 检查代理状态")
    print("=" * 50)
    
    # 检查常见的代理端口
    common_ports = [1080, 1081, 1082, 7890, 8080]
    active_ports = []
    
    print("📡 检查代理端口...")
    for port in common_ports:
        if check_proxy_port('127.0.0.1', port):
            active_ports.append(port)
            print(f"✅ 端口 {port}: 开启")
        else:
            print(f"❌ 端口 {port}: 关闭")
    
    print()
    
    if active_ports:
        print(f"🎉 发现活跃的代理端口: {active_ports}")
        
        # 测试每个活跃端口的HTTP代理功能
        print("\n🌐 测试代理HTTP访问...")
        for port in active_ports:
            print(f"\n📡 测试端口 {port}:")
            success, result = test_proxy_http('127.0.0.1', port)
            if success:
                print(f"✅ 代理工作正常，出口IP: {result}")
                
                # 更新测试脚本中的端口
                print(f"\n💡 建议:")
                print(f"  1. 使用端口 {port} 进行VPS连接")
                print(f"  2. 在GUI中确保代理配置正确")
                
                # 创建一个更新的测试脚本
                create_updated_test_script(port)
                break
            else:
                print(f"❌ 代理测试失败: {result}")
    else:
        print("❌ 没有发现活跃的代理端口")
        print("\n🔧 解决方案:")
        print("  1. 启动代理配置界面: python gui_proxy_config_final.py")
        print("  2. 输入您的VMESS链接:")
        print("     vmess://ewogICJ2IjogIjIiLAogICJwcyI6ICJ2bWVzcytrY3B8S0k2VC5sb3ZlQHhyYXkuY29tIiwKICAiYWRkIjogIjE4OC4yNTMuMTE4LjE0MSIsCiAgInBvcnQiOiA1NDQwMiwKICAiaWQiOiAiMjBkNzdjN2YtMzJiZC00M2Q2LWMxZGMtNjI0OTllNmUxM2IzIiwKICAiYWlkIjogMCwKICAibmV0IjogImtjcCIsCiAgInR5cGUiOiAiZHRscyIsCiAgImhvc3QiOiAiIiwKICAicGF0aCI6ICJUVlc1QTlWUlg4IiwKICAidGxzIjogIm5vbmUiCn0=")
        print("  3. 点击'解析链接'然后'启动代理'")
        print("  4. 等待代理启动成功后再进行VPS连接测试")

def create_updated_test_script(port):
    """创建更新的测试脚本"""
    script_content = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
更新的VPS代理连接测试 - 使用端口 {port}
"""

import sys
import time
from ssh_client import SSHClient

def test_vps_with_correct_port():
    """使用正确的代理端口测试VPS连接"""
    print("🔍 使用正确的代理端口测试VPS连接")
    print("=" * 60)
    
    # VPS配置
    vps_config = {{
        'ip': '144.172.114.134',
        'port': 22,
        'username': 'root',
        'password': 'M2muuhX7my23SY'
    }}
    
    # 使用检测到的活跃端口
    proxy_config = {{
        'host': '127.0.0.1',
        'port': {port}
    }}
    
    print(f"📡 VPS: {{vps_config['username']}}@{{vps_config['ip']}}:{{vps_config['port']}}")
    print(f"🌐 代理: {{proxy_config['host']}}:{{proxy_config['port']}}")
    print()
    
    try:
        ssh_proxy = SSHClient(
            host=vps_config['ip'],
            port=vps_config['port'],
            username=vps_config['username'],
            password=vps_config['password'],
            proxy_host=proxy_config['host'],
            proxy_port=proxy_config['port']
        )
        
        print("正在通过代理连接...")
        start_time = time.time()
        success = ssh_proxy.connect(timeout=60)
        elapsed_time = time.time() - start_time
        
        if success:
            print(f"✅ 代理连接成功！响应时间: {{elapsed_time:.2f}}秒")
            
            # 执行测试命令
            cmd_success, output, error = ssh_proxy.execute_command("echo 'Proxy SSH test successful'")
            if cmd_success:
                print(f"✅ 命令执行成功: {{output}}")
            
            ssh_proxy.close()
            
            print("\\n🎉 VPS代理连接测试成功！")
            print("💡 现在可以在GUI中使用代理进行批量操作了")
            
        else:
            print(f"❌ 代理连接失败: {{ssh_proxy.last_error}}")
            print(f"   耗时: {{elapsed_time:.2f}}秒")
            
    except Exception as e:
        print(f"❌ 测试异常: {{str(e)}}")

if __name__ == "__main__":
    test_vps_with_correct_port()
'''
    
    with open('test_vps_updated.py', 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print(f"\n📝 已创建更新的测试脚本: test_vps_updated.py")
    print("   运行命令: python test_vps_updated.py")

if __name__ == "__main__":
    main() 