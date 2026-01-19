#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web UI应用 - 定投+做T策略可视化
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, render_template, jsonify
import pandas as pd
import json
import ast
from pathlib import Path

app = Flask(__name__, 
            template_folder='./templates',
            static_folder='./static')

def get_all_local_symbols():
    """
    获取所有本地数据的标的代码和类型
    
    Returns:
        [{'code': 'xxx', 'name': 'xxx', 'type': 'etf/stock/index'}, ...]
    """
    symbols = []
    data_dir = Path('../data')
    
    # 标的名称映射
    symbol_names = {
        '510300.SH': '沪深300ETF',
        '510500.SH': '中证500ETF',
        '159915.SZ': '创业板ETF',
        '512880.SH': '证券ETF',
        '512690.SH': '酒ETF',
        '159928.SZ': '消费ETF',
        '512100.SH': '中证1000ETF',
        '512000.SH': '券商ETF',
        '516160.SH': '新能源车ETF',
        '515050.SH': '5GETF',
        '159806.SZ': '新能源ETF',
        '516970.SH': '红利低波ETF',
        '000001.SH': '上证指数',
        '399001.SZ': '深证成指',
        '399006.SZ': '创业板指',
        '000300.SH': '沪深300',
        '000905.SH': '中证500',
        '000688.SH': '科创50',
        '000016.SH': '上证50',
    }
    
    # 扫描ETF数据
    etf_dir = data_dir / 'etfs'
    if etf_dir.exists():
        for file in etf_dir.glob('*.csv'):
            symbol = file.stem
            symbols.append({
                'code': symbol,
                'name': symbol_names.get(symbol, symbol),
                'type': 'etf'
            })
    
    # 扫描股票数据
    stock_dir = data_dir / 'stocks'
    if stock_dir.exists():
        for file in stock_dir.glob('*.csv'):
            symbol = file.stem
            symbols.append({
                'code': symbol,
                'name': symbol_names.get(symbol, symbol),
                'type': 'stock'
            })
    
    # 扫描指数数据
    index_dir = data_dir / 'index'
    if index_dir.exists():
        for file in index_dir.glob('*.csv'):
            symbol = file.stem
            symbols.append({
                'code': symbol,
                'name': symbol_names.get(symbol, symbol),
                'type': 'index'
            })
    
    return symbols

# 全局变量
SYMBOLS = get_all_local_symbols()

def load_backtest_results(symbol):
    """
    加载回测结果
    
    Args:
        symbol: 标的代码
        
    Returns:
        回测结果字典
    """
    results_file = f'./results/{symbol}/results.json'
    trades_file = f'./results/{symbol}/trades.csv'
    dca_trades_file = f'./results/{symbol}/dca_trades.csv'
    t_trades_file = f'./results/{symbol}/t_trades.csv'
    daily_nav_file = f'./results/{symbol}/daily_nav.csv'
    
    results = {}
    
    # 加载结果
    if os.path.exists(results_file):
        with open(results_file, 'r', encoding='utf-8') as f:
            results['summary'] = json.load(f)
    
    # 加载交易记录
    if os.path.exists(trades_file):
        try:
            df = pd.read_csv(trades_file)
            if not df.empty:
                # 处理NaN值
                df = df.fillna('')
                results['trades'] = df.to_dict('records')
            else:
                results['trades'] = []
        except Exception as e:
            print(f"加载交易记录失败 {trades_file}: {e}")
            results['trades'] = []
    else:
        results['trades'] = []
    
    # 加载定投交易
    if os.path.exists(dca_trades_file):
        try:
            df = pd.read_csv(dca_trades_file)
            if not df.empty:
                df = df.fillna('')
                results['dca_trades'] = df.to_dict('records')
            else:
                results['dca_trades'] = []
        except Exception as e:
            print(f"加载定投交易失败 {dca_trades_file}: {e}")
            results['dca_trades'] = []
    else:
        results['dca_trades'] = []
    
    # 加载做T交易
    if os.path.exists(t_trades_file):
        try:
            df = pd.read_csv(t_trades_file)
            if not df.empty:
                df = df.fillna('')
                results['t_trades'] = df.to_dict('records')
            else:
                results['t_trades'] = []
        except Exception as e:
            print(f"加载做T交易失败 {t_trades_file}: {e}")
            results['t_trades'] = []
    else:
        results['t_trades'] = []
    
    # 加载每日净值
    if os.path.exists(daily_nav_file):
        try:
            df = pd.read_csv(daily_nav_file)
            if not df.empty:
                df = df.fillna('')
                results['daily_nav'] = df.to_dict('records')
            else:
                results['daily_nav'] = []
        except Exception as e:
            print(f"加载每日净值失败 {daily_nav_file}: {e}")
            results['daily_nav'] = []
    else:
        results['daily_nav'] = []
    
    return results

@app.route('/')
def index():
    """
    首页
    """
    return render_template('index.html', symbols=SYMBOLS)

@app.route('/api/symbols')
def get_symbols():
    """
    获取所有标的列表
    """
    return jsonify(SYMBOLS)

