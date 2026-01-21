#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v2策略ETF回测脚本
对所有ETF进行v2策略回测
"""

import sys
import os
import json
import pandas as pd
from datetime import datetime
from multiprocessing import Pool, cpu_count
from typing import Dict, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from strategies.dca_trading_strategy_v2 import DcaTradingStrategyV2
from backtesting.dca_trading_backtest import BacktestEngine
from utils.data_fetcher import AShareDataFetcher


def backtest_single_symbol(args):
    """
    回测单个标的

    Args:
        args: (symbol, symbol_type, start_date, end_date) 元组

    Returns:
        回测结果字典
    """
    import os

    symbol, symbol_type, start_date, end_date = args

    try:
        strategy = DcaTradingStrategyV2(
            total_capital=500000.0,
            dca_ratio=0.7,
            base_dca_amount_per_week=1000.0,
            base_t_amount_per_trade=5000.0,
            max_loss_ratio=0.03,
            profit_target=0.01,
            commission=0.0003,
            slippage=0.001
        )

        engine = BacktestEngine(strategy)
        result = engine.run_backtest(symbol, symbol_type, start_date, end_date)

        if result:
            # 保存详细结果到JSON文件
            output_dir = f'./results/v2_results/{symbol}'
            os.makedirs(output_dir, exist_ok=True)

            # 保存交易记录和每日净值
            strategy.save_results(output_dir)

            # 保存JSON结果
            results_file = os.path.join(output_dir, 'results.json')
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            return {
                'success': True,
                'symbol': symbol,
                'symbol_type': symbol_type,
                'result': result
            }
        else:
            return {
                'success': False,
                'symbol': symbol,
                'error': '回测结果为空'
            }
    except Exception as e:
        return {
            'success': False,
            'symbol': symbol,
            'error': str(e)
        }


def calculate_performance_metrics(result: Dict) -> Dict:
    """
    计算绩效指标

    Args:
        result: 回测结果

    Returns:
        绩效指标字典
    """
    metrics = {
        'symbol': result['symbol'],
        'symbol_type': result['symbol_type'],
        'total_return': result.get('total_return', 0),
        'annual_return': result.get('annual_return', 0),
        'max_drawdown': result.get('max_drawdown', 0),
        'sharpe_ratio': result.get('sharpe_ratio', 0),
        'final_value': result.get('final_value', 0),
        'dca_buy_count': result.get('dca_buy_count', 0),
        'dca_sell_count': result.get('dca_sell_count', 0),
        't_buy_count': result.get('t_buy_count', 0),
        't_sell_count': result.get('t_sell_count', 0),
        't_profit': result.get('t_profit', 0),
        'data_points': result.get('data_points', 0),
        'start_date': result.get('data_start_date', ''),
        'end_date': result.get('data_end_date', '')
    }

    return metrics


def run_v2_etf_backtest():
    """
    运行v2策略ETF回测
    """
    print("=" * 80)
    print("开始v2策略ETF回测")
    print("=" * 80)

    fetcher = AShareDataFetcher()

    start_date = '2015-01-01'
    end_date = datetime.now().strftime('%Y-%m-%d')

    print(f"回测期间: {start_date} 至 {end_date}")
    print(f"数据目录: {fetcher.data_path}")

    all_symbols = []

    # 只获取ETF
    etf_dir = os.path.join(fetcher.data_path, 'etfs')
    if os.path.exists(etf_dir):
        etf_files = [f for f in os.listdir(etf_dir) if f.endswith('.csv')]
        for file in etf_files:
            symbol = file.replace('.csv', '')
            all_symbols.append((symbol, 'etf', start_date, end_date))
        print(f"找到 {len(etf_files)} 个ETF")
    else:
        print("ETF目录不存在")
        return None

    print(f"总计 {len(all_symbols)} 个ETF")
    print("=" * 80)

    # 使用多进程回测
    num_processes = cpu_count()
    print(f"使用 {num_processes} 个进程进行回测")

    results = []
    failed_symbols = []

    with Pool(processes=num_processes) as pool:
        for idx, backtest_result in enumerate(pool.imap_unordered(backtest_single_symbol, all_symbols), 1):
            if backtest_result['success']:
                result = backtest_result['result']
                metrics = calculate_performance_metrics(result)
                results.append(metrics)

                if idx % 100 == 0 or idx == len(all_symbols):
                    print(f"[{idx}/{len(all_symbols)}] 进度更新...")
            else:
                failed_symbols.append(backtest_result)
                print(f"[{idx}/{len(all_symbols)}] {backtest_result['symbol']} ❌ "
                      f"失败: {backtest_result['error']}")

    print("=" * 80)
    print(f"回测完成！")
    print(f"成功: {len(results)}")
    print(f"失败: {len(failed_symbols)}")
    print("=" * 80)

    # 保存结果
    output_dir = './results/v2_comprehensive_backtest'
    os.makedirs(output_dir, exist_ok=True)

    # 保存详细结果
    results_df = pd.DataFrame(results)
    results_file = os.path.join(output_dir, 'v2_comprehensive_backtest_results.csv')
    results_df.to_csv(results_file, index=False, encoding='utf-8-sig')
    print(f"详细结果已保存到: {results_file}")

    # 保存失败标的
    if failed_symbols:
        failed_file = os.path.join(output_dir, 'failed_symbols.json')
        with open(failed_file, 'w', encoding='utf-8') as f:
            json.dump(failed_symbols, f, ensure_ascii=False, indent=2)
        print(f"失败标的已保存到: {failed_file}")

    # 生成统计报告
    generate_summary_report(results_df, output_dir)

    return results_df


def generate_summary_report(results_df: pd.DataFrame, output_dir: str):
    """
    生成统计报告

    Args:
        results_df: 回测结果DataFrame
        output_dir: 输出目录
    """
    print("\n" + "=" * 80)
    print("统计报告")
    print("=" * 80)

    # 总体统计
    print(f"\n总体统计:")
    print(f"  总标的数: {len(results_df)}")
    print(f"  平均总收益率: {results_df['total_return'].mean() * 100:.2f}%")
    print(f"  平均年化收益率: {results_df['annual_return'].mean() * 100:.2f}%")
    print(f"  年化收益率中位数: {results_df['annual_return'].median() * 100:.2f}%")
    print(f"  平均最大回撤: {results_df['max_drawdown'].mean() * 100:.2f}%")
    print(f"  平均夏普比率: {results_df['sharpe_ratio'].mean():.2f}")

    # 盈利标的统计
    profitable = results_df[results_df['annual_return'] > 0]
    print(f"\n盈利标的统计:")
    print(f"  盈利标的数: {len(profitable)} ({len(profitable)/len(results_df)*100:.1f}%)")
    print(f"  平均年化收益率: {profitable['annual_return'].mean() * 100:.2f}%")

    # 亏损标的统计
    loss = results_df[results_df['annual_return'] <= 0]
    print(f"\n亏损标的统计:")
    print(f"  亏损标的数: {len(loss)} ({len(loss)/len(results_df)*100:.1f}%)")
    print(f"  平均年化收益率: {loss['annual_return'].mean() * 100:.2f}%")

    # Top 5
    print(f"\n年化收益率 Top 5:")
    top5 = results_df.nlargest(5, 'annual_return')
    for idx, row in top5.iterrows():
        print(f"  {row['symbol']}: {row['annual_return']*100:.2f}%")

    # Bottom 5
    print(f"\n年化收益率 Bottom 5:")
    bottom5 = results_df.nsmallest(5, 'annual_return')
    for idx, row in bottom5.iterrows():
        print(f"  {row['symbol']}: {row['annual_return']*100:.2f}%")

    # 保存统计报告
    report_file = os.path.join(output_dir, 'summary_report.txt')
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("v2策略ETF回测统计报告\n")
        f.write("=" * 80 + "\n\n")

        f.write(f"回测期间: {results_df['start_date'].iloc[0]} 至 {results_df['end_date'].iloc[0]}\n")
        f.write(f"总标的数: {len(results_df)}\n\n")

        f.write("总体统计:\n")
        f.write(f"  平均总收益率: {results_df['total_return'].mean() * 100:.2f}%\n")
        f.write(f"  平均年化收益率: {results_df['annual_return'].mean() * 100:.2f}%\n")
        f.write(f"  年化收益率中位数: {results_df['annual_return'].median() * 100:.2f}%\n")
        f.write(f"  平均最大回撤: {results_df['max_drawdown'].mean() * 100:.2f}%\n")
        f.write(f"  平均夏普比率: {results_df['sharpe_ratio'].mean():.2f}\n\n")

        f.write("盈利标的统计:\n")
        f.write(f"  盈利标的数: {len(profitable)} ({len(profitable)/len(results_df)*100:.1f}%)\n")
        f.write(f"  平均年化收益率: {profitable['annual_return'].mean() * 100:.2f}%\n\n")

        f.write("亏损标的统计:\n")
        f.write(f"  亏损标的数: {len(loss)} ({len(loss)/len(results_df)*100:.1f}%)\n")
        f.write(f"  平均年化收益率: {loss['annual_return'].mean() * 100:.2f}%\n\n")

        f.write("年化收益率 Top 5:\n")
        for idx, row in top5.iterrows():
            f.write(f"  {row['symbol']}: {row['annual_return']*100:.2f}%\n")

        f.write("\n年化收益率 Bottom 5:\n")
        for idx, row in bottom5.iterrows():
            f.write(f"  {row['symbol']}: {row['annual_return']*100:.2f}%\n")

    print(f"\n统计报告已保存到: {report_file}")
    print("=" * 80)


if __name__ == '__main__':
    results_df = run_v2_etf_backtest()

    print("\n" + "=" * 80)
    print("v2策略ETF回测完成！")
    print("=" * 80)
