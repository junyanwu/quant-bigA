#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实盘交易运行脚本
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from main import QuantTrader


def main():
    """主函数"""
    print("=== MACD策略实盘交易 ===")
    print("警告: 实盘交易有风险，请谨慎操作！")
    print()
    
    # 确认操作
    confirm = input("确认启动实盘交易？(y/N): ")
    if confirm.lower() != 'y':
        print("操作已取消")
        return
    
    # 创建量化交易程序
    trader = QuantTrader()
    
    # 启动实盘交易
    trader.run_live_trading()
    
    print("\n实盘交易已启动，按 Ctrl+C 停止")
    
    try:
        # 保持程序运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n程序已停止")


if __name__ == "__main__":
    main()