@app.route('/api/results/<symbol>')
def get_results(symbol):
    """
    获取指定标的的回测结果
    """
    results = load_backtest_results(symbol)
    return jsonify(results)

@app.route('/api/trades/<symbol>')
def get_trades_data(symbol):
    """
    获取交易数据（买入卖出点）
    """
    results = load_backtest_results(symbol)
    
    # 转换为ECharts散点图格式
    buy_points = []
    sell_points = []
    
    for trade in results.get('trades', []):
        # 日期已经是字符串格式，不需要转换
        date_str = trade['date'] if isinstance(trade['date'], str) else str(trade['date'])
        
        if trade['type'] == 'buy':
            buy_points.append({
                'name': trade['symbol'],
                'value': [
                    date_str,
                    round(float(trade['price']), 2)
                ],
                'itemStyle': {
                    'color': '#10b981'
                },
                'strategy': trade.get('strategy', ''),
                'shares': trade['shares'],
                'amount': round(float(trade['amount']), 2)
            })
        elif trade['type'] == 'sell':
            sell_points.append({
                'name': trade['symbol'],
                'value': [
                    date_str,
                    round(float(trade['price']), 2)
                ],
                'itemStyle': {
                    'color': '#ef4444'
                },
                'strategy': trade.get('strategy', ''),
                'shares': trade['shares'],
                'amount': round(float(trade['amount']), 2),
                'profit': round(float(trade.get('profit', 0)), 2)
            })
    
    return jsonify({
        'buy_points': buy_points,
        'sell_points': sell_points
    })

@app.route('/api/indicators/<symbol>')
def get_indicators_data(symbol):
    """
    获取技术指标数据
    """
    from utils.data_fetcher import AShareDataFetcher
    from strategies.indicators import calculate_all_indicators
    
    fetcher = AShareDataFetcher()
    df = fetcher.get_data(symbol, 'etf', '2020-01-01', '2024-12-31')
    
    if df is None or df.empty:
        return jsonify({'error': '无法获取数据'})
    
    df = calculate_all_indicators(df)
    df = df.reset_index()
    
    # 转换为ECharts格式
    dates = [row['date'].strftime('%Y-%m-%d') for _, row in df.iterrows()]
    
    return jsonify({
        'dates': dates,
        'macd': [round(row['macd'], 4) for _, row in df.iterrows()],
        'macd_signal': [round(row['macd_signal'], 4) for _, row in df.iterrows()],
        'macd_upper': [round(row['macd_upper'], 4) for _, row in df.iterrows()],
        'macd_lower': [round(row['macd_lower'], 4) for _, row in df.iterrows()],
        'volume_ratio': [round(row['volume_ratio'], 2) for _, row in df.iterrows()],
        'atr_ratio': [round(row['atr_ratio'], 4) for _, row in df.iterrows()],
        'is_overvalued': [bool(row['is_overvalued']) for _, row in df.iterrows()],
        'is_undervalued': [bool(row['is_undervalued']) for _, row in df.iterrows()]
    })

