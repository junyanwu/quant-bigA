#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股量化交易系统 - Web UI界面
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
import threading
import time

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 动态导入，避免启动时检查
try:
    from utils.data_fetcher import AShareDataFetcher
except ImportError:
    AShareDataFetcher = None

try:
    from strategies.dca_strategy import DCAStrategy
except ImportError:
    DCAStrategy = None

try:
    from backtesting.dca_backtest_engine import DCABacktestEngine
except ImportError:
    DCABacktestEngine = None

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = 'quant_trading_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

# 全局变量
fetcher = None
dca_engine = None

class WebUIManager:
    """Web UI管理器"""
    
    def __init__(self):
        # 延迟初始化，避免启动错误
        self.fetcher = None
        self.dca_engine = None
        self.download_progress = {'current': 0, 'total': 0, 'status': 'idle'}
        self.backtest_results = {}
        
    def _init_fetcher(self):
        """延迟初始化数据获取器"""
        if self.fetcher is None:
            try:
                self.fetcher = AShareDataFetcher()
            except Exception as e:
                print(f"初始化数据获取器失败: {e}")
                return False
        return True
    
    def get_system_info(self):
        """获取系统信息"""
        if not self._init_fetcher():
            return {
                'stocks_count': 0,
                'etfs_count': 0,
                'indices_count': 0,
                'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'data_path': './data'
            }
            
        try:
            available_data = self.fetcher.get_available_symbols()
            return {
                'stocks_count': len(available_data['stocks']),
                'etfs_count': len(available_data['etfs']),
                'indices_count': len(available_data['index']),
                'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'data_path': './data'
            }
        except Exception as e:
            print(f"获取系统信息失败: {e}")
            return {
                'stocks_count': 0,
                'etfs_count': 0,
                'indices_count': 0,
                'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'data_path': './data'
            }
    
    def start_data_download(self):
        """开始数据下载"""
        def download_thread():
            try:
                # 获取股票和ETF列表
                stock_list = self.fetcher.get_stock_list()
                etf_list = self.fetcher.get_etf_list()
                
                total_symbols = len(stock_list) + len(etf_list)
                self.download_progress = {'current': 0, 'total': total_symbols, 'status': 'downloading'}
                
                # 模拟下载过程（实际项目中应调用真实下载方法）
                for i in range(total_symbols):
                    time.sleep(0.1)  # 模拟下载延迟
                    self.download_progress['current'] = i + 1
                    
                    # 发送进度更新
                    socketio.emit('download_progress', {
                        'current': i + 1,
                        'total': total_symbols,
                        'percentage': ((i + 1) / total_symbols) * 100
                    })
                
                self.download_progress['status'] = 'completed'
                socketio.emit('download_complete', {'message': '数据下载完成'})
                
            except Exception as e:
                self.download_progress['status'] = 'error'
                socketio.emit('download_error', {'error': str(e)})
        
        thread = threading.Thread(target=download_thread)
        thread.daemon = True
        thread.start()
    
    def run_dca_backtest(self, params):
        """运行定投回测"""
        try:
            # 设置回测参数
            start_date = params.get('start_date', '2018-01-01')
            end_date = params.get('end_date', '2024-12-31')
            monthly_investment = params.get('monthly_investment', 5000)
            
            # 运行回测
            results = {}
            
            # 回测热门指数
            indices_results = self.dca_engine.backtest_popular_indices(start_date, end_date)
            results['indices'] = indices_results.to_dict('records')
            
            # 回测ETF组合
            etf_results = self.dca_engine.backtest_etf_portfolio(start_date, end_date)
            results['etfs'] = etf_results.to_dict('records')
            
            # 生成图表数据
            chart_data = self.generate_chart_data(results)
            
            self.backtest_results = {
                'results': results,
                'charts': chart_data,
                'summary': self.generate_summary(results),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return self.backtest_results
            
        except Exception as e:
            return {'error': str(e)}
    
    def generate_chart_data(self, results):
        """生成图表数据"""
        chart_data = {}
        
        # 收益率对比图
        returns_data = []
        for category, data in results.items():
            for item in data:
                returns_data.append({
                    'name': item['symbol'],
                    'category': category,
                    'return': item['total_return']
                })
        
        # 按收益率排序
        returns_data.sort(key=lambda x: x['return'], reverse=True)
        chart_data['returns_comparison'] = returns_data[:15]  # 只显示前15个
        
        # 定投优势分布
        advantage_data = []
        for category, data in results.items():
            for item in data:
                advantage_data.append({
                    'name': item['symbol'],
                    'advantage': item['vs_lump_sum'] / 10000  # 转换为万元
                })
        
        chart_data['advantage_distribution'] = advantage_data
        
        return chart_data
    
    def generate_summary(self, results):
        """生成回测摘要"""
        all_results = []
        for category, data in results.items():
            all_results.extend(data)
        
        if not all_results:
            return {}
        
        returns = [item['total_return'] for item in all_results]
        advantages = [item['vs_lump_sum'] for item in all_results]
        
        return {
            'total_symbols': len(all_results),
            'avg_return': np.mean(returns),
            'max_return': max(returns),
            'min_return': min(returns),
            'avg_advantage': np.mean(advantages),
            'positive_ratio': len([a for a in advantages if a > 0]) / len(advantages) * 100
        }

# 创建UI管理器
ui_manager = WebUIManager()

# 路由定义
@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """仪表板"""
    system_info = ui_manager.get_system_info()
    return render_template('dashboard.html', system_info=system_info)

@app.route('/data_management')
def data_management():
    """数据管理"""
    try:
        available_data = ui_manager.fetcher.get_available_symbols()
        return render_template('data_management.html', available_data=available_data)
    except Exception as e:
        print(f"数据管理页面错误: {e}")
        available_data = {
            'stocks': [],
            'etfs': [],
            'index': []
        }
        return render_template('data_management.html', available_data=available_data)

@app.route('/dca_backtest')
def dca_backtest():
    """定投回测"""
    return render_template('dca_backtest.html')

@app.route('/strategy_backtest')
def strategy_backtest():
    """策略回测"""
    return render_template('strategy_backtest.html')

@app.route('/realtime_monitor')
def realtime_monitor():
    """实时监控"""
    return render_template('realtime_monitor.html')

@app.route('/chart')
def chart():
    """K线图页面"""
    return render_template('chart.html')

# API接口
@app.route('/api/system_info')
def api_system_info():
    """获取系统信息API"""
    return jsonify(ui_manager.get_system_info())

@app.route('/api/symbols')
def api_symbols():
    """获取可用标的列表"""
    try:
        available_data = ui_manager.fetcher.get_available_symbols()
        return jsonify(available_data)
    except Exception as e:
        print(f"获取标的列表失败: {e}")
        return jsonify({'stock': [], 'etf': [], 'index': []})

@app.route('/api/chart_data')
def api_chart_data():
    """获取K线图数据"""
    try:
        symbol = request.args.get('symbol', '')
        symbol_type = request.args.get('type', 'stock')
        period = request.args.get('period', '6M')
        
        if not symbol:
            return jsonify({'success': False, 'message': '请提供标的代码'})
        
        # 加载数据
        data = ui_manager.fetcher.load_data(symbol, symbol_type)
        if data is None:
            return jsonify({'success': False, 'message': '数据不存在'})
        
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

@app.route('/api/start_download', methods=['POST'])
def api_start_download():
    """开始数据下载API"""
    ui_manager.start_data_download()
    return jsonify({'status': 'started'})

@app.route('/api/download_progress')
def api_download_progress():
    """获取下载进度API"""
    return jsonify(ui_manager.download_progress)

@app.route('/api/run_dca_backtest', methods=['POST'])
def api_run_dca_backtest():
    """运行定投回测API"""
    params = request.json
    result = ui_manager.run_dca_backtest(params)
    return jsonify(result)

@app.route('/api/get_backtest_results')
def api_get_backtest_results():
    """获取回测结果API"""
    return jsonify(ui_manager.backtest_results)

# WebSocket事件
@socketio.on('connect')
def handle_connect():
    """客户端连接"""
    print('客户端连接成功')
    emit('connected', {'message': '连接成功'})

@socketio.on('start_download')
def handle_start_download():
    """开始下载"""
    ui_manager.start_data_download()

@socketio.on('request_system_info')
def handle_system_info():
    """请求系统信息"""
    emit('system_info', ui_manager.get_system_info())

if __name__ == '__main__':
    print("🚀 A股量化交易系统Web UI启动中...")
    print("📊 访问地址: http://localhost:5000")
    
    # 创建必要的目录
    os.makedirs('webui/templates', exist_ok=True)
    os.makedirs('webui/static/css', exist_ok=True)
    os.makedirs('webui/static/js', exist_ok=True)
    os.makedirs('webui/static/images', exist_ok=True)
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)