#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定投策略回测引擎 - 使用本地数据
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import matplotlib.pyplot as plt
import seaborn as sns

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.data_fetcher import AShareDataFetcher
from strategies.dca_strategy import DCAStrategy
from config.config import BACKTEST_CONFIG

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


class DCABacktestEngine:
    """定投策略回测引擎"""
    
    def __init__(self, initial_capital: float = None, monthly_investment: float = None):
        """初始化回测引擎"""
        self.fetcher = AShareDataFetcher()
        
        # 使用配置或传入参数
        self.initial_capital = initial_capital or BACKTEST_CONFIG['initial_capital']
        self.monthly_investment = monthly_investment or 5000
        
        self.dca_strategy = DCAStrategy(self.initial_capital, self.monthly_investment)
        self.results = {}
        
    def load_local_data(self, symbol: str, symbol_type: str = 'stock') -> Optional[pd.Series]:
        """从本地加载价格数据"""
        try:
            data = self.fetcher.load_data(symbol, symbol_type)
            if data is not None and not data.empty:
                return data['close']  # 返回收盘价序列
            return None
        except Exception as e:
            print(f"加载 {symbol} 数据失败: {e}")
            return None
    
    def get_available_symbols_for_backtest(self, min_records: int = 500) -> Dict[str, List[str]]:
        """获取可用于回测的标的列表"""
        available = self.fetcher.get_available_symbols()
        filtered = {'stocks': [], 'etfs': [], 'index': []}
        
        # 过滤数据量足够的标的
        for symbol_type, symbols in available.items():
            for symbol in symbols:
                data = self.load_local_data(symbol, symbol_type)
                if data is not None and len(data) >= min_records:
                    filtered[symbol_type].append(symbol)
        
        return filtered
    
    def backtest_single_symbol(self, symbol: str, symbol_type: str, 
                             start_date: str, end_date: str) -> Optional[Dict]:
        """回测单个标的"""
        prices = self.load_local_data(symbol, symbol_type)
        if prices is None:
            return None
        
        # 确保日期在数据范围内
        if start_date < prices.index[0].strftime('%Y-%m-%d'):
            start_date = prices.index[0].strftime('%Y-%m-%d')
        if end_date > prices.index[-1].strftime('%Y-%m-%d'):
            end_date = prices.index[-1].strftime('%Y-%m-%d')
        
        result = self.dca_strategy.calculate_dca_returns(prices, start_date, end_date)
        if result:
            result['symbol'] = symbol
            result['symbol_type'] = symbol_type
            result['data_points'] = len(prices.loc[start_date:end_date])
            
        return result
    
    def backtest_multiple_symbols(self, symbols: List[str], symbol_type: str,
                                start_date: str, end_date: str, 
                                max_symbols: int = 50) -> pd.DataFrame:
        """回测多个标的"""
        results = []
        
        # 限制回测数量，避免内存问题
        symbols = symbols[:max_symbols]
        
        print(f"🔄 开始回测 {len(symbols)} 个{symbol_type}...")
        
        for i, symbol in enumerate(symbols, 1):
            print(f"   进度: {i}/{len(symbols)} - {symbol}")
            
            result = self.backtest_single_symbol(symbol, symbol_type, start_date, end_date)
            if result:
                results.append(result)
        
        return pd.DataFrame(results)
    
    def backtest_popular_indices(self, start_date: str, end_date: str) -> pd.DataFrame:
        """回测热门指数"""
        # 主要A股指数
        indices = [
            '000001.SH',  # 上证指数
            '000300.SH',  # 沪深300
            '000905.SH',  # 中证500
            '399001.SZ',  # 深证成指
            '399006.SZ',  # 创业板指
            '000688.SH',  # 科创50
            '000016.SH',  # 上证50
        ]
        
        results = []
        for symbol in indices:
            result = self.backtest_single_symbol(symbol, 'index', start_date, end_date)
            if result:
                results.append(result)
        
        return pd.DataFrame(results)
    
    def backtest_etf_portfolio(self, start_date: str, end_date: str) -> pd.DataFrame:
        """回测ETF组合"""
        # 热门ETF
        etfs = [
            '510300.SH',  # 沪深300ETF
            '510500.SH',  # 中证500ETF
            '159915.SZ',  # 创业板ETF
            '588000.SH',  # 科创50ETF
            '510050.SH',  # 上证50ETF
            '512100.SH',  # 中证1000ETF
            '515000.SH',  # 科技ETF
        ]
        
        results = []
        for symbol in etfs:
            result = self.backtest_single_symbol(symbol, 'etf', start_date, end_date)
            if result:
                results.append(result)
        
        return pd.DataFrame(results)
    
    def generate_comprehensive_report(self, results_df: pd.DataFrame, test_type: str):
        """生成综合回测报告"""
        print("\n" + "=" * 60)
        print(f"           {test_type}定投策略回测报告")
        print("=" * 60)
        
        if results_df.empty:
            print("❌ 没有有效的回测结果")
            return
        
        # 基础统计
        print(f"\n📊 回测概况:")
        print(f"   回测标的数量: {len(results_df)}")
        print(f"   平均数据点数: {results_df['data_points'].mean():.0f}")
        print(f"   平均收益率: {results_df['total_return'].mean():.2f}%")
        print(f"   最高收益率: {results_df['total_return'].max():.2f}%")
        print(f"   最低收益率: {results_df['total_return'].min():.2f}%")
        
        # 收益率排名
        print(f"\n🏆 收益率排名 (前10):")
        top_results = results_df.nlargest(10, 'total_return')
        for i, (_, row) in enumerate(top_results.iterrows(), 1):
            print(f"   {i}. {row['symbol']}: {row['total_return']:.2f}%")
        
        # 定投优势分析
        positive_ratio = (results_df['vs_lump_sum'] > 0).mean() * 100
        avg_advantage = results_df['vs_lump_sum'].mean()
        
        print(f"\n💡 定投策略优势:")
        print(f"   定投优于一次性投资的比例: {positive_ratio:.1f}%")
        print(f"   平均定投优势: {avg_advantage:,.0f}元")
        
        if positive_ratio > 50:
            print("   ✅ 定投策略在多数情况下表现更好")
        else:
            print("   ⚠️ 一次性投资在多数情况下表现更好")
    
    def plot_comparison_charts(self, results_df: pd.DataFrame, test_type: str):
        """绘制比较图表"""
        if results_df.empty:
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle(f'{test_type}定投策略回测结果', fontsize=16)
        
        # 1. 收益率分布
        axes[0, 0].hist(results_df['total_return'], bins=20, alpha=0.7, color='skyblue')
        axes[0, 0].set_title('收益率分布')
        axes[0, 0].set_xlabel('总收益率 (%)')
        axes[0, 0].set_ylabel('频数')
        
        # 2. 收益率排名
        top_10 = results_df.nlargest(10, 'total_return')
        axes[0, 1].barh(range(len(top_10)), top_10['total_return'])
        axes[0, 1].set_yticks(range(len(top_10)))
        axes[0, 1].set_yticklabels(top_10['symbol'])
        axes[0, 1].set_title('收益率前10名')
        axes[0, 1].set_xlabel('总收益率 (%)')
        
        # 3. 定投优势分布
        axes[1, 0].hist(results_df['vs_lump_sum'], bins=20, alpha=0.7, color='lightgreen')
        axes[1, 0].axvline(x=0, color='red', linestyle='--', alpha=0.8)
        axes[1, 0].set_title('定投优势分布 (vs一次性投资)')
        axes[1, 0].set_xlabel('定投优势 (元)')
        axes[1, 0].set_ylabel('频数')
        
        # 4. 年化收益率分布
        axes[1, 1].hist(results_df['annual_return'], bins=20, alpha=0.7, color='orange')
        axes[1, 1].set_title('年化收益率分布')
        axes[1, 1].set_xlabel('年化收益率 (%)')
        axes[1, 1].set_ylabel('频数')
        
        plt.tight_layout()
        plt.show()