@app.route('/api/summary')
def get_summary():
    """
    获取所有标的的回测结果汇总
    """
    # 尝试从all_backtest_summary.csv读取
    summary_file = '../results/all_backtest_summary.csv'
    
    if os.path.exists(summary_file):
        df = pd.read_csv(summary_file)
        
        # 读取标的名称映射
        symbol_names_file = '../data/symbol_names.json'
        if os.path.exists(symbol_names_file):
            with open(symbol_names_file, 'r', encoding='utf-8') as f:
                symbol_names = json.load(f)
        else:
            symbol_names = {}
        
        # 如果CSV中已经有name列，就不要覆盖
        if 'name' not in df.columns:
            # 添加标的名称
            df['name'] = df['symbol'].map(symbol_names)
        
        # 将name列中的NaN值替换为symbol代码
        if 'name' in df.columns:
            df['name'] = df['name'].fillna(df['symbol'])
        
        # 将symbol_type列重命名为type（前端使用type字段）
        if 'symbol_type' in df.columns:
            df['type'] = df['symbol_type']
        
        # 将NaN值替换为None，这样JSON序列化时就不会出错
        df = df.where(pd.notnull(df), None)
        
        # 转换为字典列表
        summary = df.to_dict('records')
        
        # 确保所有必需的字段都存在
        for item in summary:
            item.setdefault('name', item.get('symbol', ''))
            item.setdefault('type', item.get('symbol_type', 'stock'))
            item.setdefault('total_return', 0)
            item.setdefault('annual_return', 0)
            item.setdefault('max_drawdown', 0)
            item.setdefault('sharpe_ratio', 0)
            item.setdefault('final_value', 0)
            item.setdefault('dca_buy_count', 0)
            item.setdefault('dca_sell_count', 0)
            item.setdefault('t_buy_count', 0)
            item.setdefault('t_sell_count', 0)
            item.setdefault('t_profit', 0)
            item.setdefault('data_start_date', '')
            item.setdefault('data_end_date', '')
            item.setdefault('annual_returns', [])
            
            # 将annual_returns从字符串转换为列表
            if 'annual_returns' in item and isinstance(item['annual_returns'], str):
                try:
                    item['annual_returns'] = ast.literal_eval(item['annual_returns'])
                except (ValueError, SyntaxError):
                    item['annual_returns'] = []
        
        return jsonify(summary)
    else:
        # 如果all_backtest_summary.csv不存在，则扫描results目录读取所有results.json
        summary = []
        results_dir = Path('../results')
        
        if not results_dir.exists():
            return jsonify(summary)
        
        # 扫描所有标的目录
        for symbol_dir in sorted(results_dir.iterdir()):
            if not symbol_dir.is_dir():
                continue
            
            symbol = symbol_dir.name
            results_file = symbol_dir / 'results.json'
            
            if not results_file.exists():
                continue
            
            try:
                with open(results_file, 'r', encoding='utf-8') as f:
                    results_data = json.load(f)
                
                # 查找标的名称和类型
                symbol_info = next((s for s in SYMBOLS if s['code'] == symbol), None)
                
                summary_item = {
                    'symbol': symbol,
                    'name': symbol_info['name'] if symbol_info else symbol,
                    'type': symbol_info['type'] if symbol_info else 'unknown',
                    'total_return': results_data.get('total_return', 0),
                    'annual_return': results_data.get('annual_return', 0),
                    'max_drawdown': results_data.get('max_drawdown', 0),
                    'sharpe_ratio': results_data.get('sharpe_ratio', 0),
                    'final_value': results_data.get('final_value', 0),
                    'dca_buy_count': results_data.get('dca_buy_count', 0),
                    'dca_sell_count': results_data.get('dca_sell_count', 0),
                    't_buy_count': results_data.get('t_buy_count', 0),
                    't_sell_count': results_data.get('t_sell_count', 0),
                    't_profit': results_data.get('t_profit', 0),
                    'data_start_date': results_data.get('data_start_date', ''),
                    'data_end_date': results_data.get('data_end_date', ''),
                    'annual_returns': results_data.get('annual_returns', [])
                }
                summary.append(summary_item)
            except Exception as e:
                print(f"读取 {symbol} 结果失败: {e}")
                continue
        
        return jsonify(summary)

@app.route('/api/strategies')
def get_strategies():
    """
    获取所有策略列表
    """
    strategies = [
        {
            'id': 'dca_trading_v1',
            'name': '定投+做T策略 v1.0',
            'description': '结合定期定额投资和日内交易的混合策略（固定参数）',
            'version': '1.0'
        },
        {
            'id': 'dca_trading_v2',
            'name': '定投+做T策略 v2.0',
            'description': '结合定期定额投资和日内交易的混合策略（动态参数）',
            'version': '2.0'
        },
        {
            'id': 'dca',
            'name': '定投策略',
            'description': '定期定额投资策略',
            'version': '1.0'
        },
        {
            'id': 'dca_only',
            'name': '纯定投策略',
            'description': '每周定投固定金额，收益达到目标且价格低于MA10时卖出',
            'version': '1.0'
        }
    ]
    return jsonify(strategies)

