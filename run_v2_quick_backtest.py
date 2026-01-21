#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v2策略ETF快速回测（前100个ETF）
"""

import sys
import os
from pathlib import Path
import pandas as pd
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from backtesting.dca_trading_backtest import BacktestEngine
from strategies.dca_trading_strategy_v2 import DcaTradingStrategyV2


def run_single_backtest(symbol, symbol_type, start_date, end_date):
    """
    运行单个标的的回测
    """
    try:
        print(f"[{symbol}] 开始回测...")

        # 初始化策略
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

        # 初始化回测引擎
        engine = BacktestEngine(strategy)
        result = engine.run_backtest(symbol, symbol_type, start_date, end_date)

        # 保存结果
        output_dir = f'./results/v2_results/{symbol}'
        os.makedirs(output_dir, exist_ok=True)
        strategy.save_results(output_dir)

        print(f"[{symbol}] ✓ 完成 - 总收益: {result['total_return']*100:.2f}%")
        return {
            'symbol': symbol,
            'success': True,
            'total_return': result.get('total_return', 0),
            'final_value': result.get('final_value', 0)
        }

    except Exception as e:
        print(f"[{symbol}] ✗ 失败: {e}")
        return {
            'symbol': symbol,
            'success': False,
            'error': str(e)
        }


def main():
    """
    主函数
    """
    print("=" * 60)
    print("开始v2策略ETF快速回测（前100个ETF）")
    print("=" * 60)

    # ETF数据目录
    etf_dir = Path('./data/etfs')

    if not etf_dir.exists():
        print(f"ETF数据目录不存在: {etf_dir}")
        return

    # 获取前100个ETF文件
    etf_files = sorted(list(etf_dir.glob('*.csv')))[:100]
    print(f"找到 {len(etf_files)} 个ETF文件（前100个）")

    # 时间范围
    start_date = '2015-01-01'
    end_date = '2026-01-21'

    # 统计信息
    success_count = 0
    failed_count = 0
    failed_symbols = []

    # 使用多线程并发回测（4个线程）
    max_workers = 4

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        futures = {
            executor.submit(
                run_single_backtest,
                file.stem,
                'etf',
                start_date,
                end_date
            ): file.stem for file in etf_files
        }

        # 收集结果
        results = []

        for future in as_completed(futures):
            symbol = futures[future]
            try:
                result = future.result()
                results.append(result)
                if result['success']:
                    success_count += 1
                else:
                    failed_count += 1
                    failed_symbols.append(symbol)
            except Exception as e:
                print(f"[{symbol}] ✗ 异常: {e}")
                failed_count += 1
                failed_symbols.append(symbol)

    # 输出统计
    print("\n" + "=" * 60)
    print("回测完成")
    print("=" * 60)
    print(f"总数: {len(etf_files)}")
    print(f"成功: {success_count}")
    print(f"失败: {failed_count}")

    if failed_symbols:
        print(f"\n失败的ETF: {', '.join(failed_symbols[:10])}")
        if len(failed_symbols) > 10:
            print(f"... 还有 {len(failed_symbols) - 10} 个")

    # 生成汇总文件
    print("\n正在生成汇总文件...")
    generate_summary()

    print("\n✅ 所有任务完成!")


def generate_summary():
    """
    生成v2策略的汇总CSV文件
    """
    results_dir = Path('./results/v2_results')
    output_file = Path('./results/v2_comprehensive_backtest/v2_comprehensive_backtest_results.csv')

    if not results_dir.exists():
        print(f"结果目录不存在: {results_dir}")
        return

    # 读取标的名称映射
    symbol_names_file = './data/symbol_names.json'
    if os.path.exists(symbol_names_file):
        with open(symbol_names_file, 'r', encoding='utf-8') as f:
            symbol_names = json.load(f)
    else:
        symbol_names = {}

    # 收集所有ETF的回测结果
    summary_data = []

    for symbol_dir in sorted(results_dir.iterdir()):
        if not symbol_dir.is_dir():
            continue

        symbol = symbol_dir.name
        results_file = symbol_dir / 'results.json'

        if not results_file.exists():
            continue

        try:
            with open(results_file, 'r', encoding='utf-8') as f:
                results = json.load(f)

            metrics = {
                'symbol': symbol,
                'symbol_type': results.get('symbol_type', 'etf'),
                'total_return': results.get('total_return', 0),
                'annual_return': results.get('annual_return', 0),
                'max_drawdown': results.get('max_drawdown', 0),
                'sharpe_ratio': results.get('sharpe_ratio', 0),
                'final_value': results.get('final_value', 0),
                'dca_buy_count': results.get('dca_buy_count', 0),
                'dca_sell_count': results.get('dca_sell_count', 0),
                't_buy_count': results.get('t_buy_count', 0),
                't_sell_count': results.get('t_sell_count', 0),
                't_profit': results.get('t_profit', 0),
                'data_points': results.get('data_points', 0),
                'start_date': results.get('start_date', ''),
                'end_date': results.get('end_date', ''),
                'data_start_date': results.get('data_start_date', ''),
                'data_end_date': results.get('data_end_date', ''),
                'annual_returns': json.dumps(results.get('annual_returns', []), ensure_ascii=False)
            }

            summary_data.append(metrics)

        except Exception as e:
            print(f"✗ 读取 {symbol} 结果失败: {e}")
            continue

    if not summary_data:
        print("没有找到任何回测结果")
        return

    # 创建DataFrame并保存
    df = pd.DataFrame(summary_data)

    # 保存到CSV
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False, encoding='utf-8')

    print(f"✅ 汇总文件已保存到: {output_file}")
    print(f"   共 {len(summary_data)} 个标的的回测结果")
    print(f"   平均总收益率: {df['total_return'].mean():.2%}")
    print(f"   最高总收益率: {df['total_return'].max():.2%}")
    print(f"   最低总收益率: {df['total_return'].min():.2%}")


if __name__ == '__main__':
    start_time = time.time()
    main()
    elapsed_time = time.time() - start_time
    print(f"\n总耗时: {elapsed_time/60:.2f} 分钟")
