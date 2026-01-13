#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版A股数据下载脚本
下载主要指数和部分ETF数据用于回测
"""

import os
import sys
import pandas as pd
import akshare as ak
from datetime import datetime
import logging

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
    
    index_symbols = [
        ('000001', 'SH', '上证指数'),
        ('000300', 'SH', '沪深300'),
        ('000905', 'SH', '中证500'),
        ('399001', 'SZ', '深证成指'),
        ('399006', 'SZ', '创业板指'),
        ('000688', 'SH', '科创50')
    ]
    
    success_count = 0
    
    for code, exchange, name in index_symbols:
        try:
            symbol = f"{code}.{exchange}"
            df = ak.index_zh_a_hist(symbol=code, period="daily", 
                                   start_date=START_DATE, end_date=END_DATE)
            
            if not df.empty:
                df.columns = ['date', 'open', 'close', 'high', 'low', 'volume', 'amount']
                df['date'] = pd.to_datetime(df['date'])
                df['symbol'] = symbol
                df = df.set_index('date').sort_index()
                
                file_path = os.path.join(DATA_PATH, 'index', f"{symbol}.csv")
                df.to_csv(file_path)
                print(f"✅ 成功下载 {name} ({symbol}) 数据，共 {len(df)} 条记录")
                success_count += 1
            else:
                print(f"⚠️  {name} ({symbol}) 数据为空")
                
        except Exception as e:
            print(f"❌ 下载 {name} ({symbol}) 失败: {e}")
    
    return success_count

def download_etf_data():
    """下载主要ETF数据"""
    print("\n📊 开始下载ETF数据...")
    
    # 主要ETF列表
    etf_symbols = [
        ('510300', 'SH', '沪深300ETF'),
        ('510500', 'SH', '中证500ETF'),
        ('510050', 'SH', '上证50ETF'),
        ('159915', 'SZ', '创业板ETF'),
        ('588000', 'SH', '科创50ETF'),
        ('512880', 'SH', '证券ETF'),
        ('512100', 'SH', '中证1000ETF'),
        ('159919', 'SZ', '沪深300ETF'),
        ('159928', 'SZ', '消费ETF'),
        ('512690', 'SH', '酒ETF')
    ]
    
    success_count = 0
    
    for code, exchange, name in etf_symbols:
        try:
            symbol = f"{code}.{exchange}"
            # 尝试使用股票接口获取ETF数据
            df = ak.stock_zh_a_hist(symbol=code, period="daily", 
                                   start_date=START_DATE, end_date=END_DATE, 
                                   adjust="qfq")
            
            if not df.empty:
                df.columns = ['date', 'open', 'close', 'high', 'low', 'volume', 'amount', 'amplitude', 
                             'change_percent', 'change_amount', 'turnover']
                df['date'] = pd.to_datetime(df['date'])
                df['symbol'] = symbol
                df = df.set_index('date').sort_index()
                
                file_path = os.path.join(DATA_PATH, 'etfs', f"{symbol}.csv")
                df.to_csv(file_path)
                print(f"✅ 成功下载 {name} ({symbol}) 数据，共 {len(df)} 条记录")
                success_count += 1
            else:
                print(f"⚠️  {name} ({symbol}) 数据为空")
                
        except Exception as e:
            print(f"❌ 下载 {name} ({symbol}) 失败: {e}")
    
    return success_count

def download_stock_data():
    """下载主要股票数据"""
    print("\n📊 开始下载股票数据...")
    
    # 主要股票列表（代表性股票）
    stock_symbols = [
        ('600519', 'SH', '贵州茅台'),
        ('000858', 'SZ', '五粮液'),
        ('601318', 'SH', '中国平安'),
        ('600036', 'SH', '招商银行'),
        ('000001', 'SZ', '平安银行'),
        ('601166', 'SH', '兴业银行'),
        ('600276', 'SH', '恒瑞医药'),
        ('000333', 'SZ', '美的集团'),
        ('000651', 'SZ', '格力电器'),
        ('002415', 'SZ', '海康威视')
    ]
    
    success_count = 0
    
    for code, exchange, name in stock_symbols:
        try:
            symbol = f"{code}.{exchange}"
            df = ak.stock_zh_a_hist(symbol=code, period="daily", 
                                   start_date=START_DATE, end_date=END_DATE, 
                                   adjust="qfq")
            
            if not df.empty:
                df.columns = ['date', 'open', 'close', 'high', 'low', 'volume', 'amount', 'amplitude', 
                             'change_percent', 'change_amount', 'turnover']
                df['date'] = pd.to_datetime(df['date'])
                df['symbol'] = symbol
                df = df.set_index('date').sort_index()
                
                file_path = os.path.join(DATA_PATH, 'stocks', f"{symbol}.csv")
                df.to_csv(file_path)
                print(f"✅ 成功下载 {name} ({symbol}) 数据，共 {len(df)} 条记录")
                success_count += 1
            else:
                print(f"⚠️  {name} ({symbol}) 数据为空")
                
        except Exception as e:
            print(f"❌ 下载 {name} ({symbol}) 失败: {e}")
    
    return success_count

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
    print("🚀 简化版A股数据下载工具")
    print("=" * 60)
    print(f"数据范围: {START_DATE} 至 {END_DATE}")
    
    # 创建数据目录
    create_data_directories()
    
    # 下载数据
    index_count = download_index_data()
    etf_count = download_etf_data()
    stock_count = download_stock_data()
    
    # 生成摘要
    generate_summary()
    
    print("\n" + "=" * 60)
    print("🎯 数据下载完成!")
    print(f"✅ 成功下载指数: {index_count} 个")
    print(f"✅ 成功下载ETF: {etf_count} 个")
    print(f"✅ 成功下载股票: {stock_count} 个")
    print("\n💡 数据已保存到本地，可用于回测分析")

if __name__ == "__main__":
    main()