def run_comprehensive_dca_backtest():
    """运行全面的定投回测"""
    print("🎯 A股定投策略全面回测系统")
    print("=" * 60)
    
    # 创建回测引擎
    engine = DCABacktestEngine(initial_capital=100000, monthly_investment=5000)
    
    # 检查可用数据
    print("📊 检查本地数据...")
    available = engine.get_available_symbols_for_backtest()
    
    print(f"   可用股票: {len(available['stocks'])} 只")
    print(f"   可用ETF: {len(available['etfs'])} 只")
    print(f"   可用指数: {len(available['index'])} 个")
    
    if len(available['stocks']) == 0 and len(available['etfs']) == 0:
        print("❌ 没有可用的本地数据，请先运行数据下载脚本")
        return
    
    # 设置回测期间
    start_date = '2018-01-01'
    end_date = '2024-12-31'
    
    print(f"\n📅 回测期间: {start_date} 至 {end_date}")
    print(f"💰 定投设置: 每月5,000元")
    
    # 1. 回测热门指数
    print("\n" + "=" * 60)
    print("           热门指数定投回测")
    print("=" * 60)
    
    indices_results = engine.backtest_popular_indices(start_date, end_date)
    engine.generate_comprehensive_report(indices_results, "热门指数")
    
    # 2. 回测ETF组合
    print("\n" + "=" * 60)
    print("           ETF组合定投回测")
    print("=" * 60)
    
    etf_results = engine.backtest_etf_portfolio(start_date, end_date)
    engine.generate_comprehensive_report(etf_results, "ETF组合")
    
    # 3. 回测随机股票样本
    if len(available['stocks']) > 0:
        print("\n" + "=" * 60)
        print("           随机股票样本回测")
        print("=" * 60)
        
        # 随机选择20只股票进行回测
        import random
        sample_stocks = random.sample(available['stocks'], min(20, len(available['stocks'])))
        
        stock_results = engine.backtest_multiple_symbols(
            sample_stocks, 'stock', start_date, end_date, max_symbols=20
        )
        engine.generate_comprehensive_report(stock_results, "随机股票样本")
    
    # 绘制综合图表
    print("\n📈 生成综合图表...")
    
    # 合并所有结果
    all_results = pd.concat([indices_results, etf_results], ignore_index=True)
    if 'stock_results' in locals():
        all_results = pd.concat([all_results, stock_results], ignore_index=True)
    
    engine.plot_comparison_charts(all_results, "综合")
    
    print("\n" + "🎉 回测完成!")
    print("=" * 60)
    
    return {
        'indices': indices_results,
        'etfs': etf_results,
        'stocks': stock_results if 'stock_results' in locals() else None
    }


if __name__ == "__main__":
    run_comprehensive_dca_backtest()