@app.route('/api/strategy/<strategy_id>')
def get_strategy_detail(strategy_id):
    """
    获取策略详情
    """
    if strategy_id == 'dca_trading_v1':
        strategy_detail = {
            'id': 'dca_trading_v1',
            'name': '定投+做T策略 v1.0',
            'description': '结合定期定额投资和日内交易的混合策略（固定参数）',
            'version': '1.0',
            'params': {
                'total_capital': 500000.0,
                'dca_ratio': 0.7,
                'dca_amount_per_week': 1000.0,
                't_amount_per_trade': 5000.0,
                'max_loss_ratio': 0.03,
                'profit_target': 0.01,
                'commission': 0.0003,
                'slippage': 0.001
            },
            'dca_logic': {
                'name': '定投逻辑',
                'description': '定期定额投资，不择时',
                'buy_condition': '每周第一个交易日定投1000元（固定金额）',
                'sell_condition': '仓位超过70%时，且盈利>20%，且macd柱>0且放量且macd柱下跌，则分批卖出',
                'sell_method': '分3次卖出，每次卖出1/3'
            },
            't_logic': {
                'name': '做T逻辑',
                'description': '基于技术指标进行加仓减仓',
                'conditions': [
                    {
                        'condition': '大盘下跌超过2%然后反弹0.3%',
                        'action': '分段买入',
                        'exit': '隔天反弹在盈利1%时卖出',
                        'stop_loss': '亏损超过3%止损'
                    },
                    {
                        'condition': '大盘下跌超过1%但小于2%，反弹0.2%',
                        'action': '买入',
                        'exit': '盈利0.5%时卖出',
                        'stop_loss': '亏损超过2%止损'
                    },
                    {
                        'condition': 'MACD柱<0且出现反转，昨天是阳线',
                        'action': '买入',
                        'exit': 'MACD柱>0时卖出',
                        'stop_loss': '无'
                    }
                ],
                'exit_conditions': {
                    'name': '平仓条件',
                    'description': 'MACD柱反转开始下跌（macd_hist < macd_hist_prev）且价格跌破5日均线',
                    'stop_loss': '基于ATR（平均真实波幅），当价格跌破买入价 - 2*ATR时止损（固定2倍）'
                },
                'position_check': {
                    'name': '仓位检查',
                    'description': '做T买入前需判断是否有足够定投仓位（定投仓位市值 >= 做T金额）'
                }
            },
            'features': [
                '固定参数模式',
                '定投金额固定1000元/周',
                '做T金额固定5000元/次',
                '止损倍数固定2倍ATR',
                '止盈目标固定1%'
            ]
        }
    elif strategy_id == 'dca_trading_v2':
        strategy_detail = {
            'id': 'dca_trading_v2',
            'name': '定投+做T策略 v2.0',
            'description': '结合定期定额投资和日内交易的混合策略（动态参数）',
            'version': '2.0',
            'params': {
                'total_capital': 500000.0,
                'dca_ratio': 0.7,
                'base_dca_amount_per_week': 1000.0,
                'base_t_amount_per_trade': 5000.0,
                'max_loss_ratio': 0.03,
                'profit_target': 0.01,
                'commission': 0.0003,
                'slippage': 0.001
            },
            'dca_logic': {
                'name': '定投逻辑',
                'description': '定期定额投资，不择时',
                'buy_condition': '每周第一个交易日定投，金额根据市场波动性动态调整（70%-115%）',
                'sell_condition': '仓位超过65%时，且满足多条件综合判断，则分批卖出',
                'sell_method': '分3次卖出，每次卖出1/3'
            },
            't_logic': {
                'name': '做T逻辑',
                'description': '基于技术指标进行加仓减仓，动态调整参数',
                'conditions': [
                    {
                        'condition': '大盘下跌超过2%然后反弹0.3%',
                        'action': '分段买入',
                        'exit': '隔天反弹在盈利1%时卖出',
                        'stop_loss': '亏损超过3%止损'
                    },
                    {
                        'condition': '大盘下跌超过1%但小于2%，反弹0.2%',
                        'action': '买入',
                        'exit': '盈利0.5%时卖出',
                        'stop_loss': '亏损超过2%止损'
                    },
                    {
                        'condition': 'MACD柱<0且出现反转，昨天是阳线',
                        'action': '买入',
                        'exit': 'MACD柱>0时卖出',
                        'stop_loss': '无'
                    }
                ],
                'exit_conditions': {
                    'name': '平仓条件',
                    'description': 'MACD柱反转开始下跌（macd_hist < macd_hist_prev）且价格跌破5日均线，或放量且盈利',
                    'stop_loss': '基于ATR（平均真实波幅），当价格跌破买入价 - 动态倍数*ATR时止损（1.5-2.5倍）'
                },
                'position_check': {
                    'name': '仓位检查',
                    'description': '做T买入前需判断是否有足够定投仓位（定投仓位市值 >= 做T金额）'
                }
            },
            'features': [
                '动态参数模式',
                '定投金额根据ATR动态调整（70%-115%）',
                '做T金额根据市场状态动态调整',
                '止损倍数根据ATR动态调整（1.5-2.5倍）',
                '止盈目标根据ATR动态调整（85%-130%）',
                '多条件综合判断开平仓'
            ]
        }
    elif strategy_id == 'dca_trading':
        strategy_detail = {
            'id': 'dca_trading',
            'name': '定投+做T策略',
            'description': '结合定期定额投资和日内交易的混合策略',
            'version': '2.0',
            'params': {
                'total_capital': 500000.0,
                'dca_ratio': 0.7,
                'dca_amount_per_week': 1000.0,
                't_amount_per_trade': 5000.0,
                'max_loss_ratio': 0.03,
                'profit_target': 0.01,
                'commission': 0.0003,
                'slippage': 0.001
            },
            'dca_logic': {
                'name': '定投逻辑',
                'description': '定期定额投资，不择时',
                'buy_condition': '每周第一个交易日定投1000元',
                'sell_condition': '仓位超过70%时，且盈利>20%，且macd柱>0且放量且macd柱下跌，则分批卖出',
                'sell_method': '分3次卖出，每次卖出1/3'
            },
            't_logic': {
                'name': '做T逻辑',
                'description': '基于技术指标进行加仓减仓',
                'conditions': [
                    {
                        'condition': '大盘下跌超过2%然后反弹0.3%',
                        'action': '分段买入',
                        'exit': '隔天反弹在盈利1%时卖出',
                        'stop_loss': '亏损超过3%止损'
                    },
                    {
                        'condition': '大盘下跌超过1%但小于2%，反弹0.2%',
                        'action': '买入',
                        'exit': '盈利0.5%时卖出',
                        'stop_loss': '亏损超过2%止损'
                    },
                    {
                        'condition': 'MACD柱<0且出现反转，昨天是阳线',
                        'action': '买入',
                        'exit': 'MACD柱>0时卖出',
                        'stop_loss': '无'
                    }
                ],
                'exit_conditions': {
                    'name': '平仓条件',
                    'description': 'MACD柱反转开始下跌（macd_hist < macd_hist_prev）且价格跌破5日均线',
                    'stop_loss': '基于ATR（平均真实波幅），当价格跌破买入价 - 2*ATR时止损'
                },
                'position_check': {
                    'name': '仓位检查',
                    'description': '做T买入前需判断是否有足够定投仓位（定投仓位市值 >= 做T金额）'
                }
            }
        }
    elif strategy_id == 'dca':
        strategy_detail = {
            'id': 'dca',
            'name': '定投策略',
            'description': '定期定额投资策略',
            'version': '1.0',
            'params': {
                'initial_capital': 100000,
                'monthly_investment': 10000
            },
            'logic': {
                'name': '定投逻辑',
                'description': '定期定额投资，不择时',
                'buy_condition': '每月第一个交易日定投',
                'sell_condition': '无（长期持有）'
            }
        }
    elif strategy_id == 'dca_only':
        strategy_detail = {
            'id': 'dca_only',
            'name': '纯定投策略',
            'description': '每周定投固定金额，收益达到目标且价格低于MA10时卖出',
            'version': '1.0',
            'params': {
                'total_capital': 500000.0,
                'dca_amount_per_week': 500.0,
                'profit_target': 0.20,
                'commission': 0.0003,
                'slippage': 0.001
            },
            'logic': {
                'name': '定投逻辑',
                'description': '每周定投固定金额，达到止盈条件时卖出',
                'buy_condition': '每周第一个交易日定投500元',
                'sell_condition': '收益达到20%且价格低于MA10时卖出全部仓位',
                'continue_investment': '卖出后继续按计划定投'
            },
            'features': [
                '纯定投策略，无做T操作',
                '每周定投500元',
                '止盈目标20%',
                '价格跌破MA10时触发卖出',
                '卖出后继续定投，形成完整投资周期'
            ]
        }
    else:
        return jsonify({'error': '策略不存在'}), 404
    
    return jsonify(strategy_detail)

