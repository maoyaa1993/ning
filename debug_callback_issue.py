#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试status_callback问题
验证ExcelManager中的回调设置问题
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_callback_issue():
    """测试回调设置问题"""
    print("=" * 60)
    print("🔍 测试ExcelManager status_callback问题")
    print("=" * 60)
    
    try:
        from excel_manager import ExcelManager
        
        # 创建测试回调函数
        callback1_calls = []
        callback2_calls = []
        
        def callback1(**kwargs):
            callback1_calls.append(kwargs)
            print(f"[CALLBACK1] 收到调用: {kwargs}")
        
        def callback2(**kwargs):
            callback2_calls.append(kwargs)
            print(f"[CALLBACK2] 收到调用: {kwargs}")
        
        print("1. 创建ExcelManager实例...")
        excel_manager = ExcelManager()
        
        print("2. 通过set_status_callback设置回调1...")
        excel_manager.set_status_callback(callback1)
        print(f"   excel_manager.status_callback: {excel_manager.status_callback}")
        
        print("3. 创建测试VPS数据...")
        test_vps = [{
            'name': 'Debug-Test',
            'ip': '192.168.1.1',
            'port': 22,
            'username': 'root',
            'password': 'test',
            'row_index': 2
        }]
        
        print("4. 调用batch_test_vps，传入callback2...")
        print(f"   传入的status_callback: {callback2}")
        
        # 这里应该会覆盖callback1
        results = excel_manager.batch_test_vps(
            test_vps,
            max_workers=1,
            status_callback=callback2
        )
        
        print("5. 检查结果...")
        print(f"   excel_manager.status_callback: {excel_manager.status_callback}")
        print(f"   callback1被调用次数: {len(callback1_calls)}")
        print(f"   callback2被调用次数: {len(callback2_calls)}")
        
        if len(callback1_calls) > 0:
            print("   ❌ callback1被调用了，说明覆盖没有发生")
        else:
            print("   ✅ callback1没有被调用，说明确实被覆盖了")
            
        if len(callback2_calls) > 0:
            print("   ✅ callback2被调用了，这是正确的")
        else:
            print("   ❌ callback2没有被调用，有其他问题")
        
        return len(callback2_calls) > 0
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gui_callback_setup():
    """测试GUI回调设置问题"""
    print("\n" + "=" * 60)
    print("🔍 测试GUI回调设置问题")
    print("=" * 60)
    
    try:
        # 模拟GUI的回调设置过程
        from excel_manager import ExcelManager
        
        gui_callback_calls = []
        
        def mock_update_batch_test_progress(**kwargs):
            gui_callback_calls.append(kwargs)
            print(f"[GUI] update_batch_test_progress被调用: {kwargs}")
        
        print("1. 模拟GUI创建ExcelManager...")
        excel_manager = ExcelManager()
        
        print("2. 模拟GUI设置status_callback...")
        excel_manager.set_status_callback(mock_update_batch_test_progress)
        print(f"   设置后的callback: {excel_manager.status_callback}")
        
        print("3. 模拟GUI调用batch_test_vps (传入相同的callback)...")
        test_vps = [{
            'name': 'GUI-Test',
            'ip': '192.168.1.2', 
            'port': 22,
            'username': 'root',
            'password': 'test',
            'row_index': 2
        }]
        
        # 这里模拟GUI的调用方式
        results = excel_manager.batch_test_vps(
            test_vps,
            max_workers=1,
            status_callback=mock_update_batch_test_progress  # 传入相同的callback
        )
        
        print("4. 检查结果...")
        print(f"   GUI回调被调用次数: {len(gui_callback_calls)}")
        
        if len(gui_callback_calls) > 0:
            print("   ✅ GUI回调工作正常")
            print("   回调内容:")
            for i, call in enumerate(gui_callback_calls, 1):
                ssh_log = call.get('ssh_log', 'None')
                vps_name = call.get('vps_name', 'None')
                print(f"     {i}. ssh_log='{ssh_log}', vps_name='{vps_name}'")
            return True
        else:
            print("   ❌ GUI回调没有被调用")
            return False
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("ExcelManager status_callback问题调试")
    print("=" * 60)
    
    # 测试1: 回调覆盖问题
    test1_result = test_callback_issue()
    
    # 测试2: GUI回调设置问题
    test2_result = test_gui_callback_setup()
    
    print("\n" + "=" * 60)
    print("🎯 调试总结")
    print("=" * 60)
    print(f"回调覆盖测试: {'✅ 正常' if test1_result else '❌ 异常'}")
    print(f"GUI回调测试: {'✅ 正常' if test2_result else '❌ 异常'}")
    
    if not test1_result or not test2_result:
        print("\n⚠️  发现问题，需要修复回调机制。")
    else:
        print("\n🎉 回调机制工作正常，问题可能在其他地方。") 