#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回测运行脚本
"""

import sys
import os
import argparse
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from main import QuantTrader
from datetime import datetime


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="MACD策略回测")
    parser.add_argument('--symbol', default='000001.SH', help='回测标的')
    parser.add_argument('--start', default='2020-01-01', help='开始日期')
    parser.add_argument('--end', default='2024-12-31', help='结束日期')
    
    args = parser.parse_args()
    
    print("=== MACD策略回测工具 ===")
    print(f"标的: {args.symbol}")
    print(f"期间: {args.start} 至 {args.end}")
    print()
    
    # 创建量化交易程序
    trader = QuantTrader()
    
    # 运行回测
    performance = trader.run_backtest(args.symbol, args.start, args.end)
    
    if performance:
        print("\n回测完成！")
        print("关键指标:")
        print(f"  总交易次数: {performance.get('total_trades', 0)}")
        print(f"  胜率: {performance.get('win_rate', 0)}%")
        print(f"  总盈亏: {performance.get('total_pnl', 0):,.2f}")
        print(f"  夏普比率: {performance.get('sharpe_ratio', 0)}")
        print(f"  最大回撤: {performance.get('max_drawdown', 0):,.2f}")
    else:
        print("回测失败！")


if __name__ == "__main__":
    main()