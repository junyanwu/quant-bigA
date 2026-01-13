#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Web UI启动
"""

import os
import sys

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试导入"""
    try:
        print("🔧 测试依赖包导入...")
        import flask
        import flask_socketio
        import eventlet
        print("✅ Flask相关包导入成功")
        
        print("🔧 测试数据科学包导入...")
        import pandas as pd
        import numpy as np
        print("✅ 数据科学包导入成功")
        
        return True
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        return False

def test_templates():
    """测试模板文件"""
    print("🔧 检查模板文件...")
    
    template_files = [
        'webui/templates/base.html',
        'webui/templates/index.html',
        'webui/templates/dashboard.html',
        'webui/templates/data_management.html',
        'webui/templates/dca_backtest.html'
    ]
    
    for template in template_files:
        if os.path.exists(template):
            print(f"✅ {template} 存在")
        else:
            print(f"❌ {template} 不存在")
            return False
    
    return True

def main():
    """主函数"""
    print("🚀 A股量化交易系统 - Web UI 测试")
    print("=" * 60)
    
    # 测试导入
    if not test_imports():
        print("\n💡 请安装依赖包: pip install flask flask-socketio eventlet pandas numpy")
        return
    
    # 测试模板
    if not test_templates():
        print("\n💡 请检查模板文件是否存在")
        return
    
    print("\n✅ 所有检查通过，开始启动Web UI...")
    
    # 导入Web应用
    try:
        from webui.app import app, socketio
        
        print("🌐 Web UI启动成功!")
        print("📊 访问地址: http://localhost:5000")
        print("💡 按 Ctrl+C 停止服务器")
        print("-" * 60)
        
        # 启动服务器
        socketio.run(app, host='0.0.0.0', port=5000, debug=True)
        
    except Exception as e:
        print(f"❌ Web UI启动失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()