@app.route('/api/strategy/<strategy_id>/results')
def get_strategy_results(strategy_id):
    """
    获取指定策略的回测结果
    """
    # 根据策略ID选择不同的结果文件
    if strategy_id == 'dca_trading_v1':
        summary_file = '../results/comprehensive_backtest/comprehensive_backtest_results.csv'
    elif strategy_id == 'dca_trading_v2':
        summary_file = '../results/v2_comprehensive_backtest/v2_comprehensive_backtest_results.csv'
    elif strategy_id == 'dca_only':
        summary_file = '../results/dca_only_comprehensive_backtest/dca_only_comprehensive_backtest_results.csv'
    else:
        summary_file = '../results/all_backtest_summary.csv'
    
    if not os.path.exists(summary_file):
        return jsonify([])
    
    df = pd.read_csv(summary_file)
    
    # 添加标的名称
    # 读取完整的标的名称映射
    symbol_names_file = '../data/symbol_names.json'
    if os.path.exists(symbol_names_file):
        with open(symbol_names_file, 'r', encoding='utf-8') as f:
            symbol_names = json.load(f)
    else:
        symbol_names = {}
    
    if 'name' not in df.columns:
        df['name'] = df['symbol'].map(symbol_names)
    
    # 将name列中的NaN值替换为symbol代码（在转换为None之前）
    if 'name' in df.columns:
        df['name'] = df['name'].fillna(df['symbol'])
    
    # 将symbol_type列重命名为type（前端使用type字段）
    if 'symbol_type' in df.columns:
        df['type'] = df['symbol_type']
    
    # 将NaN值替换为None，这样JSON序列化时就不会出错
    df = df.where(pd.notnull(df), None)
    
    # 转换为字典列表
    summary = df.to_dict('records')
    
    # 确定结果目录路径
    if strategy_id == 'dca_trading_v1':
        results_base_dir = '../results'
    elif strategy_id == 'dca_trading_v2':
        results_base_dir = '../results/v2_results'
    else:
        results_base_dir = '../results'
    
    print(f"策略ID: {strategy_id}, 结果目录: {results_base_dir}")
    print(f"CSV文件: {summary_file}")
    print(f"CSV行数: {len(df)}")
    
    # 确保所有必需的字段都存在
    for item in summary:
        item.setdefault('name', item.get('symbol', ''))
        # 兼容不同的列名
        item.setdefault('type', item.get('symbol_type', 'stock'))
        item.setdefault('total_return', 0)
        item.setdefault('annual_return', 0)
        item.setdefault('max_drawdown', 0)
        item.setdefault('sharpe_ratio', 0)
        item.setdefault('final_value', 0)
        item.setdefault('dca_buy_count', 0)
        item.setdefault('dca_sell_count', 0)
        item.setdefault('t_buy_count', 0)
        item.setdefault('t_sell_count', 0)
        item.setdefault('t_profit', 0)
        # 兼容不同的列名
        item.setdefault('data_start_date', item.get('start_date', ''))
        item.setdefault('data_end_date', item.get('end_date', ''))
        
        # 尝试从JSON文件中读取年度收益数据
        symbol = item.get('symbol', '')
        json_file = os.path.join(results_base_dir, symbol, 'results.json')
        
        if os.path.exists(json_file):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                    if 'annual_returns' in json_data and json_data['annual_returns']:
                        item['annual_returns'] = json_data['annual_returns']
                        print(f"✓ 从 {json_file} 读取到 {len(item['annual_returns'])} 年的年度收益数据")
                        continue
            except Exception as e:
                print(f"✗ 读取 {json_file} 失败: {e}")
        else:
            print(f"✗ 文件不存在: {json_file}")
        
        # 如果没有从JSON文件中读取到年度收益，就设置为空数组
        # 不再生成虚假的年度收益数据
        item['annual_returns'] = []
    
    return jsonify(summary)

