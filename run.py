#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股量化交易系统启动脚本
"""

import sys
import os
import argparse
from datetime import datetime


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="A股量化交易系统")
    parser.add_argument('--mode', choices=['gui', 'download', 'backtest', 'live', 'download_all', 'dca_backtest'], 
                       default='gui', help='运行模式')
    parser.add_argument('--symbol', default='000001.SH', help='回测标的')
    parser.add_argument('--start', default='2018-01-01', help='开始日期')
    parser.add_argument('--end', default=datetime.now().strftime('%Y-%m-%d'), help='结束日期')
    parser.add_argument('--type', choices=['stock', 'etf', 'index'], default='stock', help='标的类型')
    
    args = parser.parse_args()
    
    # 添加项目路径到Python路径
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)
    
    try:
        if args.mode == 'download_all':
            print("🚀 开始下载A股所有股票和ETF数据...")
            from scripts.download_all_data import main as download_all_main
            download_all_main()
            return
        
        elif args.mode == 'dca_backtest':
            print("🎯 开始定投策略回测...")
            from backtesting.dca_backtest_engine import run_comprehensive_dca_backtest
            run_comprehensive_dca_backtest()
            return
        
        from main import QuantTrader
        
        # 创建量化交易程序
        trader = QuantTrader()
        
        if args.mode == 'gui':
            print("启动图形界面...")
            trader.run_gui()
        
        elif args.mode == 'download':
            print("开始下载数据...")
            trader.download_data()
        
        elif args.mode == 'backtest':
            print(f"开始回测: {args.symbol} {args.start} 至 {args.end}")
            trader.run_backtest(args.symbol, args.start, args.end)
        
        elif args.mode == 'live':
            print("启动实盘交易...")
            trader.run_live_trading()
        
    except ImportError as e:
        print(f"导入错误: {e}")
        print("请确保已安装所有依赖包: pip install -r requirements.txt")
    except Exception as e:
        print(f"运行错误: {e}")


if __name__ == "__main__":
    main()