#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试优化后的代码
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from strategies.dca_trading_strategy import DcaTradingStrategy
from strategies.indicators import calculate_all_indicators, get_trading_signals
from utils.data_fetcher import AShareDataFetcher
import pandas as pd
from datetime import datetime

def test_strategy():
    """测试策略"""
    print("=" * 80)
    print("测试策略")
    print("=" * 80)
    
    try:
        strategy = DcaTradingStrategy(
            total_capital=500000.0,
            dca_ratio=0.7,
            dca_amount_per_week=1000.0,
            t_amount_per_trade=5000.0,
            max_loss_ratio=0.03,
            profit_target=0.01,
            commission=0.0003,
            slippage=0.001
        )
        
        print("✅ 策略初始化成功")
        print(f"总资金: {strategy.total_capital}")
        print(f"定投资金: {strategy.dca_capital}")
        print(f"做T资金: {strategy.t_capital}")
        print(f"每周定投金额: {strategy.dca_amount_per_week}")
        print(f"每次做T金额: {strategy.t_amount_per_trade}")
        
        return True
    except Exception as e:
        print(f"❌ 策略初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_indicators():
    """测试指标计算"""
    print("\n" + "=" * 80)
    print("测试指标计算")
    print("=" * 80)
    
    try:
        fetcher = AShareDataFetcher()
        df = fetcher.get_data('510300.SH', 'etf', '2023-01-01', '2024-12-31')
        
        if df is None or df.empty:
            print("❌ 无法获取数据")
            return False
        
        print(f"✅ 数据获取成功，共 {len(df)} 条记录")
        
        df = calculate_all_indicators(df)
        df = get_trading_signals(df)
        
        print(f"✅ 指标计算成功")
        print(f"列数: {len(df.columns)}")
        print(f"部分列: {df.columns.tolist()[:10]}")
        
        return True
    except Exception as e:
        print(f"❌ 指标计算失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_backtest():
    """测试回测"""
    print("\n" + "=" * 80)
    print("测试回测")
    print("=" * 80)
    
    try:
        from backtesting.dca_trading_backtest import BacktestEngine
        
        strategy = DcaTradingStrategy(
            total_capital=500000.0,
            dca_ratio=0.7,
            dca_amount_per_week=1000.0,
            t_amount_per_trade=5000.0,
            max_loss_ratio=0.03,
            profit_target=0.01,
            commission=0.0003,
            slippage=0.001
        )
        
        engine = BacktestEngine(strategy)
        
        result = engine.run_backtest('510300.SH', 'etf', '2023-01-01', '2024-12-31')
        
        if not result:
            print("❌ 回测失败")
            return False
        
        print(f"✅ 回测成功")
        print(f"总收益率: {result['total_return'] * 100:.2f}%")
        print(f"年化收益率: {result['annual_return'] * 100:.2f}%")
        print(f"最大回撤: {result['max_drawdown'] * 100:.2f}%")
        print(f"夏普比率: {result['sharpe_ratio']:.2f}")
        
        return True
    except Exception as e:
        print(f"❌ 回测失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_web_app():
    """测试Web应用"""
    print("\n" + "=" * 80)
    print("测试Web应用")
    print("=" * 80)
    
    try:
        from web.app import app
        
        print("✅ Web应用导入成功")
        
        with app.test_client() as client:
            response = client.get('/')
            if response.status_code == 200:
                print("✅ 首页访问成功")
            else:
                print(f"❌ 首页访问失败，状态码: {response.status_code}")
                return False
            
            response = client.get('/api/summary')
            if response.status_code == 200:
                data = response.get_json()
                print(f"✅ API访问成功，返回 {len(data)} 个标的")
            else:
                print(f"❌ API访问失败，状态码: {response.status_code}")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Web应用测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("开始测试优化后的代码")
    print("=" * 80)
    
    results = {
        '策略测试': test_strategy(),
        '指标计算测试': test_indicators(),
        '回测测试': test_backtest(),
        'Web应用测试': test_web_app()
    }
    
    print("\n" + "=" * 80)
    print("测试结果汇总")
    print("=" * 80)
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 80)
    if all_passed:
        print("所有测试通过！✅")
    else:
        print("部分测试失败！❌")
    print("=" * 80)
    
    return all_passed

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
