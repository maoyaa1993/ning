"""
AsyncSSH客户端 - 替代paramiko的高性能SSH连接模块
专门解决代理连接问题

安装依赖:
pip install asyncssh

优势:
1. 原生SOCKS代理支持
2. 异步高性能
3. 更好的错误处理
4. 现代化API设计
5. 自动检测活跃代理端口
"""

import asyncio
import asyncssh
import socket
import time
import socks
from typing import Optional, Dict, Any, Tuple, Union, List


class AsyncSSHClient:
    """基于AsyncSSH的高性能SSH客户端"""
    
    def __init__(self, proxy_host: Optional[str] = None, proxy_port: Optional[int] = None, 
                 auto_detect_proxy: bool = True):
        """
        初始化AsyncSSH客户端
        
        Args:
            proxy_host: SOCKS代理主机 (如: '127.0.0.1')
            proxy_port: SOCKS代理端口 (如: 1081)
            auto_detect_proxy: 是否自动检测活跃代理端口
        """
        self.proxy_host = proxy_host or '127.0.0.1'
        self.proxy_port = proxy_port
        self.auto_detect_proxy = auto_detect_proxy
        self.connection = None
        self.active_proxy_port = None
        
    def _detect_active_proxy_ports(self) -> List[int]:
        """检测活跃的代理端口"""
        common_ports = [1080, 1081, 1082, 7890, 8080, 8888, 1087, 7891]
        active_ports = []
        
        for port in common_ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((self.proxy_host, port))
                sock.close()
                if result == 0:
                    active_ports.append(port)
                    print(f"✅ 检测到活跃代理端口: {port}")
            except:
                continue
        
        return active_ports
    
    def _test_proxy_functionality(self, port: int) -> bool:
        """测试代理端口的实际功能"""
        try:
            import requests
            
            proxies = {
                'http': f'socks5h://{self.proxy_host}:{port}',
                'https': f'socks5h://{self.proxy_host}:{port}'
            }
            
            # 测试简单的HTTP请求
            response = requests.get('http://httpbin.org/ip', 
                                  proxies=proxies, 
                                  timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 端口 {port} 代理功能正常，出口IP: {data.get('origin', 'unknown')}")
                return True
            else:
                print(f"⚠️ 端口 {port} 响应异常: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 端口 {port} 代理测试失败: {e}")
            return False
    
    def _get_best_proxy_port(self) -> Optional[int]:
        """获取最佳的代理端口"""
        if self.proxy_port:
            # 如果指定了端口，先测试该端口
            if self._test_proxy_functionality(self.proxy_port):
                return self.proxy_port
        
        if not self.auto_detect_proxy:
            return self.proxy_port
        
        print("🔍 自动检测活跃代理端口...")
        active_ports = self._detect_active_proxy_ports()
        
        if not active_ports:
            print("❌ 未检测到活跃的代理端口")
            return None
        
        # 测试每个活跃端口的代理功能
        for port in active_ports:
            if self._test_proxy_functionality(port):
                return port
        
        print("❌ 所有检测到的端口都无法正常工作")
        return None
        
    async def connect(self, 
                     hostname: str, 
                     port: int = 22,
                     username: str = 'root',
                     password: Optional[str] = None,
                     private_key: Optional[str] = None,
                     timeout: int = 30,
                     use_proxy: bool = True) -> bool:
        """
        连接到SSH服务器
        
        Args:
            hostname: 主机地址
            port: SSH端口
            username: 用户名
            password: 密码
            private_key: 私钥路径
            timeout: 连接超时时间
            use_proxy: 是否使用代理
            
        Returns:
            bool: 连接是否成功
        """
        try:
            # 构建连接参数
            connect_kwargs = {
                'host': hostname,
                'port': port,
                'username': username,
                'known_hosts': None,  # 忽略主机密钥验证
                'connect_timeout': timeout,
            }
            
            # 添加认证信息
            if password:
                connect_kwargs['password'] = password
            if private_key:
                connect_kwargs['client_keys'] = [private_key]
            
            # 代理连接逻辑
            if use_proxy:
                self.active_proxy_port = self._get_best_proxy_port()
                
                if self.active_proxy_port:
                    print(f"🌐 使用代理连接: {self.proxy_host}:{self.active_proxy_port}")
                    # 使用自定义的代理连接工厂
                    connect_kwargs['sock'] = await self._create_proxy_socket(hostname, port, timeout)
                else:
                    print("⚠️ 未找到可用代理，切换到直连模式")
                    use_proxy = False
            
            if not use_proxy:
                print("🔗 使用直连模式")
            
            # 建立连接
            self.connection = await asyncssh.connect(**connect_kwargs)
            
            connection_mode = f"代理模式 ({self.proxy_host}:{self.active_proxy_port})" if use_proxy else "直连模式"
            print(f"✅ SSH连接成功 - {connection_mode}")
            return True
            
        except Exception as e:
            print(f"❌ SSH连接失败: {e}")
            return False
    
    async def _create_proxy_socket(self, target_host: str, target_port: int, timeout: int):
        """创建代理socket连接"""
        try:
            # 在执行器中创建SOCKS连接
            def create_socks_connection():
                # 创建SOCKS socket
                sock = socks.socksocket()
                sock.set_proxy(socks.SOCKS5, self.proxy_host, self.active_proxy_port)
                sock.settimeout(timeout)
                
                # 连接到目标主机
                sock.connect((target_host, target_port))
                return sock
            
            # 在线程池中执行阻塞的SOCKS连接
            loop = asyncio.get_event_loop()
            sock = await loop.run_in_executor(None, create_socks_connection)
            
            return sock
            
        except Exception as e:
            raise Exception(f"SOCKS代理连接失败: {e}")
    
    async def execute_command(self, command: str, timeout: int = 30) -> Tuple[str, str, int]:
        """
        执行SSH命令
        
        Args:
            command: 要执行的命令
            timeout: 执行超时时间
            
        Returns:
            Tuple[stdout, stderr, exit_code]
        """
        if not self.connection:
            raise Exception("SSH连接未建立")
        
        try:
            result = await asyncio.wait_for(
                self.connection.run(command, check=False),
                timeout=timeout
            )
            
            return (
                result.stdout or '',
                result.stderr or '',
                result.exit_status
            )
            
        except asyncio.TimeoutError:
            raise Exception(f"命令执行超时: {command}")
        except Exception as e:
            raise Exception(f"命令执行失败: {e}")
    
    async def test_connection(self) -> Dict[str, Any]:
        """测试SSH连接状态"""
        if not self.connection:
            return {
                'connected': False,
                'error': 'SSH连接未建立'
            }
        
        try:
            # 执行简单的测试命令
            start_time = time.time()
            stdout, stderr, exit_code = await self.execute_command('echo "test"', timeout=10)
            response_time = time.time() - start_time
            
            return {
                'connected': True,
                'response_time': round(response_time, 3),
                'test_output': stdout.strip(),
                'exit_code': exit_code,
                'proxy_port': self.active_proxy_port,
                'connection_mode': f"代理模式 ({self.proxy_host}:{self.active_proxy_port})" if self.active_proxy_port else "直连模式"
            }
            
        except Exception as e:
            return {
                'connected': False,
                'error': str(e)
            }
    
    async def close(self):
        """关闭SSH连接"""
        if self.connection:
            self.connection.close()
            await self.connection.wait_closed()
            self.connection = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()


class AsyncSSHManager:
    """AsyncSSH批量管理器"""
    
    def __init__(self, proxy_host: Optional[str] = None, proxy_port: Optional[int] = None,
                 auto_detect_proxy: bool = True):
        self.proxy_host = proxy_host or '127.0.0.1'
        self.proxy_port = proxy_port
        self.auto_detect_proxy = auto_detect_proxy
    
    async def test_multiple_vps(self, vps_list: list, max_concurrent: int = 10, 
                               use_proxy: bool = True) -> Dict[str, Any]:
        """
        批量测试多个VPS连接
        
        Args:
            vps_list: VPS信息列表
            max_concurrent: 最大并发数
            use_proxy: 是否使用代理
            
        Returns:
            Dict: 测试结果
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        tasks = []
        
        async def test_single_vps(vps_info):
            async with semaphore:
                return await self._test_vps_connection(vps_info, use_proxy)
        
        # 创建所有测试任务
        for vps_info in vps_list:
            task = asyncio.create_task(test_single_vps(vps_info))
            tasks.append(task)
        
        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 统计结果
        success_count = sum(1 for r in results if isinstance(r, dict) and r.get('success'))
        failed_count = len(results) - success_count
        
        return {
            'total': len(vps_list),
            'success': success_count,
            'failed': failed_count,
            'results': results
        }
    
    async def _test_vps_connection(self, vps_info: Dict[str, Any], use_proxy: bool = True) -> Dict[str, Any]:
        """测试单个VPS连接"""
        start_time = time.time()
        
        try:
            async with AsyncSSHClient(
                proxy_host=self.proxy_host,
                proxy_port=self.proxy_port,
                auto_detect_proxy=self.auto_detect_proxy
            ) as client:
                
                # 建立连接
                connected = await client.connect(
                    hostname=vps_info.get('ip'),
                    port=vps_info.get('port', 22),
                    username=vps_info.get('username', 'root'),
                    password=vps_info.get('password'),
                    timeout=30,
                    use_proxy=use_proxy
                )
                
                if not connected:
                    return {
                        'vps_info': vps_info,
                        'success': False,
                        'error': 'SSH连接失败',
                        'response_time': time.time() - start_time
                    }
                
                # 测试连接状态
                test_result = await client.test_connection()
                
                return {
                    'vps_info': vps_info,
                    'success': test_result['connected'],
                    'response_time': test_result.get('response_time', time.time() - start_time),
                    'test_output': test_result.get('test_output'),
                    'connection_mode': test_result.get('connection_mode'),
                    'proxy_port': test_result.get('proxy_port'),
                    'error': test_result.get('error')
                }
                
        except Exception as e:
            return {
                'vps_info': vps_info,
                'success': False,
                'error': str(e),
                'response_time': time.time() - start_time
            }


# 使用示例
async def example_usage():
    """使用示例"""
    
    print("🚀 AsyncSSH自动代理检测测试")
    print("=" * 50)
    
    # 1. 自动检测代理端口的单个VPS连接测试
    print("🔄 测试单个VPS连接（自动检测代理）...")
    async with AsyncSSHClient(auto_detect_proxy=True) as client:
        success = await client.connect(
            hostname='144.172.114.134',
            port=22,
            username='root',
            password='M2muuhX7my23SY',
            use_proxy=True
        )
        
        if success:
            test_result = await client.test_connection()
            print(f"📊 连接测试结果:")
            print(f"   连接状态: {'✅ 成功' if test_result['connected'] else '❌ 失败'}")
            print(f"   连接模式: {test_result.get('connection_mode', '未知')}")
            print(f"   响应时间: {test_result.get('response_time', 0)}s")
            
            if test_result['connected']:
                # 执行命令测试
                stdout, stderr, exit_code = await client.execute_command('uname -a')
                print(f"💻 系统信息: {stdout.strip()}")
        else:
            print("❌ SSH连接失败")
    
    # 2. 批量VPS测试（带自动代理检测）
    print(f"\n🔄 批量VPS连接测试（自动检测代理）...")
    vps_list = [
        {
            'name': 'VPS-1',
            'ip': '144.172.114.134',
            'port': 22,
            'username': 'root',
            'password': 'M2muuhX7my23SY'
        },
        # 可以添加更多VPS
    ]
    
    manager = AsyncSSHManager(auto_detect_proxy=True)
    batch_results = await manager.test_multiple_vps(vps_list, max_concurrent=5, use_proxy=True)
    
    print(f"📈 批量测试结果:")
    print(f"   总数: {batch_results['total']}")
    print(f"   成功: {batch_results['success']}")
    print(f"   失败: {batch_results['failed']}")
    
    # 显示详细结果
    for i, result in enumerate(batch_results['results']):
        if isinstance(result, dict):
            vps_name = result['vps_info'].get('name', f'VPS-{i+1}')
            status = '✅ 成功' if result['success'] else '❌ 失败'
            mode = result.get('connection_mode', '未知')
            time_cost = result.get('response_time', 0)
            
            print(f"   {vps_name}: {status} ({mode}) - {time_cost:.2f}s")
            if not result['success']:
                print(f"      错误: {result.get('error', '未知错误')}")
    
    # 3. 测试直连模式（不使用代理）
    print(f"\n🔄 测试直连模式...")
    async with AsyncSSHClient() as client:
        success = await client.connect(
            hostname='144.172.114.134',
            port=22,
            username='root',
            password='M2muuhX7my23SY',
            use_proxy=False
        )
        
        if success:
            test_result = await client.test_connection()
            print(f"📊 直连测试: {'✅ 成功' if test_result['connected'] else '❌ 失败'}")
            print(f"   响应时间: {test_result.get('response_time', 0)}s")


if __name__ == '__main__':
    # 运行示例
    asyncio.run(example_usage()) 