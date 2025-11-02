#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
V2Ray代理启动调试脚本
详细分析代理启动失败的原因
"""
import os
import subprocess
import json
import time
import socket
import logging
from proxy_manager import ProxyManager

# 设置详细日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def debug_v2ray_startup():
    """调试V2Ray启动过程"""
    print("="*80)
    print("🔍 V2Ray代理启动详细调试")
    print("="*80)
    
    # 测试用的VMESS配置
    test_vmess_base64 = "eyJhZGQiOiJleGFtcGxlLmNvbSIsImFpZCI6IjAiLCJhbHBuIjoiIiwiZnAiOiIiLCJob3N0IjoiZXhhbXBsZS5jb20iLCJpZCI6IjEyMzQ1Njc4LTEyMzQtMTIzNC0xMjM0LTEyMzQ1Njc4OWFiYyIsIm5ldCI6IndzIiwicGF0aCI6Ii8iLCJwb3J0IjoiNDQzIiwicHMiOiLmtYvor5XoioLngrkiLCJzY3kiOiJhdXRvIiwic25pIjoiIiwidGxzIjoidGxzIiwidHlwZSI6Im5vbmUiLCJ2IjoiMiJ9"
    test_vmess_link = f"vmess://{test_vmess_base64}"
    
    try:
        # 1. 创建代理管理器
        print("\n1. 创建代理管理器...")
        pm = ProxyManager()
        print(f"   ✓ 分配端口: {pm.local_socks_port}")
        
        # 2. 解析配置
        print(f"\n2. 解析VMESS配置...")
        config = pm.parse_vmess_link(test_vmess_link)
        if not config:
            print("   ❌ 配置解析失败")
            return
        print(f"   ✓ 配置解析成功")
        
        # 3. 检查配置文件
        print(f"\n3. 检查配置文件...")
        config_path = os.path.abspath(pm.temp_config_file)
        if os.path.exists(config_path):
            print(f"   ✓ 配置文件存在: {config_path}")
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            print(f"   ✓ 配置文件大小: {os.path.getsize(config_path)} 字节")
            print(f"   ✓ SOCKS端口: {config_data['inbounds'][0]['port']}")
        else:
            print(f"   ❌ 配置文件不存在")
            return
            
        # 4. 检查V2Ray程序
        print(f"\n4. 检查V2Ray程序...")
        v2ray_path = os.path.join(os.path.dirname(__file__), 'v2ray_core', 'v2ray.exe')
        v2ray_abs_path = os.path.abspath(v2ray_path)
        
        if os.path.exists(v2ray_abs_path):
            print(f"   ✓ V2Ray程序存在: {v2ray_abs_path}")
            
            # 测试V2Ray版本
            try:
                result = subprocess.run([v2ray_abs_path, 'version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    version_line = result.stdout.split('\n')[0]
                    print(f"   ✓ V2Ray版本: {version_line}")
                else:
                    print(f"   ❌ V2Ray版本检查失败: {result.stderr}")
                    return
            except Exception as e:
                print(f"   ❌ V2Ray版本检查异常: {e}")
                return
        else:
            print(f"   ❌ V2Ray程序不存在: {v2ray_abs_path}")
            return
            
        # 5. 检查端口可用性
        print(f"\n5. 检查端口 {pm.local_socks_port} 可用性...")
        if pm._is_port_available(pm.local_socks_port):
            print(f"   ✓ 端口 {pm.local_socks_port} 可用")
        else:
            print(f"   ❌ 端口 {pm.local_socks_port} 被占用")
            return
            
        # 6. 手动启动V2Ray并监控
        print(f"\n6. 手动启动V2Ray...")
        cmd = [v2ray_abs_path, 'run', '-config', config_path]
        print(f"   启动命令: {' '.join(cmd)}")
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.path.dirname(v2ray_abs_path)
            )
            print(f"   ✓ V2Ray进程已启动 (PID: {process.pid})")
            
            # 等待启动
            print("   等待V2Ray初始化...")
            for i in range(10):
                time.sleep(1)
                if process.poll() is not None:
                    stdout, stderr = process.communicate()
                    print(f"   ❌ V2Ray进程退出 (返回码: {process.returncode})")
                    if stdout:
                        print(f"   标准输出: {stdout.decode('utf-8', errors='ignore')}")
                    if stderr:
                        print(f"   错误输出: {stderr.decode('utf-8', errors='ignore')}")
                    return
                print(f"   等待中... ({i+1}/10)")
                
            # 检查进程状态
            if process.poll() is None:
                print(f"   ✓ V2Ray进程运行正常")
                
                # 测试端口连接
                print(f"\n7. 测试端口连接...")
                time.sleep(2)  # 等待端口完全开放
                
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.settimeout(5)
                        result = s.connect_ex(('127.0.0.1', pm.local_socks_port))
                        if result == 0:
                            print(f"   ✓ 端口 {pm.local_socks_port} 连接成功")
                            
                            # 8. 测试SOCKS代理
                            print(f"\n8. 测试SOCKS代理功能...")
                            test_socks_proxy(pm.local_socks_port)
                            
                        else:
                            print(f"   ❌ 端口 {pm.local_socks_port} 连接失败 (错误码: {result})")
                            
                except Exception as e:
                    print(f"   ❌ 端口连接测试异常: {e}")
                    
            else:
                stdout, stderr = process.communicate()
                print(f"   ❌ V2Ray进程已退出")
                if stderr:
                    print(f"   错误信息: {stderr.decode('utf-8', errors='ignore')}")
                    
            # 清理进程
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=5)
                print(f"   ✓ V2Ray进程已停止")
                
        except Exception as e:
            print(f"   ❌ 启动V2Ray失败: {e}")
            import traceback
            print(f"   详细错误: {traceback.format_exc()}")
            
    except Exception as e:
        print(f"\n❌ 调试过程异常: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")

def test_socks_proxy(port):
    """测试SOCKS代理功能"""
    try:
        import requests
        
        proxies = {
            'http': f'socks5://127.0.0.1:{port}',
            'https': f'socks5://127.0.0.1:{port}'
        }
        
        print(f"   测试HTTP请求通过SOCKS代理...")
        response = requests.get('http://httpbin.org/ip', 
                              proxies=proxies, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ SOCKS代理测试成功")
            print(f"   出口IP: {data.get('origin', '未知')}")
        else:
            print(f"   ❌ HTTP请求失败 (状态码: {response.status_code})")
            
    except Exception as e:
        print(f"   ❌ SOCKS代理测试失败: {e}")

if __name__ == "__main__":
    debug_v2ray_startup() 