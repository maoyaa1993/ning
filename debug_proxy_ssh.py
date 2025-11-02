#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试代理SSH连接问题
"""

import sys
import time
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_proxy_ssh():
    """测试代理SSH连接"""
    print("🚀 开始代理SSH连接测试")
    
    try:
        from proxy_manager_v2rayn import V2rayNStyleProxyManager
        from ssh_client import SSHClient
        
        # 1. 创建代理管理器
        print("1. 创建代理管理器...")
        pm = V2rayNStyleProxyManager()
        
        # 2. 解析SS链接
        print("2. 解析SS链接...")
        ss_url = "ss://2022-blake3-aes-256-gcm:3XkNVBmRdnEZo4QGux7ERq96FxrxKqPSZ453iOlnTibA@188.253.118.141:19009#ss"
        if not pm.parse_shadowsocks_link(ss_url):
            print("❌ SS链接解析失败")
            return False
        
        # 3. 启动代理
        print("3. 启动代理...")
        if not pm.start_proxy():
            print("❌ 代理启动失败")
            return False
        
        # 4. 获取代理信息
        print("4. 获取代理信息...")
        proxy_info = pm.get_proxy_info()
        print(f"   本地端口: {proxy_info.get('local_port')}")
        
        # 5. 创建SSH客户端
        print("5. 创建SSH客户端...")
        ssh = SSHClient(
            host='188.253.118.141',
            port=22,
            username='root',
            password='l38w1AGdYh939lOK',
            proxy_host='127.0.0.1',
            proxy_port=1081
        )
        
        # 6. 测试连接
        print("6. 测试SSH连接...")
        start_time = time.time()
        result = ssh.connect(timeout=30)
        connect_time = time.time() - start_time
        
        if result:
            print(f"✅ SSH连接成功 ({connect_time:.2f}s)")
            
            # 7. 执行测试命令
            print("7. 执行测试命令...")
            success, output, error = ssh.execute_command("whoami && curl -s ifconfig.me")
            if success:
                print(f"✅ 命令执行成功: {output.strip()}")
            else:
                print(f"❌ 命令执行失败: {error}")
            
            ssh.close()
            return True
        else:
            print(f"❌ SSH连接失败: {ssh.last_error}")
            ssh.close()
            return False
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False
    finally:
        try:
            pm.stop_proxy()
            print("🧹 代理已停止")
        except:
            pass

if __name__ == "__main__":
    test_proxy_ssh() 