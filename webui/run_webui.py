#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web UI启动脚本
"""

import os
import sys
import webbrowser
import threading
import time
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_dependencies():
    """检查依赖包"""
    required_packages = [
        ('flask', 'flask'),
        ('flask-socketio', 'flask_socketio'),
        ('eventlet', 'eventlet')
    ]
    missing_packages = []
    
    for display_name, import_name in required_packages:
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(display_name)
    
    if missing_packages:
        print("❌ 缺少必要的依赖包:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n💡 请安装依赖:")
        print("   pip install flask flask-socketio eventlet")
        return False
    
    return True

def check_data_directory():
    """检查数据目录"""
    data_path = './data'
    if not os.path.exists(data_path):
        print("⚠️  数据目录不存在，将自动创建...")
        os.makedirs(data_path, exist_ok=True)
        os.makedirs(os.path.join(data_path, 'stocks'), exist_ok=True)
        os.makedirs(os.path.join(data_path, 'etfs'), exist_ok=True)
        os.makedirs(os.path.join(data_path, 'index'), exist_ok=True)
        print("✅ 数据目录创建完成")
    
    return True

def open_browser():
    """自动打开浏览器"""
    time.sleep(2)  # 等待服务器启动
    webbrowser.open('http://localhost:5000')

def main():
    """主函数"""
    print("🚀 A股量化交易系统 - Web UI")
    print("=" * 60)
    
    # 检查依赖
    if not check_dependencies():
        return
    
    # 检查数据目录
    if not check_data_directory():
        return
    
    # 导入Web应用
    try:
        from app import app, socketio
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("💡 请确保所有文件都存在且正确配置")
        return
    
    # 启动信息
    print("📊 系统信息:")
    print(f"   启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   访问地址: http://localhost:5000")
    print(f"   数据路径: ./data")
    
    # 启动浏览器线程
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # 启动Web服务器
    print("\n🌐 启动Web服务器...")
    print("💡 按 Ctrl+C 停止服务器")
    print("-" * 60)
    
    try:
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"\n❌ 服务器启动失败: {e}")

if __name__ == "__main__":
    main()