"""
深入调试SSH通过SOCKS代理的问题
重点分析协议层面而非流量检测问题
"""

import socket
import socks
import time
import threading
import paramiko
from proxy_manager_v2rayn import V2rayNStyleProxyManager


def test_raw_socket_communication(proxy_port, target_host, target_port):
    """测试原始socket通信，逐步分析问题"""
    print(f"\n🔍 深入测试原始socket通信...")
    
    try:
        # 1. 创建SOCKS socket
        print("1. 创建SOCKS socket...")
        sock = socks.socksocket(socket.AF_INET, socket.SOCK_STREAM)
        sock.set_proxy(socks.SOCKS5, '127.0.0.1', proxy_port)
        sock.settimeout(30)
        
        # 2. 建立连接
        print(f"2. 连接到 {target_host}:{target_port}...")
        start_time = time.time()
        sock.connect((target_host, target_port))
        connect_time = time.time() - start_time
        print(f"   ✅ 连接成功 ({connect_time:.2f}s)")
        
        # 3. 设置为非阻塞模式进行详细测试
        sock.settimeout(10)
        
        # 4. 监听服务器的初始响应
        print("3. 等待SSH服务器banner...")
        try:
            # SSH服务器应该主动发送banner
            initial_data = sock.recv(1024)
            if initial_data:
                print(f"   ✅ 收到服务器banner: {initial_data[:50]}...")
                if b'SSH' in initial_data:
                    print("   ✅ 确认是SSH协议")
                    
                    # 5. 发送客户端banner
                    print("4. 发送客户端SSH banner...")
                    client_banner = b"SSH-2.0-Python-Test\r\n"
                    sock.send(client_banner)
                    print("   ✅ 客户端banner已发送")
                    
                    # 6. 等待服务器响应
                    print("5. 等待服务器响应...")
                    response = sock.recv(1024)
                    if response:
                        print(f"   ✅ 服务器响应: {response[:50]}...")
                        return True
                    else:
                        print("   ❌ 服务器无响应")
                        return False
                else:
                    print(f"   ❌ 不是SSH协议: {initial_data}")
                    return False
            else:
                print("   ❌ 未收到服务器banner")
                return False
                
        except socket.timeout:
            print("   ❌ 等待SSH banner超时")
            return False
            
    except Exception as e:
        print(f"   ❌ 连接失败: {e}")
        return False
    finally:
        try:
            sock.close()
        except:
            pass


def test_direct_ssh_handshake(target_host, target_port):
    """测试直连SSH握手过程"""
    print(f"\n🔍 测试直连SSH握手过程...")
    
    try:
        # 1. 建立直连socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        
        print(f"1. 直连到 {target_host}:{target_port}...")
        sock.connect((target_host, target_port))
        print("   ✅ 直连成功")
        
        # 2. 接收SSH banner
        print("2. 接收SSH banner...")
        banner = sock.recv(1024)
        print(f"   SSH Banner: {banner.decode().strip()}")
        
        # 3. 发送客户端banner
        print("3. 发送客户端banner...")
        client_banner = b"SSH-2.0-Python-Test\r\n"
        sock.send(client_banner)
        
        # 4. 接收后续数据
        print("4. 接收握手数据...")
        handshake_data = sock.recv(1024)
        print(f"   握手数据长度: {len(handshake_data)} bytes")
        
        sock.close()
        return True
        
    except Exception as e:
        print(f"   ❌ 直连SSH测试失败: {e}")
        return False


def test_socks_vs_direct_timing(proxy_port, target_host, target_port):
    """对比SOCKS代理和直连的时序差异"""
    print(f"\n🔍 对比SOCKS代理和直连的时序...")
    
    # 测试直连时序
    print("1. 测试直连时序...")
    direct_times = []
    for i in range(3):
        try:
            start = time.time()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((target_host, target_port))
            banner = sock.recv(1024)
            end = time.time()
            direct_times.append(end - start)
            sock.close()
            print(f"   直连测试 {i+1}: {end-start:.3f}s")
        except Exception as e:
            print(f"   直连测试 {i+1} 失败: {e}")
    
    # 测试SOCKS代理时序
    print("2. 测试SOCKS代理时序...")
    proxy_times = []
    for i in range(3):
        try:
            start = time.time()
            sock = socks.socksocket()
            sock.set_proxy(socks.SOCKS5, '127.0.0.1', proxy_port)
            sock.settimeout(10)
            sock.connect((target_host, target_port))
            banner = sock.recv(1024)
            end = time.time()
            proxy_times.append(end - start)
            sock.close()
            print(f"   代理测试 {i+1}: {end-start:.3f}s")
        except Exception as e:
            print(f"   代理测试 {i+1} 失败: {e}")
    
    # 分析结果
    if direct_times and proxy_times:
        avg_direct = sum(direct_times) / len(direct_times)
        avg_proxy = sum(proxy_times) / len(proxy_times)
        print(f"\n📊 时序对比:")
        print(f"   直连平均: {avg_direct:.3f}s")
        print(f"   代理平均: {avg_proxy:.3f}s")
        print(f"   延迟增加: {avg_proxy - avg_direct:.3f}s")


