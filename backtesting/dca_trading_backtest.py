#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回测引擎
基于VeighNa框架的回测引擎
"""

import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
import os
import json

from strategies.dca_trading_strategy import DcaTradingStrategy
from strategies.indicators import calculate_all_indicators, get_trading_signals, calculate_index_indicators
from utils.data_fetcher import AShareDataFetcher


class BacktestEngine:
    """
    回测引擎
    
    支持定投+做T策略的回测
    """
    
    def __init__(self, strategy: DcaTradingStrategy):
        """
        初始化回测引擎
        
        Args:
            strategy: 策略实例
        """
        self.strategy = strategy
        self.data_fetcher = AShareDataFetcher()
        
        # 回测结果
        self.results = {}
        
        # 大盘数据缓存
        self.index_data_cache = None
        self.index_data_date_range = None
        
        # 回测配置
        self.config = {
            'start_date': '2015-01-01',
            'end_date': datetime.now().strftime('%Y-%m-%d'),
            'symbols': []
        }
    
    def run_backtest(self, symbol: str, symbol_type: str = 'etf',
                   start_date: Optional[str] = None,
                   end_date: Optional[str] = None) -> Dict:
        """
        运行单个标的的回测
        
        Args:
            symbol: 标的代码
            symbol_type: 标的类型
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            回测结果
        """
        if start_date is None:
            start_date = self.config['start_date']
        if end_date is None:
            end_date = self.config['end_date']
        
        print(f"\n{'=' * 60}")
        print(f"开始回测 {symbol}")
        print(f"回测期间: {start_date} 至 {end_date}")
        print(f"{'=' * 60}")
        
        # 获取数据
        print(f"正在获取数据...")
        df = self.data_fetcher.get_data(symbol, symbol_type, start_date, end_date)
        
        if df is None or df.empty:
            print(f"❌ 无法获取 {symbol} 的数据")
            return {}
        
        print(f"✅ 数据获取成功，共 {len(df)} 条记录")
        
        # 获取大盘数据（上证指数）- 使用缓存
        current_date_range = (start_date, end_date)
        if self.index_data_cache is None or self.index_data_date_range != current_date_range:
            print(f"正在获取大盘数据...")
            index_df = self.data_fetcher.get_data('000001.SH', 'index', start_date, end_date)
            
            if index_df is not None and not index_df.empty:
                # 计算大盘指标
                index_df = calculate_index_indicators(index_df)
                # 缓存大盘数据
                self.index_data_cache = index_df
                self.index_data_date_range = current_date_range
                print(f"✅ 大盘数据获取成功")
            else:
                print(f"⚠️  大盘数据获取失败，将使用默认值")
                self.index_data_cache = None
                self.index_data_date_range = None
        else:
            print(f"✅ 使用缓存的大盘数据")
            index_df = self.index_data_cache
        
        if index_df is not None and not index_df.empty:
            # 合并大盘数据到标的数据
            df = df.join(index_df[['drop_2', 'drop_1', 'drop_2_rebound_03', 'drop_1_rebound_02']], how='left')
        else:
            df['drop_2'] = False
            df['drop_1'] = False
            df['drop_2_rebound_03'] = False
            df['drop_1_rebound_02'] = False
        
        # 计算技术指标
        print(f"正在计算技术指标...")
        df = calculate_all_indicators(df)
        df = get_trading_signals(df)
        print(f"✅ 技术指标计算完成")
        
        # 重置策略
        self.strategy = DcaTradingStrategy(**self.strategy.params)
        
        # 运行回测
        print(f"正在运行回测...")
        for idx, row in df.iterrows():
            date = idx
            bar_data = row.to_dict()
            bar_data['symbol'] = symbol
            
            # 添加大盘数据
            bar_data['index_data'] = {
                'drop_2': row.get('drop_2', False),
                'drop_1': row.get('drop_1', False),
                'drop_2_rebound_03': row.get('drop_2_rebound_03', False),
                'drop_1_rebound_02': row.get('drop_1_rebound_02', False)
            }
            
            self.strategy.on_bar(bar_data, date)
        
        print(f"✅ 回测完成")
        
        # 获取结果
        results = self.strategy.get_results()
        results['symbol'] = symbol
        results['symbol_type'] = symbol_type
        results['start_date'] = start_date
        results['end_date'] = end_date
        results['data_points'] = len(df)
        
        # 打印结果
        self._print_results(results)
        
        return results
    
    def run_multiple_backtests(self, symbols: List[str], symbol_types: List[str],
                            start_date: Optional[str] = None,
                            end_date: Optional[str] = None) -> List[Dict]:
        """
        运行多个标的的回测
        
        Args:
            symbols: 标的代码列表
            symbol_types: 标的类型列表
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            回测结果列表
        """
        all_results = []
        
        for symbol, symbol_type in zip(symbols, symbol_types):
            try:
                result = self.run_backtest(symbol, symbol_type, start_date, end_date)
                if result:
                    all_results.append(result)
            except Exception as e:
                print(f"❌ 回测 {symbol} 失败: {e}")
                import traceback
                traceback.print_exc()
        
        # 保存综合结果
        if all_results:
            self._save_summary_results(all_results)
        
        return all_results
    
    def _print_results(self, results: Dict):
        """
        打印回测结果
        
        Args:
            results: 回测结果
        """
        print(f"\n{'=' * 60}")
        print(f"回测结果 - {results['symbol']}")
        print(f"{'=' * 60}")
        print(f"总收益率: {results['total_return'] * 100:.2f}%")
        print(f"年化收益率: {results['annual_return'] * 100:.2f}%")
        print(f"最大回撤: {results['max_drawdown'] * 100:.2f}%")
        print(f"夏普比率: {results['sharpe_ratio']:.2f}")
        print(f"最终资产: {results['final_value']:,.2f}")
        print(f"\n定投交易:")
        print(f"  买入次数: {results['dca_buy_count']}")
        print(f"  卖出次数: {results['dca_sell_count']}")
        print(f"  剩余资金: {results['dca_cash']:,.2f}")
        print(f"  持仓市值: {results['dca_value']:,.2f}")
        print(f"\n做T交易:")
        print(f"  买入次数: {results['t_buy_count']}")
        print(f"  卖出次数: {results['t_sell_count']}")
        print(f"  做T盈亏: {results['t_profit']:,.2f}")
        print(f"  剩余资金: {results['t_cash']:,.2f}")
        print(f"  持仓市值: {results['t_value']:,.2f}")
        print(f"{'=' * 60}\n")
    
    def _save_summary_results(self, all_results: List[Dict]):
        """
        保存综合结果
        
        Args:
            all_results: 所有回测结果
        """
        output_dir = './results'
        os.makedirs(output_dir, exist_ok=True)
        
        # 保存综合结果
        summary_file = os.path.join(output_dir, 'backtest_summary.json')
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        
        # 保存为CSV
        df = pd.DataFrame(all_results)
        csv_file = os.path.join(output_dir, 'backtest_summary.csv')
        df.to_csv(csv_file, index=False, encoding='utf-8')
        
        print(f"\n✅ 综合结果已保存到: {summary_file}")
        print(f"✅ CSV文件已保存到: {csv_file}")
        
        # 打印对比表格
        print(f"\n{'=' * 80}")
        print(f"回测结果对比")
        print(f"{'=' * 80}")
        print(f"{'标的':<12} {'总收益率':<12} {'年化收益率':<12} {'最大回撤':<12} {'夏普比率':<12} {'最终资产':<15}")
        print(f"{'-' * 80}")
        
        for result in all_results:
            print(f"{result['symbol']:<12} "
                  f"{result['total_return'] * 100:>10.2f}% "
                  f"{result['annual_return'] * 100:>10.2f}% "
                  f"{result['max_drawdown'] * 100:>10.2f}% "
                  f"{result['sharpe_ratio']:>10.2f} "
                  f"{result['final_value']:>13,.2f}")
        
        print(f"{'=' * 80}")


def run_etf_backtests():
    """
    运行ETF回测
    
    测试标的：
    1. 宽基指数ETF
    2. 红利低波100ETF
    """
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
    
    # 测试标的
    symbols = [
        '510300.SH',  # 沪深300ETF
        '510500.SH',  # 中证500ETF
        '159915.SZ',  # 创业板ETF
        '512880.SH',  # 证券ETF
        '512690.SH',  # 酒ETF
        '159928.SZ',  # 消费ETF
        '512100.SH',  # 中证1000ETF
        '512000.SH',  # 券商ETF
        '516160.SH',  # 新能源车ETF
        '515050.SH',  # 5GETF
        '159806.SZ',  # 新能源ETF
        '516970.SH',  # 红利低波ETF
    ]
    
    symbol_types = ['etf'] * len(symbols)
    
    # 运行回测
    results = engine.run_multiple_backtests(
        symbols=symbols,
        symbol_types=symbol_types,
        start_date='2020-01-01',
        end_date='2024-12-31'
    )
    
    # 保存每个标的的详细结果
    for i, result in enumerate(results):
        symbol = result['symbol']
        output_dir = f'./results/{symbol}'
        
        # 重新运行单个回测以保存详细数据
        engine.strategy = DcaTradingStrategy(**strategy.params)
        engine.run_backtest(symbol, 'etf', '2020-01-01', '2024-12-31')
        engine.strategy.save_results(output_dir)
    
    print(f"\n{'=' * 60}")
    print(f"所有回测完成！")
    print(f"结果保存在: ./results/")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    run_etf_backtests()