@app.route('/api/strategy/<strategy_id>/summary')
def get_strategy_summary(strategy_id):
    """
    获取指定策略的汇总信息
    """
    # 根据策略ID选择不同的结果文件
    if strategy_id == 'dca_trading_v1':
        summary_file = '../results/comprehensive_backtest/comprehensive_backtest_results.csv'
    elif strategy_id == 'dca_trading_v2':
        summary_file = '../results/v2_comprehensive_backtest/v2_comprehensive_backtest_results.csv'
    else:
        summary_file = '../results/all_backtest_summary.csv'
    
    if not os.path.exists(summary_file):
        return jsonify({
            'total_position': 0,
            'total_buy': 0,
            'total_sell': 0,
            'total_profit': 0,
            'symbol_count': 0
        })
    
    df = pd.read_csv(summary_file)
    
    # 计算汇总信息
    total_position = df['final_value'].sum() if 'final_value' in df.columns else 0
    total_buy = (df['dca_buy_count'] * 1000 + df['t_buy_count'] * 5000).sum() if 'dca_buy_count' in df.columns and 't_buy_count' in df.columns else 0
    total_sell = (df['dca_sell_count'] * 1000 + df['t_sell_count'] * 5000).sum() if 'dca_sell_count' in df.columns and 't_sell_count' in df.columns else 0
    total_profit = (df['final_value'] - 500000).sum() if 'final_value' in df.columns else 0
    symbol_count = len(df)
    
    # 转换为万元
    total_position_wan = total_position / 10000
    total_buy_wan = total_buy / 10000
    total_sell_wan = total_sell / 10000
    total_profit_wan = total_profit / 10000
    
    return jsonify({
        'total_position': round(total_position_wan, 2),
        'total_buy': round(total_buy_wan, 2),
        'total_sell': round(total_sell_wan, 2),
        'total_profit': round(total_profit_wan, 2),
        'symbol_count': symbol_count
    })

@app.route('/api/backtest/<symbol>', methods=['POST'])
def run_backtest(symbol):
    """
    运行回测
    
    Args:
        symbol: 标的代码
        
    Returns:
        回测结果
    """
    from backtesting.dca_trading_backtest import BacktestEngine
    from strategies.dca_trading_strategy import DcaTradingStrategy
    
    try:
        # 初始化策略
        strategy = DcaTradingStrategy(
            total_capital=500000.0,
            dca_ratio=0.6,
            dca_amount_per_month=5000.0,
            t_amount_per_trade=10000.0,
            max_loss_ratio=0.05,
            profit_target=0.30,
            commission=0.0003,
            slippage=0.001
        )
        
        # 初始化回测引擎
        engine = BacktestEngine(strategy)
        
        # 运行回测
        results = engine.run_backtest(symbol, 'etf', '2020-01-01', '2024-12-31')
        
        # 保存结果
        output_dir = f'./results/{symbol}'
        os.makedirs(output_dir, exist_ok=True)
        strategy.save_results(output_dir)
        
        # 保存摘要
        summary_file = os.path.join(output_dir, 'results.json')
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            'success': True,
            'message': f'{symbol} 回测完成',
            'results': results
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'回测失败: {str(e)}'
        }), 500

@app.route('/symbol/<symbol>')
def symbol_detail(symbol):
    """
    标的详情页面
    """
    # 获取标的名称
    summary_file = '../results/all_backtest_summary.csv'
    name = symbol
    if os.path.exists(summary_file):
        df = pd.read_csv(summary_file)
        symbol_row = df[df['symbol'] == symbol]
        if not symbol_row.empty:
            if 'name' in symbol_row.columns:
                name_value = symbol_row.iloc[0]['name']
                if pd.notna(name_value):
                    name = name_value
    
    return render_template('symbol_detail.html', symbol=symbol, name=name)

