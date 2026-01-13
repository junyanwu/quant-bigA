#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
稳定版A股数据下载脚本
使用更稳定的akshare API接口
"""

import os
import sys
import pandas as pd
import akshare as ak
from datetime import datetime, timedelta
import logging
import time

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 数据配置
DATA_PATH = './data'
START_DATE = '2015-01-01'
END_DATE = datetime.now().strftime('%Y-%m-%d')

def create_data_directories():
    """创建数据目录"""
    os.makedirs(DATA_PATH, exist_ok=True)
    os.makedirs(os.path.join(DATA_PATH, 'stocks'), exist_ok=True)
    os.makedirs(os.path.join(DATA_PATH, 'etfs'), exist_ok=True)
    os.makedirs(os.path.join(DATA_PATH, 'index'), exist_ok=True)
    print("✅ 数据目录创建完成")

def download_index_data():
    """下载主要指数数据"""
    print("\n📊 开始下载指数数据...")
    
    index_list = [
        {'code': '000001', 'exchange': 'SH', 'name': '上证指数'},
        {'code': '000300', 'exchange': 'SH', 'name': '沪深300'},
        {'code': '000905', 'exchange': 'SH', 'name': '中证500'},
        {'code': '399001', 'exchange': 'SZ', 'name': '深证成指'},
        {'code': '399006', 'exchange': 'SZ', 'name': '创业板指'},
        {'code': '000688', 'exchange': 'SH', 'name': '科创50'}
    ]
    
    success_count = 0
    
    for index_info in index_list:
        try:
            symbol = f"{index_info['code']}.{index_info['exchange']}"
            
            # 使用更稳定的指数接口
            df = ak.index_zh_a_hist(symbol=index_info['code'], period="daily", 
                                   start_date=START_DATE, end_date=END_DATE)
            
            if not df.empty:
                # 标准化列名（根据实际返回的列数）
                if len(df.columns) == 7:
                    df.columns = ['date', 'open', 'close', 'high', 'low', 'volume', 'amount']
                else:
                    # 适应不同的列数
                    df.columns = df.columns[:len(df.columns)]
                
                df['date'] = pd.to_datetime(df['date'])
                df['symbol'] = symbol
                df = df.set_index('date').sort_index()
                
                file_path = os.path.join(DATA_PATH, 'index', f"{symbol}.csv")
                df.to_csv(file_path)
                print(f"✅ 成功下载 {index_info['name']} ({symbol}) 数据，共 {len(df)} 条记录")
                success_count += 1
            else:
                print(f"⚠️  {index_info['name']} ({symbol}) 数据为空")
                
            # 避免请求过快
            time.sleep(0.5)
                
        except Exception as e:
            print(f"❌ 下载 {index_info['name']} ({symbol}) 失败: {e}")
    
    return success_count

def download_etf_data():
    """下载主要ETF数据"""
    print("\n📊 开始下载ETF数据...")
    
    etf_list = [
        {'code': '510300', 'exchange': 'SH', 'name': '沪深300ETF'},
        {'code': '510500', 'exchange': 'SH', 'name': '中证500ETF'},
        {'code': '510050', 'exchange': 'SH', 'name': '上证50ETF'},
        {'code': '159915', 'exchange': 'SZ', 'name': '创业板ETF'},
        {'code': '588000', 'exchange': 'SH', 'name': '科创50ETF'},
        {'code': '512880', 'exchange': 'SH', 'name': '证券ETF'}
    ]
    
    success_count = 0
    
    for etf_info in etf_list:
        try:
            symbol = f"{etf_info['code']}.{etf_info['exchange']}"
            
            # 使用股票接口获取ETF数据（ETF也是股票）
            df = ak.stock_zh_a_hist(symbol=etf_info['code'], period="daily", 
                                   start_date=START_DATE, end_date=END_DATE)
            
            if not df.empty:
                # 标准化列名
                if len(df.columns) >= 7:
                    df.columns = ['date', 'open', 'close', 'high', 'low', 'volume', 'amount'] + list(df.columns[7:])[:len(df.columns)-7]
                
                df['date'] = pd.to_datetime(df['date'])
                df['symbol'] = symbol
                df = df.set_index('date').sort_index()
                
                file_path = os.path.join(DATA_PATH, 'etfs', f"{symbol}.csv")
                df.to_csv(file_path)
                print(f"✅ 成功下载 {etf_info['name']} ({symbol}) 数据，共 {len(df)} 条记录")
                success_count += 1
            else:
                print(f"⚠️  {etf_info['name']} ({symbol}) 数据为空")
                
            # 避免请求过快
            time.sleep(0.5)
                
        except Exception as e:
            print(f"❌ 下载 {etf_info['name']} ({symbol}) 失败: {e}")
    
    return success_count

def download_stock_data():
    """下载主要股票数据"""
    print("\n📊 开始下载股票数据...")
    
    stock_list = [
        {'code': '600519', 'exchange': 'SH', 'name': '贵州茅台'},
        {'code': '000858', 'exchange': 'SZ', 'name': '五粮液'},
        {'code': '601318', 'exchange': 'SH', 'name': '中国平安'},
        {'code': '600036', 'exchange': 'SH', 'name': '招商银行'},
        {'code': '000001', 'exchange': 'SZ', 'name': '平安银行'}
    ]
    
    success_count = 0
    
    for stock_info in stock_list:
        try:
            symbol = f"{stock_info['code']}.{stock_info['exchange']}"
            
            df = ak.stock_zh_a_hist(symbol=stock_info['code'], period="daily", 
                                   start_date=START_DATE, end_date=END_DATE)
            
            if not df.empty:
                # 标准化列名
                if len(df.columns) >= 7:
                    df.columns = ['date', 'open', 'close', 'high', 'low', 'volume', 'amount'] + list(df.columns[7:])[:len(df.columns)-7]
                
                df['date'] = pd.to_datetime(df['date'])
                df['symbol'] = symbol
                df = df.set_index('date').sort_index()
                
                file_path = os.path.join(DATA_PATH, 'stocks', f"{symbol}.csv")
                df.to_csv(file_path)
                print(f"✅ 成功下载 {stock_info['name']} ({symbol}) 数据，共 {len(df)} 条记录")
                success_count += 1
            else:
                print(f"⚠️  {stock_info['name']} ({symbol}) 数据为空")
                
            # 避免请求过快
            time.sleep(0.5)
                
        except Exception as e:
            print(f"❌ 下载 {stock_info['name']} ({symbol}) 失败: {e}")
    
    return success_count

def create_sample_data():
    """创建样本数据（用于测试）"""
    print("\n🎯 创建样本数据用于回测...")
    
    # 创建简单的指数数据样本
    dates = pd.date_range(start=START_DATE, end=END_DATE, freq='D')
    
    # 上证指数样本数据
    index_data = {
        '000001.SH': {
            'name': '上证指数',
            'start_price': 3000,
            'volatility': 0.015
        },
        '000300.SH': {
            'name': '沪深300',
            'start_price': 4000,
            'volatility': 0.012
        },
        '399006.SZ': {
            'name': '创业板指',
            'start_price': 2500,
            'volatility': 0.02
        }
    }
    
    for symbol, info in index_data.items():
        try:
            # 生成模拟数据
            import numpy as np
            np.random.seed(42)  # 固定随机种子保证可重复性
            returns = np.random.normal(0.0005, info['volatility'], len(dates))
            prices = info['start_price'] * np.exp(np.cumsum(returns))
            
            df = pd.DataFrame({
                'date': dates,
                'open': prices * (1 + np.random.normal(0, 0.002, len(dates))),
                'close': prices,
                'high': prices * (1 + np.abs(np.random.normal(0, 0.005, len(dates)))),
                'low': prices * (1 - np.abs(np.random.normal(0, 0.005, len(dates)))),
                'volume': np.random.randint(1000000, 5000000, len(dates)),
                'amount': np.random.randint(50000000, 200000000, len(dates))
            })
            
            df['date'] = pd.to_datetime(df['date'])
            df['symbol'] = symbol
            df = df.set_index('date').sort_index()
            
            file_path = os.path.join(DATA_PATH, 'index', f"{symbol}.csv")
            df.to_csv(file_path)
            print(f"✅ 创建 {info['name']} ({symbol}) 样本数据，共 {len(df)} 条记录")
            
        except Exception as e:
            print(f"❌ 创建 {info['name']} 样本数据失败: {e}")

def generate_summary():
    """生成数据摘要"""
    print("\n📄 生成数据摘要...")
    
    summary = {
        'download_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'data_range': f"{START_DATE} 至 {END_DATE}",
        'data_path': DATA_PATH
    }
    
    # 统计文件数量
    for data_type in ['stocks', 'etfs', 'index']:
        path = os.path.join(DATA_PATH, data_type)
        if os.path.exists(path):
            files = [f for f in os.listdir(path) if f.endswith('.csv')]
            summary[f'{data_type}_count'] = len(files)
        else:
            summary[f'{data_type}_count'] = 0
    
    # 保存摘要
    summary_file = os.path.join(DATA_PATH, 'data_summary.txt')
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("A股数据下载摘要\n")
        f.write("=" * 50 + "\n")
        for key, value in summary.items():
            f.write(f"{key}: {value}\n")
    
    print(f"✅ 数据摘要已保存至: {summary_file}")
    
    # 显示摘要
    print("\n📊 数据下载统计:")
    print(f"   股票数据: {summary.get('stocks_count', 0)} 个文件")
    print(f"   ETF数据: {summary.get('etfs_count', 0)} 个文件")
    print(f"   指数数据: {summary.get('index_count', 0)} 个文件")
    print(f"   数据路径: {DATA_PATH}")

def main():
    """主函数"""
    print("🚀 稳定版A股数据下载工具")
    print("=" * 60)
    print(f"数据范围: {START_DATE} 至 {END_DATE}")
    
    # 创建数据目录
    create_data_directories()
    
    # 下载真实数据
    print("\n📥 尝试下载真实数据...")
    index_count = download_index_data()
    etf_count = download_etf_data()
    stock_count = download_stock_data()
    
    # 如果真实数据下载失败，创建样本数据
    if index_count == 0 and etf_count == 0 and stock_count == 0:
        print("\n⚠️  真实数据下载失败，创建样本数据用于演示...")
        try:
            import numpy as np
            create_sample_data()
        except ImportError:
            print("❌ 需要numpy库来创建样本数据")
    
    # 生成摘要
    generate_summary()
    
    print("\n" + "=" * 60)
    print("🎯 数据准备完成!")
    print(f"✅ 成功下载/创建指数: {index_count} 个")
    print(f"✅ 成功下载/创建ETF: {etf_count} 个")
    print(f"✅ 成功下载/创建股票: {stock_count} 个")
    print("\n💡 数据已保存到本地，可用于回测分析")
    print("\n🚀 下一步操作:")
    print("   python run.py --mode dca_backtest     # 运行定投回测")
    print("   python simple_dca_test.py            # 运行简化回测")

if __name__ == "__main__":
    main()