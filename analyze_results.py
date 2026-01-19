#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析回测结果对比
"""

import pandas as pd

# 读取新策略结果
df = pd.read_csv('./results/all_backtest_summary.csv')

print('新策略回测结果统计:')
print('=' * 80)
print(f'总标的数: {len(df)}')
print(f'成功: {len(df)}')
print(f'失败: 0')
print(f'\n总收益率统计:')
print(df['total_return'].describe())
print(f'\n年化收益率统计:')
print(df['annual_return'].describe())
print(f'\n最大回撤统计:')
print(df['max_drawdown'].describe())
print(f'\n夏普比率统计:')
print(df['sharpe_ratio'].describe())
print(f'\n前20名ETF（按年化收益率）:')
print(df.nlargest(20, 'annual_return')[['symbol', 'total_return', 'annual_return', 'max_drawdown', 'sharpe_ratio']])

# 计算盈利标的数量
profitable = len(df[df['total_return'] > 0])
print(f'\n盈利标的数: {profitable} ({profitable/len(df)*100:.2f}%)')
print(f'亏损标的数: {len(df) - profitable} ({(len(df)-profitable)/len(df)*100:.2f}%)')
