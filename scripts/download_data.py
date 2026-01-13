#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据下载脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from main import QuantTrader


def main():
    """主函数"""
    print("=== A股数据下载工具 ===")
    
    # 创建量化交易程序
    trader = QuantTrader()
    
    # 下载数据
    results = trader.download_data()
    
    print("\n数据下载完成！")
    if results:
        print(f"成功: {len(results.get('success', []))} 个标的")
        print(f"失败: {len(results.get('failed', []))} 个标的")
    
    # 显示可用的标的
    available = trader.data_manager.get_available_symbols()
    print(f"\n本地可用数据:")
    print(f"股票: {len(available['stocks'])} 只")
    print(f"ETF: {len(available['etfs'])} 只")
    print(f"指数: {len(available['index'])} 个")


if __name__ == "__main__":
    main()