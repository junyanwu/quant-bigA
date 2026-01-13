#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动Web UI服务器 - 使用端口8080
"""

import os
import sys
import webbrowser
import threading
import time

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def open_browser():
    """自动打开浏览器"""
    time.sleep(3)
    webbrowser.open('http://localhost:8080')

def main():
    """主函数"""
    print("🚀 A股量化交易系统 - Web UI")
    print("=" * 60)
    
    try:
        from webui.app import app, socketio
        
        # 启动浏览器线程
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        print("🌐 Web UI启动成功!")
        print("📊 访问地址: http://localhost:8080")
        print("💡 按 Ctrl+C 停止服务器")
        print("-" * 60)
        
        # 启动服务器（使用端口8080）
        socketio.run(app, host='0.0.0.0', port=8080, debug=False)
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("💡 请安装依赖包: pip install flask flask-socketio eventlet pandas numpy")
    except Exception as e:
        print(f"❌ Web UI启动失败: {e}")

if __name__ == "__main__":
    main()