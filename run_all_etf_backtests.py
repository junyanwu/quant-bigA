#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回测所有ETF（多进程版本 - 优化版）
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from multiprocessing import Pool, cpu_count, Manager
import pandas as pd

sys.path.append(str(Path(__file__).parent))

from backtesting.dca_trading_backtest import BacktestEngine
from strategies.dca_trading_strategy import DcaTradingStrategy


def get_all_etf_symbols():
    """
    获取所有ETF标的
    """
    etf_dir = Path('./data/etfs')
    etf_files = list(etf_dir.glob('*.csv'))
    
    symbols = []
    for f in etf_files:
        symbol = f.stem
        symbols.append(symbol)
    
    return sorted(symbols)


def backtest_single_etf(args):
    """
    回测单个ETF
    
    Args:
        args: (symbol, start_date, end_date, strategy_params)
        
    Returns:
        回测结果字典
    """
    symbol, start_date, end_date, strategy_params = args
    
    try:
        # 初始化策略
        strategy = DcaTradingStrategy(**strategy_params)
        
        # 初始化回测引擎
        engine = BacktestEngine(strategy)
        
        # 运行回测
        result = engine.run_backtest(symbol, 'etf', start_date, end_date)
        
        return {
            'success': True,
            'symbol': symbol,
            'result': result
        }
    except Exception as e:
        return {
            'success': False,
            'symbol': symbol,
            'error': str(e)
        }


def run_all_etf_backtests():
    """
    运行所有ETF回测
    """
    # 获取所有ETF标的
    all_symbols = get_all_etf_symbols()
    
    print(f"找到 {len(all_symbols)} 个ETF标的")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # 策略参数
    strategy_params = {
        'total_capital': 500000.0,
        'dca_ratio': 0.7,
        'dca_amount_per_week': 1000.0,
        't_amount_per_trade': 5000.0,
        'max_loss_ratio': 0.03,
        'profit_target': 0.01,
        'commission': 0.0003,
        'slippage': 0.001
    }
    
    # 回测参数
    start_date = '2015-01-01'
    end_date = '2026-01-18'
    
    # 准备任务列表
    tasks = [(symbol, start_date, end_date, strategy_params) for symbol in all_symbols]
    
    # 确定进程数（使用所有CPU核心）
    num_processes = cpu_count()
    print(f"使用 {num_processes} 个进程进行回测")
    print("=" * 80)
    
    # 使用进程池进行回测
    results = []
    failed_symbols = []
    
    with Pool(processes=num_processes) as pool:
        # 使用 imap_unordered 来获取实时进度
        for idx, backtest_result in enumerate(pool.imap_unordered(backtest_single_etf, tasks), 1):
            if backtest_result['success']:
                result = backtest_result['result']
                results.append(result)
                # 每100个标的后输出一次进度
                if idx % 100 == 0 or idx == len(all_symbols):
                    print(f"[{idx}/{len(all_symbols)}] 进度更新...")
            else:
                failed_symbols.append(backtest_result['symbol'])
                print(f"[{idx}/{len(all_symbols)}] {backtest_result['symbol']} ❌ "
                    f"失败: {backtest_result['error']}")
    
    # 保存综合结果
    print(f"\n{'=' * 80}")
    print(f"回测完成！")
    print(f"{'=' * 80}")
    print(f"成功: {len(results)} 个")
    print(f"失败: {len(failed_symbols)} 个")
    
    if failed_symbols:
        print(f"\n失败的标的:")
        for symbol in failed_symbols:
            print(f"  - {symbol}")
    
    # 保存结果
    output_dir = './results'
    os.makedirs(output_dir, exist_ok=True)
    
    # 添加时间戳
    generated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 保存为CSV
    df = pd.DataFrame(results)
    df['generated_at'] = generated_at
    csv_file = os.path.join(output_dir, 'all_backtest_summary.csv')
    df.to_csv(csv_file, index=False, encoding='utf-8')
    
    print(f"\n✅ 综合结果已保存到: {csv_file}")
    
    # 打印排名
    print(f"\n{'=' * 80}")
    print(f"回测结果排名（按年化收益率）")
    print(f"{'=' * 80}")
    
    df_sorted = df.sort_values('annual_return', ascending=False)
    print(f"{'排名':<6} {'标的代码':<12} {'总收益率':<12} {'年化收益率':<12} {'最大回撤':<12} {'夏普比率':<12}")
    print(f"{'-' * 80}")
    
    for idx, row in df_sorted.head(20).iterrows():
        print(f"{idx+1:<6} {row['symbol']:<12} "
              f"{row['total_return']*100:>10.2f}% "
              f"{row['annual_return']*100:>10.2f}% "
              f"{row['max_drawdown']*100:>10.2f}% "
              f"{row['sharpe_ratio']:>10.2f}")
    
    print(f"{'=' * 80}")
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    run_all_etf_backtests()