@app.route('/api/symbol/<symbol>/strategies')
def get_symbol_strategies(symbol):
    """
    获取标的在各个策略下的回测结果
    """
    strategies = []
    
    # v1策略结果
    v1_json_file = f'../results/v1_results/{symbol}/results.json'
    if os.path.exists(v1_json_file):
        with open(v1_json_file, 'r', encoding='utf-8') as f:
            v1_data = json.load(f)
            strategies.append({
                'strategy_id': 'dca_trading_v1',
                'strategy_name': '定投+做T策略 v1.0',
                'version': '1.0',
                'total_return': v1_data.get('total_return', 0),
                'annual_return': v1_data.get('annual_return', 0),
                'max_drawdown': v1_data.get('max_drawdown', 0),
                'sharpe_ratio': v1_data.get('sharpe_ratio', 0),
                'final_value': v1_data.get('final_value', 0),
                'dca_buy_count': v1_data.get('dca_buy_count', 0),
                'dca_sell_count': v1_data.get('dca_sell_count', 0),
                't_buy_count': v1_data.get('t_buy_count', 0),
                't_sell_count': v1_data.get('t_sell_count', 0),
                't_profit': v1_data.get('t_profit', 0),
                'data_start_date': v1_data.get('data_start_date', ''),
                'data_end_date': v1_data.get('data_end_date', ''),
                'annual_returns': v1_data.get('annual_returns', [])
            })
    
    # v2策略结果
    v2_json_file = f'../results/v2_results/{symbol}/results.json'
    if os.path.exists(v2_json_file):
        with open(v2_json_file, 'r', encoding='utf-8') as f:
            v2_data = json.load(f)
            strategies.append({
                'strategy_id': 'dca_trading_v2',
                'strategy_name': '定投+做T策略 v2.0',
                'version': '2.0',
                'total_return': v2_data.get('total_return', 0),
                'annual_return': v2_data.get('annual_return', 0),
                'max_drawdown': v2_data.get('max_drawdown', 0),
                'sharpe_ratio': v2_data.get('sharpe_ratio', 0),
                'final_value': v2_data.get('final_value', 0),
                'dca_buy_count': v2_data.get('dca_buy_count', 0),
                'dca_sell_count': v2_data.get('dca_sell_count', 0),
                't_buy_count': v2_data.get('t_buy_count', 0),
                't_sell_count': v2_data.get('t_sell_count', 0),
                't_profit': v2_data.get('t_profit', 0),
                'data_start_date': v2_data.get('data_start_date', ''),
                'data_end_date': v2_data.get('data_end_date', ''),
                'annual_returns': v2_data.get('annual_returns', [])
            })
    
    # dca策略结果
    dca_json_file = f'../results/dca_results/{symbol}/results.json'
    if os.path.exists(dca_json_file):
        with open(dca_json_file, 'r', encoding='utf-8') as f:
            dca_data = json.load(f)
            strategies.append({
                'strategy_id': 'dca',
                'strategy_name': '定投策略',
                'version': '1.0',
                'total_return': dca_data.get('total_return', 0),
                'annual_return': dca_data.get('annual_return', 0),
                'max_drawdown': dca_data.get('max_drawdown', 0),
                'sharpe_ratio': dca_data.get('sharpe_ratio', 0),
                'final_value': dca_data.get('final_value', 0),
                'dca_buy_count': dca_data.get('dca_buy_count', 0),
                'dca_sell_count': dca_data.get('dca_sell_count', 0),
                't_buy_count': dca_data.get('t_buy_count', 0),
                't_sell_count': dca_data.get('t_sell_count', 0),
                't_profit': dca_data.get('t_profit', 0),
                'data_start_date': dca_data.get('data_start_date', ''),
                'data_end_date': dca_data.get('data_end_date', ''),
                'annual_returns': dca_data.get('annual_returns', [])
            })
    
    # dca_only策略结果
    dca_only_json_file = f'../results/dca_only_results/{symbol}/results.json'
    if os.path.exists(dca_only_json_file):
        with open(dca_only_json_file, 'r', encoding='utf-8') as f:
            dca_only_data = json.load(f)
            strategies.append({
                'strategy_id': 'dca_only',
                'strategy_name': '纯定投策略',
                'version': '1.0',
                'total_return': dca_only_data.get('total_return', 0),
                'annual_return': dca_only_data.get('annual_return', 0),
                'max_drawdown': dca_only_data.get('max_drawdown', 0),
                'sharpe_ratio': dca_only_data.get('sharpe_ratio', 0),
                'final_value': dca_only_data.get('final_value', 0),
                'dca_buy_count': dca_only_data.get('dca_buy_count', 0),
                'dca_sell_count': dca_only_data.get('dca_sell_count', 0),
                't_buy_count': dca_only_data.get('t_buy_count', 0),
                't_sell_count': dca_only_data.get('t_sell_count', 0),
                't_profit': dca_only_data.get('t_profit', 0),
                'data_start_date': dca_only_data.get('data_start_date', ''),
                'data_end_date': dca_only_data.get('data_end_date', ''),
                'annual_returns': dca_only_data.get('annual_returns', [])
            })
    
    return jsonify({
        'symbol': symbol,
        'strategies': strategies
    })