def test_paramiko_socket_reuse(proxy_port, target_host, target_port, username, password):
    """测试Paramiko使用已建立的socket"""
    print(f"\n🔍 测试Paramiko使用预建立的socket...")
    
    try:
        # 1. 先建立SOCKS连接
        print("1. 建立SOCKS连接...")
        sock = socks.socksocket()
        sock.set_proxy(socks.SOCKS5, '127.0.0.1', proxy_port)
        sock.settimeout(30)
        sock.connect((target_host, target_port))
        print("   ✅ SOCKS连接已建立")
        
        # 2. 手动进行SSH握手
        print("2. 手动SSH握手...")
        
        # 接收服务器banner
        server_banner = sock.recv(1024)
        print(f"   服务器banner: {server_banner[:50]}...")
        
        # 发送客户端banner
        client_banner = b"SSH-2.0-paramiko_2.12.0\r\n"
        sock.send(client_banner)
        print("   客户端banner已发送")
        
        # 3. 使用Transport接管socket
        print("3. 创建Paramiko Transport...")
        transport = paramiko.Transport(sock)
        
        # 4. 启动客户端
        print("4. 启动SSH客户端...")
        transport.start_client(timeout=30)
        print("   ✅ SSH客户端启动成功")
        
        # 5. 认证
        print("5. 进行SSH认证...")
        transport.auth_password(username, password, fallback=False)
        print("   ✅ SSH认证成功")
        
        # 6. 测试命令执行
        print("6. 测试命令执行...")
        channel = transport.open_session(timeout=10)
        channel.exec_command('whoami')
        output = channel.recv(1024).decode().strip()
        print(f"   命令输出: {output}")
        
        channel.close()
        transport.close()
        return True
        
    except Exception as e:
        print(f"   ❌ Paramiko socket测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("🚀 深入调试SSH通过SOCKS代理的问题")
    print("=" * 60)
    
    # 启动SS代理
    print("1. 启动SS代理...")
    ss_link = "ss://2022-blake3-aes-256-gcm:3XkNVBmRdnEZo4QGux7ERq96FxrxKqPSZ453iOlnTibA@188.253.118.141:19009#ss"
    
    proxy_manager = V2rayNStyleProxyManager()
    if not proxy_manager.parse_proxy_link(ss_link):
        print("❌ SS链接解析失败")
        return
    
    if not proxy_manager.start_proxy():
        print("❌ SS代理启动失败")
        return
    
    proxy_port = proxy_manager.local_port
    print(f"✅ SS代理启动成功，端口: {proxy_port}")
    
    # 等待代理稳定
    time.sleep(2)
    
    # 测试目标
    target_host = '144.172.114.134'
    target_port = 22
    username = 'root'
    password = 'M2muuhX7my23SY'
    
    try:
        # 1. 测试直连SSH握手
        direct_ok = test_direct_ssh_handshake(target_host, target_port)
        
        # 2. 测试原始socket通信
        raw_ok = test_raw_socket_communication(proxy_port, target_host, target_port)
        
        # 3. 测试时序对比
        test_socks_vs_direct_timing(proxy_port, target_host, target_port)
        
        # 4. 测试Paramiko socket复用
        paramiko_ok = test_paramiko_socket_reuse(proxy_port, target_host, target_port, username, password)
        
        # 总结
        print("\n" + "=" * 60)
        print("🎯 深度测试结果:")
        print(f"   直连SSH握手: {'✅ 正常' if direct_ok else '❌ 异常'}")
        print(f"   原始SOCKS通信: {'✅ 正常' if raw_ok else '❌ 异常'}")
        print(f"   Paramiko代理: {'✅ 正常' if paramiko_ok else '❌ 异常'}")
        
        if direct_ok and not raw_ok:
            print("\n💡 分析结论:")
            print("   - 直连SSH正常，说明目标服务器没问题")
            print("   - SOCKS连接建立成功，但数据传输有问题")
            print("   - 可能是代理的数据转发机制问题")
            print("   - 建议检查代理配置或尝试其他代理节点")
        elif raw_ok and not paramiko_ok:
            print("\n💡 分析结论:")
            print("   - 原始SOCKS通信正常")
            print("   - 问题在Paramiko的实现方式")
            print("   - 可能是Paramiko与SOCKS的兼容性问题")
        
    finally:
        proxy_manager.stop_proxy()
        print("\n✅ 代理已停止")


if __name__ == '__main__':
    main() 