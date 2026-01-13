#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版Web UI启动脚本
"""

import os
import sys
from flask import Flask, render_template, jsonify, request
from datetime import datetime, timedelta
import pandas as pd

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 动态导入数据获取器
try:
    from utils.data_fetcher import AShareDataFetcher
    print("✅ 数据获取器加载成功")
except ImportError as e:
    print(f"❌ 数据获取器加载失败: {e}")
    AShareDataFetcher = None

# 设置模板目录
current_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(current_dir, 'webui', 'templates')

app = Flask(__name__, template_folder=template_dir)

class SimpleDataManager:
    def __init__(self):
        self.fetcher = None
        self._init_fetcher()
    
    def _init_fetcher(self):
        """初始化数据获取器"""
        try:
            self.fetcher = AShareDataFetcher()
            print("✅ 数据管理器初始化成功")
        except Exception as e:
            print(f"❌ 数据管理器初始化失败: {e}")
            self.fetcher = None
    
    def get_available_symbols(self):
        """获取可用标的"""
        if self.fetcher is None:
            return {'stocks': [], 'etfs': [], 'index': []}
        
        try:
            return self.fetcher.get_available_symbols()
        except Exception as e:
            print(f"获取标的列表失败: {e}")
            return {'stocks': [], 'etfs': [], 'index': []}
    
    def load_chart_data(self, symbol, symbol_type, period='6M'):
        """加载K线图数据"""
        if self.fetcher is None:
            return None
        
        try:
            data = self.fetcher.load_data(symbol, symbol_type)
            if data is None:
                return None
            
            # 根据时间周期过滤数据
            if period != 'ALL':
                if period == '1M':
                    cutoff_date = datetime.now() - timedelta(days=30)
                elif period == '3M':
                    cutoff_date = datetime.now() - timedelta(days=90)
                elif period == '6M':
                    cutoff_date = datetime.now() - timedelta(days=180)
                elif period == '1Y':
                    cutoff_date = datetime.now() - timedelta(days=365)
                elif period == '2Y':
                    cutoff_date = datetime.now() - timedelta(days=730)
                
                data = data[data.index >= cutoff_date]
            
            return data
        except Exception as e:
            print(f"加载K线图数据失败: {e}")
            return None

data_manager = SimpleDataManager()

@app.route('/')
def index():
    """首页"""
    return render_template('index.html')

@app.route('/chart')
def chart():
    """K线图页面"""
    return render_template('chart.html')

@app.route('/data_management')
def data_management():
    """数据管理页面"""
    available_data = data_manager.get_available_symbols()
    return render_template('data_management.html', available_data=available_data)

@app.route('/api/symbols')
def api_symbols():
    """获取标的列表"""
    return jsonify(data_manager.get_available_symbols())

@app.route('/api/chart_data')
def api_chart_data():
    """获取K线图数据"""
    try:
        symbol = request.args.get('symbol', '')
        symbol_type = request.args.get('type', 'stock')
        period = request.args.get('period', '6M')
        
        if not symbol:
            return jsonify({'success': False, 'message': '请提供标的代码'})
        
        data = data_manager.load_chart_data(symbol, symbol_type, period)
        if data is None:
            return jsonify({'success': False, 'message': '数据不存在'})
        
        # 转换为前端需要的格式
        chart_data = []
        for date, row in data.iterrows():
            chart_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'open': float(row['open']),
                'close': float(row['close']),
                'high': float(row['high']),
                'low': float(row['low']),
                'volume': float(row.get('volume', 0)),
                'amount': float(row.get('amount', 0))
            })
        
        # 计算涨跌幅
        if len(chart_data) > 0:
            first_price = chart_data[0]['close']
            last_price = chart_data[-1]['close']
            change_percent = ((last_price - first_price) / first_price) * 100
        else:
            first_price = last_price = change_percent = 0
        
        info = {
            'symbol': symbol,
            'count': len(chart_data),
            'start_date': chart_data[0]['date'] if chart_data else '',
            'end_date': chart_data[-1]['date'] if chart_data else '',
            'last_price': round(last_price, 2),
            'change_percent': round(change_percent, 2)
        }
        
        return jsonify({
            'success': True,
            'data': chart_data,
            'info': info
        })
        
    except Exception as e:
        print(f"获取K线图数据失败: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/system_info')
def api_system_info():
    """获取系统信息"""
    available_data = data_manager.get_available_symbols()
    return jsonify({
        'stocks_count': len(available_data['stocks']),
        'etfs_count': len(available_data['etfs']),
        'indices_count': len(available_data['index']),
        'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'data_path': './data'
    })

if __name__ == '__main__':
    print("🚀 A股量化交易系统Web UI启动中...")
    print("📊 访问地址: http://localhost:8888")
    
    # 确保模板目录存在
    os.makedirs('webui/templates', exist_ok=True)
    
    app.run(host='0.0.0.0', port=8888, debug=True)