@app.route('/api/chart/<symbol>')
def get_chart_data(symbol):
    """
    获取标的的图表数据
    """
    try:
        from flask import request
        
        strategy = request.args.get('strategy', 'v1')
        
        # 读取标的数据
        data_file = f'../data/stocks/{symbol}.csv'
        if not os.path.exists(data_file):
            # 尝试ETF目录
            data_file = f'../data/etfs/{symbol}.csv'
            if not os.path.exists(data_file):
                return jsonify({'error': f'找不到标的数据: {symbol}'}), 404
        
        df = pd.read_csv(data_file)
        
        # 确保有必要的列
        required_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in df.columns:
                return jsonify({'error': f'数据缺少必要列: {col}'}), 400
        
        # 转换日期格式
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # 计算技术指标
        df['ma5'] = df['close'].rolling(window=5).mean()
        df['ma10'] = df['close'].rolling(window=10).mean()
        df['ma20'] = df['close'].rolling(window=20).mean()
        
        # 计算MACD
        ema12 = df['close'].ewm(span=12, adjust=False).mean()
        ema26 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = ema12 - ema26
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        
        # 根据策略读取交易记录
        if strategy == 'v2':
            trades_file = f'../results/v2_results/{symbol}/trades.csv'
            position_info_file = f'../results/v2_results/{symbol}/daily_position_info.csv'
            daily_nav_file = f'../results/v2_results/{symbol}/daily_nav.csv'
        elif strategy == 'v1':
            trades_file = f'../results/v1_results/{symbol}/trades.csv'
            position_info_file = f'../results/v1_results/{symbol}/daily_position_info.csv'
            daily_nav_file = f'../results/v1_results/{symbol}/daily_nav.csv'
        elif strategy == 'dca_only':
            trades_file = f'../results/dca_only_results/{symbol}/trades.csv'
            position_info_file = f'../results/dca_only_results/{symbol}/daily_position_info.csv'
            daily_nav_file = f'../results/dca_only_results/{symbol}/daily_nav.csv'
        else:
            trades_file = f'../results/{symbol}/trades.csv'
            position_info_file = f'../results/{symbol}/daily_position_info.csv'
            daily_nav_file = f'../results/{symbol}/daily_nav.csv'
        
        buy_points = []
        sell_points = []
        
        if os.path.exists(trades_file):
            trades_df = pd.read_csv(trades_file)
            trades_df['date'] = pd.to_datetime(trades_df['date'])
            
            for _, trade in trades_df.iterrows():
                point = {
                    'date': trade['date'].strftime('%Y-%m-%d'),
                    'price': trade['price']
                }
                if trade['type'] == 'buy':
                    buy_points.append(point)
                elif trade['type'] == 'sell':
                    sell_points.append(point)
        
        # 读取每日仓位信息
        position_data = []
        buy_amount_data = []
        sell_amount_data = []
        
        if os.path.exists(position_info_file):
            position_df = pd.read_csv(position_info_file)
            position_df['date'] = pd.to_datetime(position_df['date'])
            position_df = position_df.sort_values('date')
            
            position_data = position_df['position'].fillna(0).tolist()
            buy_amount_data = position_df['buy_amount'].fillna(0).tolist()
            sell_amount_data = position_df['sell_amount'].fillna(0).tolist()
        
        # 读取每日净值信息以获取累计收益
        cumulative_return_data = []
        if os.path.exists(daily_nav_file):
            nav_df = pd.read_csv(daily_nav_file)
            nav_df['date'] = pd.to_datetime(nav_df['date'])
            nav_df = nav_df.sort_values('date')
            
            # 获取初始资金
            initial_capital = nav_df['total_value'].iloc[0]
            
            # 计算累计收益（总资产 - 初始资金），转换为万元
            cumulative_return_data = ((nav_df['total_value'] - initial_capital) / 10000).fillna(0).tolist()
        
        # 准备K线数据
        kline_data = []
        for _, row in df.iterrows():
            kline_data.append([
                row['open'],
                row['close'],
                row['low'],
                row['high']
            ])
        
        # 准备日期数据
        dates = df['date'].dt.strftime('%Y-%m-%d').tolist()
        
        # 准备指标数据
        ma5_data = df['ma5'].fillna('').tolist()
        ma10_data = df['ma10'].fillna('').tolist()
        ma20_data = df['ma20'].fillna('').tolist()
        macd_data = df['macd'].fillna(0).tolist()
        macd_signal_data = df['macd_signal'].fillna(0).tolist()
        volume_data = df['volume'].tolist()
        
        return jsonify({
            'dates': dates,
            'kline': kline_data,
            'ma5': ma5_data,
            'ma10': ma10_data,
            'ma20': ma20_data,
            'macd': macd_data,
            'macd_signal': macd_signal_data,
            'volume': volume_data,
            'buy_points': buy_points,
            'sell_points': sell_points,
            'position': position_data,
            'buy_amount': buy_amount_data,
            'sell_amount': sell_amount_data,
            'cumulative_return': cumulative_return_data
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'加载图表数据失败: {str(e)}'}), 500

if __name__ == '__main__':
    print("启动Web UI服务...")
    print("访问地址: http://localhost:5001")
    app.run(host='0.0.0.0', port=5001, debug=True)